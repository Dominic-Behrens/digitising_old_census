# Purpose: download the ABS per-state census LGA volumes for Victoria, Queensland,
#   South Australia, Western Australia, Tasmania, the Northern Territory and the ACT,
#   for the census years 1911-1981, in the same raw format as the NSW LGA maps.
# Inputs: ABS AUSSTATS historical census publication pages (network); no local inputs.
# Outputs: PDFs in data/raw/historical_boundary_maps/abs_census/ (unchanged originals);
#   manifest.csv, catalogue_sources.csv, status.json in this script's explore/output/ folder.
# Note: 1911-1947 statewide maps come from the national Statistician's Report volumes that
#   are already saved for NSW; this script downloads the per-state roster volumes and the
#   later per-state LGA volumes that carry maps. 1971 maps come from the national
#   Bulletin 13 Statistical Division set that is already saved.
import csv
import hashlib
import html as html_module
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pymupdf
import requests

ROOT = Path('.')
RAW = ROOT / 'data/raw/historical_boundary_maps/abs_census'
OUT = ROOT / 'explore/output/2026-10-16_download-other-states-lga-census-maps'
OUT.mkdir(parents=True, exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)

FIELDS = ['record_id', 'title', 'date_label', 'kind', 'source_record', 'download_url',
          'local_path', 'bytes', 'sha256', 'width_px', 'height_px', 'pdf_pages',
          'downloaded_utc', 'status', 'error']

CATALOGUES = {
    1911: '2112.01911',
    1921: '2111.01921',
    1933: '2110.01933',
    1947: '2109.01947',
    1954: '2108.01954',
    1961: '2107.01961',
    1966: '2106.01966',
    1971: '2105.01971',
    1976: '2104.01976',
    1981: '2103.01981',
}

# State code -> catalogue state token used in file names.
STATES = {
    'vic': 'Victoria', 'qld': 'Queensland', 'sa': 'South Australia',
    'wa': 'Western Australia', 'tas': 'Tasmania', 'nt': 'Northern Territory',
    'act': 'Australian Capital Territory',
}

