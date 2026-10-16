# Purpose: build the LGA x census panel for Victoria, Queensland, South Australia,
#   Western Australia, Tasmania, the Northern Territory and the ACT, 1911-1981, in the same
#   shape as the NSW panel, and link every LGA-census year to a candidate map source.
# Inputs: data/raw/historical_boundary_maps/abs_census/ (national Statistician's Reports
#   1911-1947, per-state LGA volumes 1921-1981, 1976 ANU preliminary volumes, 1971
#   Bulletin 13 and field count statements), data/raw/abs_1911_census/1911 Census -
#   Volume III - Part XIII Dwellings.pdf, data/raw/nsw_lga_census_panel/census1981.gpkg,
#   and explore/output/2026-10-16_other-states-lga-census-panel/map_plate_inventory.csv.
# Outputs: explore/output/2026-10-16_other-states-lga-census-panel/: lga_census_panel.csv,
#   census_year_state_summary.csv, map_source_candidates.csv, map_plate_pages.csv,
#   name_review_queue.csv, non_council_units.csv, status.json, verification.json.
import csv
import json
import re
import unicodedata
from collections import Counter, OrderedDict, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pymupdf

ROOT = Path('.')
RAW = ROOT / 'data/raw/historical_boundary_maps/abs_census'
RAW_1911 = ROOT / 'data/raw/abs_1911_census/1911 Census - Volume III - Part XIII Dwellings.pdf'
OUT = ROOT / 'explore/output/2026-10-16_other-states-lga-census-panel'
OUT.mkdir(parents=True, exist_ok=True)

YEARS = [1911, 1921, 1933, 1947, 1954, 1961, 1966, 1971, 1976, 1981]
DATES = {1911: '1911-04-03', 1921: '1921-04-04', 1933: '1933-06-30', 1947: '1947-06-30',
         1954: '1954-06-30', 1961: '1961-06-30', 1966: '1966-06-30', 1971: '1971-06-30',
         1976: '1976-06-30', 1981: '1981-06-30'}
STATES = OrderedDict([
    ('vic', 'Victoria'), ('qld', 'Queensland'), ('sa', 'South Australia'),
    ('wa', 'Western Australia'), ('tas', 'Tasmania'), ('nt', 'Northern Territory'),
    ('act', 'Australian Capital Territory')])
STATE_BY_NAME = {v: k for k, v in STATES.items()}
LOG = []


def log(message):
    LOG.append(str(message))
    print(message, flush=True)


NOISE = re.compile(r"(?i)\b(local government|area\b|areas\b|acres?|miles?|square|population|males?|"
                   r"females?|persons?|dwellings?|occupied|private|inmates?|summary|total|continued|contd|"
                   r"table|page|division|state|represents|density|number|govern(ment)?|municipal|shire|"
                   r"road district|corporation|city|cities|towns?|boroughs?|district councils?|index|"
                   r"not incorporated|migratory|showing|located|birthplace|nationality|religion|industry|age|"
                   r"conjugal|occupational|status|residence|non-municipal|subdivision|statistical|census|"
                   r"commonwealth|australia|queensland|victoria|tasmania|nsw|territory|canberra|darwin)\b")
RURAL_KEYS = re.compile(r'(?i)\b(shires?|district councils?|road (board )?districts?)\b')
URBAN_KEYS = re.compile(r'(?i)\b(cities|cities and towns|municipalities|municipal corporations?|corporations?|towns?|boroughs?|cities, towns)\b')
DIVISION_CODES = {'M', 'P', 'R', 'S', 'T', 'PT', 'P.T', 'P.R', 'M.R', 'PM', 'P.M', 'N.M'}
CODE_TOKEN = re.compile(r'^[\(]?(M|S|B|T|C|D\.?C|R\.?D|N\.?M|D\.C|~\.?D|R,D)[\.\)]?$')
TYPE_SUFFIX = re.compile(r'\((S|C|T|B|M|D\.?C\.?|R\.?D\.?|O|Q)\)')

GENERIC_DIVISIONS = re.compile(r'(?i)^(metropolitan|central|western|northern|eastern|southern|'
                               r'north central|south western|north western|south eastern|'
                               r'gippsland|wimmera|mallee|wannon|otham|mersey|lyell|darwin)\s*(\(part\)|area)?$')


OCR_DIGIT_FIX = str.maketrans({'1': 'l', '0': 'o', '5': 's', '!': 'l', '|': 'l'})


def repair_ocr_name(name):
    """Repair common OCR digit-for-letter substitutions inside words (e.g. Valkervil1p).

    A digit is only translated when the surrounding token still looks like a word, so
    genuine numbers never enter the name column.
    """
    tokens = []
    for token in name.split():
        if any(ch.isdigit() for ch in token) and sum(ch.isalpha() for ch in token) >= 3:
            fixed = token.translate(OCR_DIGIT_FIX)
            if sum(ch.isalpha() for ch in fixed) / max(1, len(fixed)) > 0.7:
                tokens.append(fixed)
                continue
        tokens.append(token)
    return ' '.join(tokens)


def normalise_name(name):
    name = unicodedata.normalize('NFKC', name)
    name = re.sub(r'(?i)\s*\(part\s*[a-d]?\s*\)?', '', name)
    name = re.sub(r'(?i)\s*\(cont(inued)?\)', '', name)
    name = re.sub(r'\s+', ' ', name).strip(' .,-;:')
    return name


def name_key(name):
    return re.sub(r"[^a-z]", '', name.lower())


def title_case_upper(name):
    """Title-case ALL-CAPS OCR names while keeping small words lower case."""
    words = []
    for word in name.split():
        if len(word) <= 2 and word.upper() not in ('UK',):
            words.append(word.lower().capitalize())
        elif word.isupper() and len(word) > 2:
            words.append(word.capitalize())
        else:
            words.append(word)
    return ' '.join(words)


