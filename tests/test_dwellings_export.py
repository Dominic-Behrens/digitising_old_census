"""Regression checks for source-page continuation and structural label cells."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import export_abs_1911_dwellings_workbook as export


class DwellingsExportTests(unittest.TestCase):
    def test_room_continuation_does_not_overwrite_first_room(self):
        # These are the printed Private House cells on physical pages 16–17.
        rows = [
            {"page": 16, "y": 218.64, "row_id": "p16-private", "label": "Private House",
             "resolved": "Private House", "cells": {
                 1: {"label": "1", "value": "64,886"},
                 11: {"label": "11", "value": "4,896"}}},
            {"page": 17, "y": 217.67, "row_id": "p17-private", "label": "Private House",
             "resolved": "Private House", "cells": {
                 1: {"label": "12", "value": "4,043"},
                 11: {"label": "Total", "value": "888,045"}}},
        ]
        headers, body = export.assemble(10, rows, {10: export.table_fields(10)}, {}, {}, {}, {})
        values = dict(zip(headers, body[0]))
        self.assertEqual(values["rooms_1"], "64,886")
        self.assertEqual(values["rooms_11"], "4,896")
        self.assertEqual(values["rooms_12"], "4,043")
        self.assertEqual(values["rooms_total"], "888,045")

    def test_unlabelled_panel_ignores_structural_leader_cells(self):
        row = {"page": 26, "y": 200.0, "row_id": "stone-left", "label": "Stone",
               "resolved": "", "cells": {
                   i: {"label": "", "value": value} for i, value in enumerate(
                       ("..", "..", "..", "100", "152", "348", "1,001", "992",
                        "1,034", "714", "541", "298", "230", "105"), 1)}}
        headers, body = export.assemble(14, [row], {14: export.table_fields(14)}, {}, {}, {}, {})
        values = dict(zip(headers, body[0]))
        self.assertEqual(values["rooms_1"], "100")
        self.assertEqual(values["rooms_11"], "105")

    def test_mislabelled_inmate_first_panel_keeps_eleventh_column(self):
        values = ("..", "..", "..", "89", "180", "244", "223", "234",
                  "197", "131", "107", "71", "40", "28")
        headings = ("12", "13", "14", "15", "16", "17", "18", "19",
                    "", "", "Materials of which Outer Walls were Built.", "", "", "")
        row = {"page": 50, "y": 200.0, "row_id": "stone-inmates",
               "label": "Stone", "resolved": "", "cells": {
                   i: {"label": heading, "value": value}
                   for i, (heading, value) in enumerate(zip(headings, values), 1)}}
        facing = {"page": 51, "y": 200.0, "row_id": "stone-inmates-right",
                  "label": "Stone", "resolved": "", "cells": {
                      1: {"label": "12", "value": "10"},
                      2: {"label": "13", "value": "5"},
                      10: {"label": "Total", "value": "1,575"}}}
        headers, body = export.assemble(27, [row, facing], {27: export.table_fields(27)}, {}, {}, {}, {})
        observed = dict(zip(headers, body[0]))
        self.assertEqual(observed["inmates_1"], "89")
        self.assertEqual(observed["inmates_10"], "40")
        self.assertEqual(observed["inmates_11"], "28")
        self.assertEqual(observed["inmates_12"], "10")
        self.assertEqual(observed["inmates_13"], "5")
        self.assertEqual(observed["inmates_total"], "1,575")

    def test_state_sections_remain_separate_on_facing_pages(self):
        rows = [
            {"page": 18, "y": 380.0, "row_id": "qld-left", "label": "Private House",
             "resolved": "Private House", "cells": {1: {"label": "1", "value": "15,945"}}},
            {"page": 19, "y": 398.0, "row_id": "qld-right", "label": "Private House",
             "resolved": "Private House", "cells": {11: {"label": "Total", "value": "121,062"}}},
            {"page": 18, "y": 620.0, "row_id": "sa-left", "label": "Private House",
             "resolved": "Private House", "cells": {1: {"label": "1", "value": "3,053"}}},
            {"page": 19, "y": 630.0, "row_id": "sa-right", "label": "Private House",
             "resolved": "Private House", "cells": {11: {"label": "Total", "value": "80,990"}}},
        ]
        states = {18: [(371.0, "Queensland"), (596.7, "South Australia")],
                  19: [(372.1, "Queensland"), (598.4, "South Australia")]}
        headers, body = export.assemble(11, rows, {11: export.table_fields(11)}, states, {}, {}, {})
        values = {row[0]: dict(zip(headers, row)) for row in body}
        self.assertEqual(values["Queensland"]["rooms_1"], "15,945")
        self.assertEqual(values["Queensland"]["rooms_total"], "121,062")
        self.assertEqual(values["South Australia"]["rooms_1"], "3,053")
        self.assertEqual(values["South Australia"]["rooms_total"], "80,990")

    def test_printed_row_label_is_not_a_state_value(self):
        # Table 7's final panel has four structural cells before NSW.
        row = {"page": 12, "y": 716.71, "row_id": "rent-ten-pounds",
               "label": "£10 and upwards", "resolved": "£10 and upwards", "cells": {
                   1: {"label": "", "value": "£10 and upwards"},
                   2: {"label": "", "value": ".."},
                   3: {"label": "", "value": ".."},
                   4: {"label": "", "value": ".."},
                   5: {"label": "N.S.W.", "value": "227"},
                   6: {"label": "Vic.", "value": "151"},
                   13: {"label": "COMMON-WEALTH.", "value": "734"}}}
        headers, body = export.assemble(7, [row], {7: export.table_fields(7)}, {}, {}, {}, {})
        values = dict(zip(headers, body[0]))
        self.assertEqual(values["new_south_wales"], "227")
        self.assertEqual(values["victoria"], "151")
        self.assertEqual(values["commonwealth"], "734")

    def test_overview_preserves_repeated_states_and_unlabelled_section_totals(self):
        # Physical p5 Table2 repeats NSW in Remainder and Whole sections.
        # Two untitled printed totals also have distinct section identities.
        cases = [
            (587.82, "", ["779,525", "813,608", "880,721", "1,694,329", "2.17", "326,702", "12,347", "339,049", ".435", "5.00", "5.57", ".89", "14", "5"]),
            (621.72, "New South Wales", ["309,275", "544,493", "464,687", "1,009,180", "3.26", "201,339", "6,403", "207,742", ".672", "4.84", "5.10", ".94", "8", "10"]),
            (666.25, "", ["2,448,830", "1,471,988", "1,256,609", "2,728,597", "1.11", "566,062", "17,458", "583,520", ".238", "4.67", "4.96", ".94", "8", "4"]),
            (711.19, "New South Wales", ["309,460", "850,221", "788,462", "1,638,683", "5.30", "319,766", "11,210", "330,976", "1.070", "4.94", "5.29", ".93", "11", "7"]),
        ]
        rows = [{"page": 5, "y": y, "row_id": f"p5-{y}", "label": label, "resolved": "",
                 "cells": {i: {"label": "", "value": value} for i, value in enumerate(raw, 1)}}
                for y, label, raw in cases]
        headers, body = export.assemble(2, rows, {2: export.table_fields(2)}, {}, {}, {}, {})
        records = {(r["section"], r["area"]): r for r in (dict(zip(headers, row)) for row in body)}
        self.assertEqual(records[("Remainder of States", "New South Wales")]["total_dwellings"], "207,742")
        self.assertEqual(records[("Whole States and Territories", "New South Wales")]["total_dwellings"], "330,976")
        self.assertEqual(records[("Metropolitan", "")]["population_total"], "1,694,329")
        self.assertEqual(records[("Remainder of States", "")]["population_total"], "2,728,597")
        self.assertEqual(records[("Metropolitan", "")]["area_unit"], "Acres")
        self.assertEqual(records[("Whole States and Territories", "New South Wales")]["area_unit"], "Square miles")



if __name__ == "__main__":
    unittest.main()
