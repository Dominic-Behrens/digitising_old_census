"""Source-backed regressions for Table 67 leader shifts and braced denominators."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import export_abs_1911_dwellings_workbook as export
from dwellings_county_measures import assemble_county_measures
from dwellings_measure_checks import build_measure_checks


class CountyMappingTests(unittest.TestCase):
    def test_cook_leaders_do_not_become_population_columns(self):
        # Physical p180::r63: the candidate inserted two gutter marks and
        # consequently lost the final two currency fields.
        raw = ["..", "..", "17139", "2,016", "1,333", "3,349", ".20", "817", "41", "858", ".050", "3.90", "4.40", ".88"]
        row = {"page": 180, "y": 595.98, "row_id": "p180::r63", "label": "Cook", "resolved": "Cook",
               "cells": {i: {"label": "", "value": value} for i, value in enumerate(raw, 1)}}
        headers, body = assemble_county_measures([row], export.table_fields(67),
                                               {180: [(480, "Queensland")]}, {180: [(480, "Census District")]})
        observed = dict(zip(headers, body[0]))
        self.assertEqual(observed["area_square_miles"], "17139")
        self.assertEqual(observed["population_males"], "2,016")
        self.assertEqual(observed["population_females"], "1,333")
        self.assertEqual(observed["population_persons"], "3,349")
        self.assertEqual(observed["occupied_dwellings_total"], "858")
        self.assertEqual(observed["average_weekly_rental_shillings"], "5")
        self.assertEqual(observed["average_weekly_rental_pence"], "2")

    def test_braced_area_is_not_a_division_denominator(self):
        # Physical p181::r68: area/densities are braced across four Outside
        # Counties divisions; count columns belong to North Eastern alone.
        raw = ["297,967", "..", "907", "338", "1,245", ".01", "314", "13", "327", "289", "..", ".003", "3.62", "3.46", "1.05", "4", "3"]
        row = {"page": 181, "y": 626.46, "row_id": "p181::r68", "label": "North Eastern Div.", "resolved": "",
               "cells": {i: {"label": "", "value": value} for i, value in enumerate(raw, 1)}}
        headers, body = assemble_county_measures([row], export.table_fields(67),
                                               {181: [(300, "South Australia")]}, {181: [(300, "County")]})
        observed = dict(zip(headers, body[0]))
        self.assertEqual(observed["area_square_miles"], "")
        self.assertEqual(observed["area_group_square_miles"], "297,967")
        self.assertEqual(observed["population_males"], "907")
        self.assertEqual(observed["population_persons"], "1,245")
        self.assertEqual(observed["occupied_dwellings_total"], "327")
        checks = build_measure_checks(67, headers, body, 4)
        self.assertEqual(checks["Check: persons / area (printed precision)"][0][1], "N/A")
        self.assertEqual(checks["Check: males + females - persons"][0][1], 0)
        damaged = [list(body[0])]
        damaged[0][headers.index("population_persons")] = "1,246"
        self.assertEqual(build_measure_checks(67, headers, damaged, 4)["Check: males + females - persons"][0][1], -1)

    def test_actual_division_layouts_preserve_population_and_dwelling_classes(self):
        cases = [
            ("Northern Division", 620.64,
             ["..", "..", "..", "791", "468", "1,259", "..", "272", "17", "289", "..", "4.03", "4.15", ".96", "4", "3"],
             ["791", "468", "1,259", "272", "17", "289"]),
            ("North Western Div.", 632.46,
             ["920", "324", "1,244", "1,244", "..", "247", "19", "266", "..", "4.50", "3.54", "1.25", "6", "3"],
             ["920", "324", "1,244", "247", "19", "266"]),
            ("Western Division", 638.7,
             ["15", "2", "17", "..", "..", "2", "..", "2", "..", "3.00", "2.50", "1.40", "2", "6"],
             ["15", "2", "17", "2", "2", "4"]),
        ]
        fields = ["population_males", "population_females", "population_persons",
                  "occupied_dwellings_private", "occupied_dwellings_other_than_private",
                  "occupied_dwellings_total"]
        for label, y, raw, expected in cases:
            with self.subTest(label=label):
                row = {"page": 181, "y": y, "row_id": label, "label": label, "resolved": "",
                       "cells": {i: {"label": "", "value": value} for i, value in enumerate(raw, 1)}}
                headers, body = assemble_county_measures([row], export.table_fields(67),
                    {181: [(300, "South Australia")]}, {181: [(300, "County")]})
                observed = dict(zip(headers, body[0]))
                self.assertEqual([observed[field] for field in fields], expected)
                self.assertEqual(observed["area_square_miles"], "")

    def test_overlapping_york_proposals_keep_one_york_and_the_real_yilgarn(self):
        # The g3 labels/vectors are one baseline ahead of their row anchors.
        # Locate the named printed rows; do not enlarge a duplicate tolerance.
        yilgarn = ["16,875", "2,968", "982", "3,950", ".23", "1,660", "48", "1,708", ".101", "2.27", "2.06", "1.10", "4", "11"]
        york = ["3,750", "3,577", "2,259", "5,836", "1.56", "1,224", "25", "1,249", ".333", "4.62", "4.00", "1.16", "8", "9"]
        rows = [{"page": 182, "y": y, "row_id": f"p182-{y}", "label": label, "resolved": "",
                 "cells": {i: {"label": "", "value": value} for i, value in enumerate(raw, 1)}}
                for label, y, raw in [("Yilgarn", 228.39, yilgarn), ("York", 234.55, york), ("York", 240.79, york)]]
        headers, body = assemble_county_measures(rows, export.table_fields(67),
            {182: [(0, "Western Australia")]}, {182: [(0, "Statistical District")]})
        observed = [dict(zip(headers, row)) for row in body]
        self.assertEqual([row["area"] for row in observed], ["Yilgarn", "York"])
        self.assertEqual([row["population_persons"] for row in observed], ["3,950", "5,836"])
        self.assertEqual([row["occupied_dwellings_total"] for row in observed], ["1,708", "1,249"])

    def test_repeated_millewa_counts_keep_private_and_total_slots(self):
        # Physical p180::r27 prints private 19, other dots, total 19. The
        # private OCR glyph is absent from the PDF text, so the total's 19
        # must not anchor both candidate occurrences into the total column.
        raw = ["3,572", "56", "28", "84", ".02", "19", "..", "19",
               ".005", "4.42", "3.11", "1.42", "11", "0"]
        row = {"page": 180, "y": 337.27, "row_id": "p180::r27", "label": "Millewa", "resolved": "",
               "cells": {i: {"label": "", "value": value} for i, value in enumerate(raw, 1)}}
        headers, body = assemble_county_measures([row], export.table_fields(67),
            {180: [(152, "Victoria")]}, {180: [(152, "County")]})
        observed = dict(zip(headers, body[0]))
        self.assertEqual(observed["occupied_dwellings_private"], "19")
        self.assertEqual(observed["occupied_dwellings_other_than_private"], "..")
        self.assertEqual(observed["occupied_dwellings_total"], "19")
        self.assertEqual(build_measure_checks(67, headers, body, 4)["Check: private + other - occupied"][0][1], 0)

    def test_shipping_does_not_borrow_adjacent_land_summary(self):
        for state, y, counts in [
            ("Tasmania", 653.24, ["560", "16", "576"]),
            ("Northern Territory", 743.1, ["181", "..", "181"]),
        ]:
            with self.subTest(state=state):
                raw = [".."] + counts + [".."] * 10
                row = {"page": 182, "y": y, "row_id": f"shipping-{state}", "label": "Shipping", "resolved": "",
                       "cells": {i: {"label": "", "value": value} for i, value in enumerate(raw, 1)}}
                headers, body = assemble_county_measures([row], export.table_fields(67),
                    {182: [(0, state)]}, {182: [(0, "County")]})
                observed = dict(zip(headers, body[0]))
                self.assertEqual([observed[name] for name in ["population_males", "population_females", "population_persons"]], counts)
                self.assertEqual([observed[name] for name in ["area_square_miles", "occupied_dwellings_total",
                    "average_rooms_per_occupied_dwelling", "average_weekly_rental_shillings"]], [".."] * 4)

    def test_visible_area_and_printed_discrepancy_are_not_balanced(self):
        cases = [
            ("Western Australia", "North West", 167.82,
             ["17,344", "2,557", "479", "3,036", ".03", "861", "92", "953", ".008", "2.60", "2.56", "1.01", "8", "4"],
             "area_square_miles", "117,344"),
            ("Tasmania", "Longford", 502.38,
             ["398.00", "2,060", "2,095", "4,155", "10.44", "825", "16", "841", "2.113", "4.81", "4.36", "1.05", "4", "10"],
             "average_inmates_per_occupied_dwelling", "6.81"),
        ]
        for state, label, y, raw, field, expected in cases:
            with self.subTest(label=label):
                row = {"page": 182, "y": y, "row_id": label, "label": label, "resolved": "",
                       "cells": {i: {"label": "", "value": value} for i, value in enumerate(raw, 1)}}
                headers, body = assemble_county_measures([row], export.table_fields(67),
                    {182: [(0, state)]}, {182: [(0, "Statistical District" if state == "Western Australia" else "Municipality")]})
                self.assertEqual(dict(zip(headers, body[0]))[field], expected)

    def test_missing_western_shipping_is_recovered_without_duplicate_counts(self):
        panel = [
            ("WHOLE STATE", 268.62,
             ["975,920", "155,719", "119,379", "275,098", ".28", "66,553", "2,317", "68,870", ".071", "3.96", "3.97", ".99", "10", "7"]),
            ("TOTAL POPULATION", 283.74,
             ["..", "161,565", "120,549", "282,114"] + [".."] * 10),
        ]
        rows = [{"page": 182, "y": y, "row_id": label, "label": label, "resolved": "",
                 "cells": {i: {"label": "", "value": value} for i, value in enumerate(raw, 1)}}
                for label, y, raw in panel]
        states, areas = {182: [(0, "Western Australia")]}, {182: [(0, "Statistical District")]}
        for supplied in (rows, rows + [
            {"page": 182, "y": 273.6, "row_id": "existing-shipping", "label": "Shipping", "resolved": "",
             "cells": {i: {"label": "", "value": value} for i, value in enumerate(
                 ["..", "5,846", "1,170", "7,016"] + [".."] * 10, 1)}},
        ]):
            headers, body = assemble_county_measures(supplied, export.table_fields(67), states, areas)
            observed = [dict(zip(headers, row)) for row in body]
            self.assertEqual([row["area"] for row in observed], ["WHOLE STATE", "Shipping", "TOTAL POPULATION"])
            self.assertEqual([observed[1][field] for field in ["population_males", "population_females", "population_persons"]],
                             ["5,846", "1,170", "7,016"])
            self.assertEqual(observed[1]["occupied_dwellings_total"], "..")


if __name__ == "__main__":
    unittest.main()
