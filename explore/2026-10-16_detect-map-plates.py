# Purpose: detect map plates inside the ABS census LGA volumes for every state, 1911-1981,
#   and OCR each plate's title so every census-year roster can be linked to a candidate map.
# Inputs: PDFs in data/raw/historical_boundary_maps/abs_census/, the manifest written by
#   explore/2026-10-16_download-other-states-lga-census-maps.py, and the bundled OCR tools
#   in explore/output/2026-10-14_nsw-lga-census-panel/.ocr-tools/ (already extracted).
# Outputs: explore/output/2026-10-16_other-states-lga-census-panel/map_plate_inventory.csv,
#   map_plate_ocr.txt, status.json.
import csv
import io
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pymupdf
from PIL import Image, ImageOps

ROOT = Path('.').resolve()
RAW = ROOT / 'data/raw/historical_boundary_maps/abs_census'
OUT = ROOT / 'explore/output/2026-10-16_other-states-lga-census-panel'
OUT.mkdir(parents=True, exist_ok=True)
TESS_ROOT = ROOT / 'explore/output/2026-10-14_nsw-lga-census-panel/.ocr-tools/root'
os.environ['LD_LIBRARY_PATH'] = f'{TESS_ROOT}/usr/lib/x86_64-linux-gnu:{TESS_ROOT}/usr/lib'
os.environ['TESSDATA_PREFIX'] = f'{TESS_ROOT}/usr/share/tesseract-ocr/5/tessdata'
TESS = str(TESS_ROOT / 'usr/bin/tesseract')

VOLUMES = [
    # National volumes that hold the older statewide and metropolitan plates.
    ('abs1911_statisticians_report_nsw_sydney_lga_maps.pdf', 1911, 'national'),
    ('abs1921_statisticians_report_nsw_sydney_lga_maps.pdf', 1921, 'national'),
    ('abs1933_statisticians_report_nsw_sydney_lga_maps.pdf', 1933, 'national'),
    ('abs1947_statisticians_report_nsw_sydney_lga_maps.pdf', 1947, 'national'),
    ('abs_1971_bulletin13_statistical_division_colour_lga_maps.pdf', 1971, 'national'),
    ('abs_1981_nsw_lga_urban_centres_with_maps.pdf', 1981, 'nsw'),
]
# Every downloaded per-state volume is screened; the year and state come from the record id.
_manifest_path = ROOT / 'explore/output/2026-10-16_download-other-states-lga-census-maps/manifest.csv'
if _manifest_path.is_file():
    with _manifest_path.open(newline='', encoding='utf-8') as _handle:
        for _row in csv.DictReader(_handle):
            if _row['status'] != 'downloaded':
                continue
            _name = Path(_row['local_path']).name
            _match = re.match(r'abs_(\d{4})_([a-z]+)_', _name) or re.match(r'anu(\d{4})_([a-z]+)_', _name)
            if _match:
                VOLUMES.append((_name, int(_match.group(1)), _match.group(2)))

# De-duplicate while keeping order.
seen = set()
VOLUMES = [v for v in VOLUMES if not (v[0] in seen or seen.add(v[0]))]


def ocr_image(image_bytes_or_path, psm='11'):
    if isinstance(image_bytes_or_path, bytes):
        image = Image.open(io.BytesIO(image_bytes_or_path)).convert('L')
    else:
        image = Image.open(image_bytes_or_path).convert('L')
    if max(image.size) < 1400:
        scale = 1400 / max(image.size)
        image = image.resize((int(image.width * scale), int(image.height * scale)), Image.LANCZOS)
    image = ImageOps.autocontrast(image)
    target = '/tmp/_plate.png'
    image.save(target)
    result = subprocess.run([TESS, target, 'stdout', '--psm', psm], capture_output=True, text=True, env=os.environ)
    return result.stdout


def plate_pages(document):
    """Pages that carry an inserted map plate rather than a page scan."""
    found = []
    for index, page in enumerate(document):
        text = page.get_text().strip()
        infos = page.get_image_info()
        if not infos:
            continue
        largest = max(infos, key=lambda i: i['width'] * i['height'])
        area_share = (largest['width'] * largest['height']) / max(1.0, page.rect.width * page.rect.height)
        # Text pages carry an OCR text layer over the page scan. Plate pages are image-only
        # or caption-only. Keep both signals; OCR titles decide the state and map type.
        small_image = max(largest['width'], largest['height']) < 2200
        if len(text) < 150 or (small_image and len(text) < 400):
            found.append((index + 1, len(text), largest['width'], largest['height'],
                          round(area_share, 3), page.get_images(full=True)[0][0] if page.get_images(full=True) else 0))
    return found


rows = []
ocr_log = []
manifest = {}
manifest_path = ROOT / 'explore/output/2026-10-16_download-other-states-lga-census-maps/manifest.csv'
if manifest_path.is_file():
    with manifest_path.open(newline='', encoding='utf-8') as handle:
        manifest = {row['record_id']: row for row in csv.DictReader(handle)}

print(f'{len(VOLUMES)} volumes', flush=True)
for name, year, state in VOLUMES:
    path = RAW / name
    if not path.is_file():
        print(f'MISSING {name}', flush=True)
        continue
    with pymupdf.open(path) as document:
        pages = plate_pages(document)
        for page_no, text_len, width, height, share, xref in pages:
            title = ''
            try:
                info = document.extract_image(xref)
                text = ocr_image(info['image'])
                words = [w for w in text.split() if re.match(r"^[A-Za-z][A-Za-z\.\-']{3,}$", w)]
                title = ' '.join(words[:20])
            except Exception as exc:
                title = f'OCR_FAIL {exc}'
            rows.append(dict(file=name, census_year=year, state=state, pdf_page=page_no,
                             page_text_chars=text_len, image_width=width, image_height=height,
                             image_area_share=share, ocr_title_words=title))
            ocr_log.append(f'{name} p{page_no}: {title}')
    print(f'{name}: {len([r for r in rows if r["file"] == name])} plate pages', flush=True)

fields = ['file', 'census_year', 'state', 'pdf_page', 'page_text_chars', 'image_width',
          'image_height', 'image_area_share', 'ocr_title_words']
with (OUT / 'map_plate_inventory.csv').open('w', newline='', encoding='utf-8') as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
(OUT / 'map_plate_ocr.txt').write_text('\n'.join(ocr_log) + '\n', encoding='utf-8')
status = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(), state='finished',
              unit='volume plate screen', completed=len(VOLUMES), total=len(VOLUMES),
              plate_pages=len(rows), output='explore/output/2026-10-16_other-states-lga-census-panel/map_plate_inventory.csv')
(OUT / 'status.json').write_text(json.dumps(status, indent=2) + '\n', encoding='utf-8')
print(json.dumps(status))