# Selection rules: (census_year, regex on catalogue file name, state code, map-bearing flag).
# Every non-NSW state-year roster volume is downloaded. Volume numbers were read off the
# ABS catalogue pages; the catalogue file name embeds volume, part and state.
RULES = [
    # 1911: the national Part XIII Dwellings volume (already in data/raw/abs_1911_census)
    # carries the per-state LGA tables; the Statistician's Report (already saved) carries
    # the state map plates. No separate per-state download needed.
    # 1921: Volume I Parts XI-XVI Population of LGA.
    (1921, r'1921 Census - Volume I - Part XI VICTORIA Population of LGA', 'vic'),
    (1921, r'1921 Census - Volume I - Part XII QUEENSLAND Population of LGA', 'qld'),
    (1921, r'1921 Census - Volume I - Part XIII SOUTH AUSTRALIA Population of LGA', 'sa'),
    (1921, r'1921 Census - Volume I - Part XIV WESTERN AUSTRALIA Population of LGA', 'wa'),
    (1921, r'1921 Census - Volume I - Part XV TASMANIA Population of LGA', 'tas'),
    (1921, r'1921 Census - Volume I - Part XVI TERRITORIES Population of LGA', 'nt_act'),
    # 1933: Volume I Parts II-VII Analysis of Population in LGA.
    (1933, r'1933 Census - Volume I - Part II VICTORIA Analysis of Population in LGA', 'vic'),
    (1933, r'1933 Census - Volume I - Part III QUEENSLAND Analysis of Population in LGA', 'qld'),
    (1933, r'1933 Census - Volume I - Part IV SOUTH AUSTRALIA Analysis of Population in LGA', 'sa'),
    (1933, r'1933 Census - Volume I - Part V WESTERN AUSTRALIA Analysis of Population in LGA', 'wa'),
    (1933, r'1933 Census - Volume I - Part VI TASMANIA Analysis of Population in LGA', 'tas'),
    (1933, r'1933 Census - Volume I - Part VII TERRITORIES Analysis of Population in LGA', 'nt_act'),
    # 1947: Volume I Parts II-VII Analysis of Population in LGA.
    (1947, r'1947 Census - Volume I - Part II VICTORIA Analysis of Population in LGA', 'vic'),
    (1947, r'1947 Census - Volume I - Part III QUEENSLAND Analysis of Population in LGA', 'qld'),
    (1947, r'1947 Census - Volume I - Part IV SOUTH AUSTRALIA Analysis of Population in LGA', 'sa'),
    (1947, r'1947 Census - Volume I - Part V WESTERN AUSTRALIA Analysis of Population in LGA', 'wa'),
    (1947, r'1947 Census - Volume I - Part VI TASMANIA Analysis of Population in LGA', 'tas'),
    (1947, r'1947 Census - Volume I - Part VII TERRITORIES Analysis of Population in LGA', 'nt_act'),
    # 1954: Volume N Part I Analysis of Population in LGA carries the state maps (NSW proof).
    (1954, r'1954 Census - Volume II - Part I VICTORIA Analysis of Population in LGA', 'vic'),
    (1954, r'1954 Census - Volume III - Part I QUEENSLAND Analysis of Population in LGA', 'qld'),
    (1954, r'1954 Census - Volume IV - Part I SOUTH AUSTRALIA Analysis of Population in LGA', 'sa'),
    (1954, r'1954 Census - Volume V - Part I WESTERN AUSTRALIA Analysis of Population in LGA', 'wa'),
    (1954, r'1954 Census - Volume VI - Part I TASMANIA Analysis of Population in LGA', 'tas'),
    (1954, r'1954 Census - Volume VII - Part I NORTHERN TERRITORY Population', 'nt'),
    (1954, r'1954 Census - Volume VII - Part III AUSTRALIAN CAPITAL TERRITORY Population', 'act'),
    # 1961: same series.
    (1961, r'1961 Census - Volume II - Part I VICTORIA Analysis of Population in LGA', 'vic'),
    (1961, r'1961 Census - Volume III - Part I QUEENSLAND Analysis of Population in LGA', 'qld'),
    (1961, r'1961 Census - Volume IV - Part I SOUTH AUSTRALIA Analysis of Population in LGA', 'sa'),
    (1961, r'1961 Census - Volume V - Part I WESTERN AUSTRALIA Analysis of Population in LGA', 'wa'),
    (1961, r'1961 Census - Volume VI - Part I TASMANIA Analysis of Population in LGA', 'tas'),
    (1961, r'1961 Census - Volume VII - Part I NORTHERN TERRITORY Population', 'nt'),
    (1961, r'1961 Census - Volume VII - Part III AUSTRALIAN CAPITAL TERRITORY Population', 'act'),
    # 1966: Volume 4 Population and Dwellings in LGA, Parts 2-7.
    (1966, r'1966 Census - Volume 4 Population and Dwellings in LGA - Part 2 VIC', 'vic'),
    (1966, r'1966 Census - Volume 4 Population and Dwellings in LGA - Part 3 QLD', 'qld'),
    (1966, r'1966 Census - Volume 4 Population and Dwellings in LGA - Part 4 SA', 'sa'),
    (1966, r'1966 Census - Volume 4 Population and Dwellings in LGA - Part 5 WA', 'wa'),
    (1966, r'1966 Census - Volume 4 Population and Dwellings in LGA - Part 6 TAS', 'tas'),
    (1966, r'1966 Census - Volume 4 Population and Dwellings in LGA - Part 7 NT and ACT', 'nt_act'),
    # 1971: Bulletin 6 Population and Dwellings in LGA, Parts 2-8; Bulletin 13 covers all
    # states in the national Statistical Division map set already saved.
    (1971, r'1971 Census - Bulletin No 6 - Population and Dwellings in LGA - Part 2 VIC', 'vic'),
    (1971, r'1971 Census - Bulletin No 6 - Population and Dwellings in LGA - Part 3 QLD', 'qld'),
    (1971, r'1971 Census - Bulletin No 6 - Population and Dwellings in LGA - Part 4 SA', 'sa'),
    (1971, r'1971 Census - Bulletin No 6 - Population and Dwellings in LGA - Part 5 WA', 'wa'),
    (1971, r'1971 Census - Bulletin No 6 - Population and Dwellings in LGA - Part 6 TAS', 'tas'),
    (1971, r'1971 Census - Bulletin No 6 - Population and Dwellings in LGA - Part 7 NT and ACT', 'nt_act'),
    (1971, r'1971 Census - Bulletin No 6 - Population and Dwellings in LGA - Part 8 AUSTRALIA', 'australia'),
    # 1976: per-state LGA bulletins (24270-24340). Map content is checked after download.
    (1976, r'1976_LGA_NSW\.pdf', 'nsw'),
    (1976, r'1976_LGA_VIC\.pdf', 'vic'),
    (1976, r'1976_LGA_QLD\.pdf', 'qld'),
    (1976, r'1976_LGA_SA\.pdf', 'sa'),
    (1976, r'1976_LGA_WA\.pdf', 'wa'),
    (1976, r'1976_LGA_TAS\.pdf', 'tas'),
    (1976, r'1976_LGA_NT\.pdf', 'nt'),
    (1976, r'1976_LGA_ACT\.pdf', 'act'),
    # 1981: per-state Population and Dwellings in LGA bulletins (24010-24080).
    (1981, r'1981_PD_LGA_NSW\.pdf', 'nsw'),
    (1981, r'1981_PD_LGA_VIC\.pdf', 'vic'),
    (1981, r'1981_PD_LGA_QLD\.pdf', 'qld'),
    (1981, r'1981_PD_LGA_SA\.pdf', 'sa'),
    (1981, r'1981_PD_LGA_WA\.pdf', 'wa'),
    (1981, r'1981_PD_LGA_TAS\.pdf', 'tas'),
    (1981, r'1981_PD_LGA_NT\.pdf', 'nt'),
    (1981, r'1981_PD_LGA_ACT\.pdf', 'act'),
]

