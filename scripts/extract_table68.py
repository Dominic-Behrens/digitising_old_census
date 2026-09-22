"""Extract the NSW LGA table from the 1911 Dwellings volume, without API calls.

The historical script name is retained. The contents and adjacent pages call this
Table 68, but physical PDF page 186 (zero-based index 185) actually prints 69.
NSW occupies physical pages 183--187, printed pages 2031--2035.

Input: data/raw/abs_1911_census/1911 Census - Volume III - Part XIII Dwellings.pdf
Outputs: data/intermediate/nsw_1911_lga_dwellings.csv and output/extract_table68/.
"""
import csv
import hashlib
from pathlib import Path
import re
import statistics

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
pdf_path = ROOT / "data/raw/abs_1911_census/1911 Census - Volume III - Part XIII Dwellings.pdf"
OUT = ROOT / "data/intermediate/nsw_1911_lga_dwellings.csv"
AUDIT_DIR = ROOT / "output/extract_table68"
FIELDS = ["lga_name", "area", "males", "females", "persons", "persons_per_area",
          "occupied_dwellings", "dwellings_per_area", "population_per_dwelling"]
INTEGER_FIELDS = {"area", "males", "females", "persons", "occupied_dwellings"}
NUMERIC_FIELDS = FIELDS[1:]
CSV_FIELDS = ["lga_name", "section", *NUMERIC_FIELDS, "area_unit", "source_pdf",
              "source_pdf_sha256", "source_page_index", "source_pdf_page",
              "source_printed_page", "source_table_number_printed",
              "source_row_number", "source_row_y", "source_image"]

# Grid lines measured on the scan, in PDF points. Odd/even pages are offset;
# using token starts (rather than character centres) shifts multi-column tokens.
BOUNDARIES = {
    182: [212, 248, 284, 320, 355, 390, 425, 461],
    183: [205, 241, 276, 312, 348, 383, 419, 454],
    184: [213, 248, 284, 320, 355, 391, 426, 461],
    185: [204, 240, 275, 311, 347, 382, 418, 454],
    186: [232, 268, 303, 339, 375, 410, 446, 482],
}
SLOPES = {182: 0, 183: 0, 184: .006, 185: .003, 186: -.002}
# Body windows exclude headings and published subtotal/summary rows. The section
# boundary on index 184 follows the printed SHIRES heading, not a name heuristic.
BODY_RANGES = {
    182: [(194, 815, "municipality")],
    183: [(183, 803, "municipality")],
    184: [(185, 696, "municipality"), (726, 810, "shire")],
    185: [(183, 810, "shire")],
    186: [(173, 691, "shire")],
}
EXPECTED_COUNTS = {(182, "municipality"): 65, (183, "municipality"): 69,
                   (184, "municipality"): 56, (184, "shire"): 10,
                   (185, "shire"): 70, (186, "shire"): 54}

