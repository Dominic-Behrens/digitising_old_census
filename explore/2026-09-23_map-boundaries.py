# Source-page map audit. Inputs: reviewed page map and original 1911 PDFs.
# Outputs: explore/output/2026-09-23_map-boundaries/{candidates.csv,images/}.
# A candidate is an assigned-table transition without a detected page-top
# numbered heading; it is not automatically a map error.
from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path
import re

import pymupdf
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw/abs_1911_census"
INPUT = ROOT / "output/build_abs_1911_table_spans/abs_1911_reviewed_pages.csv"
OUTPUT = ROOT / "explore/output/2026-09-23_map-boundaries"
FIELDS = ["doc_id", "pdf_page", "previous_table_ids", "assigned_table_ids",
          "following_table_ids", "source_pdf", "source_sha256", "image_path",
          "image_sha256"]
HEADING = re.compile(r"^(\d{1,3})[.~-–—:]+", re.I)


def main() -> None:
    with INPUT.open(newline="", encoding="utf-8-sig") as stream:
        pages = list(csv.DictReader(stream))
    by_doc: dict[str, list[dict[str, str]]] = {}
    for row in pages:
        by_doc.setdefault(row["doc_id"], []).append(row)
    (OUTPUT / "images").mkdir(parents=True, exist_ok=True)
    candidates = []
    for doc_id, records in sorted(by_doc.items()):
        records.sort(key=lambda row: int(row["pdf_page"]))
        relative = records[0]["local_path"].replace("\\", "/")
        source = (ROOT / relative).resolve(strict=True)
        if not source.is_relative_to(SOURCE.resolve(strict=True)):
            raise ValueError(f"Source PDF outside immutable corpus: {relative}")
        source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
        with pymupdf.open(source) as pdf:
            if len(pdf) != len(records):
                raise ValueError(f"Reviewed map misses physical pages: {doc_id}")
            for i, row in enumerate(records):
                if i == 0 or not row["table_ids"] or not records[i - 1]["table_ids"]:
                    continue
                if row["table_ids"] == records[i - 1]["table_ids"]:
                    continue
                page = pdf[i]
                if any(HEADING.match(word[4]) for word in page.get_text("words")
                       if word[1] < 135):
                    continue
                number = i + 1
                frames = []
                for offset in (-1, 0, 1):
                    nearby = pdf[i + offset] if 0 <= i + offset < len(pdf) else None
                    if nearby is None:
                        continue
                    clip = pymupdf.Rect(0, 0, nearby.rect.width, min(nearby.rect.height, 255))
                    pix = nearby.get_pixmap(dpi=110, clip=clip, alpha=False)
                    frames.append((number + offset,
                                   Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")))
                width = max(image.width for _, image in frames)
                result = Image.new("RGB", (width, sum(image.height + 30 for _, image in frames)), "white")
                pen = ImageDraw.Draw(result)
                y = 0
                for physical_page, image in frames:
                    pen.text((10, y + 8), f"{doc_id}  ORIGINAL PDF physical page {physical_page}", fill="black")
                    result.paste(image, (0, y + 30))
                    y += image.height + 30
                relative_image = Path("explore/output/2026-09-23_map-boundaries/images") / f"{doc_id}_p{number}.jpg"
                image_path = ROOT / relative_image
                result.save(image_path, "JPEG", quality=90, optimize=True)
                if " | " in row["table_ids"] or " | " in records[i - 1]["table_ids"]:
                    # The second numbered table can start far below the
                    # page-top strip; retain the full original page too.
                    full = page.get_pixmap(dpi=110, alpha=False)
                    full_path = image_path.with_name(image_path.stem + "_full.jpg")
                    Image.open(io.BytesIO(full.tobytes("png"))).save(
                        full_path, "JPEG", quality=90, optimize=True)
                candidates.append({"doc_id": doc_id, "pdf_page": number,
                    "previous_table_ids": records[i - 1]["table_ids"],
                    "assigned_table_ids": row["table_ids"],
                    "following_table_ids": records[i + 1]["table_ids"] if i + 1 < len(records) else "",
                    "source_pdf": relative, "source_sha256": source_sha256,
                    "image_path": relative_image.as_posix(),
                    "image_sha256": hashlib.sha256(image_path.read_bytes()).hexdigest()})
    temporary = OUTPUT / "candidates.csv.tmp"
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(candidates)
    temporary.replace(OUTPUT / "candidates.csv")
    print(f"Rendered {len(candidates)} transition contact sheets from {len(by_doc)} original PDFs")


if __name__ == "__main__":
    main()