def rows_from_page(page, name_x_max_share=0.55):
    """Ordered line items for one table page: ('heading'|'name'|'number', value)."""
    width = page.rect.width
    words = page.get_text('words')
    if not words:
        return []
    lines = {}
    for word in words:
        lines.setdefault(round(word[1] / 3), []).append(word)
    items = []
    for key in sorted(lines):
        line_words = sorted(lines[key], key=lambda w: w[0])
        left = [w for w in line_words if w[0] < width * name_x_max_share]
        if not left:
            continue
        tokens = [w[4] for w in left]
        text = re.sub(r'\s+', ' ', ' '.join(tokens)).strip()
        plain = text.strip(' .\u00b7\u2014-~_')
        if plain and not any(ch.isdigit() for ch in plain) and len(plain) <= 64:
            letters = [ch for ch in plain if ch.isalpha()]
            if letters and sum(1 for ch in letters if ch.isupper()) / len(letters) >= 0.6:
                if RURAL_KEYS.search(plain) or URBAN_KEYS.search(plain) or 'DIVISION' in plain.upper():
                    items.append(('heading', plain))
                    continue
        if re.fullmatch(r'[\d,\.\)\s]+', text):
            for number in re.findall(r'\d{1,4}', text):
                items.append(('number', number))
            continue
        stripped = []
        for token in tokens:
            clean = token.strip('.,')
            if re.fullmatch(r'\d{1,4}[\.\)]?', token):
                items.append(('number', token.strip('.').rstrip(')')))
                continue
            if re.search(r'\d', token) or not token[0].isalpha():
                continue  # numeric column values and punctuation-led OCR debris
            if clean in DIVISION_CODES or re.fullmatch(r'[\.\u00b7~\-\u2014_]+', token):
                continue
            if len(clean) == 1 and clean.isalpha():
                continue
            stripped.append(token)
        name = re.sub(r'\s+', ' ', ' '.join(stripped)).strip(' .\u00b7')
        name = re.sub(r'\s+\(?[A-Z]{1,3}\.?$', '', name).strip(' .,')
        name = repair_ocr_name(name)
        if len(name) < 3 or not name[0].isupper():
            continue
        if any(ch.isdigit() for ch in name):
            continue
        if name.isupper():
            continue
        if not re.fullmatch(r"[A-Za-z][A-Za-z'\.\- &]{2,44}", name):
            continue
        if NOISE.search(name):
            continue
        items.append(('name', name))
    return items


def section_type(section):
    if not section:
        return '', ''
    if re.search(r'(?i)district council', section):
        return 'district_council', 'rural'
    if re.search(r'(?i)road (board )?district', section):
        return 'road_district', 'rural'
    if RURAL_KEYS.search(section):
        return 'shire', 'rural'
    if re.search(r'(?i)cities and towns', section):
        return 'city_or_town', 'urban'
    if re.search(r'(?i)\bcities\b', section):
        return 'city', 'urban'
    if re.search(r'(?i)\btowns\b', section):
        return 'town', 'urban'
    if re.search(r'(?i)boroughs?\b', section):
        return 'borough', 'urban'
    if re.search(r'(?i)(municipalit|corporation)', section):
        return 'municipality', 'urban'
    return '', ''


def type_from_code(code):
    code = code.upper().replace(' ', '')
    if code in ('S', 'SH', 'SHIRE'):
        return 'shire', 'rural'
    if code in ('DC', 'D.C', 'D,C'):
        return 'district_council', 'rural'
    if code in ('RD', 'R.D', 'R,D', '~.D'):
        return 'road_district', 'rural'
    if code in ('C', 'CITY'):
        return 'city', 'urban'
    if code in ('T', 'TOWN'):
        return 'town', 'urban'
    if code in ('B', 'BOROUGH'):
        return 'borough', 'urban'
    if code in ('M', 'MUNICIPALITY'):
        return 'municipality', 'urban'
    return '', ''


def slug_volume(year, state):
    if year in (1921, 1933, 1947, 1954, 1961):
        return f'abs_{year}_{state}_population_lga_with_maps.pdf'
    if year == 1966:
        tag = 'nt_act' if state in ('nt', 'act') else state
        return f'abs_1966_{tag}_population_dwellings_lga_with_maps.pdf'
    if year == 1971:
        tag = 'nt_act' if state in ('nt', 'act') else state
        return f'abs_1971_{tag}_field_count_statement_lga.pdf'
    if year == 1976:
        tag = 'nt_act' if state in ('nt', 'act') else state
        return f'abs_1976_{tag}_lga.pdf'
    if year == 1981:
        return f'abs_1981_{state}_lga_urban_centres_with_maps.pdf'
    raise KeyError((year, state))


MAP_SCALE = re.compile(r'(?i)\bscale\b.{0,70}?(kilom|miles)')


def detect_map_pages(pdf_name, tail=15):
    """Map plate pages of a census LGA volume.

    The ABS placed the map set in one block at the end of each volume: a statewide sheet,
    an LGA index sheet or two, and metropolitan/regional sheets. A plate page either has
    almost no text layer (the map is an image) or carries a map title with a scale bar.
    Covers and blank backs are excluded by the tail window and the minimum image size.
    """
    path = RAW / pdf_name
    if not path.is_file():
        return []
    pages = []
    with pymupdf.open(path) as document:
        total = document.page_count
        for index, page in enumerate(document):
            page_no = index + 1
            if page_no <= total - tail or page_no < 12:
                continue
            text = re.sub(r'\s+', ' ', page.get_text()).strip()
            infos = page.get_image_info()
            if not infos:
                continue
            long_edge = max(max(i['width'], i['height']) for i in infos)
            if long_edge < 300:
                continue  # blank reverse or tiny figure
            map_title = re.search(r'(?i)(scale\s*1|statistical divisions?\s|local government areas?\b.*(census|map))', text[:300])
            if len(text) < 60 or (len(text) < 1200 and map_title):
                pages.append(page_no)
    return pages


