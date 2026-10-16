# Purpose: build the NSW census LGA roster and map-gap audit, 1911 to the 1981 digital endpoint.
# Inputs: reviewed 1911 roster, historical/Sydney membership source rows, original PDFs,
#         1981 ABS GeoPackage and map manifest.
# Outputs: explore/output/2026-10-14_nsw-lga-census-panel/; raw inputs stay unchanged.
import argparse
import csv
import datetime
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import shlex

import pymupdf
from shapely import from_wkb

parser = argparse.ArgumentParser()
parser.add_argument('--project-root', default='.', help='Repository root; use the writable mount spelling in WSL.')
ROOT = Path(parser.parse_args().project_root)
OUT = ROOT / 'explore/output/2026-10-14_nsw-lga-census-panel'
OUT.mkdir(parents=True, exist_ok=True)
YEARS = [1911, 1921, 1933, 1947, 1954, 1961, 1966, 1971, 1976, 1981]
DATES = ['1911-04-03', '1921-04-04', '1933-06-30', '1947-06-30', '1954-06-30',
         '1961-06-30', '1966-06-30', '1971-06-30', '1976-06-30', '1981-06-30']
manifest = list(csv.DictReader((ROOT / 'explore/output/2026-10-10_download-boundary-maps/manifest.csv').open()))
source_by_id = {r['record_id']: r for r in manifest}
rows = []

# Keep type in the key: several municipalities and shires share a name in 1911.
roster = list(csv.DictReader((ROOT / 'data/intermediate/nsw_1911_lga_dwellings.csv').open()))
assert len(roster) == 324
assert {r['section'] for r in roster} == {'municipality', 'shire'}
for r in roster:
    rows.append(dict(census_year=1911, census_date=DATES[0], lga_code='',
        lga_name=r['lga_name'], lga_type=r['section'], unit_class='council',
        published_geography_date='1911-04-03', date_conflict='',
        source_pdf=r['source_pdf'], source_pdf_page=r['source_pdf_page'],
        source_row_number=r['source_row_number'], roster_status='reviewed_existing_extraction',
        map_source_id='abs_1911_statisticians_report_nsw_sydney_lga_maps',
        map_coverage_status='not_audited', digital_name='', digital_name_status='not_applicable'))

source = source_by_id['abs_1981_nsw_lga_maps']
doc = pymupdf.open(ROOT / source['local_path'])
# Whole-LGA subtotal rows are used; geographic Part A/B/C rows are deliberately excluded.
pattern = r'(?m)^([0-9Il ]+)\s*\n([^\n]+?\(([CMS5])\))\s*\n'
name_corrections = {'082': 'Jerilderie (S)', '092': 'Leeton (S)'}
found = {}
for page_no in [7, 8, 9]:
    for match in re.finditer(pattern, doc[page_no - 1].get_text()):
        code = match[1].split()[-1].replace('I', '1').replace('l', '1')
        if not re.fullmatch(r'\d{3}', code):
            continue
        name = match[2].strip().replace('(5)', '(S)')
        name = name_corrections.get(code, name)
        assert code not in found, ('duplicate whole-LGA row', code)
        found[code] = (name, page_no)
assert set(found) == {f'{i:03d}' for i in range(1, 177)}, '1981 published whole-LGA code sequence incomplete'

geo_path = ROOT / 'data/raw/nsw_lga_census_panel/census1981.gpkg'
con = sqlite3.connect(f'file:{geo_path}?mode=ro', uri=True)
digital = {code[-3:]: name for code, name in con.execute(
    "SELECT LGA_CODE_1981,LGA_NAME_1981 FROM local_government_area_1981 WHERE STE_CODE_1981='1'")}