# Explicit image-backed corrections, never residuals chosen to balance totals.
# Key: zero-based PDF index, uncorrected full-width name, field.
# Values are transcribed from the row image; extraction emits before/after cells,
# page/row coordinates, explanations, and rendered evidence alongside the CSV.
SOURCE_CORRECTIONS = {
    (182, "Bowral", "dwellings_per_area"): ("0.110", "Printed .110; OCR .no."),
    (182, "Brewarrina", "dwellings_per_area"): ("0.011", "Printed .011; OCR .Oll."),
    (182, "Cabramatta and Canley Vale", "population_per_dwelling"): ("4.51", "Printed 4.51; OCR decimal comma."),
    (182, "Cowra", "dwellings_per_area"): ("0.114", "Printed .114; OCR letter l."),
    (182, "Glebe", "area"): ("521", "Printed 521; OCR 5!!1."),
    (182, "Ermington and Rydalme~~", "lga_name"): ("Ermington and Rydalmere", "Image supplies final name letters."),
    (182, "Glen InllEls", "lga_name"): ("Glen Innes", "Name transcribed from scan."),
    (183, "Grafton, South", "males"): ("610", "Printed 610; OCR 1510."),
    (183, "GranvilIe", "lga_name"): ("Granville", "Name transcribed from scan."),
    (183, "HilIston", "lga_name"): ("Hillston", "Name transcribed from scan."),
    (183, "Kempsey", "population_per_dwelling"): ("5.04", "Printed 5.04; OCR 5.(14."),
    (183, "Lambton, New", "females"): ("894", "Printed 894; OCR 891."),
    (183, "Lane Cove", "females"): ("1667", "Printed 1,667; OCR ),667."),
    (183, "Mosman", "males"): ("5836", "Printed 5,836; OCR 6,836."),
    (183, "MurWl'llumbah", "lga_name"): ("Murwillumbah", "Name transcribed from scan."),
    (183, "Narrandera", "females"): ("1163", "Printed 1,163; OCR loses first 1 and comma."),
    (183, "Narromine", "females"): ("628", "Printed 628; border stroke read as leading 1."),
    (183, "Peak H ill", "lga_name"): ("Peak Hill", "OCR inserts an internal space in Hill."),
    (184, "Sydney", "occupied_dwellings"): ("18463", "Printed 18,463; OCR 18;463."),
    (184, "Ulladulla.", "dwellings_per_area"): ("0.011", "Printed .011; OCR .ou."),
    (184, "Wickham", "population_per_dwelling"): ("4.79", "Printed 4.79; OCR t.79."),
    (184, "Ashford", "dwellings_per_area"): ("0.255", "Printed .255; OCR loses decimal point."),
    (185, "Cessnock", "occupied_dwellings"): ("4312", "Printed 4,312; OCR 4.312."),
    (185, "Colo", "persons_per_area"): ("3.46", "Printed 3.46; OCR 3:46."),
    (185, "Macleay", "persons"): ("6679", "Printed 6,679; OCR adds stray leading dot."),
    (186, "MurrmIgal", "lga_name"): ("Murrungal", "Name transcribed from scan."),
    (186, "Tenterfield", "females"): ("2230", "Printed 2,230; OCR bounding box shifted down to Terania."),
    (186, "Terania", "females"): ("2421", "Printed 2,421; preceding row's 2,230 OCR overlaps this row."),
    (186, "Vlaradgery", "lga_name"): ("Waradgery", "Name transcribed from scan."),
    (186, "W ollondilly", "lga_name"): ("Wollondilly", "OCR splits initial W; old name filter omitted this entire shire."),
}

# Each independently printed total is retained, even when repeated in SUMMARY.
# Manual transcription is necessary because summary rules/merged OCR tokens cross
# cells. These are source observations, not targets used by the row extractor.
# id, index, y, group, area unit, area/M/F/P/P-area/dwellings/D-area/P-dwelling.
PUBLISHED_TOTALS = [
    ("municipality_subtotal", 184, 705, "municipality", "acres",
     ["1916800", "514873", "526886", "1041759", "0.54", "206312", "0.108", "5.05"]),
    ("shire_subtotal", 186, 702, "shire", "square_miles",
     ["181201", "323759", "255204", "578963", "3.20", "120517", "0.665", "4.80"]),
    ("municipality_summary", 186, 741, "municipality", "acres",
     ["1916800", "514873", "526886", "1041759", "0.54", "206312", "0.108", "5.05"]),
    ("shire_summary", 186, 757, "shire", "square_miles",
     ["181201", "323759", "255204", "578963", "3.20", "120517", "0.665", "4.80"]),
    ("not_incorporated_summary", 186, 765, "not_incorporated", "square_miles",
     ["125264", "11589", "6372", "17961", "0.14", "4147", "0.033", "4.33"]),
    ("whole_state_summary", 186, 781, "whole_state", "square_miles",
     ["309460", "850221", "788462", "1638683", "5.30", "330976", "1.070", "4.95"]),
    ("shipping_summary", 186, 789, "shipping", "not_applicable",
     ["", "7477", "574", "8051", "", "", "", ""]),
    ("total_population", 186, 805, "total_population", "not_applicable",
     ["", "857698", "789036", "1646734", "", "", "", ""]),
]