DATE_LABELS = {
    1911: 'Census night 2-3 April 1911',
    1921: 'Census night 3-4 April 1921',
    1933: 'Census 30 June 1933',
    1947: 'Census 30 June 1947',
    1954: 'Census 30 June 1954',
    1961: 'Census 30 June 1961',
    1966: 'Census 30 June 1966',
    1971: 'Census 30 June 1971',
    1976: 'Census 30 June 1976',
    1981: 'Census 30 June 1981; published council geography 1 January 1981',
}

STATE_BY_CODE = {'vic': 'VIC', 'qld': 'QLD', 'sa': 'SA', 'wa': 'WA', 'tas': 'TAS',
                 'nt': 'NT', 'act': 'ACT', 'nt_act': 'NT_ACT', 'nsw': 'NSW',
                 'australia': 'AUST'}


def slug_for(year, state_code, catalogue_name):
    """Local file name in the style of the saved NSW maps."""
    state = STATE_BY_CODE[state_code]
    stem = catalogue_name.lower()
    if year == 1976:
        return f'abs_1976_{state.lower()}_lga.pdf'
    if year == 1981:
        return f'abs_1981_{state.lower()}_lga_urban_centres_with_maps.pdf'
    if year == 1971:
        return f'abs_1971_{state.lower()}_population_dwellings_lga_bulletin6.pdf'
    if year == 1966:
        return f'abs_1966_{state.lower()}_population_dwellings_lga_with_maps.pdf'
    return f'abs_{year}_{state.lower()}_population_lga_with_maps.pdf'


session = requests.Session()
session.headers['User-Agent'] = 'HistoricalBoundaryMapResearch/1.0 (census LGA map digitising)'


