# Download historical municipal-boundary map scans for later digitising.
# Inputs: Dictionary atlas, Strathfield/ANU PDFs, NLA records and reviewed download
#         plan in explore/output/2026-10-10_download-boundary-maps/additional_sources.csv.
# Outputs: immutable downloads in data/raw/historical_boundary_maps/;
#          manifest and resumable status in this script's explore/output/ folder.
import csv
from datetime import datetime, timezone
import hashlib
import html
import io
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import urljoin

from PIL import Image
import pymupdf
import requests

RAW = Path('data/raw/historical_boundary_maps')
OUT = Path('explore/output/2026-10-10_download-boundary-maps')
CATALOGUE = 'https://dictionaryofsydney.org/entry/atlas_of_the_suburbs_of_sydney'
PDF_URL = 'https://strathfieldheritage.com/wp-content/uploads/2010/04/historic-maps-of-strathfield-lga.pdf'
FIELDS = ['record_id', 'title', 'date_label', 'kind', 'source_record', 'download_url',
          'local_path', 'bytes', 'sha256', 'width_px', 'height_px', 'pdf_pages',
          'downloaded_utc', 'status', 'error']
RAW.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
rows = {}
manifest = OUT / 'manifest.csv'
if manifest.exists():
    with manifest.open(newline='', encoding='utf-8') as f:
        rows = {r['record_id']: r for r in csv.DictReader(f)}
session = requests.Session()
session.headers['User-Agent'] = 'HistoricalBoundaryMapResearch/1.0'
response = session.get(CATALOGUE, timeout=45)
response.raise_for_status()
ids = list(dict.fromkeys(re.findall(r'href="/(?:index.php/)?media/(\d+)"', response.text)))
# The article's link to a painting is context, not part of the map series.
ids = [i for i in ids if i != '1421']
jobs = [(i, f'https://dictionaryofsydney.org/media/{i}') for i in ids] + [('strathfield_pdf', PDF_URL)]
NLA_ATLAS = 'https://nla.gov.au/nla.obj-231127940'
browse = session.get(NLA_ATLAS + '/browse?startIdx=0&rows=100&op=s', timeout=45)
browse.raise_for_status()
nla_ids = list(dict.fromkeys(re.findall(r'href="/(nla\.obj-\d+)"', browse.text)))
if len(nla_ids) != 34:
    raise ValueError(f'NLA atlas inventory changed: expected 34 sheets, found {len(nla_ids)}')
jobs += [(i, 'https://nla.gov.au/' + i) for i in nla_ids]
# Catalogue notes explicitly identify municipal boundaries in these overview maps.
extra_nla_ids = ['nla.obj-231540665', 'nla.obj-231444908',
                 'nla.obj-2869419748', 'nla.obj-2869419619']
jobs += [(i, 'https://nla.gov.au/' + i) for i in extra_nla_ids]
additional = {}
source_plan = OUT / 'additional_sources.csv'
if source_plan.exists():
    with source_plan.open(newline='', encoding='utf-8') as f:
        additional = {r['record_id']: r for r in csv.DictReader(f)}
    jobs += [(i, r['source_record']) for i, r in additional.items()
             if i not in {j[0] for j in jobs}]
