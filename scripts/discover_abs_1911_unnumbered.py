"""Queue possible independent unnumbered 1911 data tables for source review.

Inputs (read-only):
  output/build_abs_1911_table_spans/abs_1911_reviewed_pages.csv
  output/build_abs_1911_table_spans/abs_1911_reviewed_table_index.csv
  The 14 source PDFs named by the reviewed page map.
Outputs (script-owned):
  output/discover_abs_1911_unnumbered/page_cache.sqlite (resumable page scan)
  output/discover_abs_1911_unnumbered/page_audit.csv (every physical page)
  output/discover_abs_1911_unnumbered/candidates.csv (review queue only)
  output/discover_abs_1911_unnumbered/summary.json (coverage, not completeness of tables)

Offline PyMuPDF text/geometry screening is fallible, especially on OCR-poor scans.
Neither a mapped numbered label nor an empty candidate queue establishes that an
unnumbered table is absent. Candidate records are NOT accepted table-index entries.
Run from the project root: python3 scripts/discover_abs_1911_unnumbered.py
"""

from __future__ import annotations

import argparse
import csv
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import tempfile
import os
from collections import Counter, defaultdict

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "output/build_abs_1911_table_spans/abs_1911_reviewed_pages.csv"
INDEX = ROOT / "output/build_abs_1911_table_spans/abs_1911_reviewed_table_index.csv"
DEFAULT_OUTPUT = ROOT / "output/discover_abs_1911_unnumbered"
EXPECTED_DOCS = 14
EXPECTED_PAGES = 2292
NUMBERED = re.compile(r"^\W*(?:NO\.?\s*)?[A-Za-z0-9()]{1,5}(?:\s*[.\-—–,:~·()]){1,8}\s*[\w\\]", re.I)
CONTINUED = re.compile(r"ntin|ntln|contd|tinned|rollti|(?:con|ont|tin).{0,5}(?:ued|ullcd|inued)", re.I)
NUMERIC = re.compile(r"[\d.,;:·—−–\-]{1,14}")
STOP = {"the", "and", "of", "in", "at", "to", "for", "a", "as", "by", "on", "from", "each", "of", "with", "census", "1911", "table", "number"}
CANDIDATE_FIELDS = (
    "candidate_id", "doc_id", "pdf_page", "source_path", "suspected_title",
    "title_bbox", "grid_bbox", "evidence_text", "numeric_rows_below",
    "mapped_table_ids", "status", "reason",
)
AUDIT_FIELDS = (
    "doc_id", "pdf_page", "source_path", "mapped_table_ids", "reviewed_page_role",
    "review_status", "page_width", "page_height", "text_line_count", "numeric_row_count",
    "title_like_count", "candidate_count", "audit_status", "reason",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def source_path(value: str) -> tuple[Path, str]:
    relative = Path(value.replace("\\", "/"))
    path = (ROOT / relative).resolve()
    if relative.is_absolute() or not path.is_relative_to(ROOT / "data/raw/abs_1911_census"):
        raise ValueError(f"PDF path outside source corpus: {value}")
    return path, path.relative_to(ROOT).as_posix()


def inventory(pages: list[dict[str, str]], index: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in pages:
        groups[row["doc_id"]].append(row)
    if len(groups) != EXPECTED_DOCS or len(pages) != EXPECTED_PAGES:
        raise ValueError(f"Expected {EXPECTED_DOCS} documents/{EXPECTED_PAGES} pages, got {len(groups)}/{len(pages)}")
    for doc_id, group in groups.items():
        counts = {int(row["page_count"]) for row in group}
        sources = {row["local_path"].replace("\\", "/") for row in group}
        if len(counts) != 1 or len(sources) != 1:
            raise ValueError(f"Inconsistent document metadata: {doc_id}")
        count = counts.pop()
        numbers = [int(row["pdf_page"]) for row in group]
        if sorted(numbers) != list(range(1, count + 1)) or any(int(row["page_index"]) + 1 != int(row["pdf_page"]) for row in group):
            raise ValueError(f"Missing, duplicate or misnumbered source page: {doc_id}")
        source_path(next(iter(sources)))
        group.sort(key=lambda row: int(row["pdf_page"]))
    if {row["doc_id"] for row in index} != set(groups):
        raise ValueError("Reviewed table index and reviewed pages disagree on documents")
    return dict(sorted(groups.items()))


def box(values: tuple[float, float, float, float] | list[float]) -> list[float]:
    return [round(float(v), 2) for v in values]


def clean(text: str) -> str:
    return " ".join(text.split())


def tokens(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) >= 3 and word not in STOP}


def same_title(title: str, other: str) -> bool:
    left, right = tokens(title), tokens(other)
    if not left or not right:
        return False
    overlap = len(left & right)
    if overlap >= 2 and overlap / min(len(left), len(right)) >= .85:
        return True
    a, b = " ".join(sorted(left)), " ".join(sorted(right))
    return len(left) >= 3 and SequenceMatcher(None, a, b).ratio() > .82


def text_lines(page: pymupdf.Page) -> list[dict]:
    lines = []
    for block in page.get_text("dict")["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            text = clean("".join(span["text"] for span in line["spans"]))
            if text:
                lines.append({"text": text, "bbox": box(line["bbox"])})
    return sorted(lines, key=lambda line: (line["bbox"][1], line["bbox"][0]))


def numeric_rows(page: pymupdf.Page) -> list[dict]:
    # A scan's text blocks can combine whole columns; spatial word rows are safer.
    bands: dict[int, list[tuple]] = defaultdict(list)
    for word in page.get_text("words"):
        text = word[4].strip("()[]{}'")
        if any(ch.isdigit() for ch in text) and NUMERIC.fullmatch(text):
            bands[round((word[1] + word[3]) / 18)].append(word)
    rows = []
    for words in bands.values():
        if len(words) < 4 or max(w[0] for w in words) - min(w[0] for w in words) < page.rect.width * .22:
            continue
        rows.append({"y": sum((w[1] + w[3]) / 2 for w in words) / len(words),
                     "bbox": box((min(w[0] for w in words), min(w[1] for w in words),
                                  max(w[2] for w in words), max(w[3] for w in words)))})
    return sorted(rows, key=lambda row: row["y"])


def heading_like(line: dict, width: float, height: float) -> bool:
    text = line["text"]
    x0, y0, x1, y1 = line["bbox"]
    letters = [ch for ch in text if ch.isalpha()]
    if not (height * .065 <= y0 < height * .86) or len(letters) < 17 or len(text) > 230:
        return False
    if x1 - x0 < width * .23 or not width * .23 < (x0 + x1) / 2 < width * .78:
        return False
    if text.lstrip().lower().startswith(("note.", "note-", "source:", "footnote")):
        return False
    if sum(ch.isalpha() or ch.isspace() for ch in text) / len(text) < .65:
        return False
    return sum(ch.isupper() for ch in letters) / len(letters) >= .61


def union_bbox(lines: list[dict]) -> list[float]:
    return box((min(line["bbox"][0] for line in lines), min(line["bbox"][1] for line in lines),
                max(line["bbox"][2] for line in lines), max(line["bbox"][3] for line in lines)))


def scan_page(page: pymupdf.Page, row: dict[str, str], catalogue: dict[str, list[str]], source: str) -> tuple[dict, list[dict]]:
    width, height = page.rect.width, page.rect.height
    lines = text_lines(page)
    grids = numeric_rows(page)
    headings = [line for line in lines if heading_like(line, width, height)]
    numbered = [line for line in lines if NUMBERED.match(line["text"]) and len(line["text"]) > 20
                and line["bbox"][2] - line["bbox"][0] > width * .2
                and height * .06 <= line["bbox"][1] < height * .86]
    contents_lines = [line for line in lines if re.search(r"\bCONTENTS\b", line["text"], re.I) and line["bbox"][1] < height * .3]
    mapped = row.get("table_ids", "")
    mapped_titles = [title for table_id in mapped.split(" | ") for title in catalogue.get(table_id, [])]
    # Existing reviewed visible titles supply additional continuation evidence, not a veto.
    mapped_titles += [text for text in row.get("visible_titles", "").split(" | ") if text]
    if row.get("confirmed_page_title"):
        mapped_titles.append(row["confirmed_page_title"])
    candidates = []
    considered = set()
    for heading in headings:
        x0, y0, x1, y1 = heading["bbox"]
        title = heading["text"]
        if NUMBERED.match(title) or CONTINUED.search(title) or re.search(r"\bCONTENTS\b", title, re.I):
            continue
        # The repeated volume running head can sit inside the title y-band.
        # It is not a second table merely because the page also contains a grid.
        if y0 < height * .11 and title.upper().startswith("CENSUS"):
            continue
        # A clipped continuation often leaves only a geographic/title suffix;
        # it is not a second independent table.
        if mapped and y0 < height * .2 and re.match(r"^(?:OF |THE |IN |AND |AGES IN |COMMONWEALTH |STATE |TERRITORY )", title, re.I) and len(tokens(title)) <= 5:
            continue
        if re.match(r"^(?:CLASS|ORDER|SUB-ORDER|SECTION|DIVISION|GROUP)\s+[IVX0-9]", title, re.I):
            continue  # Hierarchical labels inside a table or contents list.
        if any(abs(y0 - seen["bbox"][1]) < 19 and same_title(title, seen["text"]) for seen in headings if id(seen) in considered):
            continue
        if any(abs(y0 - known["bbox"][1]) < 34 for known in numbered):
            # This is likely the next printed line of the numbered title.
            continue
        if any(same_title(title, known) for known in mapped_titles):
            continue
        if contents_lines and y0 < max(line["bbox"][3] for line in contents_lines) + 80:
            continue
        below = [grid for grid in grids if y1 + 7 <= grid["y"] <= min(height - 35, y1 + height * .42)]
        if len(below) < 3:
            continue
        # Separate nearby heading fragments from their table body: several numeric
        # rows must belong to this region, before the next apparent title.
        next_heading = min((other["bbox"][1] for other in headings if other["bbox"][1] > y1 + 36), default=height)
        before_next = [grid for grid in below if grid["y"] < next_heading - 5]
        if len(before_next) < 3:
            continue
        if contents_lines and len(before_next) < 9:
            continue  # Contents rows with page references are not a data grid.
        # Nearby uppercase column headers often appear inside a numbered table;
        # retain them only when a clear whitespace break makes a new table plausible.
        above = [line for line in lines if line is not heading and line["bbox"][3] <= y0 and line["bbox"][1] > y0 - 30]
        last_above = max((line["bbox"][3] for line in above), default=0)
        if last_above and y0 - last_above < 7 and y0 > height * .17:
            continue
        evidence_rows = before_next[:min(5, len(before_next))]
        grid_bbox = union_bbox(evidence_rows)
        reason = ("Unnumbered title-like line with separate multi-row numeric region on a page already "
                  "mapped to numbered table(s); verify this is independent, not a subheading or OCR loss."
                  if mapped else
                  "Unnumbered title-like line with separate multi-row numeric region; verify a distinct analytical table.")
        candidates.append({
            "candidate_id": f"{row['doc_id']}::p{row['pdf_page']}::x{round(x0)}y{round(y0)}",
            "doc_id": row["doc_id"], "pdf_page": int(row["pdf_page"]),
            "source_path": source, "suspected_title": title,
            "title_bbox": json.dumps(heading["bbox"]), "grid_bbox": json.dumps(grid_bbox),
            "evidence_text": f"title={title}; numeric rows below={len(before_next)}; first grid y={evidence_rows[0]['y']:.1f}",
            "numeric_rows_below": len(before_next), "mapped_table_ids": mapped,
            "status": "candidate_needs_review", "reason": reason,
        })
        considered.add(id(heading))
    if candidates:
        status, reason = "candidate_needs_review", "One or more geometry-backed candidate regions require image/source review; mapping does not resolve independence."
    elif not lines or len(lines) < 8:
        status, reason = "text_limited_needs_review", "Text layer has fewer than eight lines; OCR geometry cannot rule out a table."
    elif contents_lines:
        status, reason = "screened_no_candidate", "Contents heading detected in source text; no separate region passed the title-and-grid screen. Not an absence claim."
    else:
        status, reason = "screened_no_candidate", "No separate unnumbered title-and-grid region passed this fallible text/geometry screen. Not an absence claim."
    audit = {
        "doc_id": row["doc_id"], "pdf_page": int(row["pdf_page"]), "source_path": source,
        "mapped_table_ids": mapped, "reviewed_page_role": row.get("final_page_role", ""),
        "review_status": row.get("review_status", ""), "page_width": round(width, 2),
        "page_height": round(height, 2), "text_line_count": len(lines),
        "numeric_row_count": len(grids), "title_like_count": len(headings),
        "candidate_count": len(candidates), "audit_status": status, "reason": reason,
    }
    return audit, candidates


def atomic_csv(path: Path, fields: tuple[str, ...], records: list[dict]) -> None:
    with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=path.parent, delete=False) as temp:
        name = temp.name
        writer = csv.DictWriter(temp, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    os.replace(name, path)


def atomic_json(path: Path, record: dict) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temp:
        name = temp.name
        json.dump(record, temp, indent=2, sort_keys=True)
        temp.write("\n")
    os.replace(name, path)


def run(output_dir: Path = DEFAULT_OUTPUT, pages_path: Path = PAGES, index_path: Path = INDEX) -> dict:
    pages = read_csv(pages_path)
    index = read_csv(index_path)
    groups = inventory(pages, index)
    catalogue: dict[str, list[str]] = defaultdict(list)
    for row in index:
        catalogue[f"{row['doc_id']}::{row['table_number']}"].append(row["table_title"])
    output_dir.mkdir(parents=True, exist_ok=True)
    algorithm = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    con = sqlite3.connect(output_dir / "page_cache.sqlite")
    try:
        con.execute("CREATE TABLE IF NOT EXISTS pages (doc_id TEXT NOT NULL, pdf_page INTEGER NOT NULL, fingerprint TEXT NOT NULL, audit TEXT NOT NULL, candidates TEXT NOT NULL, PRIMARY KEY(doc_id, pdf_page))")
        skipped = scanned = 0
        for doc_id, rows in groups.items():
            path, relative = source_path(rows[0]["local_path"])
            stat = path.stat()
            source_revision = (stat.st_size, stat.st_mtime_ns)
            with pymupdf.open(path) as pdf:
                if len(pdf) != len(rows):
                    raise ValueError(f"Reviewed/source page count mismatch for {doc_id}: {len(rows)} != {len(pdf)}")
                doc_titles = {key: value for key, value in catalogue.items() if key.startswith(f"{doc_id}::")}
                for row in rows:
                    number = int(row["pdf_page"])
                    fingerprint = hashlib.sha256(json.dumps([algorithm, row, doc_titles, source_revision], sort_keys=True).encode()).hexdigest()
                    old = con.execute("SELECT fingerprint, audit FROM pages WHERE doc_id=? AND pdf_page=?", (doc_id, number)).fetchone()
                    if old and old[0] == fingerprint and json.loads(old[1])["audit_status"] != "scan_error_needs_review":
                        skipped += 1
                        continue
                    try:
                        audit, candidates = scan_page(pdf[number - 1], row, catalogue, relative)
                    except Exception as exc:
                        audit = {"doc_id": doc_id, "pdf_page": number, "source_path": relative,
                                 "mapped_table_ids": row.get("table_ids", ""),
                                 "reviewed_page_role": row.get("final_page_role", ""),
                                 "review_status": row.get("review_status", ""),
                                 "page_width": "", "page_height": "", "text_line_count": "",
                                 "numeric_row_count": "", "title_like_count": "", "candidate_count": 0,
                                 "audit_status": "scan_error_needs_review", "reason": f"{type(exc).__name__}: {exc}"}
                        candidates = []
                    con.execute("INSERT OR REPLACE INTO pages VALUES (?, ?, ?, ?, ?)",
                                (doc_id, number, fingerprint, json.dumps(audit), json.dumps(candidates)))
                    con.commit()  # Each page survives interruption; never cache a failed scan as success.
                    scanned += 1
            print(f"{doc_id}: {len(rows)} pages, scanned {scanned}, reused {skipped}", flush=True)
        audit_rows, candidate_rows = [], []
        for doc_id, rows in groups.items():
            for row in rows:
                cached = con.execute("SELECT audit, candidates FROM pages WHERE doc_id=? AND pdf_page=?",
                                     (doc_id, int(row["pdf_page"]))).fetchone()
                if cached is None:
                    raise RuntimeError(f"Missing scan result: {doc_id} page {row['pdf_page']}")
                audit_rows.append(json.loads(cached[0]))
                candidate_rows.extend(json.loads(cached[1]))
        statuses = Counter(row["audit_status"] for row in audit_rows)
        summary = {
            "audit_scope": "all physical pages of the 14 reviewed 1911 Volume II-III part PDFs",
            "documents": len(groups), "source_pages": len(pages), "audited_pages": len(audit_rows),
            "pages_scanned_this_run": scanned, "pages_reused_from_cache": skipped,
            "pages_by_status": dict(sorted(statuses.items())),
            "candidate_records": len(candidate_rows),
            "candidate_pages": sum(row["candidate_count"] > 0 for row in audit_rows),
            "full_page_scan": len(audit_rows) == len(pages) and not statuses["scan_error_needs_review"],
            "source_verified_unnumbered_table_count": None,
            "interpretation": "Candidates need source-image review; no candidate is an indexed/verified table. No candidate is not evidence of absence, including on pages assigned numbered labels.",
            "outputs": {"page_audit": "page_audit.csv", "candidates": "candidates.csv", "cache": "page_cache.sqlite"},
        }
        atomic_csv(output_dir / "page_audit.csv", AUDIT_FIELDS, audit_rows)
        atomic_csv(output_dir / "candidates.csv", CANDIDATE_FIELDS, candidate_rows)
        atomic_json(output_dir / "summary.json", summary)
        return summary
    finally:
        con.close()


def render_review_images(output_dir: Path) -> None:
    """Render only flagged source pages; never modify a source PDF or candidate decision."""
    flagged = {}
    for row in read_csv(output_dir / "candidates.csv"):
        flagged[(row["doc_id"], int(row["pdf_page"]))] = row["source_path"]
    for row in read_csv(output_dir / "page_audit.csv"):
        if row["audit_status"] == "text_limited_needs_review":
            flagged[(row["doc_id"], int(row["pdf_page"]))] = row["source_path"]
    images = output_dir / "review_images"
    images.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for (doc_id, page), source in sorted(flagged.items()):
        grouped[doc_id].append((page, source))
    created = 0
    for doc_id, entries in grouped.items():
        path, _ = source_path(entries[0][1])
        with pymupdf.open(path) as pdf:
            for page, source in entries:
                if source_path(source)[0] != path:
                    raise ValueError(f"Inconsistent source document for {doc_id}")
                dest = images / f"{doc_id}_p{page}.jpg"
                if dest.exists():
                    continue
                raw = pdf[page - 1].get_pixmap(matrix=pymupdf.Matrix(120 / 72, 120 / 72),
                                               alpha=False).tobytes("jpeg", jpg_quality=82)
                dest.write_bytes(raw)
                created += 1
    print(f"Rendered {created} new source-page images from {len(flagged)} flagged pages in {images}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed-pages", type=Path, default=PAGES)
    parser.add_argument("--reviewed-index", type=Path, default=INDEX)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--render-review-images", action="store_true",
                        help="Render candidate and text-limited pages from an existing offline scan")
    args = parser.parse_args()
    if args.render_review_images:
        render_review_images(args.output_dir)
        return
    summary = run(args.output_dir, args.reviewed_pages, args.reviewed_index)
    print(json.dumps(summary, indent=2))
    if not summary["full_page_scan"]:
        raise SystemExit("One or more pages could not be scanned; inspect page_audit.csv")


if __name__ == "__main__":
    main()
