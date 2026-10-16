# Purpose: rate every candidate census map plate (NSW and other states) for digitisation
#   likelihood, name the blockers, and point at the best available alternative source.
# Inputs: explore/output/2026-10-17_map-digitisation-readiness/plate_metrics.csv (resolution,
#   colour, contrast per plate) and the reviewed judgements recorded in this script.
# Outputs: explore/output/2026-10-17_map-digitisation-readiness/digitisation_readiness.csv
#   (+ summary_by_year.csv).
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path('.')
OUT = ROOT / 'explore/output/2026-10-17_map-digitisation-readiness'
OUT.mkdir(parents=True, exist_ok=True)

# Page-level judgements. Rating scale:
#   A - digitise now: clear LGA boundary line work, enough resolution, coastline/river/town
#       references and a scale bar.
#   B - digitiable with care: legible boundaries but moderate resolution, extra line work to
#       separate (railways, statistical boundaries), or colour separation needed.
#   C - hard: low resolution, boundary type ambiguous, or shading obscures the lines; tracing
#       would be unreliable without a better scan.
#   D - not digitiable as LGA polygons: no boundary line work (counties, statistical
#       districts, printed indexes) or point symbols only.
RATINGS = {
    # ---------------------------------------------------------------- NSW
    ('nsw', 1911, 'nsw', 457): ('B', 'Sydney municipal boundaries with a numbered key; small 568x941 px scan',
                                'metropolitan',
                                'No 1911 NSW statewide LGA plate was published (PDF 444 is counties only). Nearest statewide shire plates are the NSW Year Books (1927-28 onward); the ANU 1917 Sydney sheet gives finer metro line work.'),
    ('nsw', 1921, 'nsw', 407): ('A', 'Sydney municipal boundaries, numbered key, 2135x3177 px; statewide LGA index plate PDF 394/395',
                                'statewide + metropolitan', ''),
    ('nsw', 1933, 'nsw', 476): ('B', 'Sydney municipal boundaries with explicit boundary key; 1448x1696 px; statewide plate PDF 468',
                                'statewide + metropolitan',
                                'Larger scans of the same plates are not held; ANU holdings for 1933 NSW are absent.'),
    ('nsw', 1947, 'nsw', 399): ('A', 'Sydney municipal boundaries with boundary key; 2976 px; statewide shire plate PDF 392',
                                'statewide + metropolitan', ''),
    ('nsw', 1954, 'nsw', 196): ('C', 'State volume plate 946x1107 px; municipal lines dense in the metro',
                                'statewide + metropolitan',
                                'SLNSW 1954 whole-map JPG (8405x9891 px, already in raw) is the better statewide candidate; the 1954 Statistician Report plate PDF 429 (2112 px) adds a statewide alternative.'),
    ('nsw', 1961, 'nsw', 131): ('C', 'State volume Sydney plate 941 px; coarse',
                                'metropolitan',
                                'ANU Sydney 1961 JPG (7884x8611 px) is the better metro candidate; the 1961 Statistician Report plate PDF 501 (2144 px) covers statewide.'),
    ('nsw', 1966, 'nsw', 509): ('C', 'State volume regional series 845-1340 px; line work clear but coarse',
                                'regional', 'ANU 1966 NSW Bulletin 1.8 scans (2024x3088 px, already in raw) are the better candidates.'),
    ('nsw', 1971, 'nsw', 21): ('C', 'Bulletin 13 colour sheet 878 px; statistical-division and LGA lines share colour fills',
                               'statewide',
                               'Field Count Statement No 3 maps (Sydney PDF 39, Newcastle 40, Wollongong 41, long edge about 5000 px) give a monochrome metro alternative.'),
    ('nsw', 1976, 'nsw', 61): ('B', 'ANU preliminary boundary maps 2176x2368 px; LGA lines with names',
                               'statewide + metropolitan', ''),
    ('nsw', 1981, 'nsw', 64): ('A', 'Whole-of-state and Sydney sheets 3520 px with council labels',
                               'statewide + metropolitan',
                               'The official 1981 ABS GeoPackage already supplies digital geometry for NSW (no tracing needed).'),
    ('nsw', 1954, 'nsw', 0): ('A', 'SLNSW whole-of-state colour map, 8405x9891 px - the sharpest 1954 NSW source held',
                               'statewide + metropolitan', ''),
    ('nsw', 1961, 'nsw', 0): ('A', 'ANU Sydney metropolitan map, 7884x8611 px - sharpest 1961 Sydney source held',
                              'metropolitan',
                              'Statewide 1961 NSW coverage comes from the 1961 Statistician Report plate PDF 501.'),
    ('nsw', 1911, 'nsw', 444): ('D', 'Statewide plate shows counties, not local government areas', 'not-LGA',
                               'No 1911 NSW statewide shire plate was published in this volume.'),
    ('nsw', 1921, 'nsw', 394): ('A', 'Statewide NSW density and LGA plate, numbered councils', 'statewide', ''),
    ('nsw', 1961, 'nsw', 130): ('C', 'Printed LGA number index page, not a map', 'index',
                                'Use the number index to key the statewide plate PDF 129 and the Sydney plate PDF 131.'),
    ('nsw', 1966, 'nsw', 508): ('C', 'Map-series reference page, not a map', 'index', ''),
    ('nsw', 1966, 'nsw', 40): ('C', 'ANU Bulletin 1.8 map reference page, not a map', 'index', ''),
    ('nsw', 1966, 'nsw', 41): ('B', 'ANU Bulletin 1.8 Sydney scan, 2024x3088 px - the sharper 1966 NSW alternative', 'metropolitan', ''),
    ('nsw', 1966, 'nsw', 48): ('B', 'ANU Bulletin 1.8 regional sheet (Colo and Central West), sharper than the ABS volume', 'regional', ''),
    ('nsw', 1971, 'nsw', 3): ('C', 'Bulletin 13 NSW colour sheet (statistical divisions and LGA lines share fills)',
                             'statewide',
                             'Field Count Statement No 3 maps (PDF 39-41) are the monochrome metropolitan alternative.'),
    ('nsw', 1971, 'nsw', 39): ('A', 'Sydney map from Field Count Statement No 3, long edge about 5000 px', 'metropolitan', ''),
    ('nsw', 1971, 'nsw', 40): ('A', 'Newcastle map from Field Count Statement No 3', 'metropolitan', ''),
    ('nsw', 1971, 'nsw', 41): ('A', 'Wollongong map from Field Count Statement No 3', 'metropolitan', ''),
    ('nsw', 1976, 'nsw', 60): ('B', 'Statewide preliminary boundary sheet', 'statewide', ''),
    ('nsw', 1976, 'nsw', 62): ('B', 'Statewide and metropolitan preliminary boundary sheet', 'statewide + metropolitan', ''),
    ('nsw', 1981, 'nsw', 62): ('A', 'Statewide sheet with council labels, 3520 px', 'statewide', ''),
    ('nsw', 1981, 'nsw', 66): ('A', 'Regional districts sheet with council lines, 3520 px', 'regional', ''),
    # ---------------------------------------------------------------- other states, 1911
    ('other', 1911, 'vic', 445): ('D', 'Statewide plate is 500x375 px - too small to trace any boundary',
                                  'statewide',
                                  'Not held: ABS has no digitised Victorian Year Book for 1911; needs the Victorian municipal map (Lands Department) or a library scan.'),
    ('other', 1911, 'qld', 448): ('C', 'Statewide census districts at 568x941 px; district lines clear but coarse',
                                  'statewide',
                                  'The digitised Year Book Queensland series starts at 1937 (ABS catalogue 1301.3); a 1911 Lands Department map is not held.'),
    ('other', 1911, 'sa', 449): ('C', 'Counties and divisions at 575x943 px; district-council lines faint',
                                 'statewide',
                                 'Not held: no digitised South Australian statistical register for 1911; a library scan of the 1911 municipal map is needed.'),
    ('other', 1911, 'wa', 452): ('C', 'Statistical districts at 568x939 px; road-board boundaries coarse',
                                 'statewide',
                                 'Not held: no digitised WA statistical register for 1911; a library scan is needed.'),
    ('other', 1911, 'tas', 453): ('C', 'Municipality boundaries complete but only 600x941 px',
                                  'statewide',
                                  'Not held: the digitised Tasmania year book series starts later; a library scan is needed.'),
    ('other', 1911, 'nt', 456): ('D', 'No local government polygons in 1911 (districts only)', 'districts', 'Not applicable: the published units are districts, not local government areas.'),
    # ---------------------------------------------------------------- 1921
    ('other', 1921, 'vic', 397): ('A', 'LGA index plate 4426x3541 px with numbered councils and Melbourne inset',
                                  'statewide + metropolitan', ''),
    ('other', 1921, 'qld', 399): ('A', 'LGA index plate 2457x3496 px with numbered shires',
                                  'statewide', ''),
    ('other', 1921, 'sa', 401): ('A', 'LGA index plate 2265x3546 px with numbered district councils',
                                 'statewide', ''),
    ('other', 1921, 'wa', 403): ('B', 'LGA index plate 2232x3592 px, but the interior has sparse reference features',
                                 'statewide', 'Perth sheet PDF 403 inset plus railways carry most of the georeferencing load.'),
    ('other', 1921, 'tas', 405): ('A', 'LGA index plate 2573x3570 px with numbered municipalities',
                                  'statewide', ''),
    ('other', 1921, 'nt', 406): ('D', 'No local government polygons in 1921 (districts only)', 'districts', 'Not applicable: the published units are districts, not local government areas.'),
    # ---------------------------------------------------------------- 1933
    ('other', 1933, 'vic', 469): ('A', 'Statewide shire and municipality plate 2176x1778 px with printed numbers',
                                  'statewide', ''),
    ('other', 1933, 'qld', 470): ('B', 'Statewide plate 1216x1696 px; shire lines clear, metro insets small',
                                  'statewide', ''),
    ('other', 1933, 'sa', 471): ('B', 'Statewide plate 1216x1664 px; dense district-council mesh',
                                 'statewide', ''),
    ('other', 1933, 'wa', 472): ('B', 'Statewide plate 1088x1664 px; road-district lines clear, east sparse',
                                 'statewide', ''),
    ('other', 1933, 'tas', 473): ('B', 'Statewide plate 1184x1632 px; municipality lines clear',
                                  'statewide', ''),
    ('other', 1933, 'act', 474): ('C', 'Federal Capital Territory districts at 992x1632 px', 'districts', 'Not applicable: the published units are districts, not local government areas.'),
    ('other', 1933, 'nt', 475): ('C', 'Districts only, 992x1600 px', 'districts', 'Not applicable: the published units are districts, not local government areas.'),
    # ---------------------------------------------------------------- 1947
    ('other', 1947, 'vic', 391): ('A', 'Statewide plate 2144x1696 px with numbered shires and municipalities',
                                  'statewide', ''),
    ('other', 1947, 'qld', 395): ('A', 'Statewide plate 2336x3328 px with numbered units', 'statewide', ''),
    ('other', 1947, 'sa', 394): ('A', 'Statewide plate 2240x3328 px with district councils', 'statewide', ''),
    ('other', 1947, 'wa', 390): ('A', 'Statewide plate 2496x1680 px; road districts numbered', 'statewide', ''),
    ('other', 1947, 'tas', 396): ('A', 'Statewide plate 2496x3352 px', 'statewide', ''),
    ('other', 1947, 'nt', 397): ('C', 'Districts only, 2144x3328 px', 'districts', 'Not applicable: the published units are districts, not local government areas.'),
    ('other', 1947, 'act', 398): ('C', 'Districts only, 2048x3328 px', 'districts', 'Not applicable: the published units are districts, not local government areas.'),
    # ------------------------------------------- national report plates (sharpest scans)
    ('other', 1954, 'nsw', 429): ('B', 'Statistician Report statewide plate, 2112x1760 px', 'statewide', ''),
    ('other', 1954, 'vic', 431): ('C', 'Statistician Report statewide plate, 1127x976 px - the smallest of the 1954 series',
                                  'statewide', 'No sharper 1954 Victoria plate held.'),
    ('other', 1954, 'qld', 433): ('B', 'Statistician Report statewide plate, 1760x2176 px', 'statewide', ''),
    ('other', 1954, 'sa', 435): ('B', 'Statistician Report statewide plate, 2080x1856 px', 'statewide', ''),
    ('other', 1954, 'wa', 437): ('B', 'Statistician Report statewide plate, 2112x1920 px', 'statewide', ''),
    ('other', 1954, 'tas', 439): ('B', 'Statistician Report statewide plate (completes the 429-439 state series)', 'statewide', ''),
    ('other', 1954, 'nt', 440): ('B', 'Statistician Report Northern Territory plate', 'districts', ''),
    ('other', 1954, 'act', 441): ('B', 'Statistician Report Federal Capital Territory plate', 'districts', ''),
    ('other', 1954, 'sydney', 442): ('B', 'Statistician Report Sydney metropolitan plate', 'metropolitan', ''),
    ('other', 1954, 'melbourne', 443): ('B', 'Statistician Report Melbourne metropolitan plate', 'metropolitan', ''),
    ('other', 1954, 'brisbane', 444): ('B', 'Statistician Report Brisbane metropolitan plate', 'metropolitan', ''),
    ('other', 1954, 'adelaide', 445): ('B', 'Statistician Report Adelaide metropolitan plate', 'metropolitan', ''),
    ('other', 1954, 'perth', 446): ('B', 'Statistician Report Perth metropolitan plate', 'metropolitan', ''),
    ('other', 1954, 'hobart', 447): ('B', 'Statistician Report Hobart metropolitan plate', 'metropolitan', ''),
    ('other', 1961, 'nsw', 501): ('A', 'Statistician Report statewide plate, 2144x1824 px colour with LGA key', 'statewide', ''),
    ('other', 1961, 'vic', 503): ('A', 'Statistician Report statewide plate, 2080x1824 px', 'statewide', ''),
    ('other', 1961, 'qld', 505): ('A', 'Statistician Report statewide plate, 1810x2112 px', 'statewide', ''),
    ('other', 1961, 'sa', 507): ('A', 'Statistician Report statewide plate, 2112x1824 px', 'statewide', ''),
    ('other', 1961, 'wa', 509): ('A', 'Statistician Report statewide plate, 2112x1824 px', 'statewide', ''),
    ('other', 1961, 'tas', 511): ('A', 'Statistician Report statewide plate, 2112x1856 px', 'statewide', ''),
    ('other', 1961, 'nt', 513): ('B', 'Statistician Report NT and ACT plate, 2176x1664 px', 'districts', ''),
    ('other', 1961, 'act', 513): ('B', 'Statistician Report NT and ACT plate, 2176x1664 px', 'districts', ''),
    ('other', 1961, 'sydney', 514): ('A', 'Statistician Report Sydney plate, 1880x2112 px', 'metropolitan', ''),
    ('other', 1961, 'melbourne', 515): ('A', 'Statistician Report Melbourne plate, 2070x1824 px', 'metropolitan', ''),
    ('other', 1961, 'brisbane', 516): ('A', 'Statistician Report Brisbane plate, 1854x2112 px', 'metropolitan', ''),
    ('other', 1961, 'adelaide', 517): ('A', 'Statistician Report Adelaide plate, 1984x1824 px', 'metropolitan', ''),
    ('other', 1961, 'perth', 518): ('A', 'Statistician Report Perth plate, 2112x1856 px', 'metropolitan', ''),
    ('other', 1961, 'hobart', 519): ('A', 'Statistician Report Hobart plate, 2080x1856 px', 'metropolitan', ''),
    # ---------------------------------------------------------------- 1954
    ('other', 1954, 'vic', 158): ('C', 'State volume colour plate only 569x483 px',
                                  'statewide',
                                  'The 1954 Statistician Report plate PDF 431 (1127x976 px) is larger; no sharper 1954 Victoria plate is held.'),
    ('other', 1954, 'qld', 171): ('C', 'State volume colour plate 480x579 px', 'statewide',
                                  'Statistician Report plate PDF 433 (1760x2176 px) is the better candidate.'),
    ('other', 1954, 'sa', 98): ('C', 'State volume colour plate 1132x959 px', 'statewide',
                                'Statistician Report plate PDF 435 (2080x1856 px) is the better candidate.'),
    ('other', 1954, 'wa', 113): ('C', 'State volume colour plate 1125x956 px', 'statewide',
                                 'Statistician Report plate PDF 437 (2112x1920 px) is the better candidate.'),
    ('other', 1954, 'tas', 70): ('C', 'State volume colour plate 1125x956 px', 'statewide',
                                 'Use the 1954 Statistician Report plate PDF 439 (statewide series 429-439, 1760-2176 px).'),
    ('other', 1954, 'nt', 117): ('B', 'Territory districts plate 960x1139 px', 'districts',
                                 'The 1954 Statistician Report plate PDF 440 is a statewide alternative.'),
    ('other', 1954, 'act', 112): ('B', 'Territory divisions plate 1141x956 px with Canberra detail', 'districts',
                                  'The 1954 Statistician Report plate PDF 441 covers the Federal Capital Territory.'),
    # ---------------------------------------------------------------- 1961
    ('other', 1961, 'vic', 104): ('C', 'State volume colour plate 1072x953 px', 'statewide',
                                  'Statistician Report plate PDF 503 (2080x1824 px) is the better candidate.'),
    ('other', 1961, 'qld', 105): ('C', 'State volume colour plate 960x1096 px', 'statewide',
                                  'Statistician Report plate PDF 505 (1810x2112 px) is the better candidate.'),
    ('other', 1961, 'sa', 59): ('C', 'State volume colour plate 1086x964 px', 'statewide',
                                'Statistician Report plate PDF 507 (2112x1824 px) is the better candidate.'),
    ('other', 1961, 'wa', 80): ('C', 'State volume colour plate 1086x945 px', 'statewide',
                                'Statistician Report plate PDF 509 (2112x1824 px) is the better candidate.'),
    ('other', 1961, 'tas', 55): ('C', 'State volume colour plate 1076x948 px', 'statewide',
                                 'Statistician Report plate PDF 511 (2112x1856 px) is the better candidate.'),
    ('other', 1961, 'nt', 179): ('C', 'No map in the territory volume; the plate picked here is a table page',
                                 'statewide',
                                 'Use the 1961 Statistician Report NT/ACT plate PDF 513 (2176x1664 px).'),
    # ---------------------------------------------------------------- 1966
    ('other', 1966, 'vic', 486): ('C', 'Regional series 568-1043 px; line work clear but coarse',
                                  'regional',
                                  'ABS Bulletin No 2.8 holds the same series at the same resolution; no larger scan located.'),
    ('other', 1966, 'qld', 443): ('C', 'Regional series 288-1344 px; smallest sheets are index pages',
                                  'regional',
                                  'ABS Bulletin No 3.8 duplicates the series; no larger scan located.'),
    ('other', 1966, 'sa', 289): ('C', 'Regional series 558-1749 px', 'regional',
                                  'No better source located: ABS Bulletin No 4.8 and the ANU holdings do not include a larger South Australian copy.'),
    ('other', 1966, 'wa', 284): ('C', 'Regional series 529-1703 px', 'regional',
                                  'No better source located: ABS Bulletin No 5.8 duplicates the series; ANU holds no larger Western Australian copy.'),
    ('other', 1966, 'tas', 158): ('B', 'Statewide sheet 1674x2144 px plus regional sheets',
                                  'statewide + regional',
                                  'ABS Bulletin No 6.8 page 16 gives a 2161 px statewide sheet as an alternative.'),
    ('other', 1966, 'nt', 5): ('B', 'ANU Field Count Statement No 12: Northern Territory police districts map, 3240 px',
                               'districts', ''),
    ('other', 1966, 'act', 4): ('B', 'ANU Field Count Statement No 5: ACT administrative divisions map, 2712 px',
                                'districts', ''),
    # ---------------------------------------------------------------- 1971
    ('other', 1971, 'vic', 32): ('A', 'Melbourne statistical-division map, 3527x4974 px, monochrome, explicit LGA boundary key',
                                 'metropolitan',
                                 'Statewide coverage comes from Bulletin 13 sheets (colour, statistical and LGA lines).'),
    ('other', 1971, 'qld', 31): ('A', 'Brisbane statistical-division map, 3508x4961 px, LGA boundary key',
                                 'metropolitan', ''),
    ('other', 1971, 'sa', 26): ('A', 'Adelaide statistical-division map, 3508x4961 px, LGA boundary key',
                                'metropolitan', ''),
    ('other', 1971, 'tas', 17): ('A', 'Hobart statistical-division map, 3537x4981 px', 'metropolitan', ''),
    ('other', 1971, 'wa', 6): ('B', 'Perth and Kalgoorlie urban-centre sheets from Bulletin 13 (colour)',
                               'metropolitan', 'No field count statement map located for WA; Bulletin 13 sheet is the candidate.'),
    ('other', 1971, 'nt', 19): ('B', 'Northern Territory sheet from Bulletin 13 (1723x1086 px)', 'districts', ''),
    ('other', 1971, 'act', 16): ('B', 'Australia sheet with ACT inset (2897x2448 px)', 'districts', ''),
    # ---------------------------------------------------------------- 1976
    ('other', 1976, 'vic', 58): ('A', 'Monochrome preliminary boundary maps 2224-3600 px with LGA names',
                                 'statewide + metropolitan', ''),
    ('other', 1976, 'qld', 57): ('A', 'Monochrome preliminary sheets 1848-2608 px', 'statewide', ''),
    ('other', 1976, 'sa', 47): ('B', 'Monochrome sheets 1848-2600 px; some sheets show statistical divisions only',
                                'statewide',
                                'Use the detailed LGA sheets rather than the statistical-division sheets.'),
    ('other', 1976, 'wa', 45): ('B', 'Monochrome sheets 1792-2600 px; statistical-division sheet must be skipped',
                                'statewide', ''),
    ('other', 1976, 'tas', 30): ('A', 'Detailed municipality sheet plus division sheet, 1792-3000 px', 'statewide', ''),
    ('other', 1976, 'nt', 26): ('B', 'Division sheet plus Darwin statistical-division detail', 'districts', ''),
    ('other', 1976, 'act', 25): ('B', 'Division and district sheet, 25-page volume', 'districts', ''),
    # ---------------------------------------------------------------- 1981
    ('other', 1981, 'vic', 53): ('A', 'Statewide and metropolitan sheets 3520-5824 px with council labels',
                                 'statewide + metropolitan',
                                 'The 1981 ABS GeoPackage already supplies digital geometry (no tracing needed).'),
    ('other', 1981, 'qld', 58): ('A', 'Statewide and capital-city sheets 3520 px', 'statewide + metropolitan',
                                 'GeoPackage geometry available for 1981.'),
    ('other', 1981, 'sa', 47): ('A', 'Statewide and Adelaide sheets 3520 px', 'statewide + metropolitan',
                                'GeoPackage geometry available for 1981.'),
    ('other', 1981, 'wa', 42): ('A', 'Statewide and Perth sheets 3520 px', 'statewide + metropolitan',
                                'GeoPackage geometry available for 1981.'),
    ('other', 1981, 'tas', 31): ('A', 'Statewide, Hobart and Launceston sheets 3456 px', 'statewide + metropolitan',
                                 'GeoPackage geometry available for 1981.'),
    ('other', 1981, 'nt', 28): ('B', 'NT sheet 3520 px; published units are statistical districts', 'districts',
                                'GeoPackage geometry available for 1981.'),
    ('other', 1981, 'act', 27): ('B', 'ACT sheets 3520 px; published units are statistical districts', 'districts',
                                 'GeoPackage geometry available for 1981.'),
}