assert len(digital) == 179
conflicts = []
for code, (name, page_no) in sorted(found.items()):
    digital_name = digital.get(code, '')
    # Part labels attached to whole-LGA features are a conflict, not silently removed.
    name_status = 'matches_published' if digital_name == name else 'label_conflict'
    if name_status == 'label_conflict':
        conflicts.append(dict(census_year=1981, lga_code=code, published_name=name,
                              digital_name=digital_name, action='verify_geometry_and_label'))
    suffix = re.search(r'\(([CMS])\)$', name)[1]
    rows.append(dict(census_year=1981, census_date=DATES[-1], lga_code=code,
        lga_name=re.sub(r'\s*\([CMS]\)$', '', name),
        lga_type={'C': 'city', 'M': 'municipality', 'S': 'shire'}[suffix],
        unit_class='council', published_geography_date='1981-01-01',
        date_conflict='published_boundaries_precede_census_date',
        source_pdf=source['local_path'], source_pdf_page=page_no, source_row_number=code,
        roster_status='published_whole_lga_code_sequence_checked',
        map_source_id='abs_1981_nsw_lga_maps', map_coverage_status='digital_available_not_geometry_audited',
        digital_name=digital_name, digital_name_status=name_status))

historical = list(csv.DictReader((ROOT / 'data/intermediate/nsw_lga_census_panel/historical_roster_source_rows.csv').open()))
historical_sources = {
    1921: 'abs_1921_statisticians_report_nsw_sydney_lga_maps',
    1933: 'abs_1933_statisticians_report_nsw_sydney_lga_maps',
    1947: 'abs_1947_statisticians_report_nsw_sydney_lga_maps',
    1954: 'abs_1954_nsw_population_lga_maps',
    1961: 'abs_1961_nsw_population_lga_maps',
    1966: 'abs_1966_nsw_population_dwellings_lga_maps',
    1971: 'abs_1971_nsw_field_count3_lga_maps',
    1976: 'anu1976_nsw_preliminary_lga_boundary_maps',
}
expected_counts = {1911: 324, 1921: 321, 1933: 319, 1947: 289, 1954: 241,
                   1961: 225, 1966: 224, 1971: 225, 1976: 214, 1981: 176}
for r in historical:
    year = int(r['census_year'])
    rid = historical_sources[year]
    date = DATES[YEARS.index(year)]
    rows.append(dict(census_year=year, census_date=date,
        lga_code=r['source_row_number'] if year == 1976 else '',
        lga_name=r['lga_name'], lga_type=r['lga_type'], unit_class='council',
        published_geography_date='1953-09-30' if year == 1954 else (date if year >= 1961 else ''),
        date_conflict='notes_1953_09_30_map_1954_06' if year == 1954 else '',
        source_pdf=source_by_id[rid]['local_path'], source_pdf_page=r['source_pdf_page'],
        source_row_number=r['source_row_number'], roster_status=r['name_review_status'],
        map_source_id=rid, map_coverage_status='not_audited',
        digital_name='', digital_name_status='not_applicable'))

rows.sort(key=lambda r: (r['census_year'], r['lga_name'].casefold(), r['lga_type']))
for year, count in expected_counts.items():
    selected = [r for r in rows if r['census_year'] == year]
    assert len(selected) == count, (year, len(selected), count)
    if year in (1921, 1933, 1947, 1976):
        assert {int(r['source_row_number']) for r in selected} == set(range(1, count + 1))
# The 1961 notes count cities within municipalities: 92 municipal units plus 133 shires.
assert sum(r['lga_type'] == 'shire' for r in rows if r['census_year'] == 1961) == 133
assert sum(r['lga_type'] != 'shire' for r in rows if r['census_year'] == 1961) == 92
index_1961 = [r for r in historical if r['census_year'] == '1961' and r['source_pdf_page'] == '130']
assert len(index_1961) == 194
assert {int(n) for r in index_1961 for n in r['source_row_number'].split(';')} == set(range(1, 203))

specials = [dict(census_year=1981, code=code, unit_name=name, unit_class=kind,
                 source_pdf=source['local_path'], source_pdf_page=9)
            for code, name, kind in [('177', 'Unincorporated (Far West)', 'unincorporated'),
                                    ('178', 'Unincorporated (Lord Howe Island)', 'unincorporated'),
                                    ('181', 'Migratory', 'non_spatial')]]
