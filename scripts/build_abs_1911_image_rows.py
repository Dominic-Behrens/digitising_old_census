# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf>=1.24"]
# ///
"""Locate unverified image-geometry row candidates on mapped text-limited pages.

Only the original PDFs and the original page audit are read. No OCR, inferred
row numbering, transcription, or text-layer coordinates enter the candidates.
The separate output is deliberately not merged with PDF-text anchors.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data/raw/abs_1911_census"
INPUT = ROOT / "output/build_abs_1911_source_rows/pages.csv"
OUTPUT = ROOT / "output/build_abs_1911_image_rows"
ROW_FIELDS = ["doc_id", "pdf_page", "row_id", "row_y_pt", "row_text",
              "numeric_word_count", "source_pdf", "source_sha256",
              "mapped_table_ids", "anchor_status"]
PAGE_FIELDS = ["doc_id", "pdf_page", "source_pdf", "source_sha256",
               "mapped_table_ids", "anchor_count", "audit_status", "reason"]
DPI = 144
INK_THRESHOLD = 178
# A 42-pixel uninterrupted stroke is much longer than a printed word's
# individual glyphs; 28 vertical pixels is taller than the small table type.
HORIZONTAL_RULE_PX = 42
VERTICAL_RULE_PX = 28


def read_csv(path: Path, fields: list[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != fields:
            raise ValueError(f"Unexpected CSV columns in {path}: {reader.fieldnames}")
        return list(reader)


def source_path(relative: str) -> Path:
    path = Path(relative)
    if not relative or "\\" in relative or path.is_absolute() or ".." in path.parts or path.suffix.lower() != ".pdf":
        raise ValueError(f"Invalid original PDF path: {relative!r}")
    resolved = (ROOT / path).resolve(strict=True)
    if not resolved.is_relative_to(SOURCE_DIR.resolve(strict=True)):
        raise ValueError(f"PDF outside original corpus: {relative!r}")
    return resolved


def source_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def image_rows(page: pymupdf.Page, doc_id: str) -> tuple[list[float], str]:
    """Return PDF y coordinates of widespread horizontal ink bands, not text."""
    pix = page.get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY, alpha=False)
    width, height = pix.width, pix.height
    # No OCR or external image cache: all pixels are from this source PDF page.
    threshold = bytes(int(level < INK_THRESHOLD) for level in range(256))
    original = pix.samples.translate(threshold)
    ink = bytearray(original)
    left, right = int(width * .09), int(width * .91)
    # These body margins exclude visibly separate running heads and table
    # titles in the four source layouts; they are not reconstructed row grids.
    family = doc_id.rsplit("_", 1)[-1]
    body_top = {"birthplaces": .16, "education": .17,
                "schooling": .22, "religions": .27}[family]
    top, bottom = int(height * .14), int(height * .91)

    # Erase strokes that are demonstrably longer than table glyphs. Continuous
    # vertical grid segments otherwise turn many adjacent rows into one band;
    # horizontal separators otherwise masquerade as printed data lines.
    for y in range(top, bottom):
        base = y * width
        x = left
        while x < right:
            if not ink[base + x]:
                x += 1
                continue
            end = x + 1
            while end < right and ink[base + end]:
                end += 1
            if end - x >= HORIZONTAL_RULE_PX:
                ink[base + x:base + end] = bytes(end - x)
            x = end
    for x in range(left, right):
        y = top
        while y < bottom:
            if not ink[y * width + x]:
                y += 1
                continue
            end = y + 1
            while end < bottom and ink[end * width + x]:
                end += 1
            if end - y >= VERTICAL_RULE_PX:
                for line in range(y, end):
                    ink[line * width + x] = 0
            y = end

    # Horizontal strips, sampled across independent x cells, distinguish a
    # word-like text line from a speck or remnant of one grid intersection.
    cell_width = max(20, int(width * .024))
    profiles = []
    for y in range(top, bottom):
        base = y * width
        cells = set()
        count = 0
        for x in range(left, right):
            if ink[base + x]:
                count += 1
                cells.add((x - left) // cell_width)
        profiles.append((count, len(cells)))

    # At 144 dpi a glyph normally occupies 7-15 vertical pixels. Allow small
    # blank scan lines within a word, but never extrapolate a regular row grid
    # across empty space. Sparse printed ditto marks still generate candidates.
    active = [top + offset for offset, (count, cells) in enumerate(profiles)
              if count >= 8 and cells >= 3]
    bands: list[list[int]] = []
    for y in active:
        if bands and y - bands[-1][-1] <= 3:
            bands[-1].append(y)
        else:
            bands.append([y])

    found = []
    ambiguous = 0
    for band in bands:
        start, end = band[0], band[-1]
        if end - start < 2:
            continue
        if end - start > 25:
            # Touching type/grid or adjacent lines: preserve potentially real
            # data by splitting on local valleys rather than dropping the band.
            ambiguous += 1
            valleys = [y for y in range(start + 5, end - 4)
                       if profiles[y - top][0] <= min(profiles[y - top - 1][0], profiles[y - top + 1][0])
                       and profiles[y - top][0] < 12]
            cuts = [start, *[y for y in valleys if y - start >= 7], end + 1]
            parts = [(a, b - 1) for a, b in zip(cuts, cuts[1:]) if b - a >= 3]
            if not parts:
                parts = [(start, end)]
        else:
            parts = [(start, end)]
        for a, b in parts:
            # Centre of actual ink evidence, not a row index interpolated from
            # neighbouring rows. The pixmap maps linearly to page.rect.
            weighted = [(y, profiles[y - top][0]) for y in range(a, b + 1)]
            total = sum(weight for _, weight in weighted)
            if total < 22:
                continue
            centre = sum(y * weight for y, weight in weighted) / total
            found.append((round(page.rect.y0 + (centre + .5) * page.rect.height / height, 2),
                          max(weight for _, weight in weighted)))

    if family == "birthplaces":
        # The original Birthplaces pages print individual row numbers in a
        # narrow right-hand gutter. Detect glyph bands there, independently
        # of the dense ditto marks and vertical rules in the table interior.
        # Gutter position shifts slightly between scanned volumes/pages.
        options = []
        for step in range(79, 87):
            x0, x1 = int(width * step / 100), int(width * (step / 100 + .035))
            groups: list[list[tuple[int, int]]] = []
            for y in range(top, bottom):
                base = y * width
                count = sum(original[base + x0:base + x1])
                if count < 2:
                    continue
                if groups and y - groups[-1][-1][0] <= 2:
                    groups[-1].append((y, count))
                else:
                    groups.append([(y, count)])
            positions = [(sum(y * n for y, n in group) / sum(n for y, n in group) + .5)
                         * page.rect.height / height + page.rect.y0
                         for group in groups
                         if len(group) >= 3 and sum(n for _, n in group) >= 14]
            typical = sum(4 <= b - a <= 14 for a, b in zip(positions, positions[1:]))
            if len(positions) >= 40:
                options.append((typical, step, positions))
        if options:
            _, gutter, labels = max(options)
            # The first large white gap separates vertical heading lettering
            # from printed row numbers. Later section breaks are retained.
            for index, (a, b) in enumerate(zip(labels, labels[1:])):
                if b - a >= 26:
                    labels = labels[index + 1:]
                    break
            labels = [round(y, 2) for y in labels if y >= body_top * page.rect.height]
            # Totals are printed in table cells but have no gutter number.
            # Keep strongly inked non-gutter bands as unverified possibilities.
            extras = [(y, strength) for y, strength in found
                      if y >= labels[0] - 2 and strength >= 100
                      and all(abs(y - label) >= 4.2 for label in labels)] if labels else []
            found = [(y, 10000) for y in labels] + extras
            detail = f"right_gutter={gutter}% width; gutter_bands={len(labels)}"
        else:
            detail = "right_gutter=not_detected; full-width bands retained"
            found = [(y, strength) for y, strength in found
                     if y >= body_top * page.rect.height]
    else:
        detail = "full-width bands"
        found = [(y, strength) for y, strength in found
                 if y >= body_top * page.rect.height]
    # Broken ink can generate several peaks on a single printed line. Preserve
    # the strongest local evidence while leaving closely spaced actual rows.
    chosen: list[float] = []
    for y, _ in sorted(found, key=lambda item: (-item[1], item[0])):
        if all(abs(y - prior) >= 4.2 for prior in chosen):
            chosen.append(y)
    return sorted(chosen), (f"raster={DPI}dpi; ink_bands={len(bands)}; "
                            f"broad_bands={ambiguous}; {detail}; "
                            f"body_top={body_top:.0%}")


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit-pages", type=int, help="At most this many unprocessed image-only pages")
    parser.add_argument("--start-after", help="Resume after doc_id:pdf_page in page-audit order")
    args = parser.parse_args()
    if args.limit_pages is not None and args.limit_pages < 1:
        parser.error("--limit-pages must be positive")
    return args


def main() -> None:
    args = arguments()
    source_pages = read_csv(INPUT, PAGE_FIELDS)
    targets = [row for row in source_pages
               if row["mapped_table_ids"] and row["audit_status"] == "text_limited"]
    keys = [(row["doc_id"], int(row["pdf_page"])) for row in targets]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate mapped text-limited page in original audit")
    start = 0
    if args.start_after:
        doc_id, separator, number = args.start_after.rpartition(":")
        if not separator or not number.isdecimal() or (doc_id, int(number)) not in keys:
            raise ValueError("--start-after must identify a mapped text-limited doc_id:pdf_page")
        start = keys.index((doc_id, int(number))) + 1

    previous_pages = read_csv(OUTPUT / "pages.csv", PAGE_FIELDS) if (OUTPUT / "pages.csv").exists() else []
    previous_rows = read_csv(OUTPUT / "rows.csv", ROW_FIELDS) if (OUTPUT / "rows.csv").exists() else []
    if previous_rows and not previous_pages:
        raise ValueError("Image rows exist without a page audit")
    target_by_key = dict(zip(keys, targets))
    done = set()
    hashes: dict[Path, str] = {}
    for row in previous_pages:
        key = (row["doc_id"], int(row["pdf_page"]))
        if key not in target_by_key or key in done:
            raise ValueError(f"Unknown or duplicate image audit page: {key}")
        done.add(key)
        source = target_by_key[key]
        if any(row[field] != source[field] for field in
               ("source_pdf", "source_sha256", "mapped_table_ids")) or row["audit_status"] != "image_derived_unverified":
            raise ValueError(f"Original source/map or image audit changed for {key}")
    counts = {key: 0 for key in done}
    ids = set()
    for row in previous_rows:
        key = (row["doc_id"], int(row["pdf_page"]))
        counts[key] = counts.get(key, 0) + 1
        expected = f"{key[0]}::p{key[1]}::r{counts[key]}"
        source = target_by_key.get(key)
        if (key not in done or row["row_id"] != expected or row["row_id"] in ids
                or row["anchor_status"] != "image_candidate_row" or row["row_text"]
                or row["numeric_word_count"] != "0"
                or any(row[field] != source[field] for field in
                       ("source_pdf", "source_sha256", "mapped_table_ids"))):
            raise ValueError(f"Invalid existing image row: {row['row_id']}")
        ids.add(row["row_id"])
    for row in previous_pages:
        key = (row["doc_id"], int(row["pdf_page"]))
        if counts[key] != int(row["anchor_count"]):
            raise ValueError(f"Image row count mismatch: {key}")

    selected = [row for row in targets[start:]
                if (row["doc_id"], int(row["pdf_page"])) not in done]
    if args.limit_pages is not None:
        selected = selected[:args.limit_pages]
    for row in [*previous_pages, *selected]:
        path = source_path(row["source_pdf"])
        if path not in hashes:
            hashes[path] = source_hash(path)
        if hashes[path] != row["source_sha256"]:
            raise ValueError(f"Original source PDF hash mismatch: {row['source_pdf']}")

    new_pages = []
    new_rows = []
    documents: dict[Path, pymupdf.Document] = {}
    try:
        for meta in selected:
            path = source_path(meta["source_pdf"])
            if path not in documents:
                documents[path] = pymupdf.open(path)
            pdf = documents[path]
            page_no = int(meta["pdf_page"])
            if page_no < 1 or page_no > len(pdf):
                raise ValueError(f"Page outside original PDF: {meta['doc_id']}:{page_no}")
            found, metrics = image_rows(pdf[page_no - 1], meta["doc_id"])
            shared = {field: meta[field] for field in
                      ("doc_id", "pdf_page", "source_pdf", "source_sha256", "mapped_table_ids")}
            new_pages.append({**shared, "anchor_count": len(found),
                              "audit_status": "image_derived_unverified",
                              "reason": f"Source-image geometry only; {len(found)} candidate bands; {metrics}; headings, totals, split/merged and missed rows require review"})
            for number, y in enumerate(found, 1):
                new_rows.append({**shared, "row_id": f"{meta['doc_id']}::p{page_no}::r{number}",
                                 "row_y_pt": y, "row_text": "", "numeric_word_count": 0,
                                 "anchor_status": "image_candidate_row"})
    finally:
        for pdf in documents.values():
            pdf.close()

    order = {key: i for i, key in enumerate(keys)}
    all_pages = sorted([*previous_pages, *new_pages],
                       key=lambda row: order[(row["doc_id"], int(row["pdf_page"]))])
    all_rows = sorted([*previous_rows, *new_rows],
                      key=lambda row: (order[(row["doc_id"], int(row["pdf_page"]))],
                                       int(row["row_id"].rsplit("::r", 1)[1])))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "rows.csv", ROW_FIELDS, all_rows)
    write_csv(OUTPUT / "pages.csv", PAGE_FIELDS, all_pages)
    print(f"Processed {len(new_pages)} image-only pages; audit has {len(all_pages)} pages and {len(all_rows)} unverified candidate rows")
    for row in new_pages:
        print(f"{row['doc_id']}:{row['pdf_page']}: {row['anchor_count']} candidates")


if __name__ == "__main__":
    main()
