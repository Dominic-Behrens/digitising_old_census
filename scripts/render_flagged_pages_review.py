"""
Render flagged 1911 census pages for manual QA.

Input: data/intermediate/page_inventory/abs_1911_index_guided_pages_review.csv
Outputs:
- output/diagnostics/flagged_pages/review_index.csv
- output/diagnostics/flagged_pages/index.html
- output/diagnostics/flagged_pages/<doc_id>/*.png
"""

from __future__ import annotations

import argparse
import csv
import html
import pathlib
import re
from collections import Counter

import fitz


DEFAULT_INPUT = pathlib.Path(
    "data/intermediate/page_inventory/abs_1911_index_guided_pages_review.csv"
)
DEFAULT_OUTPUT = pathlib.Path("output/diagnostics/flagged_pages")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=pathlib.Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=pathlib.Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--zoom", type=float, default=2.0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "unknown"


def read_rows(path: pathlib.Path, limit: int | None) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    return rows[:limit] if limit else rows


def image_name(row: dict[str, str]) -> str:
    candidates = slug(row.get("candidate_table_numbers", "none"))
    matched = slug(row.get("matched_table_numbers", "none"))
    return (
        f"p{int(row['pdf_page']):04d}_"
        f"role_{slug(row.get('page_role', 'unknown'))}_"
        f"cand_{candidates}_match_{matched}.png"
    )


def render_images(rows: list[dict[str, str]], output_dir: pathlib.Path, zoom: float, overwrite: bool) -> None:
    matrix = fitz.Matrix(zoom, zoom)
    docs: dict[str, fitz.Document] = {}
    try:
        for row in rows:
            pdf_path = pathlib.Path(row["local_path"])
            doc_id = row["doc_id"]
            doc_dir = output_dir / doc_id
            doc_dir.mkdir(parents=True, exist_ok=True)
            image_path = doc_dir / image_name(row)
            row["image_path"] = image_path.as_posix()

            if image_path.exists() and not overwrite:
                continue

            key = str(pdf_path)
            if key not in docs:
                docs[key] = fitz.open(pdf_path)
            page = docs[key][int(row["page_index"])]
            pix = page.get_pixmap(matrix=matrix)
            pix.save(str(image_path))
    finally:
        for doc in docs.values():
            doc.close()


def write_review_index(rows: list[dict[str, str]], output_dir: pathlib.Path) -> pathlib.Path:
    path = output_dir / "review_index.csv"
    fields = [
        "doc_id",
        "pdf_page",
        "page_index",
        "page_role",
        "candidate_table_numbers",
        "matched_table_numbers",
        "visible_titles",
        "warnings",
        "image_path",
        "review_decision",
        "review_notes",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            out = {field: row.get(field, "") for field in fields}
            out["review_decision"] = ""
            out["review_notes"] = ""
            writer.writerow(out)
    return path


def html_cell(value: str) -> str:
    return html.escape(value or "")


def write_html(rows: list[dict[str, str]], output_dir: pathlib.Path) -> pathlib.Path:
    path = output_dir / "index.html"
    role_counts = Counter(row.get("page_role", "") for row in rows)
    doc_counts = Counter(row.get("doc_id", "") for row in rows)
    rows_html = []
    for row in rows:
        image_rel = pathlib.Path(row["image_path"]).relative_to(output_dir).as_posix()
        rows_html.append(
            "<section class='card'>"
            f"<h2>{html_cell(row['doc_id'])} - PDF page {html_cell(row['pdf_page'])}</h2>"
            "<div class='meta'>"
            f"<strong>Role:</strong> {html_cell(row.get('page_role', ''))} "
            f"<strong>Candidates:</strong> {html_cell(row.get('candidate_table_numbers', ''))} "
            f"<strong>Matched:</strong> {html_cell(row.get('matched_table_numbers', ''))}"
            "</div>"
            f"<p><strong>Visible titles:</strong> {html_cell(row.get('visible_titles', ''))}</p>"
            f"<p><strong>Warnings:</strong> {html_cell(row.get('warnings', ''))}</p>"
            f"<img src='{html.escape(image_rel)}' alt='Rendered page'>"
            "</section>"
        )

    role_summary = ", ".join(f"{html_cell(k)}: {v}" for k, v in role_counts.most_common())
    doc_summary = ", ".join(f"{html_cell(k)}: {v}" for k, v in doc_counts.most_common())
    content = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>1911 Census Flagged Page Review</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; background: #f5f5f5; color: #111; }}
.summary {{ background: #fff; padding: 16px; border: 1px solid #ddd; margin-bottom: 18px; }}
.card {{ background: #fff; padding: 16px; border: 1px solid #ddd; margin-bottom: 24px; }}
h1 {{ margin-top: 0; }}
h2 {{ font-size: 18px; margin: 0 0 8px; }}
.meta {{ margin-bottom: 8px; }}
.meta strong {{ margin-left: 12px; }}
.meta strong:first-child {{ margin-left: 0; }}
img {{ width: 100%; max-width: 1400px; border: 1px solid #ccc; background: #fff; }}
</style>
</head>
<body>
<h1>1911 Census Flagged Page Review</h1>
<div class="summary">
<p><strong>Total flagged pages:</strong> {len(rows)}</p>
<p><strong>By role:</strong> {role_summary}</p>
<p><strong>By document:</strong> {doc_summary}</p>
<p>Edit <code>review_index.csv</code> for review decisions and notes.</p>
</div>
{''.join(rows_html)}
</body>
</html>
"""
    path.write_text(content, encoding="utf-8")
    return path


def main() -> None:
    args = parse_args()
    rows = read_rows(args.input, args.limit)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    render_images(rows, args.output_dir, args.zoom, args.overwrite)
    csv_path = write_review_index(rows, args.output_dir)
    html_path = write_html(rows, args.output_dir)

    print(f"Rows rendered: {len(rows)}")
    print(f"Review CSV: {csv_path}")
    print(f"HTML index: {html_path}")
    print(f"Image root: {args.output_dir}")


if __name__ == "__main__":
    main()