def get_map_plate_pages():
    """Detected plate pages per raw file, from the plate detector inventory."""
    inventory = defaultdict(list)
    path = OUT / 'map_plate_inventory.csv'
    if not path.is_file():
        # The inventory is an optional audit artefact; detection below still runs without it.
        return {}
    with path.open(newline='', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            inventory[row['file']].append(int(row['pdf_page']))
    return {name: sorted(pages) for name, pages in inventory.items()}


# --------------------------------------------------------------------- extraction


def is_plausible_name(name):
    """Reject clear OCR debris; keep genuine multi-word names such as 'St. Kilda'."""
    if len(name) < 3:
        return False
    if not name[0].isupper():
        return False
    if re.match(r"(?i)^(no\.?|of|the|and|total|name|page|table|summary|note)\b", name):
        return False
    if re.fullmatch(r'[A-Z]\.?[A-Z]?\.?', name):
        return False
    if re.search(r"[^A-Za-z'\.\- &]", name):
        return False
    if re.search(r'\.{2,}|--', name):
        return False
    words = [w for w in re.split(r'\s+', name) if w]
    if len(words) > 4:
        return False
    if any(len(w.strip('.')) == 1 and w.strip('.').isupper() for w in words[:-1]):
        return False
    return True


def extract_1911():
    """Table 68 (VIC, QLD, SA, WA) and Table 65 (TAS) of the national Dwellings volume."""
    rows = []
    document = pymupdf.open(RAW_1911)
    source = str(RAW_1911.relative_to(ROOT))
    state_header = re.compile(r'^.{0,4}-?\s?(NEW SOUTH WALES|VICTORIA|QUEENSLAND|SOUTH AUSTRALIA|'
                              r'WESTERN AUSTRALIA|TASMANIA)\b', re.I)
    state = ''
    for page_no in range(183, 200):
        page = document[page_no - 1]
        for line in page.get_text().split('\n'):
            match = state_header.match(line.strip())
            if match:
                state = match.group(1).title()
        state_code = STATE_BY_NAME.get(state, '')
        if state_code not in ('vic', 'qld', 'sa', 'wa'):
            continue
        section, number = '', ''
        for kind, value in rows_from_page(page):
            if kind == 'heading':
                section = value
            elif kind == 'number':
                number = value
            else:
                lga_type, lga_class = section_type(section)
                rows.append(dict(census_year=1911, state=state_code, lga_name=value, lga_type=lga_type,
                                 lga_class=lga_class, source_row_number=number, source_pdf=source,
                                 source_pdf_page=page_no, section_raw=section,
                                 roster_status='ocr_extracted'))
                number = ''
    # Tasmania's municipalities are listed in Table 65.
    for page_no in (165, 166):
        for kind, value in rows_from_page(document[page_no - 1]):
            if kind != 'name':
                continue
            rows.append(dict(census_year=1911, state='tas', lga_name=value, lga_type='municipality',
                             lga_class='urban', source_row_number='', source_pdf=source,
                             source_pdf_page=page_no, section_raw='MUNICIPALITY',
                             roster_status='ocr_extracted'))
    document.close()
    log(f'1911: {len(rows)} rows')
    return rows


REPORT_STATE_PAGES = {
    1921: ('abs1921_statisticians_report_nsw_sydney_lga_maps.pdf',
           {'vic': (373, 375), 'qld': (376, 378), 'sa': (379, 381),
            'wa': (383, 384), 'tas': (385, 386)}),
    1933: ('abs1933_statisticians_report_nsw_sydney_lga_maps.pdf',
           {'vic': (450, 452), 'qld': (453, 455), 'sa': (456, 458),
            'wa': (459, 461), 'tas': (462, 462)}),
    1947: ('abs1947_statisticians_report_nsw_sydney_lga_maps.pdf',
           {'vic': (373, 376), 'qld': (377, 379), 'sa': (380, 381),
            'wa': (382, 384), 'tas': (385, 385)}),
}


def extract_report(year):
    report_name, state_pages = REPORT_STATE_PAGES[year]
    rows = []
    document = pymupdf.open(RAW / report_name)
    for state, (start, end) in state_pages.items():
        section, number = '', ''
        for page_no in range(start, end + 1):
            for kind, value in rows_from_page(document[page_no - 1]):
                if kind == 'heading':
                    section = value
                elif kind == 'number':
                    number = value
                else:
                    lga_type, lga_class = section_type(section)
                    rows.append(dict(census_year=year, state=state, lga_name=value, lga_type=lga_type,
                                     lga_class=lga_class, source_row_number=number,
                                     source_pdf=report_name, source_pdf_page=page_no,
                                     section_raw=section, roster_status='ocr_extracted'))
                    number = ''
    document.close()
    log(f'{year}: {len(rows)} rows')
    return rows


def extract_index(year, state):
    """1954/1961 printed index: name, code and statistical division in two column pairs."""
    source_name = slug_volume(year, state)
    document = pymupdf.open(RAW / source_name)
    rows = []
    pages = []
    for index, page in enumerate(document):
        text = page.get_text()
        if not re.search(r'(?i)index\s+of\s+.{0,45}(citi|c:rrn|c:rri|municipal|corporation|local government|shire|district)', text):
            continue
        pages.append(index + 1)
        words = page.get_text('words')
        width = page.rect.width
        tokens = [(w[0], w[1], w[4]) for w in words]
        for code_x, code_y, code_text in [t for t in tokens if CODE_TOKEN.match(t[2].strip('"'))]:
            band_lo, band_hi = (0, width / 2) if code_x < width / 2 else (width / 2, width)
            candidates = [(x, y, t) for x, y, t in tokens
                          if band_lo <= x < code_x - 2 and abs(y - code_y) <= 9
                          and re.fullmatch(r"[A-Za-z][A-Za-z'\-\.]*", t) and len(t) > 1]
            if not candidates:
                continue
            candidates.sort(key=lambda c: (abs(c[1] - code_y), c[0]))
            best_y = candidates[0][1]
            line = sorted([c for c in candidates if abs(c[1] - best_y) <= 3], key=lambda c: c[0])
            name = ' '.join(t for _, _, t in line).strip(' .')
            name = re.sub(r'(?i)\s*(N\.?M\.?|M\.?|S\.?|B\.?|T\.?|C\.?|D\.?C\.?|R\.?D\.?|and|&)\s*$', '', name).strip(' .,')
            name = repair_ocr_name(name)
            code = code_text.strip('"').strip('()').strip('.')
            if len(name) < 3 or NOISE.search(name):
                continue
            if re.fullmatch(r'(?i)(N\.?M)', code):
                continue  # non-municipal town, not a local government area
            lga_type, lga_class = type_from_code(code)
            rows.append(dict(census_year=year, state=state, lga_name=name, lga_type=lga_type,
                             lga_class=lga_class, source_row_number='', source_pdf=source_name,
                             source_pdf_page=index + 1, section_raw='INDEX OF CITIES, TOWNS, '
                             'BOROUGHS AND SHIRES', roster_status='printed_index_transcription'))
    document.close()
    log(f'{year} {state}: {len(rows)} rows, index pages {pages}')
    return rows


def extract_suffix_volume(year, state, source_name, suffix_pattern):
    """1966/1981 volumes (and 1971 state volumes): rows carry a type suffix."""
    rows = []
    document = pymupdf.open(RAW / source_name)
    for page_no in range(1, document.page_count + 1):
        for raw_line in re.split(r'\n', document[page_no - 1].get_text()):
            match = suffix_pattern.search(raw_line)
            if not match:
                continue
            name = raw_line[:match.start()].strip(' .,')
            name = re.sub(r'^[\d\s,\.\)]+', '', name)
            if not name or len(name) < 3 or NOISE.search(name) or any(ch.isdigit() for ch in name):
                continue
            if not re.fullmatch(r"[A-Za-z][A-Za-z'\.\- &]{2,44}", name):
                continue
            if name.isupper():
                name = title_case_upper(name)
            name = normalise_name(name)
            code = match.group(1)
            lga_type, lga_class = type_from_code(code)
            rows.append(dict(census_year=year, state=state, lga_name=name, lga_type=lga_type,
                             lga_class=lga_class, source_row_number='', source_pdf=source_name,
                             source_pdf_page=page_no, section_raw=match.group(0),
                             roster_status='ocr_extracted'))
    document.close()
    log(f'{year} {state}: {len(rows)} rows ({source_name})')
    return rows


def extract_1971(state):
    """1971 field count statements: table 1 index of local government areas.

    Names and their type codes often sit on separate lines, so code tokens are anchored
    and the nearest name tokens to the left in the same column band are paired with them.
    """

    def _name_like(token):
        if not token or not token[0].isalpha():
            return False
        letters = sum(ch.isalpha() for ch in token)
        return letters >= 3 and letters / len(token) > 0.6

    source_name = slug_volume(1971, state)
    rows = []
    seen = set()
    document = pymupdf.open(RAW / source_name)
    code_re = re.compile(r'^[\(\[]?([SCMTB]|D\.?C|R\.?D|5|S\.)[\.\)\]]?$')
    for page_no in range(1, document.page_count + 1):
        page = document[page_no - 1]
        text = page.get_text()
        # Index/roster tables for 1971 are headed in several OCR-damaged ways; match the
        # stable part of the heading and require table-like content.
        if not re.search(r'(?i)overnment\s+areas?', text):
            continue
        width = page.rect.width
        tokens = [(w[0], w[1], w[4]) for w in page.get_text('words')]
        for code_x, code_y, code_text in [t for t in tokens if code_re.match(t[2])]:
            band_lo, band_hi = (0, width / 2) if code_x < width / 2 else (width / 2, width)
            candidates = [(x, y, t) for x, y, t in tokens
                          if band_lo <= x < code_x - 1 and abs(y - code_y) <= 12
                          and _name_like(t)]
            if not candidates:
                continue
            candidates.sort(key=lambda c: (abs(c[1] - code_y), c[0]))
            best_y = candidates[0][1]
            line = sorted([c for c in candidates if abs(c[1] - best_y) <= 3], key=lambda c: c[0])
            name = repair_ocr_name(' '.join(t for _, _, t in line).strip(' .,'))
            name = title_case_upper(name)
            name = normalise_name(name)
            code = code_text.strip('()[]').replace('.', '').replace('5', 'S')
            if len(name) < 3 or NOISE.search(name):
                continue
            key = (page_no, name_key(name))
            if key in seen:
                continue
            seen.add(key)
            lga_type, lga_class = type_from_code(code)
            rows.append(dict(census_year=1971, state=state, lga_name=name, lga_type=lga_type,
                             lga_class=lga_class, source_row_number='', source_pdf=source_name,
                             source_pdf_page=page_no, section_raw='INDEX OF LOCAL GOVERNMENT AREAS',
                             roster_status='printed_index_transcription'))
    document.close()
    log(f'1971 {state}: {len(rows)} rows')
    return rows


def extract_1976(state):
    """1976 preliminary ANU volumes: table 1 and table 2 carry type suffixes."""
    if state in ('nt', 'act'):
        source_name = f'anu1976_{state}_preliminary_lga_boundary_maps.pdf'
    else:
        source_name = f'anu1976_{state}_preliminary_lga_boundary_maps.pdf'
    rows = []
    document = pymupdf.open(RAW / source_name)
    for page_no in range(1, document.page_count + 1):
        for raw_line in re.split(r'\n', document[page_no - 1].get_text()):
            match = re.search(r'\(([SCMTBOQ]|Part [A-D])\)', raw_line)
            if not match:
                continue
            name = raw_line[:match.start()].strip(' .,')
            name = re.sub(r'^[\d\s,\.\)]+', '', name)
            if not name or len(name) < 3 or any(ch.isdigit() for ch in name):
                continue
            if not re.fullmatch(r"[A-Za-z][A-Za-z'\.\- &]{2,44}", name):
                continue
            if NOISE.search(name):
                continue
            if name.isupper():
                name = title_case_upper(name)
            name = normalise_name(name)
            code = match.group(1)
            lga_type, lga_class = type_from_code(code) if len(code) == 1 else ('', '')
            rows.append(dict(census_year=1976, state=state, lga_name=name, lga_type=lga_type,
                             lga_class=lga_class, source_row_number='', source_pdf=source_name,
                             source_pdf_page=page_no, section_raw=match.group(0),
                             roster_status='ocr_extracted'))
    document.close()
    log(f'1976 {state}: {len(rows)} rows')
    return rows


def extract_territory(year, state=None):
    """NT and ACT published divisions/districts rather than municipal councils.

    The volumes list these units in 'Local Government Area' or 'Division or District' tables.
    Rows are recorded with unit_class 'division_or_district' unless a council-type suffix is present.
    """
    if state is not None and year == 1976:
        source_name = f'anu1976_{state}_preliminary_lga_boundary_maps.pdf'
    elif state is not None:
        source_name = slug_volume(year, state)
    else:
        source_name = slug_volume(year, 'nt')
    rows = []
    document = pymupdf.open(RAW / source_name)
    for page_no in range(1, document.page_count + 1):
        page = document[page_no - 1]
        text = page.get_text()
        if not re.search(r'(?i)(local government area|division or district|districts? and)', text):
            continue
        # Combined NT and ACT volumes: assign each page to the territory it serves.
        page_state = state
        if re.search(r'(?i)AUSTRALIAN CAPITAL TERRITORY', text):
            page_state = 'act'
        elif re.search(r'(?i)NORTHERN TERRITORY', text):
            page_state = 'nt'
        elif page_state is None:
            page_state = 'nt'
        for raw_line in re.split(r'\n', text):
            line = raw_line.strip()
            match = re.match(r"^([A-Z][A-Za-z'\-\. ]{2,40}?)\s*(?:\(([SCMTB]|D\.?C\.?|U)\))?\s*(?:[-–—]\s*)?$", line)
            if not match:
                continue
            name = match.group(1).strip(' .,-')
            if len(name) < 3 or any(ch.isdigit() for ch in name) or NOISE.search(name):
                continue
            if name.isupper():
                name = title_case_upper(name)
            name = normalise_name(name)
            code = match.group(2) or ''
            lga_type, lga_class = type_from_code(code) if code else ('', '')
            rows.append(dict(census_year=year, state=page_state, lga_name=name, lga_type=lga_type,
                             lga_class=lga_class, source_row_number='', source_pdf=source_name,
                             source_pdf_page=page_no, section_raw='DIVISION OR DISTRICT',
                             roster_status='ocr_extracted',
                             unit_class='division_or_district'))
    document.close()
    log(f'{year} {state} (territory): {len(rows)} rows')
    return rows


def extract_1981(state):
    rows = extract_suffix_volume(1981, state, slug_volume(1981, state), TYPE_SUFFIX)
    return rows


# --------------------------------------------------------------------- assembly


def edit_distance(a, b, cap=2):
    """Levenshtein distance with an early-exit cap (for OCR variant clustering)."""
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, 1):
        current = [i]
        for j, char_b in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1,
                               previous[j - 1] + (char_a != char_b)))
        if min(current) > cap:
            return cap + 1
        previous = current
    return previous[-1]


