"""Numeric Excel cells and source-preserving arithmetic checks."""
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import export_abs_1911_dwellings_workbook as export
from dwellings_numeric import numeric_value
from dwellings_count_checks import build_count_checks
from dwellings_measure_checks import build_measure_checks, build_fixed_room_checks


class DwellingsCheckTests(unittest.TestCase):
    def test_numeric_conversion_keeps_zero_precision_and_annotations(self):
        self.assertEqual(numeric_value("317,462"), 317462)
        self.assertEqual(numeric_value("4 410"), 4410)
        self.assertEqual(numeric_value(".095"), .095)
        self.assertEqual(numeric_value("*54"), 54)
        self.assertEqual(numeric_value("23†"), 23)
        self.assertEqual(numeric_value("0"), 0)
        for value in ("6 7", "5.3)", "26J", "£5", "/"):
            self.assertEqual(numeric_value(value), value)
        for value in ("", "..", "—", "“"):
            self.assertIsNone(numeric_value(value))

    def test_row_total_distinguishes_difference_missing_and_printed_absence(self):
        headers = ["state", "occupied", "unoccupied", "being_built", "total"]
        rows = [["NSW", "7", "..", "3", "10"],
                ["NSW", "7", "0", "3", "11"],
                ["NSW", "7", "", "3", "10"]]
        checks = build_count_checks(1, headers, rows, 1)["check_occupancy_total_delta"]
        self.assertEqual(checks[0][1], 0)
        self.assertEqual(checks[1][1], 1)
        self.assertEqual(checks[2][1], "INCOMPLETE")

    def test_campbell_town_is_not_excluded_as_a_camp(self):
        headers = ["state", "area_type", "area", "stone_private", "stone_other",
                   "total_private", "total_other", "other_camps_without_dwellings"]
        rows = [["Tasmania", "Municipality", "Campbell Town", "2", "..", "2", "..", ".."],
                ["Tasmania", "Municipality", "Total", "2", "..", "2", "..", ".."]]
        checks = build_count_checks(65, headers, rows, 3)
        self.assertEqual(checks["check_section_total_private_delta"][1][1], 0)

    def test_private_other_sum_requires_matching_material(self):
        headers = ["wall_material", "dwelling_class", "rooms_1", "rooms_total"]
        rows = [["Stone", "Private Dwellings", "2", "2"],
                ["Stone", "Dwellings Other Than Private", "3", "3"],
                ["Stone", "All Dwellings", "5", "5"]]
        key = "check_private_other_rooms_1_delta"
        self.assertEqual(build_count_checks(12, headers, rows, 2)[key][2][1], 0)
        rows[2][2] = "6"
        self.assertEqual(build_count_checks(12, headers, rows, 2)[key][2][1], 1)
        rows[1][0] = "Brick"
        self.assertEqual(build_count_checks(12, headers, rows, 2)[key][2][1], "INCOMPLETE")

    def test_density_checks_use_printed_precision(self):
        dims, fields, _ = export.table_fields(68)
        headers = dims + fields
        row = ["New South Wales", "Municipalities", "Aberdeen", "Acres",
               "1,491", "379", "355", "734", ".49", "142", ".095", "5.17"]
        key = "Check: persons / occupied (definition)"
        self.assertEqual(build_measure_checks(68, headers, [row], 4)[key][0][1], "PASS")
        row[-1] = "5.18"
        self.assertEqual(build_measure_checks(68, headers, [row], 4)[key][0][1], "FAIL")
        row[-1] = "5.3)"
        self.assertEqual(build_measure_checks(68, headers, [row], 4)[key][0][1], "INCOMPLETE")

    def test_currency_boundary_and_missing_unit(self):
        headers = ["state", "area_type", "area", "total_shillings", "total_pence"]
        key = "Check: total currency units"
        for shillings, pence, expected in (("18", "11", "PASS"), ("18", "12", "FAIL"),
                                           ("9", "0", "PASS"), ("9", "", "INCOMPLETE"),
                                           ("..", "", "N/A"), ("", "", "INCOMPLETE")):
            rows = [["NSW", "County", "Argyle", shillings, pence]]
            self.assertEqual(build_measure_checks(66, headers, rows, 3)[key][0][1], expected)

    def test_fixed_room_average_rounding_and_open_bin_exclusion(self):
        headers = ["number_of_rooms", "nsw"]
        source = {"headers": headers, "rows": [["7", "5.880"], ["12", "7.912"], ["16 and over", "9.000"]]}
        rows = [["7", ".840"], ["12", ".658"], ["16 and over", ".001"], ["Total", ".001"]]
        checks = build_fixed_room_checks(60, headers, rows, source)
        outcomes = [entry[1] for entry in checks["Check: Table 59 / fixed rooms nsw"].values()]
        self.assertEqual(outcomes, ["PASS", "FAIL", "N/A", "N/A"])

    def test_currency_cross_check_uses_penny_not_shilling_precision(self):
        headers = ["number_of_rooms", "nsw_shillings", "nsw_pence"]
        source = {"headers": headers, "rows": [["14", "33", "3"], ["2", "1", "11"]]}
        rows = [["14", "2", "9"], ["2", "1", "0"]]
        checks = build_fixed_room_checks(62, headers, rows, source)
        outcomes = [entry[1] for entry in checks["Check: Table 61 / fixed rooms nsw_shillings"].values()]
        self.assertEqual(outcomes, ["FAIL", "PASS"])

    def test_fixed_room_missing_duplicate_and_absent_counterparts(self):
        headers = ["number_of_rooms", "nsw"]
        source = {"headers": headers, "rows": [["1", ".."], ["2", "1.000"], ["2", "2.000"]]}
        rows = [["1", ".."], ["2", "1.000"], ["3", "1.000"]]
        checks = build_fixed_room_checks(60, headers, rows, source)
        outcomes = [entry[1] for entry in checks["Check: Table 59 / fixed rooms nsw"].values()]
        self.assertEqual(outcomes, ["N/A", "INCOMPLETE", "INCOMPLETE"])

    def test_shipping_has_no_occupied_dwelling_sum(self):
        headers = ["area", "private_dwellings", "other_than_private_dwellings", "total_dwellings"]
        rows = [["Shipping Population", "..", "..", ".."],
                ["New South Wales", "2", "3", "6"]]
        checks = build_measure_checks(2, headers, rows, 1)
        outcomes, = checks.values()
        self.assertEqual(outcomes[0][1], "N/A")
        self.assertEqual(outcomes[1][1], -1)

    def test_population_supplements_do_not_enter_dwelling_subtotal(self):
        headers = ["wall_material", "dwelling_class", "new_south_wales"]
        rows = [[label, "All Dwellings", amount] for label, amount in
                [("Stone", "5"), ("Total Inmates of Dwellings", "5"),
                 ("Other Camps without Dwellings", "11"), ("Shipping Population", "7"),
                 ("Total Population", "23")]]
        checks = build_count_checks(9, headers, rows, 2)
        self.assertEqual(checks["check_section_new_south_wales_delta"][1][1], 0)
        self.assertEqual(checks["check_population_new_south_wales_delta"][4][1], 0)
        self.assertNotIn(4, checks["check_private_other_new_south_wales_delta"])
        rows.pop(3)
        checks = build_count_checks(9, headers, rows, 2)
        self.assertEqual(checks["check_population_new_south_wales_delta"][3][1], "INCOMPLETE")

    def test_published_class_absence_is_not_a_general_missing_row_rule(self):
        headers = ["number_of_rooms", "dwelling_class", "sydney_and_suburbs"]
        rows = [["Wagons, Trains, etc.", "Dwellings Other Than Private", "2"],
                ["Wagons, Trains, etc.", "All Dwellings", "2"]]
        key = "check_private_other_sydney_and_suburbs_delta"
        self.assertEqual(build_count_checks(52, headers, rows, 2)[key][1][1], 0)
        rows[1][2] = "3"
        self.assertEqual(build_count_checks(52, headers, rows, 2)[key][1][1], 1)
        for row in rows:
            row[0] = "9"
        self.assertEqual(build_count_checks(52, headers, rows, 2)[key][1][1], "INCOMPLETE")
        for row in rows:
            row[0] = "Wagons, Trains, etc."
        rows.insert(0, list(rows[0]))
        self.assertEqual(build_count_checks(52, headers, rows, 2)[key][2][1], "INCOMPLETE")

    def test_published_material_rows_cannot_use_superseded_absence_claims(self):
        headers = ["wall_material", "dwelling_class", "rooms_total"]
        for number, label in ((14, "Sun-dried Bricks"),
                              (15, "Bushes, Rushes, Spinifex, etc."),
                              (22, "Ruberoid and other Compositions")):
            rows = [[label, "Private Dwellings", "2"], [label, "All Dwellings", "3"]]
            check = build_count_checks(number, headers, rows, 2)["check_private_other_rooms_total_delta"]
            self.assertEqual(check[1][1], "INCOMPLETE")

    def test_printed_comma_density_is_unresolved_not_an_integer_outlier(self):
        dims, fields, _ = export.table_fields(68)
        headers = dims + fields
        row = ["Queensland", "Shires", "Tinaroo", "Square miles",
               "272", "2,092", "1,152", "3,244", "11.93", "892", "3,279", "3.64"]
        checks = build_measure_checks(68, headers, [row], len(dims))
        self.assertEqual(checks["Check: occupied / area (printed precision)"][0][1], "INCOMPLETE")
        self.assertEqual(checks["Check: males + females - persons"][0][1], 0)
        field_checks = export.build_checks(68, headers, [row], len(dims))
        self.assertEqual(field_checks["check_unreadable_numeric_fields"][0][1], 1)
        self.assertEqual(numeric_value("3,279"), 3279)  # Ordinary count commas are unchanged.

    def test_export_writes_real_numeric_values(self):
        original_out, original_root = export.OUT, export.ROOT
        with tempfile.TemporaryDirectory() as temporary:
            export.ROOT = Path(temporary)
            export.OUT = Path(temporary) / "output" / "export_abs_1911_dwellings_workbook"
            try:
                row = {"page": 5, "y": 200.0, "row_id": "nsw", "label": "New South Wales",
                       "resolved": "", "cells": {
                           1: {"label": "Occupied", "value": "330,976"},
                           2: {"label": "Unoccupied", "value": "10,271"},
                           3: {"label": "Being Built", "value": "1,191"},
                           4: {"label": "Total", "value": "342,438"}}}
                path = export.export([{"table_id": export.DOC_PREFIX + "1", "table_title": "Dwellings"}],
                                     {1: [row]}, ({}, {}, {}, {}, {}))
                with zipfile.ZipFile(path) as package:
                    root = ET.fromstring(package.read("xl/worksheets/sheet1.xml"))
                ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                cells = {cell.attrib["r"]: cell for cell in root.findall(".//m:c", ns)}
                self.assertNotIn(cells["B3"].attrib.get("t"), ("s", "inlineStr", "str"))
                self.assertEqual(float(cells["B3"].findtext("m:v", namespaces=ns)), 330976)
            finally:
                export.OUT, export.ROOT = original_out, original_root


if __name__ == "__main__":
    unittest.main()
