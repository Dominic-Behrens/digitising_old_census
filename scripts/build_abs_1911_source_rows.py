"""Locate source-geometry row candidates in the original 1911 census PDFs.

Input: output/build_abs_1911_table_spans/abs_1911_reviewed_pages.csv and its
       original PDFs under data/raw/abs_1911_census/.
Output: output/build_abs_1911_source_rows/{rows,pages}.csv only.

These are PDF-text anchors for image review, not accepted transcriptions or cells.
Uncertain anchors and pages with insufficient PDF text remain explicitly flagged.
No network or model calls are made.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
from pathlib import Path
import re
import statistics

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data/raw/abs_1911_census"
INPUT = ROOT / "output/build_abs_1911_table_spans/abs_1911_reviewed_pages.csv"
OUTPUT = ROOT / "output/build_abs_1911_source_rows"
ROW_FIELDS = ["doc_id", "pdf_page", "row_id", "row_y_pt", "row_text",
              "numeric_word_count", "source_pdf", "source_sha256",
              "mapped_table_ids", "anchor_status"]
PAGE_FIELDS = ["doc_id", "pdf_page", "source_pdf", "source_sha256",
               "mapped_table_ids", "anchor_count", "audit_status", "reason"]
# Midpoint geometry resists differences in font boxes across columns. A 2.7pt
# cluster radius does not join successive rows spaced roughly 8pt apart.
NUMERIC_Y_TOLERANCE_PT = 2.7
ROW_TEXT_Y_TOLERANCE_PT = 3.3
NUMBER = re.compile(r"[+-]?(?:\d[\d,]*(?:\.\d+)?|\.\d+)%?")
SPACE = re.compile(r"\s+")


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit-pages", type=int, help="Process at most this many not-yet-emitted physical pages")
    parser.add_argument("--start-after", help="Resume after doc_id:pdf_page, in reviewed-map order")
    args = parser.parse_args()
    if args.limit_pages is not None and args.limit_pages < 1:
        parser.error("--limit-pages must be positive")
    return args


def read_csv(path: Path, fields: list[str] | None = None) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if fields is not None and reader.fieldnames != fields:
            raise ValueError(f"Unexpected CSV columns in {path}: {reader.fieldnames}")
        return list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str | int | float]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def source_path(value: str) -> tuple[str, Path]:
    relative = Path(value.replace("\\", "/"))
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe source PDF path: {value}")
    absolute = (ROOT / relative).resolve(strict=True)
    if not absolute.is_relative_to(SOURCE_DIR.resolve(strict=True)) or absolute.suffix.lower() != ".pdf":
        raise ValueError(f"Source PDF outside data/raw/abs_1911_census/: {value}")
    return absolute.relative_to(ROOT).as_posix(), absolute


def source_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def mapped_pages() -> list[dict[str, str | int | Path]]:
    rows = read_csv(INPUT)
    if not rows:
        raise ValueError("Reviewed page map is empty")
    pages = []
    seen = set()
    documents: dict[str, tuple[str, int]] = {}
    for row in rows:
        doc_id, page_no = row["doc_id"], int(row["pdf_page"])
        key = (doc_id, page_no)
        if not doc_id or page_no < 1 or key in seen:
            raise ValueError(f"Invalid or repeated reviewed page: {key}")
        seen.add(key)
        page_count = int(row["page_count"])
        if int(row["page_index"]) + 1 != page_no or page_no > page_count:
            raise ValueError(f"Inconsistent reviewed page numbering: {key}")
        source_pdf, path = source_path(row["local_path"])
        identity = (source_pdf, page_count)
        if doc_id in documents and documents[doc_id] != identity:
            raise ValueError(f"Inconsistent PDF source or page count for {doc_id}")
        documents[doc_id] = identity
        pages.append({"doc_id": doc_id, "pdf_page": page_no,
                      "source_pdf": source_pdf, "path": path,
                      "mapped_table_ids": row["table_ids"].strip()})
    for doc_id, (_, page_count) in documents.items():
        actual = {page for source_doc, page in seen if source_doc == doc_id}
        if actual != set(range(1, page_count + 1)):
            raise ValueError(f"Reviewed page map omits physical pages in {doc_id}")
    return pages


def numeric_token(text: str) -> bool:
    # Punctuation outside a printed number (leader dots or OCR border strokes)
    # is not a cell: accepting a token here identifies geometry, not its value.
    return bool(NUMBER.fullmatch(text.strip("()[]{}*'\";:· ")))


def anchors(words: list[tuple]) -> list[dict[str, str | int | float]]:
    positioned = [(0.5 * (word[1] + word[3]), word) for word in words]
    positioned.sort(key=lambda entry: entry[0])
    numeric = [(y, word) for y, word in positioned if numeric_token(word[4])]
    groups: list[list[tuple[float, tuple]]] = []
    for item in numeric:
        if groups and abs(item[0] - statistics.median(y for y, _ in groups[-1])) <= NUMERIC_Y_TOLERANCE_PT:
            groups[-1].append(item)
        else:
            groups.append([item])
    ys = [y for y, _ in positioned]
    found = []
    for group in groups:
        y = statistics.median(value for value, _ in group)
        x_positions = [word[0] for _, word in group]
        candidate = len(group) >= 2 and max(x_positions) - min(x_positions) >= 24
        left = bisect.bisect_left(ys, y - ROW_TEXT_Y_TOLERANCE_PT)
        right = bisect.bisect_right(ys, y + ROW_TEXT_Y_TOLERANCE_PT)
        vicinity = sorted((word for _, word in positioned[left:right]), key=lambda w: (w[0], w[1]))
        text = SPACE.sub(" ", " ".join(word[4] for word in vicinity)).strip()
        found.append({"row_y_pt": round(y, 2), "row_text": text,
                      "numeric_word_count": len(group),
                      "anchor_status": "candidate_numeric_row" if candidate else "uncertain_row"})
    return found


def audit_status(mapped: bool, word_count: int, numeric_count: int, candidate_count: int) -> tuple[str, str]:
    if not mapped:
        return "non_table", "No mapped table IDs on this physical page"
    if word_count < 25 or (numeric_count < 4 and word_count < 100):
        return "text_limited", f"PDF text layer has {word_count} words and {numeric_count} numeric words; inspect source image"
    if not candidate_count:
        return "missing_anchors", f"PDF text layer has {word_count} words but no multi-column numeric row anchors"
    return "anchored", "Candidate geometry only; printed rows and cells require image review"


def main() -> None:
    args = arguments()
    pages = mapped_pages()
    keys = [(p["doc_id"], p["pdf_page"]) for p in pages]
    if args.start_after:
        doc, separator, number = args.start_after.rpartition(":")
        if not separator or not number.isdecimal() or (doc, int(number)) not in keys:
            raise ValueError("--start-after must identify a reviewed doc_id:pdf_page")
        start = keys.index((doc, int(number))) + 1
    else:
        start = 0

    existing_pages = read_csv(OUTPUT / "pages.csv", PAGE_FIELDS) if (OUTPUT / "pages.csv").exists() else []
    existing_rows = read_csv(OUTPUT / "rows.csv", ROW_FIELDS) if (OUTPUT / "rows.csv").exists() else []
    if bool(existing_pages) != bool(existing_rows) and existing_rows:
        raise ValueError("rows.csv exists without its page audit")
    key_set = set(keys)
    done = set()
    for row in existing_pages:
        key = (row["doc_id"], int(row["pdf_page"]))
        if key not in key_set or key in done:
            raise ValueError(f"Unknown or duplicate page in existing audit: {key}")
        done.add(key)
        mapped = pages[keys.index(key)]
        if row["source_pdf"] != mapped["source_pdf"] or row["mapped_table_ids"] != mapped["mapped_table_ids"]:
            raise ValueError(f"Reviewed source/map changed for already emitted page {key}")
    ids = set()
    for row in existing_rows:
        key = (row["doc_id"], int(row["pdf_page"]))
        if key not in done or row["row_id"] in ids:
            raise ValueError(f"Orphan or duplicate existing row {row['row_id']}")
        ids.add(row["row_id"])
    prior_hashes = {}
    for row in [*existing_pages, *existing_rows]:
        source = row["source_pdf"]
        if source in prior_hashes and prior_hashes[source] != row["source_sha256"]:
            raise ValueError(f"Inconsistent existing source hashes for {source}")
        prior_hashes[source] = row["source_sha256"]

    hashes: dict[Path, str] = {}
    documents: dict[Path, pymupdf.Document] = {}
    new_pages = []
    new_rows = []
    try:
        selected = [page for page in pages[start:] if (page["doc_id"], page["pdf_page"]) not in done]
        if args.limit_pages is not None:
            selected = selected[:args.limit_pages]
        # Verify already emitted sources as well, including runs that select no new pages.
        for source, old_hash in prior_hashes.items():
            relative, path = source_path(source)
            if relative != source:
                raise ValueError(f"Noncanonical existing source path: {source}")
            hashes[path] = source_hash(path)
            if hashes[path] != old_hash:
                raise ValueError(f"Original PDF changed since previous extraction: {source}")
        for page in selected:
            path = page["path"]
            if path not in hashes:
                hashes[path] = source_hash(path)
            if path not in documents:
                documents[path] = pymupdf.open(path)
            document = documents[path]
            page_no = page["pdf_page"]
            if page_no > len(document):
                raise ValueError(f"Reviewed page beyond original PDF: {page['doc_id']}:{page_no}")
            words = document[page_no - 1].get_text("words", sort=False)
            found = anchors(words) if page["mapped_table_ids"] else []
            candidate_count = sum(item["anchor_status"] == "candidate_numeric_row" for item in found)
            numeric_count = sum(numeric_token(word[4]) for word in words)
            status, reason = audit_status(bool(page["mapped_table_ids"]), len(words), numeric_count, candidate_count)
            shared = {"doc_id": page["doc_id"], "pdf_page": page_no,
                      "source_pdf": page["source_pdf"], "source_sha256": hashes[path],
                      "mapped_table_ids": page["mapped_table_ids"]}
            new_pages.append({**shared, "anchor_count": len(found), "audit_status": status, "reason": reason})
            for sequence, found_row in enumerate(found, start=1):
                new_rows.append({**shared, "row_id": f"{page['doc_id']}::p{page_no}::r{sequence}", **found_row})
    finally:
        for document in documents.values():
            document.close()

    OUTPUT.mkdir(parents=True, exist_ok=True)
    order = {key: index for index, key in enumerate(keys)}
    all_pages = sorted([*existing_pages, *new_pages], key=lambda r: order[(r["doc_id"], int(r["pdf_page"]))])
    all_rows = sorted([*existing_rows, *new_rows], key=lambda r: (order[(r["doc_id"], int(r["pdf_page"]))],
                                                                   int(r["row_id"].rsplit("::r", 1)[1])))
    write_csv(OUTPUT / "rows.csv", ROW_FIELDS, all_rows)
    write_csv(OUTPUT / "pages.csv", PAGE_FIELDS, all_pages)
    print(f"Processed {len(new_pages)} pages; audit has {len(all_pages)} pages and {len(all_rows)} anchors")


if __name__ == "__main__":
    main()