def merge_ocr_variants(rows):
    """Cluster OCR spelling variants per state-year, keeping the most frequent spelling.

    The 1976 ANU scans OCR poorly; the same council can appear as 'Bairnsdale',
    'Baimsdaie' and 'BairnsdaJe'. Variants within edit distance 1 (2 for long names)
    of the cluster representative are merged and recorded in name_alternates.
    """
    counts = Counter()
    for row in rows:
        counts[(row['census_year'], row['state'], name_key(row['lga_name']))] += 1
    groups = defaultdict(list)
    for (year, state, key), count in counts.items():
        groups[(year, state)].append((key, count))
    canonical = {}
    alternates = defaultdict(list)
    for (year, state), items in groups.items():
        clusters = []
        for key, count in sorted(items, key=lambda item: (-item[1], item[0])):
            cap = 1 if len(key) <= 8 else 2
            placed = False
            for cluster in clusters:
                if edit_distance(key, cluster['key'], cap) <= cap:
                    cluster['members'].append(key)
                    placed = True
                    break
            if not placed:
                clusters.append({'key': key, 'members': [key]})
        for cluster in clusters:
            for member in cluster['members']:
                canonical[(year, state, member)] = cluster['key']
            if len(cluster['members']) > 1:
                alternates[(year, state, cluster['key'])] = sorted(
                    m for m in cluster['members'] if m != cluster['key'])
    merged = {}
    for row in rows:
        key = canonical[(row['census_year'], row['state'], name_key(row['lga_name']))]
        slot = (row['census_year'], row['state'], key)
        current = merged.get(slot)
        if current is None:
            merged[slot] = row
            continue
        if not current['lga_type'] and row['lga_type']:
            merged[slot] = row
    out = []
    by_key = {}
    for row in rows:
        by_key.setdefault((row['census_year'], row['state'], name_key(row['lga_name'])), row)
    for slot, row in merged.items():
        row = dict(row)
        row['name_alternates'] = '; '.join(alternates.get(slot, []))
        out.append(row)
    return out