def fetch_catalogue(year):
    """Return list of (file_name, full_url, catalogue_no) from an AUSSTATS catalogue page."""
    url = f'https://www.abs.gov.au/AUSSTATS/abs@.nsf/DetailsPage/{CATALOGUES[year]}'
    response = session.get(url, timeout=60)
    response.raise_for_status()
    text = response.text
    records = []
    for match in re.finditer(r'href="(/AUSSTATS/FREE\.NSF/log\?openagent&[^"]+)"', text, re.I):
        href = html_module.unescape(match.group(1))
        body = href.split('log?openagent&', 1)[1]
        parts = body.split('&')
        records.append((parts[0], 'https://www.abs.gov.au' + href, parts[1] if len(parts) > 1 else ''))
    return records


manifest_path = OUT / 'manifest.csv'
existing = {}
if manifest_path.is_file():
    with manifest_path.open(newline='', encoding='utf-8') as handle:
        existing = {row['record_id']: row for row in csv.DictReader(handle)}

catalogue_rows = []
jobs = []
for year, pattern, state_code in RULES:
    records = fetch_catalogue(year)
    for file_name, url, catalogue_no in records:
        if re.search(pattern, file_name):
            record_id = f'abs_{year}_{state_code}_lga_maps'
            catalogue_rows.append(dict(census_year=year, state_code=state_code, state=STATE_BY_CODE[state_code],
                                       file_name=file_name, catalogue=catalogue_no, source_record=url))
            jobs.append((record_id, year, state_code, file_name, url))
            break
    else:
        raise RuntimeError(f'No catalogue match for {year} {pattern}')

# Fail loudly if the catalogue no longer yields a match for any planned rule.
assert len(jobs) == len(RULES), f'expected {len(RULES)} jobs, built {len(jobs)}'

with (OUT / 'catalogue_sources.csv').open('w', newline='', encoding='utf-8') as handle:
    writer = csv.DictWriter(handle, fieldnames=['census_year', 'state_code', 'state', 'file_name', 'catalogue', 'source_record'])
    writer.writeheader()
    writer.writerows(catalogue_rows)

started = time.monotonic()
new_successes = 0
skipped = 0
for index, (record_id, year, state_code, file_name, url) in enumerate(jobs, 1):
    row = existing.get(record_id, {})
    local_path = RAW / slug_for(year, state_code, file_name)
    if (row.get('status') == 'downloaded' and local_path.is_file()
            and local_path.stat().st_size == int(row.get('bytes', -1))):
        skipped += 1
        existing[record_id] = row
        continue
    status, error = 'downloaded', ''
    try:
        response = session.get(url, timeout=180)
        response.raise_for_status()
        content = response.content
        if not content.startswith(b'%PDF'):
            raise ValueError(f'not a PDF: first bytes {content[:8]!r}')
        local_path.write_bytes(content)
    except Exception as exc:  # keep the batch running; record the failure
        status, error = 'failed', f'{type(exc).__name__}: {exc}'
    row = dict(record_id=record_id, title=file_name, date_label=DATE_LABELS[year],
               kind='report_with_lga_boundary_maps', source_record=url, download_url=url,
               local_path=str(local_path.relative_to(ROOT)).replace('\\', '/'), bytes='', sha256='',
               width_px='', height_px='', pdf_pages='', status=status, error=error,
               downloaded_utc=datetime.now(timezone.utc).isoformat())
    if status == 'downloaded':
        data = local_path.read_bytes()
        row['bytes'] = str(len(data))
        row['sha256'] = hashlib.sha256(data).hexdigest()
        with pymupdf.open(local_path) as document:
            row['pdf_pages'] = str(document.page_count)
        new_successes += 1
    existing[record_id] = row
    print(f'[{index}/{len(jobs)}] {record_id}: {status} {row["bytes"]} bytes {row["pdf_pages"]} pages {error}')
    time.sleep(0.2)