for year, page_no, units in [
    (1921, 371, [('Not incorporated', 'unincorporated'), ('Migratory', 'non_spatial')]),
    (1947, 372, [('Not incorporated', 'unincorporated'), ('Migratory', 'non_spatial')]),
    (1954, 7, [('Not incorporated', 'unincorporated')]),
    (1961, 4, [('Unincorporated area', 'unincorporated')]),
    (1971, 6, [('Unincorporated (Far West)', 'unincorporated'),
               ('Unincorporated (Lord Howe Island)', 'unincorporated'), ('Migratory', 'non_spatial')]),
    (1976, 10, [('Unincorporated (Far West)', 'unincorporated'),
                ('Lord Howe Island', 'unincorporated'), ('Migratory', 'non_spatial')]),
]:
    specials.extend(dict(census_year=year, code='', unit_name=name, unit_class=kind,
        source_pdf=source_by_id[historical_sources[year]]['local_path'], source_pdf_page=page_no)
        for name, kind in units)
assert len(rows) == 2558
keys = [(r['census_year'], r['lga_code'] or (r['lga_name'], r['lga_type'])) for r in rows]
assert len(keys) == len(set(keys))
assert len({(r['census_year'], r['lga_name'].casefold(), r['lga_type']) for r in rows}) == len(rows)
assert all((ROOT / r['source_pdf']).is_file() for r in rows)
for source_pdf in {r['source_pdf'] for r in rows}:
    with pymupdf.open(ROOT / source_pdf) as document:
        assert all(1 <= int(r['source_pdf_page']) <= len(document)
                   for r in rows if r['source_pdf'] == source_pdf)
for r in rows:
    r['source_conflict'] = ('printed_municipality_in_1971_city_in_1966_index'
        if r['census_year'] == 1971 and r['lga_name'] in ('Parramatta', 'Penrith') else '')
    r['name_review_required'] = 'yes' if r['census_year'] in (1921, 1933, 1947, 1954, 1966) else 'no'

gap_priorities = []
for r in rows:
    year = r['census_year']
    digital = year == 1981
    priority = 1 if year <= 1954 and r['lga_type'] != 'shire' else (3 if digital else 2)
    action = ('verify_digital_label_and_geometry' if r['digital_name_status'] == 'label_conflict' else
              'verify_digital_geometry' if digital else
              'find_or_verify_municipal_outline' if priority == 1 else 'verify_historical_outline')
    gap_priorities.append(dict(census_year=year, lga_code=r['lga_code'], lga_name=r['lga_name'],
        lga_type=r['lga_type'], priority=priority, next_action=action,
        digital_feature_present='yes' if digital else 'not_established',
        outline_verified='not_audited', map_source_id=r['map_source_id'],
        map_source_url=source_by_id[r['map_source_id']]['source_record'],
        date_conflict=r['date_conflict'], roster_status=r['roster_status']))

name_review_queue = [r for r in rows if r['name_review_required'] == 'yes']

for filename, data in [('nsw_lga_census_panel.csv', rows), ('non_council_units.csv', specials),
                       ('digital_label_conflicts.csv', conflicts),
                       ('council_gap_priorities.csv', gap_priorities),
                       ('name_review_queue.csv', name_review_queue)]:
    with (OUT / filename).open('w', newline='') as h:
        writer = csv.DictWriter(h, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)

