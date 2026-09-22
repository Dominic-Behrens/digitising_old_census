"""
Detect contents/index pages in the first pages of downloaded 1911 census PDFs.

Inputs:
- data/raw/abs_1911_census/abs_1911_download_manifest.csv

Outputs:
- data/intermediate/page_inventory/abs_1911_contents_detection_raw.jsonl
- data/intermediate/page_inventory/abs_1911_contents_detection_pages.csv
- data/intermediate/page_inventory/abs_1911_contents_detection_summary.csv
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import fitz


DEFAULT_MANIFEST = pathlib.Path("data/raw/abs_1911_census/abs_1911_download_manifest.csv")
DEFAULT_MODEL = "google/gemini-3.1-flash-lite"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


SYSTEM_PROMPT = """You classify pages from historical Australian census PDFs.
Classify only the page type. Do not transcribe the page. Return only valid JSON."""


USER_PROMPT_TEMPLATE = """Document:
- title: {title}
- file_name: {file_name}
- page_index: {page_index} (zero-based)
- pdf_page: {pdf_page} (one-based)

Classify this page.

Return exactly this JSON object:
{{
  "printed_page": string or null,
  "page_type": "title_page" or "contents" or "index" or "table" or "text" or "blank" or "other",
  "is_contents_or_index": true or false,
  "contains_numbered_table_list": true or false,
  "contains_page_reference_column": true or false,
  "is_table_page": true or false,
  "likely_continues_contents": true or false,
  "confidence": number from 0 to 1,
  "reason": string,
  "warnings": [string]
}}

Definitions:
- contents/index pages list tables, sections, headings, or page references.
- table pages contain statistical data tables, not just a list of contents.
- If a page is a contents page for a separate index publication, still mark it
  as contents or index.
- Be conservative: if the page has a table of contents layout with No./Page or
  repeated page references, set is_contents_or_index to true.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect contents pages with OpenRouter.")
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--scan-pages", type=int, default=10)
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--jpeg-quality", type=int, default=80)
    parser.add_argument("--max-workers", type=int, default=5)
    parser.add_argument("--max-tokens", type=int, default=600)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument("--no-opencode-auth", action="store_true")
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=pathlib.Path("data/intermediate/page_inventory"),
    )
    parser.add_argument("--run-id", default="abs_1911_contents_detection")
    parser.add_argument("--no-resume", action="store_true")
    return parser.parse_args()


def slugify(value: str) -> str:
    value = pathlib.Path(value).stem.lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


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


def read_manifest(path: pathlib.Path) -> list[dict[str, str]]:
    rows = []
    with path.open("r", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            if row.get("excluded") == "False" and row.get("local_path"):
                rows.append(row)
    return rows


def render_page_jpeg(pdf_path: pathlib.Path, page_index: int, dpi: int, quality: int) -> bytes:
    doc = fitz.open(pdf_path)
    try:
        page = doc[page_index]
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False)
        return pix.tobytes("jpeg", jpg_quality=quality)
    finally:
        doc.close()


def page_count(pdf_path: pathlib.Path) -> int:
    doc = fitz.open(pdf_path)
    try:
        return doc.page_count
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
    task: dict[str, Any],
    image_bytes: bytes,
    include_response_format: bool,
) -> dict[str, Any]:
    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    prompt = USER_PROMPT_TEMPLATE.format(
        title=task["title"],
        file_name=task["file_name"],
        page_index=task["page_index"],
        pdf_page=task["page_index"] + 1,
    )
    payload: dict[str, Any] = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
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
    return payload


