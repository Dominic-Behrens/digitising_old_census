"""Source-backed regressions for Table 68 scalar and section-scope errors."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import export_abs_1911_dwellings_workbook as export
from dwellings_council_panels import assemble_council_panels


def source_row(page, y, label):
    return {"page": page, "y": y, "row_id": f"p{page}-{y}", "label": label,
            "resolved": "", "cells": {1: {"label": "", "value": ".."}}}


class CouncilAuditTests(unittest.TestCase):
    def test_burra_correction_is_scoped_to_the_printed_section(self):
        # Both source rows are on physical p194 and have the same name, but
        # the corporation prints 4.46 and the district council prints 4.47.
        rows = [source_row(194, 210.69, "Burra"), source_row(194, 700.51, "Burra")]
        headers, body = assemble_council_panels(rows, export.table_fields(68), {}, {})
        observed = [dict(zip(headers, row)) for row in body]
        self.assertEqual([(row["area_type"], row["area_unit"], row["population_per_occupied_dwelling"])
                          for row in observed],
                         [("Corporations", "Acres", "4.46"),
                          ("District Councils", "Square miles", "4.47")])
        self.assertEqual([row["population_persons"] for row in observed], ["1,751", "420"])

    def test_visible_scalars_recover_areas_and_population_counts(self):
        cases = [
            (184, 756.72, "Orange, East", "area", "685", "Acres"),
            (187, 436.44, "Terania", "area", "347", "Square miles"),
            (198, 775.64, "Nullagine", "area", "93,438", "Square miles"),
            (199, 428.95, "York", "population_females", "491", "Square miles"),
        ]
        for page, y, label, field, expected, unit in cases:
            with self.subTest(council=label):
                headers, body = assemble_council_panels(
                    [source_row(page, y, label)], export.table_fields(68), {}, {})
                observed = dict(zip(headers, body[0]))
                self.assertEqual(observed[field], expected)
                self.assertEqual(observed["area_unit"], unit)

    def test_damaged_dublin_density_stays_unreadable(self):
        # Physical p195: the last printed digit is damaged. 769 / 142.58 is
        # not source evidence for substituting a guessed 9 in the density.
        headers, body = assemble_council_panels(
            [source_row(195, 218.24, "Dublin")], export.table_fields(68), {}, {})
        observed = dict(zip(headers, body[0]))
        self.assertEqual(observed["population_per_area_unit"], "5.3)")
        self.assertEqual(observed["population_persons"], "769")
        self.assertEqual(observed["occupied_dwellings"], "153")

    def test_tinaroo_printed_comma_is_not_replaced_by_a_ratio(self):
        headers, body = assemble_council_panels(
            [source_row(193, 553.09, "Tinaroo")], export.table_fields(68), {}, {})
        observed = dict(zip(headers, body[0]))
        self.assertEqual(observed["occupied_dwellings_per_area_unit"], "3,279")
        self.assertEqual(observed["area"], "272")
        self.assertEqual(observed["occupied_dwellings"], "892")


if __name__ == "__main__":
    unittest.main()