def dedupe(rows):
    best = OrderedDict()
    for row in rows:
        key = (row['census_year'], row['state'], name_key(row['lga_name']))
        current = best.get(key)
        if current is None:
            best[key] = row
            continue
        if not current['lga_type'] and row['lga_type']:
            best[key] = row
    return list(best.values())


MAP_SOURCE_PAGES = {
    # National Statistician's Reports: identified plate pages per state (1911-1947).
    (1911, 'vic'): ('abs1911_statisticians_report_nsw_sydney_lga_maps.pdf', '445', 'State map: Victoria, counties and population density'),
    (1911, 'qld'): ('abs1911_statisticians_report_nsw_sydney_lga_maps.pdf', '448', 'State map: Queensland census districts'),
    (1911, 'sa'): ('abs1911_statisticians_report_nsw_sydney_lga_maps.pdf', '449', 'State map: South Australia counties and divisions'),
    (1911, 'wa'): ('abs1911_statisticians_report_nsw_sydney_lga_maps.pdf', '452', 'State map: Western Australia statistical districts'),
    (1911, 'tas'): ('abs1911_statisticians_report_nsw_sydney_lga_maps.pdf', '453', 'State map: Tasmania municipalities'),
    (1911, 'nt'): ('abs1911_statisticians_report_nsw_sydney_lga_maps.pdf', '456', 'State map: Northern Territory counties and sub-districts'),
    (1921, 'vic'): ('abs1921_statisticians_report_nsw_sydney_lga_maps.pdf', '396;397', 'State maps: Victoria density and LGA index (Melbourne inset)'),
    (1921, 'qld'): ('abs1921_statisticians_report_nsw_sydney_lga_maps.pdf', '398;399', 'State maps: Queensland density and LGA index (Brisbane inset)'),
    (1921, 'sa'): ('abs1921_statisticians_report_nsw_sydney_lga_maps.pdf', '400;401', 'State maps: South Australia density and LGA index'),
    (1921, 'wa'): ('abs1921_statisticians_report_nsw_sydney_lga_maps.pdf', '402;403', 'State maps: Western Australia density and LGA index'),
    (1921, 'tas'): ('abs1921_statisticians_report_nsw_sydney_lga_maps.pdf', '404;405', 'State maps: Tasmania density and LGA index'),
    (1921, 'nt'): ('abs1921_statisticians_report_nsw_sydney_lga_maps.pdf', '406', 'State map: Northern Territory districts'),
    (1933, 'vic'): ('abs1933_statisticians_report_nsw_sydney_lga_maps.pdf', '469', 'State map: Victoria shires and municipalities'),
    (1933, 'qld'): ('abs1933_statisticians_report_nsw_sydney_lga_maps.pdf', '470', 'State map: Queensland shires and municipalities'),
    (1933, 'sa'): ('abs1933_statisticians_report_nsw_sydney_lga_maps.pdf', '471', 'State map: South Australia district councils and municipalities'),
    (1933, 'wa'): ('abs1933_statisticians_report_nsw_sydney_lga_maps.pdf', '472', 'State map: Western Australia road districts and municipalities'),
    (1933, 'tas'): ('abs1933_statisticians_report_nsw_sydney_lga_maps.pdf', '473', 'State map: Tasmania municipalities'),
    (1933, 'nt'): ('abs1933_statisticians_report_nsw_sydney_lga_maps.pdf', '475', 'State map: Northern Territory districts'),
    (1933, 'act'): ('abs1933_statisticians_report_nsw_sydney_lga_maps.pdf', '474', 'Federal Capital Territory map'),
    (1947, 'vic'): ('abs1947_statisticians_report_nsw_sydney_lga_maps.pdf', '391', 'State map: Victoria cities, towns, boroughs and shires'),
    (1947, 'qld'): ('abs1947_statisticians_report_nsw_sydney_lga_maps.pdf', '395', 'State map: Queensland cities, towns and shires'),
    (1947, 'sa'): ('abs1947_statisticians_report_nsw_sydney_lga_maps.pdf', '394', 'State map: South Australia municipalities and district councils'),
    (1947, 'wa'): ('abs1947_statisticians_report_nsw_sydney_lga_maps.pdf', '390', 'State map: Western Australia municipalities and road districts'),
    (1947, 'tas'): ('abs1947_statisticians_report_nsw_sydney_lga_maps.pdf', '396', 'State map: Tasmania municipalities'),
    (1947, 'nt'): ('abs1947_statisticians_report_nsw_sydney_lga_maps.pdf', '397', 'State map: Northern Territory districts'),
    (1947, 'act'): ('abs1947_statisticians_report_nsw_sydney_lga_maps.pdf', '398', 'Australian Capital Territory districts'),
}
METRO_PLATES = {
    1911: {'vic': '460', 'qld': '461', 'sa': '464', 'wa': '465', 'tas': '468'},
    1921: {'vic': '408', 'qld': '409'},
    1933: {'vic': '481', 'qld': '480', 'sa': '479', 'wa': '478', 'tas': '477', 'nsw': '476'},
    1947: {'vic': '400', 'qld': '401', 'sa': '402', 'wa': '403', 'tas': '404', 'nsw': '399'},
}
METRO_NOTE = {
    1911: 'Metropolitan map: municipal boundaries within the census metropolitan area',
    1921: 'Metropolitan map: municipal boundaries within the census metropolitan area',
    1933: 'Metropolitan map: municipal boundaries within the census metropolitan area',
    1947: 'Metropolitan map: municipal boundaries within the census metropolitan area',
}
# 1971 metropolitan map sheets inside the per-state Field Count Statements: monochrome,
# with an explicit statistical-division / local-government-area boundary legend.
# 1966 territory maps survive only in the ANU field count statements; Tasmania's map also
# exists as a larger scan in the ABS Bulletin No 6.8 volume.
SOURCES_1966_TERRITORY_MAPS = {
    'nt': ('anu_1966_fcs12_nt_police_districts.pdf', '5',
           'ANU Field Count Statement No. 12: Northern Territory police districts map'),
    'act': ('anu_1966_fcs05_act_administrative_divisions.pdf', '4',
            'ANU Field Count Statement No. 5: ACT administrative divisions map'),
}
SOURCES_1966_ALTERNATE = {
    'tas': ('abs_1966_tas_bulletin_x8_with_lga_maps.pdf', '16',
            'Larger scan of the same Tasmania map series in ABS Bulletin No 6.8'),
}

