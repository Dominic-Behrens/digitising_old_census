"""
Build a cross-document table index dataset from detected 1911 contents pages.

Inputs:
- data/intermediate/page_inventory/abs_1911_contents_detection_summary.csv
- data/intermediate/page_inventory/abs_1911_contents_detection_pages.csv

Outputs:
- data/intermediate/table_index/abs_1911_table_index_raw.jsonl
- data/intermediate/table_index/abs_1911_table_index.csv
- data/intermediate/table_index/abs_1911_table_index_subentries.csv

The contents pages are first detected by a cheap VLM. This script uses a
stronger VLM only on those contents pages to extract the table list.
"""

from __future__ import annotations

import argparse
import base64
import csv
import datetime as dt
import json
import os
import pathlib
import re
import statistics
import time
import urllib.error
import urllib.request
from typing import Any

import fitz


SUMMARY_PATH = pathlib.Path(
    "data/intermediate/page_inventory/abs_1911_contents_detection_summary.csv"
)
PAGES_PATH = pathlib.Path(
    "data/intermediate/page_inventory/abs_1911_contents_detection_pages.csv"
)
OUT_DIR = pathlib.Path("data/intermediate/table_index")
DEFAULT_MODEL = "google/gemini-3.5-flash"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


SYSTEM_PROMPT = """You extract table index metadata from historical Australian census PDFs.
Use only the visible contents/index pages supplied. Return only valid JSON.
Do not invent tables, page numbers, or subentries."""


