"""
Classify each page of a historical census PDF with an OpenRouter vision model.

Outputs:
- data/intermediate/page_inventory/<run_id>_raw.jsonl
- data/intermediate/page_inventory/<run_id>_pages.csv
- data/intermediate/page_inventory/<run_id>_tables.csv

The raw JSONL file is append-only so interrupted runs can be resumed.
"""

from __future__ import annotations

import argparse
import base64
import csv
import datetime as dt
import json
import os
import pathlib
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import fitz


DEFAULT_PDF = pathlib.Path(
    "data/raw/abs_1911_census/1911_census_volume_iii_part_xiii_dwellings.pdf"
)
DEFAULT_MODEL = "qwen/qwen3.5-flash-02-23"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


SYSTEM_PROMPT = """You are building an audit inventory of tables in historical Australian census PDFs.
Classify exactly what is visible on this one page image. Be conservative.
Do not infer a table number or title if it is not visible on the page.
Return only valid JSON. No markdown. No commentary."""


USER_PROMPT_TEMPLATE = """Document metadata:
- doc_id: {doc_id}
- year: {year}
- pdf_page_index: {page_index} (zero-based)
- pdf_page_number: {pdf_page} (one-based)

Task:
Create a page-level inventory record for this page.

Return this JSON object shape exactly:
{{
  "printed_page": string or null,
  "page_type": "table" or "text" or "title_or_front_matter" or "index" or "blank" or "other",
  "has_table": true or false,
  "tables": [
    {{
      "table_number": string or null,
      "table_title": string or null,
      "table_subject": string or null,
      "geography": string or null,
      "is_continuation": true or false or null,
      "continuation_of_table_number": string or null,
      "page_role": "starts" or "continues" or "ends" or "complete_on_page" or "unknown",
      "columns_visible": [string],
      "sections_visible": [string],
      "notes": string or null
    }}
  ],
  "confidence": number from 0 to 1,
  "warnings": [string]
}}

Guidance:
- A page can contain more than one table if one table ends and another starts.
- If the page says a table is continued but the table number is visible, put that number in table_number.
- If only "continued" is visible and the table number is not visible, set table_number to null and describe the continuation in notes.
- Use concise table titles and subjects. Preserve original wording where readable.
- printed_page should be the printed page number on the page, not the PDF index.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify PDF pages with an OpenRouter vision model."
    )
    parser.add_argument("--pdf", type=pathlib.Path, default=DEFAULT_PDF)
    parser.add_argument(
        "--doc-id",
        default="abs_1911_census_volume_iii_part_xiii_dwellings",
    )
    parser.add_argument("--year", default="1911")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=pathlib.Path("data/intermediate/page_inventory"),
    )
    parser.add_argument(
        "--pages",
        default="all",
        help="Page selection such as all, 0, 10-20, or 0,10-20,30.",
    )
    parser.add_argument("--dpi", type=int, default=160)
    parser.add_argument("--jpeg-quality", type=int, default=82)
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--max-tokens", type=int, default=1400)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument(
        "--provider-data-collection",
        choices=["allow", "deny"],
        default=None,
        help="Optional OpenRouter provider data-collection routing preference.",
    )
    parser.add_argument(
        "--api-key-env",
        default="OPENROUTER_API_KEY",
        help="Environment variable containing the OpenRouter API key.",
    )
    parser.add_argument(
        "--no-opencode-auth",
        action="store_true",
        help="Do not fall back to OpenCode's stored OpenRouter credential.",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Output file prefix. Defaults to doc_id plus sanitized model name.",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Re-classify pages even if successful records already exist.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render pages and create output paths without calling OpenRouter.",
    )
    return parser.parse_args()


def sanitize_name(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_").lower()


def parse_pages(selection: str, page_count: int) -> list[int]:
    if selection == "all":
        return list(range(page_count))

    pages: set[int] = set()
    for part in selection.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))

    invalid = [p for p in pages if p < 0 or p >= page_count]
    if invalid:
        raise ValueError(f"Page selection outside document range: {invalid}")
    return sorted(pages)


def render_page_jpeg(pdf_path: pathlib.Path, page_index: int, dpi: int, quality: int) -> bytes:
    doc = fitz.open(pdf_path)
    try:
        page = doc[page_index]
        matrix = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        return pix.tobytes("jpeg", jpg_quality=quality)
    finally:
        doc.close()


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(cleaned[start : end + 1])

    if not isinstance(parsed, dict):
        raise ValueError("Model output was not a JSON object")
    return parsed


def build_payload(
    args: argparse.Namespace,
    page_index: int,
    image_bytes: bytes,
    include_response_format: bool,
) -> dict[str, Any]:
    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    user_prompt = USER_PROMPT_TEMPLATE.format(
        doc_id=args.doc_id,
        year=args.year,
        page_index=page_index,
        pdf_page=page_index + 1,
    )

    payload: dict[str, Any] = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}",
                        },
                    },
                ],
            },
        ],
        "temperature": 0,
        "max_tokens": args.max_tokens,
    }
    if include_response_format:
        payload["response_format"] = {"type": "json_object"}
    if args.provider_data_collection:
        payload["provider"] = {"data_collection": args.provider_data_collection}
    return payload


def post_openrouter(
    api_key: str,
    payload: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    request = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/",
            "X-Title": "digitising_old_census page inventory",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def get_api_key(args: argparse.Namespace) -> tuple[str, str]:
    env_key = os.getenv(args.api_key_env)
    if env_key:
        return env_key, args.api_key_env

    if args.no_opencode_auth:
        raise RuntimeError(
            f"{args.api_key_env} is not set and OpenCode auth fallback is disabled."
        )

    auth_path = pathlib.Path.home() / ".local/share/opencode/auth.json"
    if not auth_path.exists():
        raise RuntimeError(
            f"{args.api_key_env} is not set and OpenCode auth was not found at "
            f"{auth_path}."
        )

    with auth_path.open("r", encoding="utf-8") as file:
        auth = json.load(file)

    openrouter_auth = auth.get("openrouter") if isinstance(auth, dict) else None
    if not isinstance(openrouter_auth, dict) or not openrouter_auth.get("key"):
        raise RuntimeError(
            f"{args.api_key_env} is not set and OpenCode auth has no OpenRouter key."
        )

    return str(openrouter_auth["key"]), "OpenCode OpenRouter credential"


def classify_page(
    args: argparse.Namespace,
    api_key: str,
    page_index: int,
) -> dict[str, Any]:
    started_at = dt.datetime.now(dt.UTC).isoformat()
    image_bytes = render_page_jpeg(args.pdf, page_index, args.dpi, args.jpeg_quality)

    if args.dry_run:
        return {
            "doc_id": args.doc_id,
            "model": args.model,
            "page_index": page_index,
            "pdf_page": page_index + 1,
            "started_at": started_at,
            "finished_at": dt.datetime.now(dt.UTC).isoformat(),
            "dry_run": True,
            "image_bytes": len(image_bytes),
            "parsed": None,
            "content": None,
            "usage": None,
            "error": None,
        }

    last_error = None
    include_response_format = True
    for attempt in range(1, args.retries + 1):
        payload = build_payload(args, page_index, image_bytes, include_response_format)
        try:
            response = post_openrouter(api_key, payload, args.timeout)
            message = response["choices"][0]["message"]
            content = message.get("content", "")
            parsed = extract_json_object(content)
            return {
                "doc_id": args.doc_id,
                "model": args.model,
                "page_index": page_index,
                "pdf_page": page_index + 1,
                "started_at": started_at,
                "finished_at": dt.datetime.now(dt.UTC).isoformat(),
                "dry_run": False,
                "image_bytes": len(image_bytes),
                "parsed": parsed,
                "content": content,
                "usage": response.get("usage"),
                "provider": response.get("provider"),
                "error": None,
            }
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            last_error = f"HTTP {error.code}: {body[:1000]}"
            if error.code in (400, 422) and include_response_format:
                include_response_format = False
                continue
        except Exception as error:  # noqa: BLE001 - record page-level failures.
            last_error = repr(error)

        if attempt < args.retries:
            time.sleep(min(2**attempt, 30))

    return {
        "doc_id": args.doc_id,
        "model": args.model,
        "page_index": page_index,
        "pdf_page": page_index + 1,
        "started_at": started_at,
        "finished_at": dt.datetime.now(dt.UTC).isoformat(),
        "dry_run": False,
        "image_bytes": len(image_bytes),
        "parsed": None,
        "content": None,
        "usage": None,
        "error": last_error,
    }


def read_latest_records(path: pathlib.Path) -> dict[int, dict[str, Any]]:
    if not path.exists():
        return {}

    records: dict[int, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            record = json.loads(line)
            records[int(record["page_index"])] = record
    return records


def successful_pages(records: dict[int, dict[str, Any]]) -> set[int]:
    return {
        page_index
        for page_index, record in records.items()
        if record.get("parsed") is not None and not record.get("error")
    }


def value_join(values: list[Any]) -> str:
    cleaned = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, list):
            cleaned.extend(str(v) for v in value if v is not None)
        else:
            cleaned.append(str(value))
    unique = []
    for value in cleaned:
        value = value.strip()
        if value and value not in unique:
            unique.append(value)
    return " | ".join(unique)


def get_tables(parsed: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not parsed:
        return []
    tables = parsed.get("tables") or []
    return [table for table in tables if isinstance(table, dict)]


def write_page_csv(records: list[dict[str, Any]], path: pathlib.Path) -> None:
    fields = [
        "doc_id",
        "model",
        "page_index",
        "pdf_page",
        "printed_page",
        "page_type",
        "has_table",
        "table_count",
        "table_numbers",
        "table_titles",
        "table_subjects",
        "geographies",
        "page_roles",
        "confidence",
        "warnings",
        "error",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for record in sorted(records, key=lambda r: r["page_index"]):
            parsed = record.get("parsed") or {}
            tables = get_tables(parsed)
            writer.writerow(
                {
                    "doc_id": record.get("doc_id"),
                    "model": record.get("model"),
                    "page_index": record.get("page_index"),
                    "pdf_page": record.get("pdf_page"),
                    "printed_page": parsed.get("printed_page"),
                    "page_type": parsed.get("page_type"),
                    "has_table": parsed.get("has_table"),
                    "table_count": len(tables),
                    "table_numbers": value_join(
                        [
                            table.get("table_number")
                            or table.get("continuation_of_table_number")
                            for table in tables
                        ]
                    ),
                    "table_titles": value_join([table.get("table_title") for table in tables]),
                    "table_subjects": value_join(
                        [table.get("table_subject") for table in tables]
                    ),
                    "geographies": value_join([table.get("geography") for table in tables]),
                    "page_roles": value_join([table.get("page_role") for table in tables]),
                    "confidence": parsed.get("confidence"),
                    "warnings": value_join(parsed.get("warnings") or []),
                    "error": record.get("error"),
                }
            )


def table_key(table: dict[str, Any], active_key: str | None) -> str:
    number = table.get("table_number") or table.get("continuation_of_table_number")
    if number:
        return f"table_{sanitize_name(str(number))}"
    if table.get("is_continuation") and active_key:
        return active_key
    title = table.get("table_title") or table.get("table_subject")
    if title:
        return f"title_{sanitize_name(str(title))[:80]}"
    return "unknown_table"


def build_table_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    active_key: str | None = None

    for record in sorted(records, key=lambda r: r["page_index"]):
        parsed = record.get("parsed") or {}
        tables = get_tables(parsed)
        if not tables:
            continue

        for table in tables:
            key = table_key(table, active_key)
            grouped.setdefault(key, []).append(
                {
                    "record": record,
                    "parsed": parsed,
                    "table": table,
                }
            )
            if key != "unknown_table":
                active_key = key

    rows = []
    for key, entries in sorted(
        grouped.items(), key=lambda item: min(e["record"]["page_index"] for e in item[1])
    ):
        page_indexes = [entry["record"]["page_index"] for entry in entries]
        pdf_pages = [entry["record"]["pdf_page"] for entry in entries]
        confidences = [
            entry["parsed"].get("confidence")
            for entry in entries
            if isinstance(entry["parsed"].get("confidence"), (int, float))
        ]
        table_values = [entry["table"] for entry in entries]
        parsed_values = [entry["parsed"] for entry in entries]

        rows.append(
            {
                "doc_id": entries[0]["record"].get("doc_id"),
                "model": entries[0]["record"].get("model"),
                "table_key": key,
                "table_numbers": value_join(
                    [
                        table.get("table_number")
                        or table.get("continuation_of_table_number")
                        for table in table_values
                    ]
                ),
                "table_titles": value_join(
                    [table.get("table_title") for table in table_values]
                ),
                "table_subjects": value_join(
                    [table.get("table_subject") for table in table_values]
                ),
                "geographies": value_join(
                    [table.get("geography") for table in table_values]
                ),
                "start_page_index": min(page_indexes),
                "end_page_index": max(page_indexes),
                "pdf_pages": value_join(pdf_pages),
                "printed_pages": value_join(
                    [parsed.get("printed_page") for parsed in parsed_values]
                ),
                "page_count": len(set(page_indexes)),
                "page_roles": value_join([table.get("page_role") for table in table_values]),
                "confidence_min": min(confidences) if confidences else "",
                "confidence_mean": statistics.mean(confidences) if confidences else "",
                "notes": value_join([table.get("notes") for table in table_values]),
                "warnings": value_join(
                    [parsed.get("warnings") for parsed in parsed_values]
                ),
            }
        )
    return rows


def write_table_csv(records: list[dict[str, Any]], path: pathlib.Path) -> None:
    fields = [
        "doc_id",
        "model",
        "table_key",
        "table_numbers",
        "table_titles",
        "table_subjects",
        "geographies",
        "start_page_index",
        "end_page_index",
        "pdf_pages",
        "printed_pages",
        "page_count",
        "page_roles",
        "confidence_min",
        "confidence_mean",
        "notes",
        "warnings",
    ]
    rows = build_table_rows(records)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def append_jsonl(path: pathlib.Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    if not args.pdf.exists():
        raise FileNotFoundError(args.pdf)

    run_id = args.run_id or f"{sanitize_name(args.doc_id)}_{sanitize_name(args.model)}"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.output_dir / f"{run_id}_raw.jsonl"
    page_path = args.output_dir / f"{run_id}_pages.csv"
    table_path = args.output_dir / f"{run_id}_tables.csv"

    doc = fitz.open(args.pdf)
    try:
        page_count = doc.page_count
    finally:
        doc.close()

    pages = parse_pages(args.pages, page_count)
    existing = read_latest_records(raw_path)
    done = set() if args.no_resume else successful_pages(existing)
    todo = [page for page in pages if page not in done]

    if args.dry_run:
        api_key = "dry-run"
        api_key_source = "dry-run"
    else:
        api_key, api_key_source = get_api_key(args)

    print(f"PDF: {args.pdf}")
    print(f"Pages in document: {page_count}")
    print(f"Selected pages: {len(pages)}")
    print(f"Already classified: {len(done & set(pages))}")
    print(f"Pages to classify: {len(todo)}")
    print(f"Model: {args.model}")
    print(f"API key source: {api_key_source}")
    print(f"Raw output: {raw_path}")

    failures = 0
    if todo:
        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            future_to_page = {
                executor.submit(classify_page, args, api_key, page): page for page in todo
            }
            for future in as_completed(future_to_page):
                page = future_to_page[future]
                record = future.result()
                append_jsonl(raw_path, record)
                status = "ok" if not record.get("error") else "failed"
                if status == "failed":
                    failures += 1
                print(f"page {page:03d} ({page + 1:03d}) {status}")

    latest = read_latest_records(raw_path)
    selected_records = [latest[page] for page in pages if page in latest]
    write_page_csv(selected_records, page_path)
    write_table_csv(selected_records, table_path)

    successful = sum(
        1 for record in selected_records if record.get("parsed") is not None and not record.get("error")
    )
    print(f"Successful classified pages: {successful}/{len(pages)}")
    print(f"Failures this run: {failures}")
    print(f"Page inventory: {page_path}")
    print(f"Table inventory: {table_path}")


if __name__ == "__main__":
    main()