SOURCES_1971_FIELD_COUNT_MAPS = {
    'vic': ('abs_1971_vic_field_count_statement_lga.pdf', '32', 'Melbourne statistical division map with LGA boundary key'),
    'qld': ('abs_1971_qld_field_count_statement_lga.pdf', '31', 'Brisbane statistical division map with LGA boundary key'),
    'sa': ('abs_1971_sa_field_count_statement_lga.pdf', '26', 'Adelaide statistical division map with LGA boundary key'),
    'tas': ('abs_1971_tas_field_count_statement_lga.pdf', '17', 'Hobart statistical division map'),
    'wa': ('abs_1971_wa_field_count_statement_lga.pdf', '', 'no metropolitan map sheet found in the field count statement'),
    'nt': ('abs_1971_nt_act_field_count_statement_lga.pdf', '', 'no metropolitan map sheet found in the field count statement'),
    'act': ('abs_1971_nt_act_field_count_statement_lga.pdf', '', 'no metropolitan map sheet found in the field count statement'),
}

SOURCES_1971_BULLETIN13 = {
    # Sheet titles were read by OCR; sheets that only repeat the Australia-wide key stay unassigned.
    'vic': ('abs_1971_bulletin13_statistical_division_colour_lga_maps.pdf', '20', 'Melbourne statistical division sheet'),
    'qld': ('abs_1971_bulletin13_statistical_division_colour_lga_maps.pdf', '12;13', 'Queensland statistical division and urban centre sheets'),
    'sa': ('abs_1971_bulletin13_statistical_division_colour_lga_maps.pdf', '7;9;10;11', 'South Australia statistical division and urban centre sheets'),
    'wa': ('abs_1971_bulletin13_statistical_division_colour_lga_maps.pdf', '6;8', 'Western Australia statistical division and urban centre sheets'),
    'tas': ('abs_1971_bulletin13_statistical_division_colour_lga_maps.pdf', '2;14', 'Tasmania statistical division sheet'),
    'nt': ('abs_1971_bulletin13_statistical_division_colour_lga_maps.pdf', '19', 'Northern Territory statistical division sheet'),
    'act': ('abs_1971_bulletin13_statistical_division_colour_lga_maps.pdf', '16', 'Australia statistical division sheet (ACT inset)'),
}


NATIONAL_REPORT_MAPS = {
    1954: ('abs_1954_statisticians_report.pdf',
           {'nsw': '429', 'vic': '431', 'qld': '433', 'sa': '435', 'wa': '437', 'tas': '439',
            'nt': '440', 'act': '441', 'sydney': '442', 'melbourne': '443', 'brisbane': '444',
            'adelaide': '445', 'perth': '446', 'hobart': '447'},
           'National Statistician\'s Report population-density plates: Australia 427; states 429-439; '
           'Northern Territory 440; Federal Capital Territory 441; capital cities 442-447'),
    1961: ('abs_1961_statisticians_report.pdf',
           {'nsw': '501', 'vic': '503', 'qld': '505', 'sa': '507', 'wa': '509', 'tas': '511',
            'nt': '513', 'act': '513', 'sydney': '514', 'melbourne': '515', 'brisbane': '516',
            'adelaide': '517', 'perth': '518', 'hobart': '519'},
           'National Statistician\'s Report population-density maps; Northern Territory and ACT share page 513'),
}


