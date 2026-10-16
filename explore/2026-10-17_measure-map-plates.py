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

# The NSW panel records one representative plate per census; the full NSW plate list is
# documented in data/raw/historical_boundary_maps/README.md and the panel notes.
NSW_PLATES = {
    'abs1911_statisticians_report_nsw_sydney_lga_maps': [444, 457],
    'abs1921_statisticians_report_nsw_sydney_lga_maps': [394, 395, 407],
    'abs1933_statisticians_report_nsw_sydney_lga_maps': [468, 476],
    'abs1947_statisticians_report_nsw_sydney_lga_maps': [392, 399],
    'abs_1954_nsw_population_lga_maps': [194, 196],
    'abs_1961_nsw_population_lga_maps': [129, 130, 131],
    'abs_1966_nsw_population_dwellings_lga_maps': list(range(509, 521)),
    'abs_1971_bulletin13_colour_lga_maps': [3, 17],
    'anu_1966_nsw_bulletin1_8_with_lga_maps': [40, 41, 48],
    'abs_1971_nsw_field_count_statement_lga': [39, 40, 41],
    'anu1976_nsw_preliminary_lga_boundary_maps': [60, 61, 62],
    'abs_1981_nsw_lga_urban_centres_with_maps': [62, 64, 66],
    'anu_1981_nsw_lga_urban_centres_with_maps': [36, 37, 38],
}
NSW_FILES = {
    'abs1911_statisticians_report_nsw_sydney_lga_maps': 'data/raw/historical_boundary_maps/abs_census/abs1911_statisticians_report_nsw_sydney_lga_maps.pdf',
    'abs1921_statisticians_report_nsw_sydney_lga_maps': 'data/raw/historical_boundary_maps/abs_census/abs1921_statisticians_report_nsw_sydney_lga_maps.pdf',
    'abs1933_statisticians_report_nsw_sydney_lga_maps': 'data/raw/historical_boundary_maps/abs_census/abs1933_statisticians_report_nsw_sydney_lga_maps.pdf',
    'abs1947_statisticians_report_nsw_sydney_lga_maps': 'data/raw/historical_boundary_maps/abs_census/abs1947_statisticians_report_nsw_sydney_lga_maps.pdf',
    'abs_1954_nsw_population_lga_maps': 'data/raw/historical_boundary_maps/abs_census/abs_1954_nsw_population_lga_with_maps.pdf',
    'abs_1961_nsw_population_lga_maps': 'data/raw/historical_boundary_maps/abs_census/abs_1961_nsw_population_lga_with_maps.pdf',
    'abs_1966_nsw_population_dwellings_lga_maps': 'data/raw/historical_boundary_maps/abs_census/abs_1966_nsw_population_dwellings_lga_with_maps.pdf',
    'abs_1971_bulletin13_colour_lga_maps': 'data/raw/historical_boundary_maps/abs_census/abs_1971_bulletin13_statistical_division_colour_lga_maps.pdf',
    'anu_1966_nsw_bulletin1_8_with_lga_maps': 'data/raw/historical_boundary_maps/abs_census/anu_1966_nsw_bulletin1_8_with_lga_maps.pdf',
    'abs_1971_nsw_field_count_statement_lga': 'data/raw/historical_boundary_maps/abs_census/abs_1971_nsw_field_count_statement_lga.pdf',
    'anu1976_nsw_preliminary_lga_boundary_maps': 'data/raw/historical_boundary_maps/abs_census/anu1976_nsw_preliminary_lga_boundary_maps.pdf',
    'abs_1981_nsw_lga_urban_centres_with_maps': 'data/raw/historical_boundary_maps/abs_census/abs_1981_nsw_lga_urban_centres_with_maps.pdf',
    'anu_1981_nsw_lga_urban_centres_with_maps': 'data/raw/historical_boundary_maps/abs_census/anu_1981_nsw_lga_urban_centres_with_maps.pdf',
}
NSW_YEARS = {
    'abs1911_statisticians_report_nsw_sydney_lga_maps': 1911,
    'abs1921_statisticians_report_nsw_sydney_lga_maps': 1921,
    'abs1933_statisticians_report_nsw_sydney_lga_maps': 1933,
    'abs1947_statisticians_report_nsw_sydney_lga_maps': 1947,
    'abs_1954_nsw_population_lga_maps': 1954,
    'abs_1961_nsw_population_lga_maps': 1961,
    'abs_1966_nsw_population_dwellings_lga_maps': 1966,
    'abs_1971_bulletin13_colour_lga_maps': 1971,
    'anu_1966_nsw_bulletin1_8_with_lga_maps': 1966,
    'abs_1971_nsw_field_count_statement_lga': 1971,
    'anu1976_nsw_preliminary_lga_boundary_maps': 1976,
    'abs_1981_nsw_lga_urban_centres_with_maps': 1981,
    'anu_1981_nsw_lga_urban_centres_with_maps': 1981,
}
for source_id, pages in NSW_PLATES.items():
    sources.append(dict(scope='nsw', census_year=str(NSW_YEARS[source_id]), state_code='nsw',
                        source_id=source_id, local_path=NSW_FILES[source_id],
                        pages=';'.join(str(p) for p in pages), role='census_report_plate'))

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