DEFAULT_BY_RESOLUTION = [(600, 'D', 'under 600 px on the short edge - too coarse to trace'),
                         (1000, 'C', 'under 1000 px on the short edge - tracing would be unreliable'),
                         (1800, 'B', 'moderate resolution; digitiable with care'),
                         (10 ** 9, 'A', 'good resolution and line work')]


def default_rating(short_edge):
    for limit, rating, basis in DEFAULT_BY_RESOLUTION:
        if short_edge < limit:
            return rating, basis
    return 'B', 'unrated'


def main():
    metrics = list(csv.DictReader((OUT / 'plate_metrics.csv').open()))
    rows = []
    for metric in metrics:
        if metric['status'] != 'ok':
            continue
        width = int(metric['native_width'] or 0)
        height = int(metric['native_height'] or 0)
        short_edge = min(width, height) if width and height else 0
        key = (metric['scope'] if metric['scope'] == 'nsw' else 'other',
               int(metric['census_year']), metric['state_code'], int(metric['page']) if metric['page'].isdigit() else 0)
        lookup = RATINGS.get(key)
        if lookup is None:
            # fall back to a state-year entry on any page of the same source
            lookup = next((value for (scope, year, state, _page), value in RATINGS.items()
                           if scope == key[0] and year == key[1] and state == key[2]), None)
        if lookup:
            rating, basis, target, better = lookup
        else:
            rating, basis = default_rating(short_edge)
            target, better = 'unrated', ''
        rows.append(dict(scope='nsw' if key[0] == 'nsw' else 'other_states',
                         census_year=key[1], state_code=key[2], source_id=metric['source_id'],
                         page=metric['page'], native_width=width, native_height=height,
                         short_edge=short_edge, contrast=metric['contrast'],
                         rating=rating, rating_basis=basis, digitisation_target=target,
                         better_candidate=better))
    rows.sort(key=lambda r: (r['scope'], r['census_year'], r['state_code'], r['source_id'], int(r['page']) if str(r['page']).isdigit() else 0))
    # The NSW plate inventory and the Sydney panel list overlap; keep one row per plate.
    deduped = {}
    for row in rows:
        deduped.setdefault((row['scope'], row['source_id'], row['page']), row)
    rows = list(deduped.values())
    fields = ['scope', 'census_year', 'state_code', 'source_id', 'page', 'native_width', 'native_height',
              'short_edge', 'contrast', 'rating', 'rating_basis', 'digitisation_target', 'better_candidate']
    with (OUT / 'digitisation_readiness.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    summary = []
    by_year = defaultdict(list)
    for row in rows:
        by_year[(int(row['census_year']), row['scope'])].append(row)
    for (year, scope) in sorted(by_year):
        group = by_year[(year, scope)]
        counts = Counter(r['rating'] for r in group)
        summary.append(dict(census_year=year, scope=scope, plates=len(group),
                            A=counts.get('A', 0), B=counts.get('B', 0), C=counts.get('C', 0),
                            D=counts.get('D', 0),
                            needs_rescue=sum(1 for r in group if r['rating'] in ('C', 'D') and r['better_candidate'])))
    with (OUT / 'summary_by_year.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)
    print(f'{len(rows)} plates rated -> {OUT/"digitisation_readiness.csv"}')
    for row in summary:
        print(row)


if __name__ == '__main__':
    main()