# Candidate extraction stays outside the accepted panel until source rows are reviewed.
# Older OCR splits row numbers and sometimes shifts text coordinates; retain raw evidence.
from collections import Counter
candidate_rows = []
for year, rid, page_numbers, last_number in [
    (1921, 'abs_1921_statisticians_report_nsw_sydney_lga_maps', range(366, 372), 321),
    (1933, 'abs_1933_statisticians_report_nsw_sydney_lga_maps', range(444, 449), 319),
    (1947, 'abs_1947_statisticians_report_nsw_sydney_lga_maps', range(368, 373), 289),
]:
    source_pdf = source_by_id[rid]['local_path']
    document = pymupdf.open(ROOT / source_pdf)
    for page_no in page_numbers:
        page = document[page_no - 1]
        words = page.get_text('words')
        end_x = {1921: 230, 1933: 305, 1947: 185}[year]
        anchors = [w for w in words if re.fullmatch(r'[0-9IlO]+[.,]?', w[4]) and (
            (year == 1921 and 40 < w[0] < 100 and (page_no != 366 or w[1] > 740)) or
            (year == 1933 and 95 < w[0] < 145) or
            (year == 1947 and 15 < w[0] < 75 and (page_no != 368 or w[1] > 290)))]
        seen_y = []
        for anchor in anchors:
            if any(abs(anchor[1] - y) < 3 for y in seen_y):
                continue
            seen_y.append(anchor[1])
            left_x = min(anchor[0] - 20, {1921: 80, 1933: 115, 1947: 18}[year])
            line = sorted([w for w in words if abs(w[1] - anchor[1]) < 3 and left_x <= w[0] < end_x], key=lambda w: w[0])
            text = ' '.join(w[4] for w in line)
            match = re.match(r'([0-9IlO.,\s]+)\s+([A-Za-z].+)', text)
            if not match:
                continue
            number = re.sub(r'[.,\s]', '', match[1]).translate(str.maketrans('IlO', '110'))
            if not number.isdigit() or not 1 <= int(number) <= last_number:
                continue
            name = re.split(r'\s+(?:[0-9]|[MPR]\.)', match[2])[0]
            name = ' '.join(re.sub(r'(?:[.·•]|\|)', ' ', name).split()).strip(', ')
            if len(name) < 2:
                continue
            candidate_rows.append(dict(census_year=year, source_record_id=rid,
                source_pdf_page=page_no, source_row_number=int(number), lga_name_raw=name,
                source_y=round(anchor[1], 2), review_status='unreviewed'))
with (OUT / 'early_roster_extraction_candidates.csv').open('w', newline='') as h:
    writer = csv.DictWriter(h, fieldnames=list(candidate_rows[0])); writer.writeheader(); writer.writerows(candidate_rows)

summary = []
for year, date in zip(YEARS, DATES):
    year_rows = [r for r in rows if r['census_year'] == year]
    summary.append(dict(census_year=year, census_date=date,
        roster_state='extracted_name_review_pending' if year in (1921, 1933, 1947, 1954, 1966) else 'indexed',
        council_rows=len(year_rows) if year_rows else '',
        map_outline_audit_state='not_audited', priority=1 if year <= 1954 else (3 if year == 1981 else 2),
        next_action='review_names_and_audit_municipal_outlines' if year <= 1954 else
                    ('reconcile_digital_labels_and_verify_geometry' if year == 1981 else 'audit_council_outline_coverage')))
with (OUT / 'census_year_priorities.csv').open('w', newline='') as h:
    writer = csv.DictWriter(h, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)

# Sydney uses each census's published region, including councils split by that region.
# Membership is a reviewed source input; geographic visibility on a map is not membership.
sydney_input = list(csv.DictReader((ROOT / 'data/intermediate/nsw_lga_census_panel/sydney_membership_source_rows.csv').open()))
nsw_lookup = {(r['census_year'], r['lga_name'], r['lga_type']): r for r in rows}
sydney_rows = []
preferred_images = {1954: 'slnsw.74VKdrqKvk7A.Z3JJAMwbNBre7',
                    1961: 'anu_sydney_1961_metropolitan_statistical_area_lga_map'}