with manifest_path.open('w', newline='', encoding='utf-8') as handle:
    writer = csv.DictWriter(handle, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(existing[record_id] for record_id, *_ in jobs)

# ANU holds the complete 1976 preliminary "Population and Dwellings in Local Government
# Areas and Urban Centres" series with the original boundary maps. The NSW item (20_084)
# is already saved as anu1976_nsw_preliminary_lga_boundary_maps.pdf; fetch the rest.
ANU_JOBS = [
    ('anu1976_vic_preliminary_lga_boundary_maps', '20_085', 'vic', '26a9c327-f334-4d72-aad8-ad7edc816dc2'),
    ('anu1976_qld_preliminary_lga_boundary_maps', '20_086', 'qld', 'a590efba-12bb-45de-bb27-e992239da909'),
    ('anu1976_sa_preliminary_lga_boundary_maps', '20_087', 'sa', '50e0f4b9-3a02-4ccd-aa2d-3b70d9fe3656'),
    ('anu1976_wa_preliminary_lga_boundary_maps', '20_088', 'wa', '2996a2b9-a170-4ae4-81ad-6ee6cabce76e'),
    ('anu1976_tas_preliminary_lga_boundary_maps', '20_089', 'tas', 'bbfe634a-4524-43e5-859c-f51c48436dff'),
    ('anu1976_nt_preliminary_lga_boundary_maps', '20_090', 'nt', '74cfb5e1-6829-4079-bd84-1e0ac6db3009'),
    ('anu1976_act_preliminary_lga_boundary_maps', '20_091', 'act', '4e065754-1a4c-482e-b087-4f5970638c01'),
]
for record_id, item_no, state_code, bitstream_id in ANU_JOBS:
    local_path = RAW / f'{record_id}.pdf'
    url = f'https://openresearch-repository.anu.edu.au/server/api/core/bitstreams/{bitstream_id}/content'
    row = existing.get(record_id, {})
    if (row.get('status') == 'downloaded' and local_path.is_file()
            and local_path.stat().st_size == int(row.get('bytes', -1))):
        continue
    status, error = 'downloaded', ''
    try:
        response = session.get(url, timeout=300)
        response.raise_for_status()
        content = response.content
        if not content.startswith(b'%PDF'):
            raise ValueError(f'not a PDF: first bytes {content[:8]!r}')
        local_path.write_bytes(content)
    except Exception as exc:
        status, error = 'failed', f'{type(exc).__name__}: {exc}'
    row = dict(record_id=record_id,
               title=f'1976 Census preliminary population and dwellings in LGAs: {state_code.upper()} boundary maps (ANU copy)',
               date_label=DATE_LABELS[1976], kind='report_with_lga_boundary_maps',
               source_record=f'https://openresearch-repository.anu.edu.au/items/{item_no}', download_url=url,
               local_path=str(local_path.relative_to(ROOT)).replace('\\', '/'), bytes='', sha256='',
               width_px='', height_px='', pdf_pages='', status=status, error=error,
               downloaded_utc=datetime.now(timezone.utc).isoformat())
    if status == 'downloaded':
        data = local_path.read_bytes()
        row['bytes'] = str(len(data))
        row['sha256'] = hashlib.sha256(data).hexdigest()
        with pymupdf.open(local_path) as document:
            row['pdf_pages'] = str(document.page_count)
        new_successes += 1
    existing[record_id] = row
    print(f'ANU {record_id}: {status} {row["bytes"]} bytes {row["pdf_pages"]} pages {error}')


# National Statistician's Reports for 1954 and 1961 carry statewide LGA map plates, and the
# 1971 field count statements per state give the published LGA index used for the panel rosters.
EXTRA_CATALOGUE_FILES = [
    ('abs_1954_statisticians_report', 1954, 'census_report',
     r'1954 Census - Volume VIII - Part IV Statisticians Report'),
    ('abs_1961_statisticians_report', 1961, 'census_report',
     r'1961 Census - Volume VIII - Part IV Statisticians Report'),
]
FIELD_COUNT_STATES = {'No 3': 'nsw', 'No 4': 'vic', 'No 5': 'qld', 'No 6': 'sa',
                      'No 7': 'wa', 'No 8': 'tas', 'No 9': 'nt_act'}

extra_jobs = []
for record_id, year, kind, pattern in EXTRA_CATALOGUE_FILES:
    local_path = RAW / f'{record_id}.pdf'
    extra_jobs.append((record_id, year, kind, pattern, local_path))
for year in (1971,):
    for label, state_code in FIELD_COUNT_STATES.items():
        record_id = f'abs_1971_{state_code}_field_count'
        pattern = rf'1971 Census - Field Count Statements\s*-\s*{label} '
        local_path = RAW / f'abs_1971_{state_code}_field_count_statement_lga.pdf'
        extra_jobs.append((record_id, year, 'field_count_statement', pattern, local_path))

for record_id, year, kind, pattern, local_path in extra_jobs:
    row = existing.get(record_id, {})
    if (row.get('status') == 'downloaded' and local_path.is_file()
            and local_path.stat().st_size == int(row.get('bytes', -1))):
        continue
    status, error, url = 'downloaded', '', ''
    try:
        records = fetch_catalogue(year)
        match = None
        for file_name, candidate_url, _catalogue in records:
            if re.search(pattern, file_name):
                match = (file_name, candidate_url)
                break
        if match is None:
            raise LookupError(f'no catalogue match for {pattern}')
        file_name, url = match
        response = session.get(url, timeout=300)
        response.raise_for_status()
        content = response.content
        if not content.startswith(b'%PDF'):
            raise ValueError(f'not a PDF: first bytes {content[:8]!r}')
        local_path.write_bytes(content)
    except Exception as exc:
        status, error = 'failed', f'{type(exc).__name__}: {exc}'
    row = dict(record_id=record_id, title=pattern, date_label=DATE_LABELS[year], kind=kind,
               source_record=f'https://www.abs.gov.au/AUSSTATS/abs@.nsf/DetailsPage/{CATALOGUES[year]}',
               download_url=url, local_path=str(local_path.relative_to(ROOT)).replace('\\', '/'),
               bytes='', sha256='', width_px='', height_px='', pdf_pages='', status=status, error=error,
               downloaded_utc=datetime.now(timezone.utc).isoformat())
    if status == 'downloaded':
        data = local_path.read_bytes()
        row['bytes'] = str(len(data))
        row['sha256'] = hashlib.sha256(data).hexdigest()
        with pymupdf.open(local_path) as document:
            row['pdf_pages'] = str(document.page_count)
        new_successes += 1
    existing[record_id] = row
    print(f'EXTRA {record_id}: {status} {row["bytes"]} bytes {row["pdf_pages"]} pages {error}')



# 1966 additions: the ABS per-state "Bulletin No X.8" volumes carry the same map series as
# Volume 4 (useful where their scans are larger), and the ANU copies of the 1966 Field Count
# Statements for the ACT and Northern Territory carry the only located 1966 territory maps.
BULLETIN_1966 = [('vic', 'No 2.8'), ('qld', 'No 3.8'), ('wa', 'No 5.8'), ('tas', 'No 6.8')]
ANU_1966_FIELD_COUNTS = [
    ('anu_1966_fcs01_act_population', 'Field Count Statement No. 1: ACT population',
     'https://openresearch-repository.anu.edu.au/server/api/core/bitstreams/f835ea9c-4a23-47cb-9ec0-22f3fa9ab1f5/content'),
    ('anu_1966_fcs05_act_administrative_divisions', 'Field Count Statement No. 5: ACT administrative divisions map',
     'https://openresearch-repository.anu.edu.au/server/api/core/bitstreams/dd54b589-2d0c-4b84-a9f1-311f6ebf8483/content'),
    ('anu_1966_fcs12_nt_police_districts', 'Field Count Statement No. 12: NT police districts map',
     'https://openresearch-repository.anu.edu.au/server/api/core/bitstreams/9d5c8d76-2431-41fb-b3dc-1278cb6dc8ff/content'),
]

extra_jobs_1966 = []
for state_code, label in BULLETIN_1966:
    record_id = f'abs_1966_{state_code}_bulletin_x8'
    pattern = rf'1966 Census - Bulletin {label.replace(".", "\\.")}'
    local_path = RAW / f'abs_1966_{state_code}_bulletin_x8_with_lga_maps.pdf'
    extra_jobs_1966.append((record_id, 1966, pattern, local_path))
for record_id, title, url in ANU_1966_FIELD_COUNTS:
    local_path = RAW / f'{record_id}.pdf'
    extra_jobs_1966.append((record_id, 1966, '', local_path, url))

for job in extra_jobs_1966:
    record_id, year, pattern, local_path = job[0], job[1], job[2], job[3]
    if (existing.get(record_id, {}).get('status') == 'downloaded' and local_path.is_file()
            and local_path.stat().st_size == int(existing[record_id].get('bytes', -1))):
        continue
    status, error, url = 'downloaded', '', job[4] if len(job) > 4 else ''
    try:
        if not url:
            records = fetch_catalogue(year)
            match = next((u for f, u, _c in records if re.search(pattern, f)), None)
            if match is None:
                raise LookupError(f'no catalogue match for {pattern}')
            url = match
        if not local_path.is_file():
            response = session.get(url, timeout=300)
            response.raise_for_status()
            if not response.content.startswith(b'%PDF'):
                raise ValueError('not a PDF')
            local_path.write_bytes(response.content)
    except Exception as exc:
        status, error = 'failed', f'{type(exc).__name__}: {exc}'
    row = dict(record_id=record_id, title=pattern or record_id, date_label=DATE_LABELS[year],
               kind='report_with_lga_boundary_maps',
               source_record=f'https://www.abs.gov.au/AUSSTATS/abs@.nsf/DetailsPage/{CATALOGUES[year]}',
               download_url=url, local_path=str(local_path.relative_to(ROOT)).replace('\\', '/'),
               bytes='', sha256='', width_px='', height_px='', pdf_pages='', status=status, error=error,
               downloaded_utc=datetime.now(timezone.utc).isoformat())
    if status == 'downloaded':
        data = local_path.read_bytes()
        row['bytes'] = str(len(data))
        row['sha256'] = hashlib.sha256(data).hexdigest()
        with pymupdf.open(local_path) as document:
            row['pdf_pages'] = str(document.page_count)
        new_successes += 1
    existing[record_id] = row
    print(f'1966EXTRA {record_id}: {status} {row["bytes"]} bytes {row["pdf_pages"]} pages {error}')

with manifest_path.open('w', newline='', encoding='utf-8') as handle:
    writer = csv.DictWriter(handle, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(existing[record_id] for record_id, *_ in jobs)
    writer.writerows(existing[record_id] for record_id, *_ in ANU_JOBS)
    writer.writerows(existing[job[0]] for job in extra_jobs_1966 if job[0] in existing)
    writer.writerows(existing[record_id] for record_id, _y, _k, _p, _l in extra_jobs if record_id in existing)

status = dict(
    timestamp_utc=datetime.now(timezone.utc).isoformat(),
    state='finished',
    unit='per-state LGA census volume',
    completed=sum(1 for record_id, *_ in jobs if existing[record_id]['status'] == 'downloaded'),
    total=len(jobs),
    failed=sum(1 for record_id, *_ in jobs if existing[record_id]['status'] == 'failed'),
    skipped=skipped,
    new_successes=new_successes,
    remaining=0,
    elapsed_seconds=round(time.monotonic() - started, 1),
    last_successful_output='explore/output/2026-10-16_download-other-states-lga-census-maps/manifest.csv',
    checkpoint='explore/output/2026-10-16_download-other-states-lga-census-maps/status.json',
    resume_command='python3 explore/2026-10-16_download-other-states-lga-census-maps.py',
    historical_source_note=('1911-1947 statewide maps come from the national Statistician\'s Report volumes '
                            'already saved for NSW; 1971 maps come from the national Bulletin 13 set already saved.'),
)
(OUT / 'status.json').write_text(json.dumps(status, indent=2) + '\n', encoding='utf-8')
print(json.dumps(status))