def build_map_sources(plate_pages):
    """Assemble the candidate map-source table for every state-year."""
    sources = []
    for year in YEARS:
        for state in STATES:
            if year in (1911, 1921, 1933, 1947):
                key = (year, state)
                if key not in MAP_SOURCE_PAGES:
                    sources.append(dict(census_year=year, state_code=state, source_record_id='',
                                        role='no_candidate_map_found',
                                        local_path='', pdf_map_pages='',
                                        boundary_date_evidence='No statewide or metropolitan plate located for this state-year.',
                                        individual_outline_status='no_candidate_map'))
                    continue
                if key in MAP_SOURCE_PAGES:
                    pdf_name, pages, evidence = MAP_SOURCE_PAGES[key]
                    metro = METRO_PLATES.get(year, {}).get(state)
                    if metro:
                        pages = f'{pages};{metro}'
                        evidence = f'{evidence}. {METRO_NOTE[year]} on page {metro}'
                    sources.append(dict(census_year=year, state_code=state, source_record_id=pdf_name.replace('.pdf', ''),
                                        role='census_report_plate', local_path=f'data/raw/historical_boundary_maps/abs_census/{pdf_name}',
                                        pdf_map_pages=pages, boundary_date_evidence=evidence,
                                        individual_outline_status='not_audited'))
                continue
            if year == 1971:
                if state in SOURCES_1971_FIELD_COUNT_MAPS:
                    fc_pdf, fc_pages, fc_note = SOURCES_1971_FIELD_COUNT_MAPS[state]
                    if fc_pages:
                        sources.append(dict(census_year=year, state_code=state,
                                            source_record_id=fc_pdf.replace('.pdf', ''),
                                            role='field_count_metropolitan_map',
                                            local_path=f'data/raw/historical_boundary_maps/abs_census/{fc_pdf}',
                                            pdf_map_pages=fc_pages, boundary_date_evidence=fc_note,
                                            individual_outline_status='not_audited'))
                pdf_name, pages, evidence = SOURCES_1971_BULLETIN13[state]
                sources.append(dict(census_year=year, state_code=state, source_record_id=pdf_name.replace('.pdf', ''),
                                    role='census_bulletin_map_sheet',
                                    local_path=f'data/raw/historical_boundary_maps/abs_census/{pdf_name}',
                                    pdf_map_pages=pages, boundary_date_evidence=evidence,
                                    individual_outline_status='not_audited'))
                continue
            if year in (1954, 1961) and state in NATIONAL_REPORT_MAPS.get(year, (None, {}))[1]:
                # The national Statistician's Report plate is the sharper scan for these years;
                # the state volume plate stays as an alternate candidate.
                report_pdf, page_map, note = NATIONAL_REPORT_MAPS[year]
                pages = page_map[state]
                sources.append(dict(census_year=year, state_code=state,
                                    source_record_id=report_pdf.replace('.pdf', ''),
                                    role='national_report_plate',
                                    local_path=f'data/raw/historical_boundary_maps/abs_census/{report_pdf}',
                                    pdf_map_pages=pages, boundary_date_evidence=note,
                                    individual_outline_status='not_audited'))
                volume_pdf = slug_volume(year, state)
                volume_pages = detect_map_pages(volume_pdf)
                if volume_pages:
                    sources.append(dict(census_year=year, state_code=state,
                                        source_record_id=volume_pdf.replace('.pdf', ''),
                                        role='alternate_plate_extra',
                                        local_path=f'data/raw/historical_boundary_maps/abs_census/{volume_pdf}',
                                        pdf_map_pages=';'.join(str(p) for p in volume_pages),
                                        boundary_date_evidence='State volume colour plate (smaller scan)',
                                        individual_outline_status='not_audited'))
                continue
            if year == 1966 and state in SOURCES_1966_TERRITORY_MAPS:
                pdf_name, pages, evidence = SOURCES_1966_TERRITORY_MAPS[state]
                sources.append(dict(census_year=year, state_code=state,
                                    source_record_id=pdf_name.replace('.pdf', ''),
                                    role='field_count_map',
                                    local_path=f'data/raw/historical_boundary_maps/abs_census/{pdf_name}',
                                    pdf_map_pages=pages, boundary_date_evidence=evidence,
                                    individual_outline_status='not_audited'))
                continue
            if year == 1966 and state in SOURCES_1966_ALTERNATE:
                pdf_name, pages, evidence = SOURCES_1966_ALTERNATE[state]
                sources.append(dict(census_year=year, state_code=state,
                                    source_record_id=pdf_name.replace('.pdf', ''),
                                    role='alternate_plate_extra',
                                    local_path=f'data/raw/historical_boundary_maps/abs_census/{pdf_name}',
                                    pdf_map_pages=pages, boundary_date_evidence=evidence,
                                    individual_outline_status='not_audited'))
            if year == 1976:
                pdf_name = f'anu1976_{state}_preliminary_lga_boundary_maps.pdf'
                pages = detect_map_pages(pdf_name, tail=12)
                sources.append(dict(census_year=year, state_code=state, source_record_id=pdf_name.replace('.pdf', ''),
                                    role='census_preliminary_boundary_maps',
                                    local_path=f'data/raw/historical_boundary_maps/abs_census/{pdf_name}',
                                    pdf_map_pages=';'.join(str(p) for p in pages),
                                    boundary_date_evidence='Census 30 June 1976 preliminary LGA boundary maps (ANU copy)',
                                    individual_outline_status='not_audited'))
                continue
            pdf_name = slug_volume(year, state)
            page_count = None
            try:
                with pymupdf.open(RAW / pdf_name) as document:
                    page_count = document.page_count
            except Exception:
                page_count = None
            pages = detect_map_pages(pdf_name)
            sources.append(dict(census_year=year, state_code=state, source_record_id=pdf_name.replace('.pdf', ''),
                                role='census_report_plate',
                                local_path=f'data/raw/historical_boundary_maps/abs_census/{pdf_name}',
                                pdf_map_pages=';'.join(str(p) for p in pages),
                                boundary_date_evidence=f'Census {DATES[year]} LGA plates at the end of the state volume',
                                individual_outline_status='not_audited'))
    # Additional national-report map candidates (not linked to panel rows, kept as evidence).
    for year, (pdf_name, page_map, note) in NATIONAL_REPORT_MAPS.items():
        for key, pages in page_map.items():
            sources.append(dict(census_year=year, state_code=key, source_record_id=pdf_name.replace('.pdf', ''),
                                role='national_report_plate_extra',
                                local_path=f'data/raw/historical_boundary_maps/abs_census/{pdf_name}',
                                pdf_map_pages=pages, boundary_date_evidence=note,
                                individual_outline_status='not_audited'))
    return sources



def coverage_against_1981_geopackage(panel):
    """Match 1981 panel names against the ABS 1981 GeoPackage whole-LGA names.

    Queensland's 1981 layer includes Brisbane suburbs as separate features; only rows whose
    name carries a council-type suffix are treated as whole local government areas.
    """
    gpkg = ROOT / 'data/raw/nsw_lga_census_panel/census1981.gpkg'
    if not gpkg.is_file():
        return []
    import sqlite3
    connection = sqlite3.connect(f'file:{gpkg}?mode=ro', uri=True)
    rows = []
    for ste, code in [('2', 'vic'), ('3', 'qld'), ('4', 'sa'), ('5', 'wa'), ('6', 'tas')]:
        reference = set()
        for (name,) in connection.execute(
                'SELECT LGA_NAME_1981 FROM local_government_area_1981 WHERE STE_CODE_1981=?', (ste,)):
            if not re.search(r'\((S|C|T|M|Shire|City|Town|Municipality|B|DC|R)\)', name):
                continue
            reference.add(name_key(re.sub(r'\s*\(part[^)]*\)', '', name, flags=re.I)))
        panel_keys = {name_key(row['lga_name']) for row in panel
                      if row['census_year'] == 1981 and row['state_code'] == code}
        matched = sum(1 for key in reference
                      if any(edit_distance(key, candidate, 2) <= 2 for candidate in panel_keys))
        rows.append(dict(census_year=1981, state_code=code,
                         reference_whole_lga_names=len(reference), panel_rows=len(panel_keys),
                         matched=matched,
                         matched_percent=round(100 * matched / len(reference)) if reference else 0))
    connection.close()
    return rows


