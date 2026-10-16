"""Offline map preparation tests: source integrity, PDF routes and coordinates."""
import contextlib
import csv
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
import pymupdf

SPEC = importlib.util.spec_from_file_location('map_pilot', 'explore/2026-10-10_map-gis-pilot.py')
PILOT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PILOT)


class MapPilotTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.image = self.root / 'source.png'
        Image.new('RGB', (1237, 987), '#a34567').save(self.image)

    def record(self, path=None):
        path = path or self.image
        return dict(record_id='test', title='Test map', kind='municipal_boundary_map',
                    date_label='circa 1910', source_record='catalogue:test',
                    local_path=str(path), sha256=PILOT.sha256(path.read_bytes()), status='downloaded')

    def test_changed_raw_file_is_rejected(self):
        record = self.record()
        self.image.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'hash differs'):
            PILOT.inspect_record(record)

    def test_preview_coordinates_preserve_native_pixels(self):
        row = PILOT.inspect_record(self.record())[0]
        prepared = PILOT.prepare_case(row, self.root / 'case')
        self.assertEqual(prepared['image_sha256'], row['source_sha256'])
        self.assertEqual(prepared['image_path'], str(self.image))
        self.assertAlmostEqual(prepared['preview_width_px'] * prepared['preview_to_image_x'], 1237)
        self.assertAlmostEqual(prepared['preview_height_px'] * prepared['preview_to_image_y'], 987)
        self.assertEqual(prepared['acceptance_status'], 'not_accepted')

    def test_native_pdf_image_is_extracted_without_upscaling(self):
        path = self.root / 'scan.pdf'
        with pymupdf.open() as pdf:
            for _ in range(2):
                page = pdf.new_page()
                page.insert_image(page.rect, filename=str(self.image))
            pdf.save(path)
        rows = PILOT.inspect_record(self.record(path))
        self.assertEqual([r['page_number'] for r in rows], [1, 2])
        self.assertEqual(rows[0]['route'], 'embedded_image')
        prepared = PILOT.prepare_case(rows[0], self.root / 'case')
        with Image.open(prepared['image_path']) as image, Image.open(self.image) as source:
            self.assertEqual(image.size, source.size)
            self.assertEqual(image.convert('RGB').tobytes(), source.convert('RGB').tobytes())

    def test_mixed_pdf_page_keeps_vector_and_text_content(self):
        path = self.root / 'mixed.pdf'
        with pymupdf.open() as pdf:
            page = pdf.new_page()
            page.insert_image(page.rect, filename=str(self.image))
            page.insert_text((50, 50), 'Boundary legend')
            page.draw_line((20, 20), (200, 200))
            pdf.save(path)
        row = PILOT.inspect_record(self.record(path))[0]
        self.assertEqual(row['route'], 'render_page')
        self.assertGreater(row['pdf_text_chars'], 0)
        self.assertGreater(row['pdf_drawing_count'], 0)
        prepared = PILOT.prepare_case(row, self.root / 'case')
        self.assertTrue(Path(prepared['image_path']).exists())

    def test_annotations_prevent_native_only_route(self):
        path = self.root / 'annotation.pdf'
        with pymupdf.open() as pdf:
            page = pdf.new_page()
            page.insert_image(page.rect, filename=str(self.image))
            page.add_text_annot((50, 50), 'Boundary correction')
            pdf.save(path)
        self.assertEqual(PILOT.inspect_record(self.record(path))[0]['route'], 'render_page')

    def test_cropped_pdf_preserves_visible_extent(self):
        path = self.root / 'cropped.pdf'
        with pymupdf.open() as pdf:
            page = pdf.new_page()
            page.insert_image(page.rect, filename=str(self.image))
            page.set_cropbox(pymupdf.Rect(100, 100, 300, 400))
            pdf.save(path)
        self.assertEqual(PILOT.inspect_record(self.record(path))[0]['route'], 'render_page')

    def test_change_between_inventory_and_preparation_is_rejected(self):
        row = PILOT.inspect_record(self.record())[0]
        Image.new('RGB', (1237, 987), 'white').save(self.image)
        with self.assertRaisesRegex(ValueError, 'changed after inspection'):
            PILOT.prepare_case(row, self.root / 'case')

    def test_manifest_rejects_duplicate_ids_and_paths_outside_raw(self):
        row = self.record()
        row['status'] = 'failed'
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(row))
        writer.writeheader()
        writer.writerows([row, row])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            PILOT.load_records(buffer.getvalue().encode())
        row['status'] = 'downloaded'
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
        with self.assertRaisesRegex(ValueError, 'outside raw'):
            PILOT.load_records(buffer.getvalue().encode())

    def test_frozen_inventory_does_not_follow_live_downloads(self):
        # Change cwd so the same relative-source policy applies to this fixture.
        import os
        old_cwd = Path.cwd()
        self.addCleanup(os.chdir, old_cwd)
        os.chdir(self.root)
        raw = Path('raw')
        raw.mkdir()
        path = raw / 'map.png'
        path.write_bytes(self.image.read_bytes())
        record = self.record(path)
        manifest = Path('downloads.csv')
        PILOT.write_csv(manifest, list(record), [record])
        out = Path('pilot')
        with patch.multiple(PILOT, OUT=out, RAW=raw, SOURCE_MANIFEST=manifest,
                            __file__=str(self.root / 'pilot.py'),
                            CASES=[('test', 1, 'calibration', 'test', 'fixture')]):
            Path('pilot.py').write_text('# fixture')
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(PILOT.main(), 0)
                baseline = (out / 'pilot.csv').read_bytes()
                manifest.write_text('broken live manifest')
                self.assertEqual(PILOT.main(), 0)
            self.assertEqual(baseline, (out / 'pilot.csv').read_bytes())