started = time.monotonic()
skipped = 0
new_successes = 0
last_successful_output = ''
browser_context = None
browser_ws = None
for index, (record_id, record_url) in enumerate(jobs, 1):
    row = rows.get(record_id, {})
    if row.get('status') == 'downloaded' and Path(row['local_path']).exists():
        if hashlib.sha256(Path(row['local_path']).read_bytes()).hexdigest() != row['sha256']:
            raise ValueError(f'Existing raw map changed: {row["local_path"]}')
        skipped += 1
        if record_id in additional:
            row.update(date_label=additional[record_id]['date_label'], kind=additional[record_id]['kind'])
    else:
        row = dict.fromkeys(FIELDS, '')
        row.update(record_id=record_id, source_record=record_url)
        try:
            if record_id.startswith('nla.obj-'):
                page = session.get(record_url, timeout=45)
                page.raise_for_status()
                match = re.search(r'var work = JSON.parse\(JSON.stringify\((.*?)\)\);', page.text)
                work = json.loads(match[1])
                if work['accessConditions'] != 'Unrestricted':
                    raise ValueError('NLA scan is not unrestricted')
                title = work['title']
                row['date_label'] = work.get('startDate', '')
                # The normalised start date can hide uncertain decades. Retain
                # the catalogue's publication date, including brackets and ?.
                publication_dates = []
                for catalogue_record in work.get('marcData', {}).get('record', []):
                    for field in catalogue_record.get('datafield', []):
                        if str(field['tag']) not in ['260', '264']:
                            continue
                        subfields = field.get('subfield', [])
                        if isinstance(subfields, dict):
                            subfields = [subfields]
                        publication_dates += [str(s['content']) for s in subfields if s['code'] == 'c']
                if publication_dates:
                    row['date_label'] = 'Publication: ' + '; '.join(dict.fromkeys(publication_dates))
                if record_id in additional:
                    row['date_label'] = additional[record_id]['date_label']
                nonmaps = {'nla.obj-231127954': 'atlas_cover',
                           'nla.obj-231128110': 'atlas_title_page',
                           'nla.obj-231128273': 'atlas_statistics_page',
                           'nla.obj-231133238': 'atlas_cover',
                           'nla.obj-2869419619': 'map_index_statistics_page'}
                row['kind'] = nonmaps.get(record_id, 'municipal_boundary_map')
                if record_id in additional:
                    row['kind'] = additional[record_id]['kind']
                download_url = record_url + '/image'
                suffix = '.jpg'
                (OUT / 'nla_metadata').mkdir(exist_ok=True)
                (OUT / 'nla_metadata' / f'{record_id}.json').write_text(json.dumps(work, indent=2)+'\n')
            elif record_id in additional:
                planned = additional[record_id]
                title = planned['title']
                row.update(date_label=planned['date_label'], kind=planned['kind'])
                download_url = planned['download_url']
                suffix = planned.get('file_type') or '.jpg'
            elif record_id == 'strathfield_pdf':
                title = 'Historic maps of Strathfield LGA'
                download_url = PDF_URL
                row['kind'] = 'historical_map_compilation'
                row['date_label'] = 'Multiple map dates; see PDF pages'
                suffix = '.pdf'
            else:
                page = session.get(record_url, timeout=45)
                page.raise_for_status()
                title = html.unescape(re.sub('<[^>]+>', '', re.search(r'<h1[^>]*>(.*?)</h1>', page.text, re.S)[1])).strip()
                # Related-place thumbnails use typeof="Image"; the main scan
                # is the catalogue's foaf:Image, independent of thumbnail order.
                candidates = re.findall(r'<img[^>]+src="([^"]*?/sites/default/files/media/[^"]+)"[^>]+typeof="foaf:Image"', page.text)
                if len(candidates) != 1:
                    raise ValueError(f'Expected one catalogue scan, found {len(candidates)}')
                download_url = urljoin(record_url, html.unescape(candidates[0]))
                suffix = Path(download_url).suffix
                row['date_label'] = '; '.join(re.findall(r'\b(?:18|19|20)\d{2}(?:\s*[-–]\s*(?:18|19|20)\d{2})?\b', title))
                row['kind'] = 'atlas_cover' if 'cover' in title.lower() else 'municipal_boundary_map'
            slug = re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')
            source_folder = ('nla_overview_maps' if record_id in extra_nla_ids else 'nla_atlas') if record_id.startswith('nla.obj-') else ('strathfield' if suffix == '.pdf' else 'dictionary_of_sydney')
            if record_id in additional:
                source_folder = additional[record_id]['folder']
            target = RAW / source_folder / f'{record_id}_{slug}{suffix}'
            row.update(title=title, download_url=download_url, local_path=target.as_posix())
            if additional.get(record_id, {}).get('download_transport') == 'browser':
                # The library offers originals through its public catalogue browser.
                # Only load this optional dependency when a new browser download is needed.
                if browser_ws is None:
                    module_path = os.environ.get('SHUCK_MODULE_PATH', '')
                    if not module_path or not Path(module_path).is_file():
                        raise ValueError('Set SHUCK_MODULE_PATH to the shuck program for browser downloads')
                    loader = importlib.machinery.SourceFileLoader('shuck', module_path)
                    spec = importlib.util.spec_from_loader(loader.name, loader)
                    shuck = importlib.util.module_from_spec(spec)
                    loader.exec_module(shuck)
                    browser_context = shuck.session(record_url, expand=False, wait=6)
                    browser_ws, _ = browser_context.__enter__()
                data, content_type, _ = shuck.fetch_bytes(browser_ws, download_url)
                if data is None:
                    raise ValueError(f'Public browser download failed: {content_type}')
            else:
                file_response = session.get(download_url, timeout=90)
                file_response.raise_for_status()
                data = file_response.content
            if suffix == '.pdf':
                with pymupdf.open(stream=data, filetype='pdf') as pdf:
                    row['pdf_pages'] = len(pdf)
            elif suffix == '.geojson':
                # Keep the source export intact; this is already digitised geometry.
                collection = json.loads(data)
                if collection.get('type') != 'FeatureCollection' or not collection.get('features'):
                    raise ValueError('Expected a nonempty GeoJSON FeatureCollection')
                if collection.get('exceededTransferLimit'):
                    raise ValueError('Source export is truncated')
                for feature in collection['features']:
                    geometry = feature.get('geometry') or {}
                    if geometry.get('type') not in ('Polygon', 'MultiPolygon') or not geometry.get('coordinates'):
                        raise ValueError('Expected council boundary polygon geometry')
                    if not {'StartDate', 'EndDate', 'CouncilName'} <= feature.get('properties', {}).keys():
                        raise ValueError('Boundary export lacks date or council fields')
            else:
                with Image.open(io.BytesIO(data)) as image:
                    image.load()
                    row.update(width_px=image.width, height_px=image.height)
            target.parent.mkdir(parents=True, exist_ok=True)
            # Raw downloads are never overwritten, including after a source changes.
            if target.exists():
                if target.read_bytes() != data:
                    raise ValueError('Source differs from existing raw file; preserve both versions explicitly')
            else:
                temporary = target.with_suffix(target.suffix + '.part')
                temporary.write_bytes(data)
                temporary.rename(target)
            row.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                       downloaded_utc=datetime.now(timezone.utc).isoformat(), status='downloaded')
            new_successes += 1
        except Exception as error:
            row.update(status='failed', error=f'{type(error).__name__}: {str(error)[:220]}')
        rows[record_id] = row
    with manifest.with_suffix('.csv.tmp').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows.values())
    manifest.with_suffix('.csv.tmp').replace(manifest)
    done = sum(r['status'] == 'downloaded' for r in rows.values())
    failed = sum(r['status'] == 'failed' for r in rows.values())
    if row['status'] == 'downloaded':
        last_successful_output = row['local_path']
    elapsed = time.monotonic() - started
    rate = new_successes / elapsed if elapsed else None
    remaining = len(jobs) - done - failed
    status = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),
                  state='running' if index < len(jobs) else ('finished_with_failures' if failed else 'finished'),
                  completed_records=done, total_records=len(jobs), failed_records=failed,
                  skipped_existing_records=skipped, remaining_records=remaining,
                  last_successful_output=last_successful_output,
                  new_downloads_per_second=round(rate, 3) if rate else None,
                  conditional_eta_seconds=round(remaining / rate) if rate else None,
                  elapsed_seconds=round(elapsed, 1), checkpoint=manifest.as_posix(),
                  resume_command='python3 explore/2026-10-10_download-boundary-maps.py')
    (OUT / 'status.json').write_text(json.dumps(status, indent=2)+'\n')
    print(f'{index}/{len(jobs)} {record_id} {row["status"]} {row["title"]}', flush=True)
    time.sleep(0.2)
if browser_context is not None:
    browser_context.__exit__(None, None, None)
