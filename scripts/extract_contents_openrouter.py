"""
Extract the table of contents from a historical census PDF with OpenRouter.

Outputs:
- data/intermediate/page_inventory/<run_id>_index_raw.json
- data/intermediate/page_inventory/<run_id>_index.csv

This is intended to provide an index prior for page-level VLM inventories.
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import pathlib
import re
import urllib.error
import urllib.request
from typing import Any

import fitz


DEFAULT_PDF = pathlib.Path(
    "data/raw/abs_1911_census/1911_census_volume_iii_part_xiii_dwellings.pdf"
)
DEFAULT_MODEL = "google/gemini-3.1-flash-lite"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


SYSTEM_PROMPT = """You extract tables of contents from historical census documents.
Read the visible contents/index pages carefully. Return only valid JSON.
Do not invent tables that are not in the contents pages."""


USER_PROMPT = """The images are the contents pages for a census volume.

Extract the numbered table list. Return exactly this JSON shape:
{
  "doc_title": string or null,
  "contents_printed_pages": [string],
  "tables": [
    {
      "table_number": integer,
      "title": string,
      "start_printed_page": integer,
      "subentries": [
        {"label": string, "printed_page": integer}
      ],
      "warnings": [string]
    }
  ],
  "warnings": [string]
}

Rules:
- Extract all numbered tables in order.
- The right-hand Page column is the printed page number where the table starts.
- If a table has roman-numeral subentries, include those in subentries.
- Preserve the title wording, but normalise obvious OCR-like line breaks.
- If a number is hard to read, use the surrounding sequence and add a warning.
- The final output must be valid JSON only, with no markdown fences.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract PDF contents via OpenRouter.")
    parser.add_argument("--pdf", type=pathlib.Path, default=DEFAULT_PDF)
    parser.add_argument("--doc-id", default="abs_1911_census_volume_iii_part_xiii_dwellings")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--pages", default="1-3", help="Zero-based index pages, e.g. 1-3.")
    parser.add_argument("--dpi", type=int, default=190)
    parser.add_argument("--jpeg-quality", type=int, default=86)
    parser.add_argument("--max-tokens", type=int, default=16000)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument("--no-opencode-auth", action="store_true")
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=pathlib.Path("data/intermediate/page_inventory"),
    )
    parser.add_argument("--run-id", default=None)
    return parser.parse_args()


def sanitize_name(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_").lower()


def parse_pages(selection: str) -> list[int]:
    pages: set[int] = set()
    for part in selection.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            pages.update(range(int(start_text), int(end_text) + 1))
        else:
            pages.add(int(part))
    return sorted(pages)


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


def build_payload(args: argparse.Namespace, pages: list[int]) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": USER_PROMPT}]
    for page_index in pages:
        image_bytes = render_page_jpeg(
            args.pdf, page_index, args.dpi, args.jpeg_quality
        )
        image_b64 = base64.b64encode(image_bytes).decode("ascii")
        content.append({"type": "text", "text": f"PDF page index {page_index}"})
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
            }
        )

    return {
        "model": args.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        "temperature": 0,
        "max_tokens": args.max_tokens,
        "response_format": {"type": "json_object"},
    }


def post_openrouter(api_key: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/",
            "X-Title": "digitising_old_census contents extraction",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def clean_title(value: Any) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def write_index_csv(parsed: dict[str, Any], path: pathlib.Path, doc_id: str, model: str) -> None:
    fields = [
        "doc_id",
        "model",
        "table_number",
        "index_title",
        "index_start_printed_page",
        "index_subentries",
        "warnings",
    ]
    rows = []
    for table in parsed.get("tables", []):
        if not isinstance(table, dict):
            continue
        rows.append(
            {
                "doc_id": doc_id,
                "model": model,
                "table_number": table.get("table_number"),
                "index_title": clean_title(table.get("title")),
                "index_start_printed_page": table.get("start_printed_page"),
                "index_subentries": json.dumps(table.get("subentries") or [], ensure_ascii=False),
                "warnings": " | ".join(str(w) for w in table.get("warnings") or []),
            }
        )

    rows.sort(key=lambda row: int(row["table_number"]))
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    pages = parse_pages(args.pages)
    api_key, api_key_source = get_api_key(args)

    run_id = args.run_id or f"{sanitize_name(args.doc_id)}_{sanitize_name(args.model)}"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.output_dir / f"{run_id}_index_raw.json"
    csv_path = args.output_dir / f"{run_id}_index.csv"

    payload = build_payload(args, pages)
    print(f"PDF: {args.pdf}")
    print(f"Index pages: {pages}")
    print(f"Model: {args.model}")
    print(f"API key source: {api_key_source}")
    response = post_openrouter(api_key, payload, args.timeout)
    content = response["choices"][0]["message"].get("content", "")
    parsed = extract_json_object(content)
    raw = {"response": response, "parsed": parsed}

    with raw_path.open("w", encoding="utf-8") as file:
        json.dump(raw, file, ensure_ascii=False, indent=2)
    write_index_csv(parsed, csv_path, args.doc_id, args.model)

    table_count = len(parsed.get("tables", []))
    usage = response.get("usage") or {}
    print(f"Extracted tables: {table_count}")
    print(f"Cost: {usage.get('cost')}")
    print(f"Raw output: {raw_path}")
    print(f"Index CSV: {csv_path}")


if __name__ == "__main__":
    main()