USER_PROMPT_TEMPLATE = """Document metadata:
- doc_id: {doc_id}
- title: {title}
- file_name: {file_name}
- detected_contents_page_indexes: {contents_page_indexes}

The images are the detected contents/index pages for this document.

Extract the document's table list. Return exactly this JSON object:
{{
  "doc_title": string or null,
  "is_table_index_document": true or false,
  "tables": [
    {{
      "table_number": string,
      "table_title": string,
      "start_printed_page": integer or null,
      "topic": string or null,
      "geography": string or null,
      "part_or_section": string or null,
      "subentries": [
        {{
          "label": string,
          "printed_page": integer or null
        }}
      ],
      "warnings": [string]
    }}
  ],
  "warnings": [string]
}}

Rules:
- Extract numbered tables from the contents/index pages.
- If the page is itself a detailed table index publication, still extract the
  numbered table entries visible in it.
- table_number should preserve the visible table number, usually digits.
- start_printed_page is the page reference shown in the contents, not the PDF
  page number.
- If a table has roman numeral, state, territory, or section subentries with
  separate page references, include them in subentries.
- If a table appears across line breaks, combine the title into one readable
  string.
- If there is no numbered table list, return an empty tables array and explain
  why in warnings.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build ABS 1911 table index dataset.")
    parser.add_argument("--summary", type=pathlib.Path, default=SUMMARY_PATH)
    parser.add_argument("--pages", type=pathlib.Path, default=PAGES_PATH)
    parser.add_argument("--output-dir", type=pathlib.Path, default=OUT_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--dpi", type=int, default=190)
    parser.add_argument("--jpeg-quality", type=int, default=86)
    parser.add_argument("--max-tokens", type=int, default=16000)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument("--no-opencode-auth", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    return parser.parse_args()


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
        raise RuntimeError(f"OpenCode auth was not found at {auth_path}.")
    with auth_path.open("r", encoding="utf-8") as file:
        auth = json.load(file)
    openrouter_auth = auth.get("openrouter") if isinstance(auth, dict) else None
    if not isinstance(openrouter_auth, dict) or not openrouter_auth.get("key"):
        raise RuntimeError("OpenCode auth has no OpenRouter key.")
    return str(openrouter_auth["key"]), "OpenCode OpenRouter credential"


def read_csv(path: pathlib.Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def parse_page_indexes(value: str) -> list[int]:
    if not value.strip():
        return []
    return [int(part.strip()) for part in value.split("|") if part.strip()]


def numeric_or_none(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def clean_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def render_page_jpeg(pdf_path: pathlib.Path, page_index: int, dpi: int, quality: int) -> bytes:
    doc = fitz.open(pdf_path)
    try:
        page = doc[page_index]
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False)
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
    doc: dict[str, Any],
    include_response_format: bool,
) -> dict[str, Any]:
    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": USER_PROMPT_TEMPLATE.format(
                doc_id=doc["doc_id"],
                title=doc["title"],
                file_name=doc["file_name"],
                contents_page_indexes=" | ".join(str(p) for p in doc["contents_pages"]),
            ),
        }
    ]
    for page_index in doc["contents_pages"]:
        image_bytes = render_page_jpeg(
            pathlib.Path(doc["local_path"]), page_index, args.dpi, args.jpeg_quality
        )
        image_b64 = base64.b64encode(image_bytes).decode("ascii")
        content.append({"type": "text", "text": f"PDF page index {page_index}"})
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
            }
        )

    payload: dict[str, Any] = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        "temperature": 0,
        "max_tokens": args.max_tokens,
        "reasoning": {"effort": "minimal"},
    }
    if include_response_format:
        payload["response_format"] = {"type": "json_object"}
    return payload


def post_openrouter(api_key: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/",
            "X-Title": "digitising_old_census table index builder",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def extract_doc(args: argparse.Namespace, api_key: str, doc: dict[str, Any]) -> dict[str, Any]:
    started_at = dt.datetime.now(dt.UTC).isoformat()
    include_response_format = True
    last_error = None
    for attempt in range(1, args.retries + 1):
        try:
            payload = build_payload(args, doc, include_response_format)
            response = post_openrouter(api_key, payload, args.timeout)
            content = response["choices"][0]["message"].get("content", "")
            parsed = extract_json_object(content)
            return {
                **doc,
                "model": args.model,
                "started_at": started_at,
                "finished_at": dt.datetime.now(dt.UTC).isoformat(),
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
        except Exception as error:  # noqa: BLE001 - document-level audit record.
            last_error = repr(error)

        if attempt < args.retries:
            time.sleep(min(2**attempt, 30))

    return {
        **doc,
        "model": args.model,
        "started_at": started_at,
        "finished_at": dt.datetime.now(dt.UTC).isoformat(),
        "parsed": None,
        "content": None,
        "usage": None,
        "provider": None,
        "error": last_error,
    }


def read_existing(raw_path: pathlib.Path) -> dict[str, dict[str, Any]]:
    if not raw_path.exists():
        return {}
    records = {}
    with raw_path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            record = json.loads(line)
            records[record["doc_id"]] = record
    return records


def append_jsonl(path: pathlib.Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def infer_printed_page_offset(doc_id: str, pages_rows: list[dict[str, str]]) -> int | None:
    offsets = []
    for row in pages_rows:
        if row["doc_id"] != doc_id:
            continue
        printed_page = numeric_or_none(row.get("printed_page"))
        page_index = numeric_or_none(row.get("page_index"))
        if printed_page is not None and page_index is not None:
            offsets.append(printed_page - page_index)
    if not offsets:
        return None
    return int(statistics.median(offsets))


def build_docs(summary_rows: list[dict[str, str]], pages_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    docs = []
    for row in summary_rows:
        contents_pages = parse_page_indexes(row.get("contents_page_indexes", ""))
        if not contents_pages:
            continue
        docs.append(
            {
                "doc_id": row["doc_id"],
                "file_name": row["file_name"],
                "title": row["title"],
                "local_path": row["local_path"],
                "page_count": int(row["page_count"]),
                "contents_pages": contents_pages,
                "printed_page_offset": infer_printed_page_offset(row["doc_id"], pages_rows),
            }
        )
    return docs


def estimate_page_index(printed_page: Any, offset: int | None) -> int | None:
    printed = numeric_or_none(printed_page)
    if printed is None or offset is None:
        return None
    return printed - offset


def table_sort_key(value: Any) -> tuple[int, str]:
    text = str(value or "")
    match = re.search(r"\d+", text)
    if match:
        return (int(match.group()), text)
    return (10**9, text)


def write_table_csv(records: list[dict[str, Any]], path: pathlib.Path) -> None:
    fields = [
        "doc_id",
        "file_name",
        "title",
        "local_path",
        "page_count",
        "contents_page_indexes",
        "model",
        "is_table_index_document",
        "table_number",
        "table_title",
        "start_printed_page",
        "start_page_index_estimate",
        "topic",
        "geography",
        "part_or_section",
        "subentry_count",
        "doc_warnings",
        "table_warnings",
        "error",
    ]
    rows = []
    for record in records:
        parsed = record.get("parsed") or {}
        doc_warnings = " | ".join(str(w) for w in parsed.get("warnings") or [])
        for table in parsed.get("tables") or []:
            if not isinstance(table, dict):
                continue
            rows.append(
                {
                    "doc_id": record["doc_id"],
                    "file_name": record["file_name"],
                    "title": record["title"],
                    "local_path": record["local_path"],
                    "page_count": record["page_count"],
                    "contents_page_indexes": " | ".join(
                        str(p) for p in record["contents_pages"]
                    ),
                    "model": record["model"],
                    "is_table_index_document": parsed.get("is_table_index_document"),
                    "table_number": clean_text(table.get("table_number")),
                    "table_title": clean_text(table.get("table_title")),
                    "start_printed_page": table.get("start_printed_page"),
                    "start_page_index_estimate": estimate_page_index(
                        table.get("start_printed_page"), record.get("printed_page_offset")
                    ),
                    "topic": clean_text(table.get("topic")),
                    "geography": clean_text(table.get("geography")),
                    "part_or_section": clean_text(table.get("part_or_section")),
                    "subentry_count": len(table.get("subentries") or []),
                    "doc_warnings": doc_warnings,
                    "table_warnings": " | ".join(
                        str(w) for w in table.get("warnings") or []
                    ),
                    "error": record.get("error"),
                }
            )
    rows.sort(key=lambda row: (row["doc_id"], table_sort_key(row["table_number"])))
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_numbered_table_csv(table_path: pathlib.Path, numbered_path: pathlib.Path) -> None:
    with table_path.open("r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
        fields = rows[0].keys() if rows else []
    numbered = [
        row for row in rows if re.fullmatch(r"\d+", clean_text(row.get("table_number")))
    ]
    with numbered_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(numbered)


def write_subentry_csv(records: list[dict[str, Any]], path: pathlib.Path) -> None:
    fields = [
        "doc_id",
        "file_name",
        "table_number",
        "table_title",
        "subentry_index",
        "subentry_label",
        "subentry_printed_page",
        "subentry_page_index_estimate",
    ]
    rows = []
    for record in records:
        parsed = record.get("parsed") or {}
        for table in parsed.get("tables") or []:
            if not isinstance(table, dict):
                continue
            for subentry_index, subentry in enumerate(table.get("subentries") or [], start=1):
                if not isinstance(subentry, dict):
                    continue
                rows.append(
                    {
                        "doc_id": record["doc_id"],
                        "file_name": record["file_name"],
                        "table_number": clean_text(table.get("table_number")),
                        "table_title": clean_text(table.get("table_title")),
                        "subentry_index": subentry_index,
                        "subentry_label": clean_text(subentry.get("label")),
                        "subentry_printed_page": subentry.get("printed_page"),
                        "subentry_page_index_estimate": estimate_page_index(
                            subentry.get("printed_page"), record.get("printed_page_offset")
                        ),
                    }
                )
    rows.sort(key=lambda row: (row["doc_id"], table_sort_key(row["table_number"]), row["subentry_index"]))
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def numeric_table_numbers(tables: list[dict[str, Any]]) -> list[int]:
    values = []
    for table in tables:
        number = clean_text(table.get("table_number"))
        if re.fullmatch(r"\d+", number):
            values.append(int(number))
    return values


def write_summary_csv(records: list[dict[str, Any]], path: pathlib.Path) -> None:
    fields = [
        "doc_id",
        "file_name",
        "title",
        "local_path",
        "page_count",
        "contents_page_indexes",
        "printed_page_offset",
        "model",
        "table_count",
        "numeric_table_count",
        "numeric_table_min",
        "numeric_table_max",
        "missing_numeric_table_numbers",
        "non_numeric_table_numbers",
        "subentry_count",
        "is_table_index_document",
        "doc_warnings",
        "cost",
        "error",
        "needs_review",
    ]
    rows = []
    for record in records:
        parsed = record.get("parsed") or {}
        tables = [table for table in parsed.get("tables") or [] if isinstance(table, dict)]
        numeric = numeric_table_numbers(tables)
        numeric_set = set(numeric)
        if numeric:
            missing = [
                str(value)
                for value in range(min(numeric), max(numeric) + 1)
                if value not in numeric_set
            ]
            numeric_min = min(numeric)
            numeric_max = max(numeric)
        else:
            missing = []
            numeric_min = ""
            numeric_max = ""
        non_numeric = [
            clean_text(table.get("table_number"))
            for table in tables
            if not re.fullmatch(r"\d+", clean_text(table.get("table_number")))
        ]
        subentry_count = sum(len(table.get("subentries") or []) for table in tables)
        error = record.get("error") or ""
        rows.append(
            {
                "doc_id": record["doc_id"],
                "file_name": record["file_name"],
                "title": record["title"],
                "local_path": record["local_path"],
                "page_count": record["page_count"],
                "contents_page_indexes": " | ".join(
                    str(p) for p in record["contents_pages"]
                ),
                "printed_page_offset": record.get("printed_page_offset"),
                "model": record["model"],
                "table_count": len(tables),
                "numeric_table_count": len(numeric),
                "numeric_table_min": numeric_min,
                "numeric_table_max": numeric_max,
                "missing_numeric_table_numbers": " | ".join(missing),
                "non_numeric_table_numbers": " | ".join(non_numeric),
                "subentry_count": subentry_count,
                "is_table_index_document": parsed.get("is_table_index_document"),
                "doc_warnings": " | ".join(str(w) for w in parsed.get("warnings") or []),
                "cost": (record.get("usage") or {}).get("cost"),
                "error": error,
                "needs_review": bool(error or missing),
            }
        )
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: row["file_name"]))


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.output_dir / "abs_1911_table_index_raw.jsonl"
    table_path = args.output_dir / "abs_1911_table_index.csv"
    numbered_table_path = args.output_dir / "abs_1911_numbered_table_index.csv"
    subentry_path = args.output_dir / "abs_1911_table_index_subentries.csv"
    summary_path = args.output_dir / "abs_1911_table_index_summary.csv"

    summary_rows = read_csv(args.summary)
    pages_rows = read_csv(args.pages)
    docs = build_docs(summary_rows, pages_rows)
    existing = {} if args.no_resume else read_existing(raw_path)
    todo = [doc for doc in docs if doc["doc_id"] not in existing or existing[doc["doc_id"]].get("error")]
    api_key, api_key_source = get_api_key(args)

    print(f"Documents with contents pages: {len(docs)}")
    print(f"Documents to extract: {len(todo)}")
    print(f"Model: {args.model}")
    print(f"API key source: {api_key_source}")
    print(f"Raw output: {raw_path}")

    for doc in todo:
        record = extract_doc(args, api_key, doc)
        append_jsonl(raw_path, record)
        status = "failed" if record.get("error") else "ok"
        table_count = len((record.get("parsed") or {}).get("tables") or [])
        print(f"{doc['doc_id']} {status} tables={table_count}")

    records_by_doc = read_existing(raw_path)
    records = [records_by_doc[doc["doc_id"]] for doc in docs if doc["doc_id"] in records_by_doc]
    write_table_csv(records, table_path)
    write_numbered_table_csv(table_path, numbered_table_path)
    write_subentry_csv(records, subentry_path)
    write_summary_csv(records, summary_path)

    total_cost = sum(
        record.get("usage", {}).get("cost") or 0
        for record in records
        if record.get("usage")
    )
    total_tables = sum(len((record.get("parsed") or {}).get("tables") or []) for record in records)
    failures = sum(1 for record in records if record.get("error"))
    print(f"Extracted records: {len(records)}")
    print(f"Total tables: {total_tables}")
    print(f"Failures: {failures}")
    print(f"Total cost in records: {total_cost:.6f}")
    print(f"Table index: {table_path}")
    print(f"Numbered table index: {numbered_table_path}")
    print(f"Subentries: {subentry_path}")
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()
