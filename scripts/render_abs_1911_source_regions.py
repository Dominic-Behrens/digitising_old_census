# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf>=1.24"]
# ///
"""Render source-PDF row regions with a 54-point, source-aligned row-ID gutter.

Inputs (read-only): output/build_abs_1911_source_rows/{rows,pages}.csv,
output/build_abs_1911_image_rows/{rows,pages}.csv for mapped text-limited pages,
and original PDFs. Outputs (script-owned):
output/render_abs_1911_source_regions/{regions.jsonl,page_review.csv,images/}.
Offline only. Run with --limit-pages N and --start-after doc_id:pdf_page to
process bounded slices; rerunning a slice replaces its manifest rows. Use
--region-id to rerender only named regions with the full bottom row visible.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import fcntl
import hashlib
import io
import math
import json
from pathlib import Path
import re
import tempfile

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "output/build_abs_1911_source_rows"
OUTPUT = ROOT / "output/render_abs_1911_source_regions"
ROW_FIELDS = ("doc_id", "pdf_page", "row_id", "row_y_pt", "row_text",
              "numeric_word_count", "source_pdf", "source_sha256",
              "mapped_table_ids", "anchor_status")
PAGE_FIELDS = ("doc_id", "pdf_page", "source_pdf", "source_sha256",
               "mapped_table_ids", "anchor_count", "audit_status", "reason")
REVIEW_FIELDS = ("doc_id", "pdf_page", "reason")
GUTTER_PT = 54
MAX_ROWS = 12
MAX_GAP_PT = 40
# A numbered, substantial source heading; mere age/row numbers are not titles.
NUMBERED_TITLE = re.compile(r"^\s*(?:(?:NO\.?\s*)?\d{1,3}|[IVX]{1,3})\s*[.\-—–:]+\s*\S", re.I)


def read_csv(path: Path, expected: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(expected):
            raise ValueError(f"Unexpected columns in {path}: {reader.fieldnames}")
        return list(reader)


def source_path(relative: str) -> Path:
    if not relative or "\\" in relative:
        raise ValueError(f"Source path must be project-relative POSIX: {relative!r}")
    source = (ROOT / relative).resolve()
    if Path(relative).is_absolute() or not source.is_relative_to(ROOT / "data/raw/abs_1911_census"):
        raise ValueError(f"Source PDF outside immutable corpus: {relative!r}")
    return source


def digest(path: Path) -> str:
    hashed = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hashed.update(chunk)
    return hashed.hexdigest()


def atomic_text(path: Path, content: str) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                     prefix=f".{path.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(content)
    temporary.replace(path)


def headings(page: pymupdf.Page) -> list[tuple[float, float]]:
    found = []
    for block in page.get_text("dict")["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            text = " ".join(span["text"] for span in line["spans"]).strip()
            letters = [ch for ch in text if ch.isalpha()]
            x0, y0, x1, y1 = line["bbox"]
            if (NUMBERED_TITLE.match(text) and len(letters) >= 14 and
                    x1 - x0 >= page.rect.width * .27 and
                    sum(ch.isupper() for ch in letters) / len(letters) >= .48):
                found.append((y0, y1))
    return sorted(found)


def batches(rows: list[dict], titles: list[tuple[float, float]]) -> list[list[dict]]:
    groups: list[list[dict]] = []
    current: list[dict] = []
    previous_y: float | None = None
    for row in rows:
        if row["anchor_status"] not in {"candidate_numeric_row", "image_candidate_row", "uncertain_row"}:
            if current:
                groups.append(current)
                current = []
            previous_y = None
            continue
        y = float(row["row_y_pt"])
        boundary = (previous_y is not None and any(previous_y < top < y for top, _ in titles))
        if current and (len(current) == MAX_ROWS or y - previous_y > MAX_GAP_PT or boundary):
            groups.append(current)
            current = []
        current.append(row)
        previous_y = y
    if current:
        groups.append(current)
    return groups


def clip_for(rows: list[dict], all_rows: list[dict], titles: list[tuple[float, float]],
             bounds: pymupdf.Rect) -> pymupdf.Rect:
    first, last = float(rows[0]["row_y_pt"]), float(rows[-1]["row_y_pt"])
    other_y = [float(row["row_y_pt"]) for row in all_rows if row not in rows]
    prior = max((y for y in other_y if y < first), default=None)
    following = min((y for y in other_y if y > last), default=None)
    # Source rows typically stand 8-12pt apart. Never bisect a neighbouring anchor.
    top = max(bounds.y0, first - 12, (first + prior) / 2 if prior is not None else bounds.y0)
    bottom = min(bounds.y1, last + 12, (last + following) / 2 if following is not None else bounds.y1)
    previous_heading = max((end for start, end in titles if end < first), default=None)
    next_heading = min((start for start, end in titles if start > last), default=None)
    if previous_heading is not None and previous_heading + 1 < first:
        top = max(top, previous_heading + 1)
    if next_heading is not None and next_heading - 1 > last:
        bottom = min(bottom, next_heading - 1)
    if not (top < first <= last < bottom):
        raise ValueError("Source heading or neighbouring anchor overlaps the row crop")
    return pymupdf.Rect(bounds.x0, round(top, 2), bounds.x1, round(bottom, 2))


def header_clip(rows: list[dict], all_rows: list[dict],
                titles: list[tuple[float, float]], bounds: pymupdf.Rect) -> pymupdf.Rect | None:
    first = float(rows[0]["row_y_pt"])
    first_data = min((float(row["row_y_pt"]) for row in all_rows
                      if row["anchor_status"] in {"candidate_numeric_row", "image_candidate_row"}), default=first)
    matches = [(start, end) for start, end in titles if end < first - 12]
    # A running section title can occur below the column labels. PDF number
    # anchors can also land on the column headings rather than the first
    # data row. Keep a bounded page-top strip through those headings; only
    # the marked first image defines the rows to transcribe.
    if not matches or matches[-1][0] < first_data:
        bottom = min(bounds.y0 + 240, max(bounds.y0 + 190, first_data + 40))
        return (pymupdf.Rect(bounds.x0, bounds.y0, bounds.x1, bottom)
                if bottom > bounds.y0 + 20 else None)
    # A later numbered table on the same page needs its own heading, not the
    # page-top header belonging to the preceding table.
    start, end = matches[-1]
    first_data_after_title = min(
        (float(row["row_y_pt"]) for row in all_rows
         if float(row["row_y_pt"]) > end
         and row["anchor_status"] in {"candidate_numeric_row", "image_candidate_row"}),
        default=first)
    bottom = min(first - 9, first_data_after_title - 3, start + 170)
    if bottom <= end:
        return None
    return pymupdf.Rect(bounds.x0, max(bounds.y0, start - 5), bounds.x1, bottom)

def render_region(pdf: pymupdf.Document, page_number: int, clip: pymupdf.Rect,
                  rows: list[dict], target: Path, dpi: int) -> None:
    with pymupdf.open() as guide:
        canvas = guide.new_page(width=clip.width + GUTTER_PT, height=clip.height)
        canvas.show_pdf_page(pymupdf.Rect(GUTTER_PT, 0, GUTTER_PT + clip.width, clip.height),
                             pdf, page_number - 1, clip=clip)
        canvas.draw_line((GUTTER_PT - 3, 0), (GUTTER_PT - 3, clip.height),
                         color=(.6, .6, .6))
        for row in rows:
            y = float(row["row_y_pt"]) - clip.y0
            if not 0 < y < clip.height:
                raise ValueError(f"Row outside clip: {row['row_id']}")
            # The full ID remains in the manifest. Its page-local suffix is
            # unique in this crop and fits the gutter without distortion.
            label = row["row_id"].rsplit("::", 1)[1]
            canvas.insert_text((3, y + 2), label, fontsize=7)
        target.write_bytes(canvas.get_pixmap(dpi=dpi, alpha=False).tobytes("jpeg", jpg_quality=93))


def render_page(pdf: pymupdf.Document, meta: dict[str, str], rows: list[dict],
                dpi: int, region_ids: set[str] | None = None) -> tuple[list[dict], str]:
    number = int(meta["pdf_page"])
    page = pdf[number - 1]
    titles = headings(page)
    ordered = sorted(rows, key=lambda row: (float(row["row_y_pt"]), row["row_id"]))
    problems = []
    usable = []
    if len(rows) != int(meta["anchor_count"]):
        raise ValueError(f"Anchor count mismatch: {meta['doc_id']}:{number}")
    for row in ordered:
        y = float(row["row_y_pt"])
        if not math.isfinite(y) or not page.rect.y0 < y < page.rect.y1:
            problems.append("invalid_anchor_coordinates")
        else:
            usable.append(row)
    uncertain = sum(row["anchor_status"] == "uncertain_row" for row in usable)
    if uncertain:
        problems.append(f"uncertain_row_anchors:{uncertain}")
    for row in usable:
        if (row["anchor_status"] in {"candidate_numeric_row", "image_candidate_row"} and
                float(row["row_y_pt"]) < page.rect.y0 + page.rect.height * .08):
            problems.append(f"candidate_near_page_header:{row['row_id']}")
    if not any(row["anchor_status"] in {"candidate_numeric_row", "image_candidate_row"} for row in usable):
        problems.append("zero_candidate_anchors")
    if meta["audit_status"] not in {"anchored", "non_table"}:
        problems.append(f"page_audit:{meta['audit_status']}:{meta['reason']}")
    table_ids = meta["mapped_table_ids"].split(" | ") if meta["mapped_table_ids"] else []
    regions = []
    images = OUTPUT / "images"
    images.mkdir(parents=True, exist_ok=True)
    for index, group in enumerate(batches(usable, titles), 1):
        region_id = f"{meta['doc_id']}::p{number}::g{index}"
        if region_ids is not None and region_id not in region_ids:
            continue
        try:
            clip = clip_for(group, usable, titles, page.rect)
        except ValueError as exc:
            raise ValueError(f"{meta['doc_id']} page {number} region {index}: {exc}") from exc
        if region_ids is not None:
            # The last marker can be cut by the midpoint to the next row.
            # Keep the complete marked line; unmarked neighbours are context.
            clip.y1 = min(page.rect.y1, max(clip.y1, float(group[-1]["row_y_pt"]) + 10))
        relative = Path("output/render_abs_1911_source_regions/images") / f"{meta['doc_id']}_p{number}_g{index}_{dpi}dpi.jpg"
        image = ROOT / relative
        render_region(pdf, number, clip, group, image, dpi)
        header = header_clip(group, usable, titles, page.rect)
        header_path = None
        header_hash = None
        if header is not None:
            header_relative = relative.with_name(relative.stem + "_header.jpg")
            header_image = ROOT / header_relative
            header_image.write_bytes(page.get_pixmap(dpi=dpi, clip=header,
                                                      alpha=False).tobytes("jpeg", jpg_quality=93))
            header_path = header_relative.as_posix()
            header_hash = digest(header_image)
        else:
            problems.append(f"header_review_required:{region_id}")
        regions.append({
            "doc_id": meta["doc_id"], "pdf_page": number, "region_id": region_id,
            "source_pdf": meta["source_pdf"], "source_sha256": meta["source_sha256"],
            "table_ids": table_ids,
            "rows": [{"row_id": row["row_id"], "row_y_pt": float(row["row_y_pt"]),
                      "row_text": row["row_text"], "anchor_status": row["anchor_status"]}
                     for row in group],
            "clip_bbox_pt": [round(value, 2) for value in clip],
            "image_path": relative.as_posix(), "image_sha256": digest(image),
            "header_image_path": header_path, "header_image_sha256": header_hash,
        })
    return regions, "; ".join(dict.fromkeys(problems))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit-pages", type=int, help="Maximum input pages to process")
    parser.add_argument("--region-id", action="append",
                        help="Rerender exact region IDs with room below the last row")
    parser.add_argument("--start-after", help="Exclusive resume cursor doc_id:pdf_page")
    parser.add_argument("--dpi", type=int, default=180, help="Rendered image resolution (default: 180)")
    args = parser.parse_args()
    if args.limit_pages is not None and args.limit_pages < 1:
        parser.error("--limit-pages must be positive")
    if args.dpi < 72:
        parser.error("--dpi must be at least 72")
    pages = read_csv(INPUT / "pages.csv", PAGE_FIELDS)
    rows = read_csv(INPUT / "rows.csv", ROW_FIELDS)
    image_input = ROOT / "output/build_abs_1911_image_rows"
    image_pages = (read_csv(image_input / "pages.csv", PAGE_FIELDS)
                   if (image_input / "pages.csv").exists() else [])
    image_rows = (read_csv(image_input / "rows.csv", ROW_FIELDS)
                  if (image_input / "rows.csv").exists() else [])
    if bool(image_pages) != bool(image_rows):
        raise ValueError("Image-page audit and row candidates must both exist")
    by_page: dict[tuple[str, int], list[dict]] = defaultdict(list)
    seen_ids: set[str] = set()
    for row in rows:
        key = (row["doc_id"], int(row["pdf_page"]))
        if not re.fullmatch(r"[A-Za-z0-9_-]+", row["doc_id"]):
            raise ValueError(f"Unsafe document ID: {row['doc_id']!r}")
        prefix = f"{row['doc_id']}::p{key[1]}::r"
        if not row["row_id"].startswith(prefix) or not row["row_id"][len(prefix):].isdigit():
            raise ValueError(f"Malformed source row ID: {row['row_id']!r}")
        if row["row_id"] in seen_ids:
            raise ValueError(f"Duplicate source row ID: {row['row_id']!r}")
        seen_ids.add(row["row_id"])
        if row["anchor_status"] not in {"candidate_numeric_row", "uncertain_row"}:
            raise ValueError(f"Unknown anchor status: {row['anchor_status']}")
        by_page[key].append(row)
    ordered = sorted(pages, key=lambda row: (row["doc_id"], int(row["pdf_page"])))
    keys = [(row["doc_id"], int(row["pdf_page"])) for row in ordered]
    if len(keys) != len(set(keys)) or set(by_page) - set(keys):
        raise ValueError("Duplicate page audit or anchors without a page audit")
    page_by_key = {(row["doc_id"], int(row["pdf_page"])): row for row in pages}
    image_by_key: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for row in image_rows:
        image_by_key[(row["doc_id"], int(row["pdf_page"]))].append(row)
    if {(row["doc_id"], int(row["pdf_page"])) for row in image_pages} != set(image_by_key):
        raise ValueError("Image-row candidates and page audit differ")
    for audit in image_pages:
        key = (audit["doc_id"], int(audit["pdf_page"]))
        original = page_by_key.get(key)
        if (original is None or original["audit_status"] != "text_limited"
                or audit["audit_status"] != "image_derived_unverified"
                or int(audit["anchor_count"]) != len(image_by_key[key])
                or any(audit[field] != original[field] for field in
                       ("source_pdf", "source_sha256", "mapped_table_ids"))):
            raise ValueError(f"Image candidates do not match mapped text-limited page: {key}")
        for row in image_by_key[key]:
            if (row["anchor_status"] != "image_candidate_row"
                    or any(row[field] != original[field] for field in
                           ("source_pdf", "source_sha256", "mapped_table_ids"))):
                raise ValueError(f"Image candidate provenance mismatch: {row['row_id']}")
        by_page[key] = image_by_key[key]
        original["anchor_count"] = audit["anchor_count"]
        original["reason"] += "; image-derived row positions unverified"
    if args.start_after:
        try:
            doc_id, page = args.start_after.rsplit(":", 1)
            cursor = (doc_id, int(page))
            start = keys.index(cursor) + 1
        except (ValueError, IndexError) as exc:
            parser.error(f"Unknown --start-after page: {args.start_after!r} ({exc})")
        ordered = ordered[start:]
    if args.limit_pages is not None:
        ordered = ordered[:args.limit_pages]
    region_ids = set(args.region_id) if args.region_id else None
    if region_ids is not None:
        if len(region_ids) != len(args.region_id):
            parser.error("Duplicate --region-id")
        pages_to_render = set()
        for region_id in region_ids:
            match = re.fullmatch(r"(.+)::p([1-9]\d*)::g[1-9]\d*", region_id)
            if match is None:
                parser.error(f"Invalid --region-id: {region_id}")
            pages_to_render.add((match[1], int(match[2])))
        if pages_to_render - set(keys):
            parser.error(f"Unknown --region-id page: {pages_to_render - set(keys)}")
        ordered = [meta for meta in ordered
                   if (meta["doc_id"], int(meta["pdf_page"])) in pages_to_render]
        if len(ordered) != len(pages_to_render):
            parser.error("--region-id cannot be combined with page cursor or limit")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = OUTPUT / "regions.jsonl"
    review_path = OUTPUT / "page_review.csv"
    if region_ids is not None and not manifest.exists():
        parser.error("--region-id requires an existing region manifest")
    retained: list[dict] = []
    if manifest.exists():
        retained = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line]
    review: dict[tuple[str, int], str] = {}
    if review_path.exists():
        review = {(row["doc_id"], int(row["pdf_page"])): row["reason"]
                  for row in read_csv(review_path, REVIEW_FIELDS)}
    selected = {(row["doc_id"], int(row["pdf_page"])) for row in ordered}
    if region_ids is None:
        retained = [row for row in retained
                    if (row["doc_id"], row["pdf_page"]) not in selected]
    else:
        retained = [row for row in retained if row["region_id"] not in region_ids]
    if region_ids is None:
        for key in selected:
            review.pop(key, None)
    hashes: dict[Path, str] = {}
    open_pdf: pymupdf.Document | None = None
    last_source: Path | None = None
    try:
        for meta in ordered:
            key = (meta["doc_id"], int(meta["pdf_page"]))
            source = source_path(meta["source_pdf"])
            if source not in hashes:
                hashes[source] = digest(source)
            if hashes[source] != meta["source_sha256"]:
                raise ValueError(f"Source PDF hash mismatch: {meta['source_pdf']}")
            page_rows = by_page[key]
            for row in page_rows:
                if any(row[field] != meta[field] for field in
                       ("doc_id", "pdf_page", "source_pdf", "source_sha256", "mapped_table_ids")):
                    raise ValueError(f"Anchor/page provenance mismatch: {row['row_id']}")
            if source != last_source:
                if open_pdf is not None:
                    open_pdf.close()
                open_pdf = pymupdf.open(source)
                last_source = source
            if not 1 <= key[1] <= len(open_pdf):
                raise ValueError(f"PDF page outside source: {key}")
            regions, reason = render_page(open_pdf, meta, page_rows, args.dpi, region_ids)
            retained.extend(regions)
            if region_ids is None and meta["mapped_table_ids"] and reason:
                review[key] = reason
    finally:
        if open_pdf is not None:
            open_pdf.close()
    if region_ids is not None:
        missing = region_ids - {row["region_id"] for row in retained}
        if missing:
            raise ValueError(f"Requested regions missing from source rows: {missing}")
    retained.sort(key=lambda region: (region["doc_id"], region["pdf_page"],
                                      int(region["region_id"].rsplit("::g", 1)[1])))
    atomic_text(manifest, "".join(json.dumps(region, ensure_ascii=False) + "\n" for region in retained))
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=REVIEW_FIELDS)
    writer.writeheader()
    writer.writerows({"doc_id": doc, "pdf_page": page, "reason": reason}
                     for (doc, page), reason in sorted(review.items()))
    atomic_text(review_path, buffer.getvalue())
    print(f"Processed {len(ordered)} pages; {len(retained)} manifest regions; "
          f"{len(review)} pages for review")


if __name__ == "__main__":
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "render.lock").open("a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        main()