def get_cols(page_idx):
    cuts = BOUNDARIES[page_idx]
    return list(zip([0, *cuts], [*cuts, 530]))




def is_numeric(s):
    return bool(re.fullmatch(r"\d+(?:\.\d+)?", s))


def clean_name(s):
    return re.sub(r"\s+", " ", s).strip(" .")


def clean_num(s):
    """Remove grouping and edge rule/leader artifacts, not ambiguous OCR digits."""
    s = s.strip(" ,'·*I").replace(" ", "").replace(",", "").rstrip(".")
    return "0" + s if s.startswith(".") else s


def source_metadata(page_idx, y, sha256=""):
    return {
        "source_pdf": pdf_path.relative_to(ROOT).as_posix(),
        "source_pdf_sha256": sha256,
        "source_page_index": page_idx,
        "source_pdf_page": page_idx + 1,
        "source_printed_page": page_idx + 1849,
        "source_table_number_printed": 69 if page_idx == 185 else 68,
        "source_row_y": round(y, 2),
        "source_image": f"output/extract_table68/evidence/pdf_page_{page_idx + 1}.png",
    }


def extract_page(page_idx, document):
    """Return full-width name-anchored rows and untouched character cell strings.

    Name words are joined using their geometric gaps, including lower-case words
    and one-letter fragments. Numeric cells use character centres inside the
    printed grid, avoiding whole-token column shifts and adjacent border strokes.
    Scan skew is removed before matching rows; real OCR displacement is corrected
    only by SOURCE_CORRECTIONS with image evidence.
    """
    page = document[page_idx]
    words = page.get_text("words")
    chars = [c for block in page.get_text("rawdict")["blocks"] if block["type"] == 0
             for line in block["lines"] for span in line["spans"] for c in span["chars"]]
    cols = get_cols(page_idx)
    slope = SLOPES[page_idx]
    rows = []
    for low, high, section in BODY_RANGES[page_idx]:
        candidates = [w for w in words if w[2] < cols[0][1]
                      and low < (w[1] + w[3]) / 2 < high
                      and any(c.isalpha() for c in w[4])]
        candidates.sort(key=lambda w: (w[1] + w[3]) / 2)
        groups = []
        for word in candidates:
            y = (word[1] + word[3]) / 2 - slope * ((word[0] + word[2]) / 2 - 100)
            if groups and abs(y - statistics.mean(item[0] for item in groups[-1])) < 3:
                groups[-1].append((y, word))
            else:
                groups.append([(y, word)])
        for group in groups:
            y = statistics.mean(item[0] for item in group)
            name_words = sorted((item[1] for item in group), key=lambda w: w[0])
            name = ""
            for i, word in enumerate(name_words):
                if i and word[0] - name_words[i - 1][2] > 1:
                    name += " "
                name += word[4]
            raw = {"lga_name": name}
            for field, (lo, hi) in zip(NUMERIC_FIELDS, cols[1:]):
                selected = []
                for char in chars:
                    x0, y0, x1, y1 = char["bbox"]
                    x, cy = (x0 + x1) / 2, (y0 + y1) / 2
                    if lo + 2 < x < hi - 2 and abs(cy - slope * (x - 100) - y) < 3.7:
                        selected.append(char)
                selected.sort(key=lambda c: c["bbox"][0])
                raw[field] = "".join(c["c"] for c in selected).strip()
            row = {"lga_name": clean_name(name), "section": section,
                   **{field: clean_num(raw[field]) for field in NUMERIC_FIELDS},
                   "area_unit": "acres" if section == "municipality" else "square_miles",
                   **source_metadata(page_idx, y), "source_row_number": len(rows) + 1,
                   "raw_cells": raw}
            rows.append(row)
    return rows


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    sha256 = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    rows, cells, corrections = [], [], []
    applied = set()
    evidence_dir = AUDIT_DIR / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    with pymupdf.open(pdf_path) as document:
        for page_idx in BODY_RANGES:
            document[page_idx].get_pixmap(matrix=pymupdf.Matrix(2, 2)).save(
                evidence_dir / f"pdf_page_{page_idx + 1}.png")
            for row in extract_page(page_idx, document=document):
                row["source_pdf_sha256"] = sha256
                raw = row.pop("raw_cells")
                for field in FIELDS:
                    key = (page_idx, raw["lga_name"], field)
                    before = row[field]
                    if key in SOURCE_CORRECTIONS:
                        value, reason = SOURCE_CORRECTIONS[key]
                        row[field] = value
                        applied.add(key)
                        corrections.append({
                            **source_metadata(page_idx, row["source_row_y"], sha256),
                            "source_row_number": row["source_row_number"],
                            "source_lga_name": raw["lga_name"], "field": field,
                            "raw_value": raw[field], "automatic_value": before,
                            "corrected_value": value, "evidence": reason,
                        })
                    cells.append({"source_page_index": page_idx,
                                  "source_pdf_page": page_idx + 1,
                                  "source_row_number": row["source_row_number"],
                                  "source_row_y": row["source_row_y"],
                                  "source_lga_name": raw["lga_name"], "field": field,
                                  "raw_value": raw[field], "automatic_value": before,
                                  "final_value": row[field],
                                  "image_corrected": key in SOURCE_CORRECTIONS})
                # Fail rather than silently deleting unexpected OCR characters or
                # turning missing values into zero. Arithmetic is validate.py's job.
                for field in NUMERIC_FIELDS:
                    if not is_numeric(row[field]) or (field in INTEGER_FIELDS and "." in row[field]):
                        raise ValueError(f"Unresolved source cell: page {page_idx + 1}, "
                                         f"{row['lga_name']}, {field}={row[field]!r}")
                rows.append(row)
    if applied != SOURCE_CORRECTIONS.keys():
        raise ValueError(f"Source corrections did not match extraction: {SOURCE_CORRECTIONS.keys() - applied}")
    totals = []
    for total_id, page_idx, y, group, unit, values in PUBLISHED_TOTALS:
        totals.append({"total_id": total_id, "group": group, "area_unit": unit,
                       **dict(zip(NUMERIC_FIELDS, values)),
                       **source_metadata(page_idx, y, sha256),
                       "transcription_method": "manual_image_transcription"})
    write_csv(OUT, CSV_FIELDS, rows)
    write_csv(AUDIT_DIR / "extraction_cells.csv", list(cells[0]), cells)
    write_csv(AUDIT_DIR / "corrections.csv", list(corrections[0]), corrections)
    write_csv(AUDIT_DIR / "published_totals.csv", list(totals[0]), totals)
    source_notes = [{
        "category": "printed_table_number_discrepancy", "source_page_index": 185,
        "source_pdf_page": 186, "source_printed_page": 2034,
        "source_table_number_printed": 69, "contents_table_number": 68,
        "evidence": "This continuation prints 69; neighbouring NSW pages and contents say 68. "
                    "Preserve the printed heading without creating another analytical table.",
    }]
    write_csv(AUDIT_DIR / "source_notes.csv", list(source_notes[0]), source_notes)
    print(f"Extracted {len(rows)} LGAs; applied {len(corrections)} image-backed cell/name corrections.")
    print(f"Data: {OUT}")
    print(f"Source cells, corrections, totals, and page images: {AUDIT_DIR}")
    print("Run scripts/validate.py for independent row and published-total checks.")


if __name__ == "__main__":
    main()
