# Purpose: render contact sheets of every candidate map plate so digitisation readiness
#   can be judged visually (boundary line work, graticule, coastline, scale bar, contrast).
# Inputs: the two map_source_candidates tables; raw PDFs under data/raw/.
# Outputs: /tmp/rate/<census_year>_sheet<n>.png contact sheets (throwaway review aid).
import csv
import io
import math
import re
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

ROOT = Path('.')
OUT = Path('/tmp/rate')
OUT.mkdir(parents=True, exist_ok=True)

sources = []
for path, scope in [(ROOT / 'explore/output/2026-10-16_other-states-lga-census-panel/map_source_candidates.csv', 'other'),
                    (ROOT / 'explore/output/2026-10-14_nsw-lga-census-panel/sydney_map_source_candidates.csv', 'nsw')]:
    with path.open(newline='', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            sources.append(dict(scope=scope, year=int(row['census_year']),
                                state=row.get('state_code', 'nsw'), source_id=row['source_record_id'],
                                local_path=row['local_path'], pages=row['pdf_map_pages'],
                                role=row['role']))

# One plate per state-year for the review sheet (first listed page), plus the statewide
# plate where a page list holds several.
plates = []
for source in sources:
    if source['role'] == 'no_candidate_map_found':
        continue
    pages = [int(p) for p in re.split(r'[;,\s]+', source['pages']) if p.isdigit()]
    if not pages:
        continue
    plates.append((source, pages))

for year in sorted({p[0]['year'] for p in plates}):
    selection = [p for p in plates if p[0]['year'] == year]
    thumbs = []
    for source, pages in selection:
        path = ROOT / source['local_path']
        if not path.is_file():
            continue
        if path.suffix.lower() in ('.jpg', '.jpeg', '.png'):
            image = Image.open(path)
            image.thumbnail((430, 430))
            thumbs.append((f"{source['state']} {source['source_id'][:24]} img", image))
            continue
        with pymupdf.open(path) as document:
            for page_no in pages[:2]:
                if not 1 <= page_no <= document.page_count:
                    continue
                target_dpi = 150 if document[page_no - 1].rect.width < 220 else 42
                pix = document[page_no - 1].get_pixmap(dpi=target_dpi)
                image = Image.open(io.BytesIO(pix.tobytes('png')))
                thumbs.append((f"{source['state']} {Path(source['local_path']).name[:26]} p{page_no}", image))
    if not thumbs:
        continue
    columns = 4
    cell_w = max(t[1].width for t in thumbs) + 10
    cell_h = max(t[1].height for t in thumbs) + 26
    rows = math.ceil(len(thumbs) / columns)
    canvas = Image.new('RGB', (columns * cell_w, rows * cell_h), 'white')
    draw = ImageDraw.Draw(canvas)
    for index, (label, image) in enumerate(thumbs):
        row, column = divmod(index, columns)
        x, y = column * cell_w + 4, row * cell_h + 20
        canvas.paste(image.convert('RGB'), (x, y))
        draw.text((x, row * cell_h + 4), label, fill='red')
    for sheet_no, start in enumerate(range(0, len(thumbs), 12), 1):
        chunk = thumbs[start:start + 12]
        rows = math.ceil(len(chunk) / columns)
        canvas = Image.new('RGB', (columns * cell_w, rows * cell_h), 'white')
        draw = ImageDraw.Draw(canvas)
        for index, (label, image) in enumerate(chunk):
            row, column = divmod(index, columns)
            x, y = column * cell_w + 4, row * cell_h + 20
            canvas.paste(image.convert('RGB'), (x, y))
            draw.text((x, row * cell_h + 4), label, fill='red')
        target = OUT / f'{year}_sheet{sheet_no}.png'
        canvas.save(target)
        print(f'{target} {canvas.size} ({len(chunk)} plates)')
