"""
Run first-pass QA on flagged 1911 census page assignments with a vision model.

Input: output/diagnostics/flagged_pages/review_index.csv
Outputs:
- data/intermediate/page_inventory/abs_1911_flagged_page_qa_raw.jsonl
- data/intermediate/page_inventory/abs_1911_flagged_page_qa.csv
- data/intermediate/page_inventory/abs_1911_flagged_page_qa_human_review.csv
"""

from __future__ import annotations

import argparse
import base64
import csv
import datetime as dt
import json
import mimetypes
import os
import pathlib
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any


DEFAULT_INPUT = pathlib.Path("output/diagnostics/flagged_pages/review_index.csv")
DEFAULT_OUTPUT_DIR = pathlib.Path("data/intermediate/page_inventory")
DEFAULT_MODEL = "google/gemini-3.1-flash-lite"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You QA page-to-table assignments for historical Australian census PDFs.
Use only the supplied candidate table numbers for final assignments.
Return only valid JSON. No markdown."""

USER_PROMPT_TEMPLATE = """Review this flagged page assignment.

Metadata:
- doc_id: {doc_id}
- pdf_page: {pdf_page}
- page_index: {page_index}
- original_page_role: {page_role}
- candidate_table_numbers: {candidate_table_numbers}
- original_matched_table_numbers: {matched_table_numbers}
- visible_titles_from_prior_model: {visible_titles}
- warnings_from_prior_model: {warnings}

Task:
Decide whether the current page-to-table assignment is acceptable for extraction.

Return exactly this JSON object:
{{
  "qa_decision": "accept_current_match" or "correct_match_from_candidates" or "boundary_confirmed" or "non_table_confirmed" or "contents_or_index_confirmed" or "candidate_set_wrong" or "unreadable_or_low_quality" or "needs_human_review" or "model_error",
  "final_page_role": "starts" or "continues" or "ends" or "complete_on_page" or "boundary_multiple_tables" or "contents_or_index" or "non_table" or "unknown",
  "final_table_numbers": [string],
  "candidate_set_complete": true or false,
  "visible_table_numbers": [string],
  "visible_title_snippet": string or null,
  "printed_page": string or null,
  "issue_type": "none" or "wrong_table_match" or "missing_table_match" or "extra_table_match" or "boundary_page" or "candidate_set_wrong" or "not_a_table" or "unreadable" or "ambiguous_continuation",
  "confidence": number from 0 to 1,
  "needs_human_review": true or false,
  "qa_notes": string
}}

Rules:
- final_table_numbers must be selected only from candidate_table_numbers.
- If a visible table number is not in candidate_table_numbers, do not assign it.
  Set qa_decision to candidate_set_wrong, candidate_set_complete to false, and
  needs_human_review to true.
- Contents/index pages can mention table numbers; do not assign a table unless a
  table body, heading, or continuation header is visibly present.
- Boundary pages can legitimately contain two adjacent tables.
- Do not transcribe numeric cells.
- Keep qa_notes brief and evidence-based.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=pathlib.Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=pathlib.Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--run-id", default="abs_1911_flagged_page_qa")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--max-tokens", type=int, default=900)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument("--no-opencode-auth", action="store_true")
    return parser.parse_args()


def get_api_key(args: argparse.Namespace) -> tuple[str, str]:
    env_key = os.getenv(args.api_key_env)
    if env_key:
        return env_key, args.api_key_env
    if args.no_opencode_auth:
        raise RuntimeError(f"{args.api_key_env} is not set and OpenCode auth fallback is disabled.")
    auth_path = pathlib.Path.home() / ".local/share/opencode/auth.json"
    with auth_path.open("r", encoding="utf-8") as file:
        auth = json.load(file)
    key = auth.get("openrouter", {}).get("key") if isinstance(auth, dict) else None
    if not key:
        raise RuntimeError("OpenCode auth has no OpenRouter key.")
    return str(key), "OpenCode OpenRouter credential"


def normalise_row(row: dict[str, str]) -> dict[str, str]:
    row = dict(row)
    row.setdefault("page_role", row.get("original_page_role", ""))
    row.setdefault("matched_table_numbers", row.get("original_matched_table_numbers", ""))
    row.setdefault("visible_titles", row.get("visible_title_snippet", ""))
    row.setdefault("warnings", row.get("qa_notes", ""))
    return row


def read_rows(path: pathlib.Path, limit: int | None) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as file:
        rows = [normalise_row(row) for row in csv.DictReader(file)]
    return rows[:limit] if limit else rows


def row_key(row: dict[str, str]) -> str:
    return f"{row['doc_id']}|{row['page_index']}|{row['image_path']}"


def read_completed(path: pathlib.Path) -> dict[str, dict[str, Any]]:
    completed = {}
    if not path.exists():
        return completed
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            record = json.loads(line)
            if not record.get("error"):
                completed[record["key"]] = record
    return completed


def image_data_url(path: pathlib.Path) -> str:
    mime = mimetypes.guess_type(path)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def make_payload(row: dict[str, str], model: str, max_tokens: int) -> dict[str, Any]:
    prompt = USER_PROMPT_TEMPLATE.format(**row)
    return {
        "model": model,
        "temperature": 0,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url(pathlib.Path(row["image_path"]))}},
                ],
            },
        ],
    }


