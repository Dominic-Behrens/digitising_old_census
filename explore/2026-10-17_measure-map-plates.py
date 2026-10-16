# Purpose: measure every candidate census map plate (NSW and other states): native resolution,
#   page size, colour mode, tonal contrast and any text-layer map cues (scale bar, graticule).
# Inputs: the two map_source_candidates.csv files and the raw PDFs/images they reference.
# Outputs: explore/output/2026-10-17_map-digitisation-readiness/plate_metrics.csv
import csv
import io
import re
import statistics
from pathlib import Path

import pymupdf
from PIL import Image, ImageOps

ROOT = Path('.').resolve()
OUT = ROOT / 'explore/output/2026-10-17_map-digitisation-readiness'
OUT.mkdir(parents=True, exist_ok=True)

sources = []
for path, scope in [(ROOT / 'explore/output/2026-10-16_other-states-lga-census-panel/map_source_candidates.csv', 'other_states'),
                    (ROOT / 'explore/output/2026-10-14_nsw-lga-census-panel/sydney_map_source_candidates.csv', 'nsw')]:
    if not path.is_file():
        continue
    with path.open(newline='', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            sources.append(dict(scope=scope, census_year=row['census_year'],
                                state_code=row.get('state_code', 'nsw'), source_id=row['source_record_id'],
                                local_path=row['local_path'], pages=row['pdf_map_pages'], role=row['role']))

rows = []
for source in sources:
    path = ROOT / source['local_path']
    if not path.is_file():
        rows.append(dict(scope=source['scope'], census_year=source['census_year'], state_code=source['state_code'],
                         source_id=source['source_id'], role=source['role'], page='', status='missing_file'))
        continue
    if path.suffix.lower() in ('.jpg', '.jpeg', '.png'):
        image = Image.open(path)
        grey = ImageOps.grayscale(image)
        rows.append(dict(scope=source['scope'], census_year=source['census_year'], state_code=source['state_code'],
                         source_id=source['source_id'], role=source['role'], page='image', status='ok',
                         native_width=image.width, native_height=image.height, page_width_pt='', page_height_pt='',
                         colour_mode=image.mode, contrast=round(statistics.pstdev(list(grey.getdata())[::37]), 1),
                         scale_bar='', graticule='', text_head=''))
        continue
    with pymupdf.open(path) as document:
        pages = [int(p) for p in re.split(r'[;,\s]+', source['pages']) if p.isdigit()]
        for page_no in pages:
            if not 1 <= page_no <= document.page_count:
                continue
            page = document[page_no - 1]
            infos = page.get_image_info()
            largest = max(infos, key=lambda i: i['width'] * i['height']) if infos else None
            pix = page.get_pixmap(dpi=90)
            grey = (Image.frombytes('L', (pix.width, pix.height), pix.samples) if pix.n == 1
                    else Image.open(io.BytesIO(pix.tobytes('png'))).convert('L'))
            text = page.get_text()
            rows.append(dict(scope=source['scope'], census_year=source['census_year'], state_code=source['state_code'],
                             source_id=source['source_id'], role=source['role'], page=page_no, status='ok',
                             native_width=largest['width'] if largest else 0,
                             native_height=largest['height'] if largest else 0,
                             page_width_pt=round(page.rect.width), page_height_pt=round(page.rect.height),
                             colour_mode=pix.n, contrast=round(statistics.pstdev(list(grey.getdata())[::37]), 1),
                             scale_bar='yes' if re.search(r'SCALE', text.upper()) else '',
                             graticule='yes' if re.search(r'\d+\s*[°º]\s*\d*', text) else '',
                             text_head=re.sub(r'\s+', ' ', text.strip())[:120]))
    print(f"{source['census_year']} {source['state_code']}: {len(pages)} pages", flush=True)

fields = ['scope', 'census_year', 'state_code', 'source_id', 'role', 'page', 'status', 'native_width',
          'native_height', 'page_width_pt', 'page_height_pt', 'colour_mode', 'contrast', 'scale_bar',
          'graticule', 'text_head']
with (OUT / 'plate_metrics.csv').open('w', newline='', encoding='utf-8') as handle:
    writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
print(f'wrote {OUT/"plate_metrics.csv"} ({len(rows)} rows)')