for membership in sydney_input:
    key = (int(membership['census_year']), membership['lga_name'], membership['lga_type'])
    parent = nsw_lookup[key]
    assert membership['lga_code'] == parent['lga_code']
    source = source_by_id[membership['map_source_id']]
    region_source = source_by_id[membership['membership_source_id']]
    item = dict(parent)
    item.update(membership)
    item.update(map_source_pdf=source['local_path'], map_source_url=source['source_record'],
        membership_source_pdf=region_source['local_path'], map_date_evidence=source['date_label'],
        membership_status='published_region_membership_reviewed',
        membership_name_conflict='printed_Erskinville_full_roster_Erskineville'
            if key[0] == 1947 and membership['membership_label'] == 'Erskinville' else '',
        map_type_conflict='Blacktown_shire_in_census_table_municipality_on_1954_map'
            if key[0] == 1954 and key[1] == 'Blacktown' else '',
        full_council_outline_status='not_audited',
        historical_geometry_status='not_digitised' if key[0] != 1981 else 'digital_candidate_exported',
        next_action='reconcile_digital_label_and_geometry' if parent['digital_name_status'] == 'label_conflict'
            else 'verify_digital_geometry' if key[0] == 1981
            else 'verify_full_lga_outline_outside_region' if membership['region_includes'] == 'part'
            else 'verify_outline_legibility_and_boundary_date')
    preferred = source_by_id[preferred_images.get(key[0], membership['map_source_id'])]
    item.update(preferred_map_source_id=preferred['record_id'],
                preferred_map_source_file=preferred['local_path'],
                preferred_map_date_evidence=preferred['date_label'])
    sydney_rows.append(item)
for source_id in {r['membership_source_id'] for r in sydney_rows}:
    with pymupdf.open(ROOT / source_by_id[source_id]['local_path']) as document:
        assert all(1 <= int(n) <= len(document) for r in sydney_rows
                   if r['membership_source_id'] == source_id for n in r['membership_pdf_pages'].split(';'))
assert len(sydney_rows) == len({(r['census_year'], r['lga_name'], r['lga_type']) for r in sydney_rows}) == 424
sydney_counts = Counter(int(r['census_year']) for r in sydney_rows)
assert dict(sydney_counts) == {1911: 42, 1921: 42, 1933: 50, 1947: 50, 1954: 35,
                              1961: 35, 1966: 40, 1971: 41, 1976: 45, 1981: 44}

# Independently compare 1966 membership against the typed alphabetical index's SD column.
sydney_1966_labels = set()
with pymupdf.open(ROOT / source_by_id[historical_sources[1966]]['local_path']) as document:
    for page_no in range(501, 507):
        words = document[page_no - 1].get_text('words')
        for anchor in words:
            if anchor[4] != 'Sydney' or not 135 < anchor[0] < 280:
                continue
            line = sorted([w for w in words if abs(w[1] - anchor[1]) < 3 and w[0] < anchor[0]], key=lambda w: w[0])
            types = [w for w in line if re.fullmatch('[CMSs5]', w[4]) and 120 < w[0] < 155]
            if len(types) != 1:
                continue
            name = ' '.join(w[4] for w in line if w[0] < types[0][0])
            name = re.sub(r'\(part\)|[.•]', '', name).strip()
            # Printed image/OCR confirms Waverley; the native text layer drops the l.
            name = 'Waverley' if name == 'Waverey' else name
            sydney_1966_labels.add(re.sub('[^a-z]', '', name.lower()))
assert sydney_1966_labels == {re.sub('[^a-z]', '', r['lga_name'].lower()) for r in sydney_rows if r['census_year'] == '1966'}

sydney_years = []
preview = pymupdf.open()
for year in YEARS:
    selected = [r for r in sydney_rows if int(r['census_year']) == year]
    first = selected[0]
    sydney_years.append(dict(census_year=year, published_region=first['published_region'],
        council_rows=len(selected), council_parts=sum(r['region_includes'] == 'part' for r in selected),
        digital_features=44 if year == 1981 else 0, full_outlines_verified='',
        outline_audit_status='not_audited', map_source_id=first['map_source_id'],
        map_pdf_pages=first['map_pdf_pages']))
    with pymupdf.open(ROOT / first['map_source_pdf']) as source_document:
        for page_number in first['map_pdf_pages'].split(';'):
            page_no = int(page_number)
            assert 1 <= page_no <= len(source_document)
            page = preview.new_page(width=842, height=595)
            page.insert_text((24, 25), f"Sydney {year} | {first['published_region']} | source PDF page {page_no}", fontsize=12)
            page.insert_textbox(pymupdf.Rect(24, 35, 818, 67),
                first['map_date_evidence'].replace('–', '-').replace('—', '-'), fontsize=8)
            page.show_pdf_page(pymupdf.Rect(24, 72, 818, 552), source_document, page_no - 1)
            page.insert_textbox(pymupdf.Rect(24, 559, 818, 591),
                'Candidate plate: individual full-LGA outlines remain unverified. ' + first['map_source_pdf'], fontsize=7)
