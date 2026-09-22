"""
Classify 1911 census table pages using the contents-derived table spans.

Inputs:
- data/intermediate/table_index/abs_1911_table_page_spans.csv

Outputs:
- data/intermediate/page_inventory/abs_1911_index_guided_pages_raw.jsonl
- data/intermediate/page_inventory/abs_1911_index_guided_pages.csv
- data/intermediate/page_inventory/abs_1911_index_guided_review.csv

The VLM is constrained to choose only from candidate table numbers supplied from
the index-derived page spans. This prevents invented table numbers.
"""

from __future__ import annotations

import argparse
import base64
import csv
import datetime as dt
import json
import os
import pathlib
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import fitz


SPANS_PATH = pathlib.Path("data/intermediate/table_index/abs_1911_table_page_spans.csv")
OUT_DIR = pathlib.Path("data/intermediate/page_inventory")
DEFAULT_MODEL = "google/gemini-3.1-flash-lite"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


SYSTEM_PROMPT = """You classify pages from historical Australian census PDFs.
You are given candidate table numbers and titles from the document's contents index.
Choose only from the candidate table numbers. Do not invent table numbers.
Return only valid JSON."""


USER_PROMPT_TEMPLATE = """Document:
- doc_id: {doc_id}
- file_name: {file_name}
- page_index: {page_index} (zero-based)
- pdf_page: {pdf_page} (one-based)

Candidate indexed tables expected on or near this page:
{candidate_text}

Task:
Classify which candidate table(s) are visible on this page and describe the page's role.

Return exactly this JSON object:
{{
  "printed_page": string or null,
  "matched_table_numbers": [string],
  "page_role": "starts" or "continues" or "ends" or "complete_on_page" or "boundary_multiple_tables" or "contents_or_index" or "non_table" or "unknown",
  "visible_titles": [string],
  "visible_subentry": string or null,
  "visible_section": string or null,
  "contains_multiple_tables": true or false,
  "contains_table_header": true or false,
  "contains_table_body": true or false,
  "confidence": number from 0 to 1,
  "warnings": [string]
}}

Rules:
- matched_table_numbers must be selected only from candidate table numbers.
- If no candidate table is visible, return an empty matched_table_numbers array.
- If two candidate tables are visible on the same page, include both and set
  page_role to boundary_multiple_tables.
- If the page is a contents/index page or title page, do not match a table unless
  a candidate table body/title is visibly present.
- Do not transcribe numeric cells.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Index-guided page classifier.")
    parser.add_argument("--spans", type=pathlib.Path, default=SPANS_PATH)
    parser.add_argument("--output-dir", type=pathlib.Path, default=OUT_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--jpeg-quality", type=int, default=80)
    parser.add_argument("--max-workers", type=int, default=6)
    parser.add_argument("--max-tokens", type=int, default=900)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument("--no-opencode-auth", action="store_true")
    parser.add_argument("--run-id", default="abs_1911_index_guided_pages")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument(
        "--doc-id",
        default=None,
        help="Optional single doc_id to classify for testing.",
    )
    parser.add_argument(
        "--limit-pages",
        type=int,
        default=None,
        help="Optional maximum number of unique pages to classify.",
    )
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


def read_spans(path: pathlib.Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def parse_page_indexes(value: str) -> list[int]:
    if not value.strip():
        return []
    return [int(part.strip()) for part in value.split("|") if part.strip()]


def candidate_from_span(span: dict[str, str]) -> dict[str, str]:
    return {
        "table_number": span["table_number"],
        "table_title": span["table_title"],
        "start_page_index": span["start_page_index"],
        "end_page_index": span["end_page_index"],
        "topic": span["topic"],
        "geography": span["geography"],
        "subentry_count": span["subentry_count"],
        "span_flags": span["span_flags"],
    }


def add_candidate(task: dict[str, Any], span: dict[str, str]) -> None:
    candidate = candidate_from_span(span)
    existing = {item["table_number"] for item in task["candidates"]}
    if candidate["table_number"] not in existing:
        task["candidates"].append(candidate)


def table_number_sort(value: str) -> tuple[int, str]:
    try:
        return (int(value), value)
    except ValueError:
        return (10**9, value)


def build_tasks(spans: list[dict[str, str]], doc_id: str | None, limit_pages: int | None) -> list[dict[str, Any]]:
    spans_by_doc: dict[str, list[dict[str, str]]] = {}
    for span in spans:
        if doc_id and span["doc_id"] != doc_id:
            continue
        spans_by_doc.setdefault(span["doc_id"], []).append(span)

    for doc_spans in spans_by_doc.values():
        doc_spans.sort(key=lambda span: table_number_sort(span["table_number"]))

    by_page: dict[tuple[str, int], dict[str, Any]] = {}
    for doc_spans in spans_by_doc.values():
        for span_index, span in enumerate(doc_spans):
            prev_span = doc_spans[span_index - 1] if span_index > 0 else None
            next_span = doc_spans[span_index + 1] if span_index + 1 < len(doc_spans) else None
            for page_index in parse_page_indexes(span.get("page_indexes", "")):
                key = (span["doc_id"], page_index)
                task = by_page.setdefault(
                    key,
                    {
                        "doc_id": span["doc_id"],
                        "file_name": span["file_name"],
                        "local_path": span["local_path"],
                        "page_count": int(span["page_count"]),
                        "page_index": page_index,
                        "pdf_page": page_index + 1,
                        "candidates": [],
                    },
                )
                add_candidate(task, span)
                if prev_span is not None:
                    add_candidate(task, prev_span)
                if next_span is not None:
                    add_candidate(task, next_span)
    tasks = sorted(by_page.values(), key=lambda task: (task["doc_id"], task["page_index"]))
    if limit_pages is not None:
        tasks = tasks[:limit_pages]
    return tasks


def candidate_text(candidates: list[dict[str, str]]) -> str:
    lines = []
    for candidate in candidates:
        lines.append(
            "- table_number={table_number}; title={table_title}; span={start_page_index}-{end_page_index}; "
            "topic={topic}; geography={geography}; flags={span_flags}".format(**candidate)
        )
    return "\n".join(lines)


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


def build_payload(args: argparse.Namespace, task: dict[str, Any], image_bytes: bytes, include_response_format: bool) -> dict[str, Any]:
    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    prompt = USER_PROMPT_TEMPLATE.format(
        doc_id=task["doc_id"],
        file_name=task["file_name"],
        page_index=task["page_index"],
        pdf_page=task["pdf_page"],
        candidate_text=candidate_text(task["candidates"]),
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
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
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
            "X-Title": "digitising_old_census guided page classifier",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def classify_page(args: argparse.Namespace, api_key: str, task: dict[str, Any]) -> dict[str, Any]:
    started_at = dt.datetime.now(dt.UTC).isoformat()
    image_bytes = render_page_jpeg(pathlib.Path(task["local_path"]), task["page_index"], args.dpi, args.jpeg_quality)
    include_response_format = True
    last_error = None
    for attempt in range(1, args.retries + 1):
        try:
            payload = build_payload(args, task, image_bytes, include_response_format)
            response = post_openrouter(api_key, payload, args.timeout)
            content = response["choices"][0]["message"].get("content", "")
            parsed = extract_json_object(content)
            return {
                **task,
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
        **task,
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
    serialisable = dict(record)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(serialisable, ensure_ascii=False) + "\n")


def join_values(values: list[Any]) -> str:
    return " | ".join(str(value) for value in values if value is not None and str(value).strip())


def write_pages_csv(records: list[dict[str, Any]], path: pathlib.Path) -> None:
    fields = [
        "doc_id", "file_name", "local_path", "page_count", "page_index", "pdf_page",
        "candidate_table_numbers", "matched_table_numbers", "candidate_count", "matched_count",
        "printed_page", "page_role", "visible_titles", "visible_subentry", "visible_section",
        "contains_multiple_tables", "contains_table_header", "contains_table_body", "confidence",
        "warnings", "candidate_mismatch", "error",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for record in sorted(records, key=lambda r: (r["doc_id"], int(r["page_index"]))):
            parsed = record.get("parsed") or {}
            candidates = [candidate["table_number"] for candidate in record.get("candidates") or []]
            matched = [str(value) for value in parsed.get("matched_table_numbers") or []]
            mismatch = any(value not in candidates for value in matched)
            writer.writerow(
                {
                    "doc_id": record.get("doc_id"),
                    "file_name": record.get("file_name"),
                    "local_path": record.get("local_path"),
                    "page_count": record.get("page_count"),
                    "page_index": record.get("page_index"),
                    "pdf_page": record.get("pdf_page"),
                    "candidate_table_numbers": join_values(candidates),
                    "matched_table_numbers": join_values(matched),
                    "candidate_count": len(candidates),
                    "matched_count": len(matched),
                    "printed_page": parsed.get("printed_page"),
                    "page_role": parsed.get("page_role"),
                    "visible_titles": join_values(parsed.get("visible_titles") or []),
                    "visible_subentry": parsed.get("visible_subentry"),
                    "visible_section": parsed.get("visible_section"),
                    "contains_multiple_tables": parsed.get("contains_multiple_tables"),
                    "contains_table_header": parsed.get("contains_table_header"),
                    "contains_table_body": parsed.get("contains_table_body"),
                    "confidence": parsed.get("confidence"),
                    "warnings": join_values(parsed.get("warnings") or []),
                    "candidate_mismatch": mismatch,
                    "error": record.get("error"),
                }
            )


def write_review_csv(records: list[dict[str, Any]], path: pathlib.Path) -> None:
    tmp = path.with_suffix(".tmp.csv")
    write_pages_csv(records, tmp)
    with tmp.open("r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
        fields = rows[0].keys() if rows else []
    review = []
    for row in rows:
        confidence = float(row["confidence"]) if row["confidence"] else 0
        if (
            row["error"]
            or row["candidate_mismatch"] == "True"
            or not row["matched_table_numbers"]
            or row["page_role"] in {"boundary_multiple_tables", "unknown"}
            or confidence < 0.8
        ):
            review.append(row)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(review)
    tmp.unlink()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.output_dir / f"{args.run_id}_raw.jsonl"
    pages_path = args.output_dir / f"{args.run_id}.csv"
    review_path = args.output_dir / f"{args.run_id}_review.csv"

    spans = read_spans(args.spans)
    tasks = build_tasks(spans, args.doc_id, args.limit_pages)
    existing = {} if args.no_resume else read_existing(raw_path)
    todo = [
        task for task in tasks
        if (task["doc_id"], task["page_index"]) not in existing
        or existing[(task["doc_id"], task["page_index"])].get("error")
    ]
    api_key, api_key_source = get_api_key(args)

    print(f"Unique pages selected: {len(tasks)}")
    print(f"Pages to classify: {len(todo)}")
    print(f"Model: {args.model}")
    print(f"API key source: {api_key_source}")
    print(f"Raw output: {raw_path}")

    failures = 0
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        future_to_task = {executor.submit(classify_page, args, api_key, task): task for task in todo}
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            record = future.result()
            append_jsonl(raw_path, record)
            if record.get("error"):
                failures += 1
            print(f"{task['doc_id']} page {task['page_index']:03d} {'failed' if record.get('error') else 'ok'}")

    latest = read_existing(raw_path)
    records = [latest[(task["doc_id"], task["page_index"])] for task in tasks if (task["doc_id"], task["page_index"]) in latest]
    write_pages_csv(records, pages_path)
    write_review_csv(records, review_path)
    total_cost = sum((record.get("usage") or {}).get("cost") or 0 for record in records)

    print(f"Classified records: {len(records)}")
    print(f"Failures this run: {failures}")
    print(f"Total cost in records: {total_cost:.6f}")
    print(f"Pages output: {pages_path}")
    print(f"Review output: {review_path}")


if __name__ == "__main__":
    main()