class AffineTrialTests(unittest.TestCase):
    def setUp(self):
        self.points = [dict(point_id=str(i), role=role, pixel_x=x, pixel_y=y,
                            map_x=321000 + 2*x + .2*y, map_y=6252000 + .1*x - 3*y)
                       for i, (x, y, role) in enumerate([
                           (10, 10, 'fit'), (90, 10, 'fit'), (90, 90, 'fit'), (10, 90, 'fit'),
                           (30, 30, 'check'), (70, 70, 'check')])]

    def test_known_rotated_transform_and_edge_coordinates(self):
        import numpy as np
        coefficient, _, metrics = PILOT.fit_affine(self.points, 100, 100)
        np.testing.assert_allclose(np.array([0, 0, 1]) @ coefficient, [321000, 6252000])
        np.testing.assert_allclose(np.array([.5, .5, 1]) @ coefficient, [321001.1, 6251998.55])
        self.assertLess(metrics['check']['max_metres'], 1e-6)

    def test_held_out_errors_do_not_change_fit(self):
        import numpy as np
        baseline, _, _ = PILOT.fit_affine(self.points, 100, 100)
        self.points[4]['map_x'] += 30
        self.points[5]['map_y'] += 40
        coefficient, _, metrics = PILOT.fit_affine(self.points, 100, 100)
        np.testing.assert_array_equal(coefficient, baseline)
        self.assertAlmostEqual(metrics['check']['rmse_metres'], (1250)**.5, places=5)
        self.assertAlmostEqual(metrics['check']['max_metres'], 40, places=5)

    def test_diagnostic_point_cannot_improve_check_score(self):
        self.points.append(dict(self.points[0], point_id='diagnostic', role='diagnostic', map_x=999999))
        _, _, metrics = PILOT.fit_affine(self.points, 100, 100)
        self.assertLess(metrics['check']['max_metres'], 1e-6)
        self.assertGreater(metrics['diagnostic']['max_metres'], 100000)

    def test_collinear_fitting_points_are_rejected(self):
        for i, point in enumerate(self.points[:4]):
            point['pixel_x'] = 10 + 15*i
            point['pixel_y'] = point['pixel_x']
        with self.assertRaisesRegex(ValueError, 'Degenerate'):
            PILOT.fit_affine(self.points, 100, 100)

    def test_check_cannot_reuse_fitting_location(self):
        self.points[4].update(map_x=self.points[0]['map_x'], map_y=self.points[0]['map_y'])
        with self.assertRaisesRegex(ValueError, 'reuse a fitting location'):
            PILOT.fit_affine(self.points, 100, 100)

    def test_outside_image_and_nonfinite_controls_are_rejected(self):
        self.points[0]['pixel_x'] = 101
        with self.assertRaisesRegex(ValueError, 'outside'):
            PILOT.fit_affine(self.points, 100, 100)
        self.points[0]['pixel_x'] = float('nan')
        with self.assertRaisesRegex(ValueError, 'Non-finite'):
            PILOT.fit_affine(self.points, 100, 100)


if __name__ == '__main__':
    unittest.main()