def post_openrouter(api_key: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/",
            "X-Title": "digitising_old_census contents detector",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def classify_page(
    args: argparse.Namespace,
    api_key: str,
    task: dict[str, Any],
) -> dict[str, Any]:
    started_at = dt.datetime.now(dt.UTC).isoformat()
    image_bytes = render_page_jpeg(
        task["pdf_path"], task["page_index"], args.dpi, args.jpeg_quality
    )
    last_error = None
    include_response_format = True
    for attempt in range(1, args.retries + 1):
        try:
            payload = build_payload(args, task, image_bytes, include_response_format)
            response = post_openrouter(api_key, payload, args.timeout)
            content = response["choices"][0]["message"].get("content", "")
            parsed = extract_json_object(content)
            return {
                **{k: v for k, v in task.items() if k != "pdf_path"},
                "model": args.model,
                "started_at": started_at,
                "finished_at": dt.datetime.now(dt.UTC).isoformat(),
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
        except Exception as error:  # noqa: BLE001 - page-level audit record.
            last_error = repr(error)

        if attempt < args.retries:
            time.sleep(min(2**attempt, 30))

    return {
        **{k: v for k, v in task.items() if k != "pdf_path"},
        "model": args.model,
        "started_at": started_at,
        "finished_at": dt.datetime.now(dt.UTC).isoformat(),
        "image_bytes": len(image_bytes),
        "parsed": None,
        "content": None,
        "usage": None,
        "provider": None,
        "error": last_error,
    }


def read_existing(path: pathlib.Path) -> dict[tuple[str, int], dict[str, Any]]:
    if not path.exists():
        return {}
    records = {}
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            record = json.loads(line)
            records[(record["doc_id"], int(record["page_index"]))] = record
    return records


def append_jsonl(path: pathlib.Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_tasks(manifest_rows: list[dict[str, str]], scan_pages: int) -> list[dict[str, Any]]:
    tasks = []
    for row in manifest_rows:
        pdf_path = pathlib.Path(row["local_path"])
        count = page_count(pdf_path)
        doc_id = slugify(row["file_name"])
        for page_index in range(min(scan_pages, count)):
            tasks.append(
                {
                    "doc_id": doc_id,
                    "title": row["title"],
                    "file_name": row["file_name"],
                    "local_path": row["local_path"],
                    "pdf_path": pdf_path,
                    "page_count": count,
                    "page_index": page_index,
                    "pdf_page": page_index + 1,
                }
            )
    return tasks


def join_values(values: list[Any]) -> str:
    cleaned = []
    for value in values:
        if value is None:
            continue
        value = str(value).strip()
        if value:
            cleaned.append(value)
    return " | ".join(cleaned)


def write_pages_csv(records: list[dict[str, Any]], path: pathlib.Path) -> None:
    fields = [
        "doc_id",
        "file_name",
        "title",
        "local_path",
        "page_count",
        "page_index",
        "pdf_page",
        "printed_page",
        "page_type",
        "is_contents_or_index",
        "contains_numbered_table_list",
        "contains_page_reference_column",
        "is_table_page",
        "likely_continues_contents",
        "confidence",
        "reason",
        "warnings",
        "error",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for record in sorted(records, key=lambda r: (r["doc_id"], int(r["page_index"]))):
            parsed = record.get("parsed") or {}
            writer.writerow(
                {
                    "doc_id": record.get("doc_id"),
                    "file_name": record.get("file_name"),
                    "title": record.get("title"),
                    "local_path": record.get("local_path"),
                    "page_count": record.get("page_count"),
                    "page_index": record.get("page_index"),
                    "pdf_page": record.get("pdf_page"),
                    "printed_page": parsed.get("printed_page"),
                    "page_type": parsed.get("page_type"),
                    "is_contents_or_index": parsed.get("is_contents_or_index"),
                    "contains_numbered_table_list": parsed.get(
                        "contains_numbered_table_list"
                    ),
                    "contains_page_reference_column": parsed.get(
                        "contains_page_reference_column"
                    ),
                    "is_table_page": parsed.get("is_table_page"),
                    "likely_continues_contents": parsed.get("likely_continues_contents"),
                    "confidence": parsed.get("confidence"),
                    "reason": parsed.get("reason"),
                    "warnings": join_values(parsed.get("warnings") or []),
                    "error": record.get("error"),
                }
            )


def summarise_doc(records: list[dict[str, Any]]) -> dict[str, Any]:
    first = records[0]
    content_pages = []
    confidences = []
    page_types = []
    errors = 0
    for record in records:
        parsed = record.get("parsed") or {}
        if record.get("error"):
            errors += 1
        if parsed.get("is_contents_or_index") is True:
            content_pages.append(int(record["page_index"]))
            confidence = parsed.get("confidence")
            if isinstance(confidence, (int, float)):
                confidences.append(float(confidence))
        if parsed.get("page_type"):
            page_types.append(str(parsed.get("page_type")))

    return {
        "doc_id": first["doc_id"],
        "file_name": first["file_name"],
        "title": first["title"],
        "local_path": first["local_path"],
        "page_count": first["page_count"],
        "scanned_pages": len(records),
        "contents_page_indexes": join_values(content_pages),
        "contents_pdf_pages": join_values([page + 1 for page in content_pages]),
        "contents_page_count": len(content_pages),
        "contents_confidence_min": min(confidences) if confidences else "",
        "contents_confidence_mean": statistics.mean(confidences) if confidences else "",
        "page_types_seen": join_values(sorted(set(page_types))),
        "errors": errors,
        "needs_review": len(content_pages) == 0 or errors > 0,
    }


def write_summary_csv(records: list[dict[str, Any]], path: pathlib.Path) -> None:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(record["doc_id"], []).append(record)

    rows = [summarise_doc(group) for group in grouped.values()]
    fields = [
        "doc_id",
        "file_name",
        "title",
        "local_path",
        "page_count",
        "scanned_pages",
        "contents_page_indexes",
        "contents_pdf_pages",
        "contents_page_count",
        "contents_confidence_min",
        "contents_confidence_mean",
        "page_types_seen",
        "errors",
        "needs_review",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: row["file_name"]))


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.output_dir / f"{args.run_id}_raw.jsonl"
    pages_path = args.output_dir / f"{args.run_id}_pages.csv"
    summary_path = args.output_dir / f"{args.run_id}_summary.csv"

    manifest_rows = read_manifest(args.manifest)
    tasks = build_tasks(manifest_rows, args.scan_pages)
    existing = {} if args.no_resume else read_existing(raw_path)
    todo = [
        task
        for task in tasks
        if (task["doc_id"], task["page_index"]) not in existing
        or existing[(task["doc_id"], task["page_index"])].get("error")
    ]
    api_key, api_key_source = get_api_key(args)

    print(f"Documents: {len(manifest_rows)}")
    print(f"Pages selected: {len(tasks)}")
    print(f"Pages to classify: {len(todo)}")
    print(f"Model: {args.model}")
    print(f"API key source: {api_key_source}")
    print(f"Raw output: {raw_path}")

    failures = 0
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        future_to_task = {
            executor.submit(classify_page, args, api_key, task): task for task in todo
        }
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            record = future.result()
            append_jsonl(raw_path, record)
            if record.get("error"):
                failures += 1
            print(
                f"{task['doc_id']} page {task['page_index']:03d} "
                f"{'failed' if record.get('error') else 'ok'}"
            )

    latest = read_existing(raw_path)
    records = [latest[(task["doc_id"], task["page_index"])] for task in tasks]
    write_pages_csv(records, pages_path)
    write_summary_csv(records, summary_path)

    total_cost = sum(
        record.get("usage", {}).get("cost") or 0
        for record in records
        if record.get("usage")
    )
    print(f"Failures this run: {failures}")
    print(f"Total cost in selected records: {total_cost:.6f}")
    print(f"Page inventory: {pages_path}")
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()