preview.save(OUT / 'sydney_map_preview.pdf', garbage=4, deflate=True)
preview.close()

map_candidates = []
for record in sydney_years:
    year = record['census_year']
    candidates = [(record['map_source_id'], record['map_pdf_pages'], 'census_report_plate')]
    if year in preferred_images:
        candidates.append((preferred_images[year], '', 'higher_resolution_census_map'))
    for rid, pages, role in candidates:
        source = source_by_id[rid]
        assert (ROOT / source['local_path']).is_file()
        map_candidates.append(dict(census_year=year, source_record_id=rid, role=role,
            local_path=source['local_path'], pdf_map_pages=pages, source_url=source['source_record'],
            boundary_date_evidence=source['date_label'], width_px=source['width_px'],
            height_px=source['height_px'], sha256=source['sha256'],
            individual_outline_status='not_audited'))

for filename, data in [('sydney_lga_census_panel.csv', sydney_rows), ('sydney_census_year_summary.csv', sydney_years),
                       ('sydney_map_source_candidates.csv', map_candidates)]:
    with (OUT / filename).open('w', newline='') as h:
        writer = csv.DictWriter(h, fieldnames=list(data[0])); writer.writeheader(); writer.writerows(data)

# Keep original 1981 GeoPackage geometry bytes and CRS. No clipping, repair or relabelling.
sydney_1981 = {r['lga_code']: r for r in sydney_rows if r['census_year'] == '1981'}
geometry_records = []
geometry_audit = []
for fid, blob, code, name in con.execute(
        "SELECT OBJECTID,SHAPE,LGA_CODE_1981,LGA_NAME_1981 FROM local_government_area_1981 WHERE STE_CODE_1981='1'"):
    if code[-3:] not in sydney_1981:
        continue
    envelope_type = (blob[3] >> 1) & 7
    offset = 8 + {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[envelope_type]
    geometry = from_wkb(blob[offset:])
    assert not geometry.is_empty
    member = sydney_1981[code[-3:]]
    geometry_records.append((fid, blob, code, name, member['lga_name'], member['digital_name_status'], '1981-01-01'))
    geometry_audit.append(dict(lga_code=code, published_name=member['lga_name'], digital_name=name,
        label_status=member['digital_name_status'], geometry_valid=bool(geometry.is_valid),
        bounds=list(geometry.bounds)))
assert len(geometry_records) == 44
export_path = OUT / 'sydney_lga_1981.gpkg'
temporary_path = export_path.with_suffix('.gpkg.tmp')
temporary_path.unlink(missing_ok=True)
target = sqlite3.connect(temporary_path)
target.execute('PRAGMA application_id=1196444487')
target.execute('PRAGMA user_version=10300')
for table in ['gpkg_spatial_ref_sys', 'gpkg_contents', 'gpkg_geometry_columns']:
    target.execute(con.execute('SELECT sql FROM sqlite_master WHERE name=?', (table,)).fetchone()[0])
for entry in con.execute('SELECT * FROM gpkg_spatial_ref_sys'):
    target.execute('INSERT INTO gpkg_spatial_ref_sys VALUES (?,?,?,?,?,?)', entry)
target.execute('CREATE TABLE sydney_lga_1981 (fid INTEGER PRIMARY KEY, shape MULTIPOLYGON, lga_code TEXT, digital_name TEXT, published_name TEXT, label_status TEXT, published_boundary_date TEXT)')
target.executemany('INSERT INTO sydney_lga_1981 VALUES (?,?,?,?,?,?,?)', geometry_records)
extent = [min(a['bounds'][0] for a in geometry_audit), min(a['bounds'][1] for a in geometry_audit),
          max(a['bounds'][2] for a in geometry_audit), max(a['bounds'][3] for a in geometry_audit)]
target.execute("INSERT INTO gpkg_contents (table_name,data_type,identifier,description,min_x,min_y,max_x,max_y,srs_id) VALUES (?,?,?,?,?,?,?,?,?)",
    ('sydney_lga_1981', 'features', 'Sydney LGA 1981 candidates', 'Published Sydney SD membership; original ABS GDA94 geometry, labels retained; geometry-to-council identity not audited.', *extent, 4283))
target.execute("INSERT INTO gpkg_geometry_columns VALUES ('sydney_lga_1981','shape','MULTIPOLYGON',4283,0,0)")
target.commit()
assert target.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
target.close()
temporary_path.replace(export_path)
(OUT / 'sydney_1981_geometry_audit.json').write_text(json.dumps(geometry_audit, indent=2) + '\n')

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
status = dict(timestamp_utc=now, state='rosters_extracted_review_pending', unit='census-year roster',
              completed=10, total=10, failed=0, skipped=0, remaining=0, council_rows=len(rows),
              last_successful_output='explore/output/2026-10-14_nsw-lga-census-panel/nsw_lga_census_panel.csv',
              checkpoint='explore/output/2026-10-14_nsw-lga-census-panel/status.json',
              resume_command='python3 explore/2026-10-14_nsw-lga-census-panel.py --project-root ' + shlex.quote(str(ROOT)),
              live_job=False, next_action='Resolve name-review queue, then audit individual map outlines.',
              blocker=None, full_panel_complete=False, all_census_rosters_extracted=True)
status['name_review_rows'] = len(name_review_queue)
status['sydney_council_rows'] = len(sydney_rows)
status['sydney_rosters_completed'] = 10
status['sydney_digital_candidates'] = 44
status['sydney_last_successful_output'] = 'explore/output/2026-10-14_nsw-lga-census-panel/sydney_lga_census_panel.csv'
status['sydney_next_action'] = 'Audit full outlines for the 12 council-part entries; georeference and trace historical candidates.'
(OUT / 'status.json').write_text(json.dumps(status, indent=2) + '\n')
checks = dict(timestamp_utc=now, unique_census_council_keys=True, source_paths_exist=True,
              source_pdf_pages_in_range=True, unique_year_name_type_keys=True,
              priority_queue_covers_every_council=len(gap_priorities) == len(rows),
              full_1961_map_index_references_001_to_202=True,
              published_1961_notes_total_and_types_match=True,
              published_1981_whole_lga_codes_001_to_176=True, council_rows=len(rows),
              council_counts=expected_counts, non_council_rows=len(specials), digital_label_conflicts=len(conflicts),
              name_review_rows=len(name_review_queue),
              coverage_percentage=None, reason='Individual-outline audits and some name reviews remain incomplete',
              raw_1981_gpkg_sha256=hashlib.file_digest(geo_path.open('rb'), 'sha256').hexdigest())
checks.update(sydney_council_rows=len(sydney_rows), sydney_counts=dict(sydney_counts),
              sydney_1966_membership_matches_typed_sd_index=True, sydney_1981_digital_features=44,
              sydney_1981_valid_geometries=sum(a['geometry_valid'] for a in geometry_audit),
              sydney_1981_digital_label_conflicts=sum(a['label_status'] == 'label_conflict' for a in geometry_audit),
              sydney_map_source_candidates=len(map_candidates),
              sydney_map_preview_pages=sum(len(r['map_pdf_pages'].split(';')) for r in sydney_years))
(OUT / 'verification.json').write_text(json.dumps(checks, indent=2) + '\n')
print(json.dumps(status))
