# Prepare an offline historical-map pilot for 1911 NSW local government areas.
# Inputs: downloader manifest and unchanged historical maps in data/raw/.
# Outputs: frozen inventory, native PDF images, previews, review templates and
#          status in explore/output/2026-10-10_map-gis-pilot/ only.
# Optional --trial reads reviewed trial inputs in data/intermediate/map_gis_pilot/,
# fits an affine transform and exports candidate GeoTIFF/GeoPackage and QA images.
# No network calls or automatic census acceptance.
# First extraction target: LGA boundaries; ward lines are context only.
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pillow==12.3.0", "pymupdf==1.28.2", "numpy==2.5.3",
#   "rasterio==1.5.2", "pyproj==3.8.0", "fiona==1.10.1", "shapely==2.2.0"
# ]
# ///
from __future__ import annotations

import csv
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import sys
import time

from PIL import Image, ImageDraw, ImageFont
import pymupdf


OUT = Path('explore/output/2026-10-10_map-gis-pilot')
SOURCE_MANIFEST = Path('explore/output/2026-10-10_download-boundary-maps/manifest.csv')
RAW = Path('data/raw/historical_boundary_maps')
TARGET_FEATURE_TYPE = 'lga_boundary'
# Keep alternate scans/editions of a place in the same group to limit leakage.
# The statewide case tests overview handling, not the pilot's geography scope.
CASES = [
    ('nla.obj-231128914', 1, 'calibration', 'strathfield', 'Atlas baseline; compare alternate scan'),
    ('3933', 1, 'calibration', 'strathfield', 'Lower-resolution alternate scan; edition not assumed identical'),
    ('nla.obj-231129875', 1, 'calibration', 'darlington', 'Rotated map text; small urban municipality'),
    ('nla.obj-231130194', 1, 'calibration', 'canterbury', 'Sparse outer area and river boundary'),
    ('nla.obj-231130513', 1, 'calibration', 'leichhardt', 'LGA perimeter versus coastline and internal ward colours'),
    ('3914', 1, 'calibration', 'leichhardt', 'Alternate edition; distinguish LGA perimeter from internal boundaries'),
    ('strathfield_pdf', 1, 'calibration', 'strathfield', 'Negative control: circa-1810 land grants, not census LGAs'),
    ('strathfield_pdf', 4, 'calibration', 'strathfield', 'Retrospective circa-1910 figure; boundary date unverified'),
    ('nla.obj-231130030', 1, 'evaluation', 'balmain', 'Coastal LGA perimeter; ward colours are context only'),
    ('nla.obj-231105413', 1, 'evaluation', 'enfield', 'Landscape atlas sheet; distinguish LGA perimeter from coloured wards'),
    ('nla.obj-231540665', 1, 'evaluation', 'sydney_overview', 'Dense multi-municipality overview; uncertain catalogue date'),
    ('nla.obj-2869419748', 1, 'evaluation', 'nsw_overview', 'Statewide overview and insets; deliberately resolution-limited'),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    # An interrupted write must not leave a readable but incomplete checkpoint.
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def load_records(data: bytes) -> list[dict]:
    records = list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
    if not records:
        raise ValueError('Empty source manifest')
    seen = set()
    for row in records:
        record_id = row['record_id']
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', record_id) or record_id in seen:
            raise ValueError(f'Unsafe or duplicate record ID: {record_id}')
        seen.add(record_id)
        if row['status'] == 'downloaded':
            path = Path(row['local_path'])
            if path.is_absolute() or not path.resolve().is_relative_to(RAW.resolve()):
                raise ValueError(f'Source outside raw map folder: {record_id}')
            if not re.fullmatch(r'[0-9a-f]{64}', row['sha256']):
                raise ValueError(f'Missing source fingerprint: {record_id}')
    return records


def inspect_record(row: dict) -> list[dict]:
    path = Path(row['local_path'])
    data = path.read_bytes()
    if sha256(data) != row['sha256']:
        raise ValueError('Raw source hash differs from frozen download register')
    base = dict(record_id=row['record_id'], title=row['title'], kind=row['kind'],
                catalogue_date=row['date_label'], source_record=row['source_record'],
                source_path=path.as_posix(), source_sha256=row['sha256'],
                source_bytes=len(data), source_family=path.parent.name,
                boundary_date_status='unverified', census_link_status='unverified')
    pages = []
    if path.suffix.lower() == '.pdf':
        with pymupdf.open(stream=data, filetype='pdf') as pdf:
            for number, page in enumerate(pdf, 1):
                images = page.get_image_info(xrefs=True)
                text_chars = len(page.get_text().strip())
                drawings = len(page.get_drawings())
                image_objects = {item[0]: item for item in page.get_images(full=True)}
                # Extract native image bytes only if they are the sole visible
                # content. Other PDFs need page rendering and separate panel QA.
                native = (len(images) == 1 and images[0]['xref'] > 0
                          and not text_chars and not drawings
                          and not list(page.annots() or [])
                          and page.rotation == 0
                          and page.rect.contains(pymupdf.Rect(images[0]['bbox']))
                          and images[0]['xref'] in image_objects
                          and image_objects[images[0]['xref']][1] == 0)
                info = images[0] if native else {}
                pages.append(dict(base, page_number=number,
                                  map_id=f"{row['record_id']}_p{number:03d}",
                                  route='embedded_image' if native else 'render_page',
                                  width_px=info.get('width', ''), height_px=info.get('height', ''),
                                  pdf_image_count=len(images), pdf_text_chars=text_chars,
                                  pdf_drawing_count=drawings, pdf_image_xref=info.get('xref', ''),
                                  pdf_image_transform=json.dumps(info.get('transform', [])),
                                  pdf_page_rotation=page.rotation))
    else:
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            pages.append(dict(base, page_number=1, map_id=f"{row['record_id']}_p001",
                              route='source_image', width_px=image.width, height_px=image.height,
                              pdf_image_count='', pdf_text_chars='', pdf_drawing_count='',
                              pdf_image_xref='', pdf_image_transform='', pdf_page_rotation=''))
    return pages


def prepare_case(row: dict, directory: Path) -> dict:
    directory.mkdir(parents=True, exist_ok=True)
    source = Path(row['source_path'])
    if sha256(source.read_bytes()) != row['source_sha256']:
        raise ValueError(f"Source changed after inspection: {row['map_id']}")
    if row['route'] == 'source_image':
        image_path = source
    else:
        with pymupdf.open(source) as pdf:
            if row['route'] == 'embedded_image':
                extracted = pdf.extract_image(int(row['pdf_image_xref']))
                image_path = directory / ('native.' + extracted['ext'])
                image_path.write_bytes(extracted['image'])
            else:
                image_path = directory / 'page.png'
                pdf[int(row['page_number']) - 1].get_pixmap(dpi=200, alpha=False).save(image_path)
    with Image.open(image_path) as original:
        width, height = original.size
        preview = original.convert('RGB')
        preview.thumbnail((900, 1100))
        preview_path = directory / 'preview.jpg'
        preview.save(preview_path, quality=90)
    return dict(row, image_path=image_path.as_posix(), image_sha256=sha256(image_path.read_bytes()),
                width_px=width, height_px=height, preview_path=preview_path.as_posix(),
                preview_width_px=preview.width, preview_height_px=preview.height,
                # Coordinates are measured from the top-left image edge, not
                # pixel centres. Separate scales handle rounded preview sizes.
                preview_to_image_x=width / preview.width,
                preview_to_image_y=height / preview.height,
                pixel_convention='top-left edge; x right; y down; first centre at 0.5,0.5',
                preparation_status='prepared', georeferencing_status='not_started',
                geometry_status='not_started', historical_status='unverified',
                acceptance_status='not_accepted')


def fit_affine(points: list[dict], width: int, height: int):
    """Fit only designated points; report held-out and diagnostic errors separately."""
    import numpy as np

    identifiers = [p['point_id'] for p in points]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError('Duplicate control-point ID')
    for point in points:
        if point['role'] not in {'fit', 'check', 'diagnostic'}:
            raise ValueError('Unknown control-point role')
        values = np.array([point[k] for k in ['pixel_x', 'pixel_y', 'map_x', 'map_y']], dtype=float)
        if not np.isfinite(values).all():
            raise ValueError('Non-finite control coordinate')
        if not (0 <= values[0] <= width and 0 <= values[1] <= height):
            raise ValueError('Control coordinate outside native image')
    fitting = [p for p in points if p['role'] == 'fit']
    checking = [p for p in points if p['role'] == 'check']
    fit_pixels = {(p['pixel_x'], p['pixel_y']) for p in fitting}
    fit_world = {(p['map_x'], p['map_y']) for p in fitting}
    if len(fit_pixels) != len(fitting):
        raise ValueError('Repeated fitting location')
    if any((p['pixel_x'], p['pixel_y']) in fit_pixels or (p['map_x'], p['map_y']) in fit_world for p in checking):
        raise ValueError('A held-out check cannot reuse a fitting location')
    if len(fitting) < 4 or len(checking) < 2:
        raise ValueError('Pilot needs at least four fit points and two held-out checks')
    pixels = np.array([[p['pixel_x'], p['pixel_y'], 1] for p in fitting], dtype=float)
    world = np.array([[p['map_x'], p['map_y']] for p in fitting], dtype=float)
    coefficient, _, rank, _ = np.linalg.lstsq(pixels, world, rcond=None)
    if rank != 3 or np.linalg.cond(coefficient[:2]) > 1e6:
        raise ValueError('Degenerate control geometry or affine transformation')
    residuals = []
    for point in points:
        predicted = np.array([point['pixel_x'], point['pixel_y'], 1]) @ coefficient
        dx, dy = predicted - [point['map_x'], point['map_y']]
        residuals.append(dict(point, predicted_x=float(predicted[0]), predicted_y=float(predicted[1]),
                              dx_metres=float(dx), dy_metres=float(dy), error_metres=float(np.hypot(dx, dy))))
    metrics = {}
    for role in ['fit', 'check', 'diagnostic']:
        errors = np.array([p['error_metres'] for p in residuals if p['role'] == role])
        metrics[role] = dict(count=len(errors), rmse_metres=float(np.sqrt(np.mean(errors ** 2)))
                            if len(errors) else None, max_metres=float(errors.max()) if len(errors) else None)
    return coefficient, residuals, metrics


def run_trial(config_path: Path) -> int:
    import fiona
    import numpy as np
    import pyproj
    import rasterio
    from rasterio import Affine
    from shapely.geometry import MultiLineString, MultiPoint, Point, Polygon, mapping, shape

    trial_bytes = config_path.read_bytes()
    trial = json.loads(trial_bytes)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', trial['map_id']):
        raise ValueError('Unsafe map ID')
    if trial['target_feature_type'] != TARGET_FEATURE_TYPE:
        raise ValueError('This pilot exports LGA boundaries only')
    if not trial['reference_approved'] or trial['method'] != 'affine':
        raise ValueError('An approved reference and the explicit affine trial method are required')
    if trial['pixel_convention'] != 'top-left edge; x right; y down; first centre at 0.5,0.5':
        raise ValueError('Unsupported pixel coordinate convention')
    crs = pyproj.CRS.from_user_input(trial['target_crs'])
    if not crs.is_projected or any(a.unit_name != 'metre' for a in crs.axis_info[:2]):
        raise ValueError('Residuals need a projected CRS in metres')
    for path_key, hash_key in [('source_path', 'source_sha256'), ('reference_path', 'reference_sha256')]:
        path = Path(trial[path_key])
        if path.is_absolute() or not path.resolve().is_relative_to(Path.cwd().resolve()):
            raise ValueError('Trial paths must be relative and inside the repository')
        if sha256(path.read_bytes()) != trial[hash_key]:
            raise ValueError(f'Changed trial input: {path_key}')
    reference = json.loads(Path(trial['reference_path']).read_bytes())
    if reference.get('exceededTransferLimit') or reference.get('error'):
        raise ValueError('Reference response is incomplete or failed')
    reference_crs = reference['spatialReference'].get('latestWkid', reference['spatialReference']['wkid'])
    if pyproj.CRS.from_epsg(reference_crs) != crs:
        raise ValueError('Reference coordinates use a different CRS')
    reference_features = {f['attributes']['OBJECTID']: f for f in reference['features']}
    for control in trial['control_points']:
        names = set()
        for object_id in control['reference_object_ids']:
            feature = reference_features[object_id]
            lines = MultiLineString(feature['geometry']['paths'])
            if lines.distance(Point(control['map_x'], control['map_y'])) > 0.001:
                raise ValueError(f"Control does not match cited reference roads: {control['point_id']}")
            names.add(feature['attributes']['roadnamebase'])
        if len(names) < 2:
            raise ValueError('Road-intersection control needs two named reference roads')
    image = Image.open(trial['source_path']).convert('RGB')
    coefficient, residuals, metrics = fit_affine(trial['control_points'], image.width, image.height)
    transform = Affine(coefficient[0, 0], coefficient[1, 0], coefficient[2, 0],
                       coefficient[0, 1], coefficient[1, 1], coefficient[2, 1])
    pixel_rings = trial['boundary_pixel_rings']
    for ring in pixel_rings:
        if len(ring) < 4 or ring[0] != ring[-1]:
            raise ValueError('Boundary rings must already be closed; no inferred closing segment')
        coords = np.array(ring, dtype=float)
        if not np.isfinite(coords).all() or np.any(coords < 0) or np.any(coords > [image.width, image.height]):
            raise ValueError('Boundary coordinate outside native image')
    pixel_polygon = Polygon(pixel_rings[0], pixel_rings[1:])
    if not pixel_polygon.is_valid or pixel_polygon.is_empty:
        raise ValueError('Invalid source polygon; inspect it rather than silently repairing it')
    rings = [[transform * tuple(p) for p in ring] for ring in pixel_rings]
    geometry = Polygon(rings[0], rings[1:])
    if not geometry.is_valid or geometry.is_empty:
        raise ValueError('Invalid transformed polygon')
    fit_hull = MultiPoint([(p['pixel_x'], p['pixel_y']) for p in residuals if p['role'] == 'fit']).convex_hull
    outside = sum(not fit_hull.covers(Point(p)) for p in pixel_rings[0][:-1])

    directory = OUT / 'cases' / trial['map_id'] / 'georeferencing'
    directory.mkdir(parents=True, exist_ok=True)
    state = dict(state='running', unit='map_cases', total=1, completed=0, failed=0, skipped=0,
                 remaining=1, updated_utc=datetime.now(timezone.utc).isoformat(),
                 checkpoint=config_path.as_posix(), config_sha256=sha256(trial_bytes),
                 resume_command=(f'UV_CACHE_DIR={shlex.quote(os.environ["UV_CACHE_DIR"])} ' if os.environ.get('UV_CACHE_DIR') else '')
                 + f'uv run --locked --offline {shlex.quote(Path(__file__).relative_to(Path.cwd()).as_posix())} --trial {shlex.quote(config_path.as_posix())}',
                 blocker=None)
    write_json(OUT / 'trial_status.json', state)
    tif = directory / 'candidate_georeferenced.tif'
    temporary_tif = directory / 'candidate_georeferenced.tmp.tif'
    # Attach the affine mapping without resampling source pixels. Rotation/shear
    # are supported by GeoTIFF. A north-up warp can be a separate later product.
    with rasterio.open(temporary_tif, 'w', driver='GTiff', width=image.width, height=image.height,
                       count=3, dtype='uint8', crs=crs.to_wkt(), transform=transform,
                       compress='deflate', tiled=True) as destination:
        destination.write(np.moveaxis(np.asarray(image), -1, 0))
        destination.update_tags(source_sha256=trial['source_sha256'], config_sha256=sha256(trial_bytes),
                                review_status='candidate', census_link_status='not_accepted')
    temporary_tif.replace(tif)
    gpkg = directory / 'candidate_lga.gpkg'
    temporary_gpkg = directory / 'candidate_lga.tmp.gpkg'
    if temporary_gpkg.exists():
        temporary_gpkg.unlink()
    properties = dict(map_id=trial['map_id'], feature_type=TARGET_FEATURE_TYPE,
                      name_as_printed=trial['name_as_printed'], source_sha256=trial['source_sha256'],
                      config_sha256=sha256(trial_bytes), review_status='candidate_needs_source_review',
                      historical_status=trial['historical_status'], census_link_status='not_accepted')
    with fiona.open(temporary_gpkg, 'w', driver='GPKG', layer='lga_candidate', crs_wkt=crs.to_wkt(),
                    schema={'geometry': 'Polygon', 'properties': {key: 'str' for key in properties}}) as layer:
        layer.write({'geometry': mapping(geometry), 'properties': properties})
    point_schema = {'geometry': 'Point', 'properties': {'point_id': 'str', 'role': 'str',
                    'landmark': 'str', 'error_m': 'float', 'reference_ids': 'str'}}
    with fiona.open(temporary_gpkg, 'w', driver='GPKG', layer='reference_points', crs_wkt=crs.to_wkt(),
                    schema=point_schema) as layer:
        for row in residuals:
            layer.write({'geometry': mapping(Point(row['map_x'], row['map_y'])),
                         'properties': dict(point_id=row['point_id'], role=row['role'], landmark=row['landmark'],
                                            error_m=row['error_metres'], reference_ids=json.dumps(row['reference_object_ids']))})
    with fiona.open(temporary_gpkg, 'w', driver='GPKG', layer='reference_roads', crs_wkt=crs.to_wkt(),
                    schema={'geometry': 'MultiLineString', 'properties': {'object_id': 'int', 'name': 'str'}}) as layer:
        for feature in reference['features']:
            layer.write({'geometry': {'type': 'MultiLineString', 'coordinates': feature['geometry']['paths']},
                         'properties': {'object_id': feature['attributes']['OBJECTID'],
                                        'name': feature['attributes']['roadnamebase']}})
    temporary_gpkg.replace(gpkg)
    write_csv(directory / 'point_errors.csv', list(residuals[0]), residuals)

    # Two views: trace on the untouched scan, and current road reference projected
    # back into source pixels. The latter exposes distortions and changed roads.
    font = ImageFont.truetype('DejaVuSans.ttf', 38)
    views = []
    colours = {'fit': '#1166cc', 'check': '#14813b', 'diagnostic': '#b26400'}
    for roads_on in [False, True]:
        canvas = image.copy()
        pen = ImageDraw.Draw(canvas)
        if roads_on:
            inverse = ~transform
            for feature in reference['features']:
                for path in feature['geometry']['paths']:
                    pen.line([inverse * tuple(p[:2]) for p in path], fill='#0066ff', width=4)
        for ring in pixel_rings:
            pen.line([tuple(p) for p in ring], fill='#00c4a7', width=10)
        pen.line(list(fit_hull.exterior.coords), fill='#ec6f00', width=5)
        for point in residuals:
            x, y = point['pixel_x'], point['pixel_y']
            pen.ellipse((x-15, y-15, x+15, y+15), fill=colours[point['role']], outline='white', width=3)
            pen.text((x+20, y-12), point['point_id'], font=font, fill=colours[point['role']], stroke_width=2, stroke_fill='white')
        canvas.thumbnail((900, 1250))
        views.append(canvas)
    review = Image.new('RGB', (1800, 1370), 'white')
    pen = ImageDraw.Draw(review)
    small = ImageFont.truetype('DejaVuSans.ttf', 20)
    pen.text((15, 12), 'Candidate LGA trace on original scan', font=small, fill='black')
    pen.text((915, 12), 'Same scan with current NSW road reference', font=small, fill='black')
    for i, canvas in enumerate(views):
        review.paste(canvas, (i*900, 50))
    pen.text((15, 1310), 'Teal: candidate perimeter | Orange: fit-point coverage | Blue: fit | Green: check | Brown: diagnostic', font=small, fill='black')
    pen.text((15, 1340), 'Source-date candidate. Not accepted as the 1911 boundary. Geometry outside orange coverage is extrapolated.', font=small, fill='black')
    review.save(directory / 'review.jpg', quality=92)
    # Read back both GIS products rather than counting successful write calls.
    with rasterio.open(tif) as saved:
        if saved.crs != rasterio.crs.CRS.from_wkt(crs.to_wkt()) or saved.transform != transform:
            raise ValueError('GeoTIFF CRS/transform read-back mismatch')
        if not np.array_equal(saved.read(), np.moveaxis(np.asarray(image), -1, 0)):
            raise ValueError('GeoTIFF changed source pixels')
    with fiona.open(gpkg, layer='lga_candidate') as saved:
        if len(saved) != 1 or pyproj.CRS(saved.crs) != crs:
            raise ValueError('GeoPackage feature/CRS read-back mismatch')
        if not shape(next(iter(saved))['geometry']).equals_exact(geometry, 1e-8):
            raise ValueError('GeoPackage geometry read-back mismatch')
    for layer_name, expected in [('reference_points', len(residuals)), ('reference_roads', len(reference['features']))]:
        with fiona.open(gpkg, layer=layer_name) as saved:
            if len(saved) != expected or pyproj.CRS(saved.crs) != crs:
                raise ValueError(f'GeoPackage reference-layer read-back mismatch: {layer_name}')
    report = dict(map_id=trial['map_id'], target_crs=crs.to_string(), method='affine',
                  affine=list(transform)[:6], errors=metrics, boundary_vertex_count=len(pixel_rings[0])-1,
                  vertices_outside_fit_hull=outside, geometry_valid=geometry.is_valid,
                  spatial_acceptance='unassessed_no_tolerance', census_link_status='not_accepted',
                  historical_status=trial['historical_status'], accepted_features=0,
                  source_sha256=trial['source_sha256'], reference_sha256=trial['reference_sha256'],
                  config_sha256=sha256(trial_bytes), script_sha256=sha256(Path(__file__).read_bytes()),
                  boundary_notes=trial['boundary_notes'], review_limitations=trial['review_limitations'],
                  outputs={p.name: sha256(p.read_bytes()) for p in [tif, gpkg, directory/'review.jpg']},
                  runtime={'rasterio': rasterio.__version__, 'fiona': fiona.__version__,
                           'pyproj': pyproj.__version__, 'numpy': np.__version__})
    write_json(directory / 'report.json', report)
    state.update(state='candidate_ready', completed=1, remaining=0,
                 updated_utc=datetime.now(timezone.utc).isoformat(),
                 last_successful_output=(directory / 'report.json').as_posix())
    write_json(OUT / 'trial_status.json', state)
    print(json.dumps({'outputs': str(directory), 'errors': metrics,
                      'vertices_outside_fit_hull': outside, 'census_link_status': 'not_accepted'}, indent=2))
    return 0


def main() -> int:
    if not SOURCE_MANIFEST.exists():
        raise ValueError('Run from the repository root; source manifest is required')
    OUT.mkdir(parents=True, exist_ok=True)
    frozen = OUT / 'source_manifest.csv'
    # Snapshot once. Growing downloads must not silently change a pilot cohort.
    if not frozen.exists():
        content = SOURCE_MANIFEST.read_bytes()
        load_records(content)
        with frozen.open('xb') as stream:
            stream.write(content)
    snapshot = frozen.read_bytes()
    records = load_records(snapshot)
    started = time.monotonic()
    status = dict(state='running', unit='source_files', total=len(records), completed=0,
                  failed=0, skipped=0, remaining=len(records), last_successful_output=None,
                  checkpoint=(OUT / 'inventory.csv').as_posix(),
                  resume_command=f'python3 {Path(__file__).relative_to(Path.cwd()).as_posix()}',
                  source_manifest_sha256=sha256(snapshot), blocker=None)

    def checkpoint() -> None:
        elapsed = time.monotonic() - started
        processed = status['completed'] + status['failed'] + status['skipped']
        status.update(updated_utc=datetime.now(timezone.utc).isoformat(),
                      remaining=len(records) - processed,
                      recent_rate_files_per_second=processed / max(elapsed, .001),
                      rate_basis='run_average',
                      conditional_eta_seconds=(len(records) - processed) * elapsed / processed
                      if processed else None)
        write_json(OUT / 'status.json', status)

    inventory, issues = [], []
    checkpoint()
    for record in records:
        if record['status'] != 'downloaded':
            status['skipped'] += 1
            issues.append(dict(record_id=record['record_id'], error='Source not downloaded in snapshot'))
        else:
            try:
                inventory.extend(inspect_record(record))
                status['completed'] += 1
                if inventory:
                    write_csv(OUT / 'inventory.csv', list(inventory[0]), inventory)
                    status['last_successful_output'] = (OUT / 'inventory.csv').as_posix()
            except Exception as error:
                status['failed'] += 1
                issues.append(dict(record_id=record['record_id'], error=f'{type(error).__name__}: {error}'))
        checkpoint()
    write_csv(OUT / 'source_issues.csv', ['record_id', 'error'], issues)
    if status['failed']:
        status.update(state='failed', blocker='Source integrity/readability failures; see source_issues.csv')
        checkpoint()
        return 1

    lookup = {(r['record_id'], r['page_number']): r for r in inventory}
    pilot = []
    for record_id, number, role, group, reason in CASES:
        if (record_id, number) not in lookup:
            status.update(state='blocked', blocker=f'Missing pilot case: {record_id}, page {number}')
            checkpoint()
            return 1
        row = dict(lookup[(record_id, number)], pilot_role=role, comparison_group=group,
                   selection_reason=reason, target_feature_type=TARGET_FEATURE_TYPE)
        pilot.append(prepare_case(row, OUT / 'cases' / row['map_id']))
    write_csv(OUT / 'pilot.csv', list(pilot[0]), pilot)

    templates = OUT / 'templates'
    templates.mkdir(exist_ok=True)
    write_csv(templates / 'map_review.csv', [
        'map_id', 'source_sha256', 'image_sha256', 'target_feature_type', 'feature_type', 'printed_title',
        'printed_date', 'boundary_valid_from', 'boundary_valid_to', 'date_evidence',
        'panel_left_px', 'panel_top_px', 'panel_right_px', 'panel_bottom_px',
        'legend_evidence', 'reference_dataset', 'reference_version', 'target_crs',
        'positional_tolerance_metres', 'boundary_tolerance_metres',
        'reviewer', 'reviewed_utc', 'decision', 'notes'],
        [dict(map_id=r['map_id'], source_sha256=r['source_sha256'], image_sha256=r['image_sha256'],
              target_feature_type=TARGET_FEATURE_TYPE, decision='needs_review') for r in pilot])
    write_csv(templates / 'control_points.csv', [
        'map_id', 'image_sha256', 'point_id', 'pixel_x', 'pixel_y', 'map_x', 'map_y',
        'target_crs', 'role', 'landmark', 'reference_source', 'reference_version',
        'reference_feature_id', 'review_status', 'reviewer'], [])
    write_csv(templates / 'feature_review.csv', [
        'map_id', 'feature_id', 'source_sha256', 'image_sha256', 'area_version_id',
        'name_as_printed', 'feature_type', 'geometry_file', 'geometry_layer',
        'date_evidence', 'obscured_segments', 'review_minutes', 'decision', 'reviewer'], [])
    write_csv(templates / 'census_links.csv', [
        'census_year', 'census_source_row_id', 'name_as_printed', 'area_version_id',
        'match_method', 'date_evidence', 'decision', 'reviewer'], [])
    write_json(OUT / 'source_regions.json', {'target': '1911 NSW local government areas',
               'target_feature_type': TARGET_FEATURE_TYPE, 'ward_boundaries': 'context_only_deferred',
               'source_manifest_sha256': sha256(snapshot), 'cases': pilot})
    font = ImageFont.truetype('DejaVuSans.ttf', 17)
    sheet = Image.new('RGB', (1800, 2280), 'white')
    pen = ImageDraw.Draw(sheet)
    for i, row in enumerate(pilot):
        x, y = (i % 4) * 450, (i // 4) * 760
        with Image.open(row['preview_path']) as preview:
            preview.thumbnail((430, 660))
            sheet.paste(preview, (x + 10, y + 75))
        pen.text((x + 10, y + 8), row['map_id'], font=font, fill='black')
        pen.text((x + 10, y + 31), row['pilot_role'] + ' | ' + row['comparison_group'], font=font, fill='black')
        pen.text((x + 10, y + 54), f"{row['width_px']} x {row['height_px']} px", font=font, fill='black')
    sheet.save(OUT / 'contact_sheet.jpg', quality=92)
    fingerprint = dict(source_manifest_sha256=sha256(snapshot),
                       script_sha256=sha256(Path(__file__).read_bytes()),
                       python=sys.version.split()[0], pillow=Image.__version__,
                       pymupdf=pymupdf.__version__, target='1911 NSW local government areas',
                       target_feature_type=TARGET_FEATURE_TYPE,
                       source_files=len(records), source_pages=len(inventory),
                       pilot_cases=len(pilot),
                       calibration_cases=sum(r['pilot_role'] == 'calibration' for r in pilot),
                       evaluation_cases=sum(r['pilot_role'] == 'evaluation' for r in pilot),
                       georeferenced_cases=0, accepted_features=0,
                       note='Preparation only; evaluation scenes inspected for selection, no method tuned on them')
    write_json(OUT / 'source_fingerprints.json', fingerprint)
    status.update(state='prepared', last_successful_output=(OUT / 'source_regions.json').as_posix(),
                  next_stage='Review map panels, feature definitions, dates and reference data; collect control points')
    checkpoint()
    print(json.dumps(fingerprint, indent=2))
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trial', type=Path, help='Export a candidate GIS case from explicit trial inputs')
    arguments = parser.parse_args()
    try:
        code = run_trial(arguments.trial) if arguments.trial else main()
    except Exception as error:
        checkpoint_path = OUT / ('trial_status.json' if arguments.trial else 'status.json')
        if checkpoint_path.exists():
            status = json.loads(checkpoint_path.read_text())
            status.update(state='failed', updated_utc=datetime.now(timezone.utc).isoformat(),
                          blocker=f'{type(error).__name__}: {error}')
            write_json(checkpoint_path, status)
        raise
    raise SystemExit(code)