def parse_json_response(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return json.loads(text)


def call_openrouter(row: dict[str, str], args: argparse.Namespace, api_key: str) -> dict[str, Any]:
    payload = make_payload(row, args.model, args.max_tokens)
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        OPENROUTER_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/",
            "X-Title": "digitising_old_census flagged page QA",
        },
        method="POST",
    )
    last_error = None
    for attempt in range(1, args.retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=args.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            parsed = parse_json_response(content)
            return {
                "key": row_key(row),
                "created_at": dt.datetime.now(dt.UTC).isoformat(),
                "model": args.model,
                "row": row,
                "parsed": parsed,
                "usage": data.get("usage"),
                "raw_response": data,
                "error": None,
            }
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
            last_error = str(exc)
            time.sleep(min(2 ** attempt, 20))
    return {
        "key": row_key(row),
        "created_at": dt.datetime.now(dt.UTC).isoformat(),
        "model": args.model,
        "row": row,
        "parsed": None,
        "usage": None,
        "raw_response": None,
        "error": last_error,
    }


def append_record(path: pathlib.Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def join_values(values: Any) -> str:
    if not values:
        return ""
    if isinstance(values, list):
        return " | ".join(str(value) for value in values)
    return str(values)


def write_outputs(records: list[dict[str, Any]], csv_path: pathlib.Path, review_path: pathlib.Path) -> None:
    fields = [
        "doc_id", "pdf_page", "page_index", "image_path", "original_page_role",
        "candidate_table_numbers", "original_matched_table_numbers", "qa_decision",
        "final_page_role", "final_table_numbers", "candidate_set_complete",
        "visible_table_numbers", "visible_title_snippet", "printed_page", "issue_type",
        "confidence", "needs_human_review", "qa_notes", "model", "cost", "error",
    ]
    rows = []
    for record in records:
        row = record["row"]
        parsed = record.get("parsed") or {}
        usage = record.get("usage") or {}
        rows.append(
            {
                "doc_id": row.get("doc_id"),
                "pdf_page": row.get("pdf_page"),
                "page_index": row.get("page_index"),
                "image_path": row.get("image_path"),
                "original_page_role": row.get("page_role"),
                "candidate_table_numbers": row.get("candidate_table_numbers"),
                "original_matched_table_numbers": row.get("matched_table_numbers"),
                "qa_decision": parsed.get("qa_decision"),
                "final_page_role": parsed.get("final_page_role"),
                "final_table_numbers": join_values(parsed.get("final_table_numbers")),
                "candidate_set_complete": parsed.get("candidate_set_complete"),
                "visible_table_numbers": join_values(parsed.get("visible_table_numbers")),
                "visible_title_snippet": parsed.get("visible_title_snippet"),
                "printed_page": parsed.get("printed_page"),
                "issue_type": parsed.get("issue_type"),
                "confidence": parsed.get("confidence"),
                "needs_human_review": parsed.get("needs_human_review"),
                "qa_notes": parsed.get("qa_notes"),
                "model": record.get("model"),
                "cost": usage.get("cost"),
                "error": record.get("error"),
            }
        )

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    with review_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            confidence = float(row["confidence"] or 0)
            if (
                row["error"]
                or str(row["needs_human_review"]).lower() == "true"
                or row["qa_decision"] in {"candidate_set_wrong", "unreadable_or_low_quality", "needs_human_review", "model_error"}
                or confidence < 0.8
            ):
                writer.writerow(row)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.output_dir / f"{args.run_id}_raw.jsonl"
    csv_path = args.output_dir / f"{args.run_id}.csv"
    review_path = args.output_dir / f"{args.run_id}_human_review.csv"

    rows = read_rows(args.input, args.limit)
    completed = {} if args.no_resume else read_completed(raw_path)
    todo = [row for row in rows if row_key(row) not in completed]
    api_key, key_source = get_api_key(args)

    print(f"Rows selected: {len(rows)}")
    print(f"Rows to QA: {len(todo)}")
    print(f"Model: {args.model}")
    print(f"API key source: {key_source}")
    print(f"Raw output: {raw_path}")

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {executor.submit(call_openrouter, row, args, api_key): row for row in todo}
        for future in as_completed(futures):
            record = future.result()
            append_record(raw_path, record)
            status = "failed" if record.get("error") else "ok"
            row = record["row"]
            print(f"{row['doc_id']} page {int(row['pdf_page']):04d} {status}")

    records_by_key = read_completed(raw_path)
    records = [records_by_key[row_key(row)] for row in rows if row_key(row) in records_by_key]
    write_outputs(records, csv_path, review_path)

    total_cost = sum(((record.get("usage") or {}).get("cost") or 0) for record in records)
    failures = len(rows) - len(records)
    print(f"QA records: {len(records)}")
    print(f"Failures or missing records: {failures}")
    print(f"Total cost in records: {total_cost:.6f}")
    print(f"QA output: {csv_path}")
    print(f"Human-review output: {review_path}")


if __name__ == "__main__":
    main()