def main():
    plate_pages = get_map_plate_pages()
    roster_rows = []
    roster_rows += extract_1911()
    for year in (1921, 1933, 1947):
        roster_rows += extract_report(year)
    for state in STATES:
        for year in (1954, 1961):
            roster_rows += extract_index(year, state)
        roster_rows += extract_suffix_volume(1966, state, slug_volume(1966, state), TYPE_SUFFIX)
        roster_rows += extract_1971(state)
        roster_rows += extract_1976(state)
        roster_rows += extract_1981(state)
    for year in (1954, 1961):
        for territory in ('nt', 'act'):
            roster_rows += extract_territory(year, territory)
    for year in (1966, 1971):
        roster_rows += extract_territory(year)
    for year in (1976, 1981):
        for territory in ('nt', 'act'):
            existing_state_rows = [r for r in roster_rows
                                   if r['census_year'] == year and r['state'] == territory]
            if len(existing_state_rows) < 3:
                # ACT publishes divisions and districts instead of councils; add them only
                # where no council-type rows exist for the year.
                roster_rows += extract_territory(year, territory)
    log(f'raw rows {len(roster_rows)}')
    rows = dedupe(roster_rows)
    before_filter = len(rows)
    rows = [row for row in rows if is_plausible_name(row['lga_name'])]
    log(f'name filter: {before_filter - len(rows)} rows dropped as OCR debris')
    rows = merge_ocr_variants(rows)
    log(f'deduped rows {len(rows)} (after OCR-variant merge)')
    counts = Counter((r['census_year'], r['state']) for r in rows)
    for key in sorted(counts):
        log(f'  {key[0]} {key[1]}: {counts[key]}')

    sources = build_map_sources(plate_pages)
    source_lookup = {(s['census_year'], s['state_code']): s for s in sources
                     if s['role'] not in ('national_report_plate_extra', 'alternate_plate_extra')}
    for year in YEARS:
        for state in STATES:
            if (year, state) not in source_lookup:
                source_lookup[(year, state)] = dict(source_record_id='', pdf_map_pages='',
                                                    role='no_candidate_map_found',
                                                    individual_outline_status='no_candidate_map')

    def resolve_source(name):
        if '/' in name or not name:
            return name
        candidate = RAW / name
        return str(candidate.relative_to(ROOT)).replace('\\', '/') if candidate.is_file() else name

    alternate_plates = {}
    for year, (pdf_name, page_map, _note) in NATIONAL_REPORT_MAPS.items():
        for key, pages in page_map.items():
            alternate_plates[(year, key)] = (pdf_name, pages)
    panel = []
    for row in rows:
        source = source_lookup[(row['census_year'], row['state'])]
        alternate_pdf, alternate_pages = alternate_plates.get((row['census_year'], row['state']), ('', ''))
        panel.append(OrderedDict([
            ('census_year', row['census_year']), ('census_date', DATES[row['census_year']]),
            ('state_code', row['state']), ('state_name', STATES[row['state']]),
            ('lga_code', ''), ('lga_name', row['lga_name']), ('lga_type', row['lga_type']),
            ('lga_class', row['lga_class']), ('unit_class', row.get('unit_class', 'council')),
            ('published_geography_date', DATES[row['census_year']]), ('date_conflict', ''),
            ('source_pdf', resolve_source(row['source_pdf'])),
            ('source_pdf_page', row['source_pdf_page']),
            ('source_row_number', row['source_row_number']), ('section_raw', row['section_raw']),
            ('name_alternates', row.get('name_alternates', '')),
            ('roster_status', row['roster_status']),
            ('map_source_id', source['source_record_id']),
            ('map_source_pdf', resolve_source(Path(source['local_path']).name) if source['local_path'] else ''),
            ('map_coverage_status', 'not_audited'),
            ('map_pdf_pages', source['pdf_map_pages']),
            ('map_role', source['role']),
            ('map_source_alternate_id', Path(alternate_pdf).name.replace('.pdf', '') if alternate_pdf else ''),
            ('map_source_alternate_file', resolve_source(alternate_pdf) if alternate_pdf else ''),
            ('map_pdf_pages_alternate', alternate_pages),
            ('digital_name', ''), ('digital_name_status', 'not_applicable'),
            ('source_conflict', ''),
            ('name_review_required', 'yes' if row['roster_status'] == 'ocr_extracted' else 'no'),
            ('next_action', 'Review OCR name against the source page; then audit the map plate.'),
        ]))
    panel.sort(key=lambda r: (r['census_year'], r['state_code'], name_key(r['lga_name'])))

    fields = list(panel[0].keys())
    with (OUT / 'lga_census_panel.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(panel)

    with (OUT / 'map_source_candidates.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sources[0].keys()))
        writer.writeheader()
        writer.writerows(sources)

    summary = []
    for year in YEARS:
        for state in STATES:
            selected = [r for r in panel if r['census_year'] == year and r['state_code'] == state]
            source = source_lookup[(year, state)]
            summary.append(OrderedDict([
                ('census_year', year), ('state_code', state), ('state_name', STATES[state]),
                ('council_rows', len(selected)),
                ('typed_rows', sum(1 for r in selected if r['lga_type'])),
                ('untyped_rows', sum(1 for r in selected if not r['lga_type'])),
                ('urban_rows', sum(1 for r in selected if r['lga_class'] == 'urban')),
                ('rural_rows', sum(1 for r in selected if r['lga_class'] == 'rural')),
                ('map_source_id', source['source_record_id']),
                ('map_pdf_pages', source['pdf_map_pages']),
                ('map_role', source['role']),
                ('individual_outline_status', source['individual_outline_status']),
            ]))
    with (OUT / 'census_year_state_summary.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)

    review = [r for r in panel if r['name_review_required'] == 'yes']
    with (OUT / 'name_review_queue.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(review)

    coverage = coverage_against_1981_geopackage(panel)
    if coverage:
        with (OUT / 'coverage_vs_1981_geopackage.csv').open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(coverage[0].keys()))
            writer.writeheader()
            writer.writerows(coverage)
        for row in coverage:
            log(f"  1981 coverage {row['state_code']}: {row['matched']}/{row['reference_whole_lga_names']} "
                f"({row['matched_percent']}%)")
    log(f'panel rows {len(panel)}; review queue {len(review)}; sources {len(sources)}')
    status = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(), state='panel_built',
                  unit='LGA census year', completed=len(panel), total=len(panel), failed=0, skipped=0,
                  remaining=0, states=list(STATES), census_years=YEARS,
                  last_successful_output='explore/output/2026-10-16_other-states-lga-census-panel/lga_census_panel.csv',
                  checkpoint='explore/output/2026-10-16_other-states-lga-census-panel/status.json',
                  resume_command='python3 explore/2026-10-16_other-states-lga-census-panel.py',
                  live_job=False,
                  next_action='Review the OCR name queue, then audit individual map outlines.',
                  blocker=None, full_panel_complete=False,
                  candidate_map_for_every_row=all(r['map_source_id'] for r in panel))
    (OUT / 'status.json').write_text(json.dumps(status, indent=2) + '\n', encoding='utf-8')
    verification = dict(timestamp_utc=status['timestamp_utc'],
                        panel_rows=len(panel),
                        unique_keys=len({(r['census_year'], r['state_code'], name_key(r['lga_name'])) for r in panel}),
                        all_rows_have_map_source=all(r['map_source_id'] for r in panel),
                        state_year_pairs=len({(r['census_year'], r['state_code']) for r in panel}),
                        sources_with_pages=sum(1 for s in sources if s['pdf_map_pages']),
                        sources_without_pages=[f"{s['census_year']}-{s['state_code']}"
                                               for s in sources if not s['pdf_map_pages']])
    (OUT / 'verification.json').write_text(json.dumps(verification, indent=2) + '\n', encoding='utf-8')
    (OUT / 'panel_build.log').write_text('\n'.join(LOG) + '\n', encoding='utf-8')
    print(json.dumps(verification, indent=2))


if __name__ == '__main__':
    main()
