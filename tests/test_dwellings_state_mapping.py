"""Source-backed facing-panel regressions, without the candidate CSV or APIs."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from dwellings_state_panels import LEFT_AREAS, RIGHT_AREAS, assemble_state_panels


def source_row(page, y, label, values):
    return {"page": page, "y": y, "row_id": f"{page}/{y}",
            "label": label, "resolved": label, "cells": {
                i: {"label": "", "value": value}
                for i, value in enumerate(values, 1)}}


def assemble(number, rows):
    fields = [f"{area}_{unit}" for area in LEFT_AREAS + RIGHT_AREAS
              for unit in ("shillings", "pence")] if number >= 61 else list(LEFT_AREAS + RIGHT_AREAS)
    headers, body = assemble_state_panels(
        number, rows, (["number_of_rooms"], fields, "number_of_rooms"))
    return {row[0]: dict(zip(headers, row)) for row in body}


def amounts(row, areas):
    return [(row[f"{area}_shillings"], row[f"{area}_pence"]) for area in areas]


class StateMappingTests(unittest.TestCase):
    def test_false_federal_absence_does_not_shift_commonwealth_averages(self):
        # PDF p.127 y=238.62/244.38: candidate inserted a rule as '..'
        # before Federal Territory and lost the final Commonwealth value.
        rows = [source_row(127, 238.62, "9",
                           "6.357 6.556 6.450 5.554 6.116 5.930 15.000 .. 4.429 5.851 6.377".split()),
                source_row(127, 244.38, "10",
                           "6.707 6.866 6.792 5.988 6.133 6.091 4.000 .. 6.875 6.053 6.657".split())]
        observed = assemble(59, rows)
        self.assertEqual([observed["9"][a] for a in RIGHT_AREAS[6:]],
                         ["15.000", "4.429", "5.851", "6.377", "6.166"])
        self.assertEqual([observed["10"][a] for a in RIGHT_AREAS[6:]],
                         ["4.000", "6.875", "6.053", "6.657", "6.416"])

    def test_perth_combined_currency_units_keep_their_printed_order(self):
        # PDF p.129 rows 1–2: row 1 is correctly s./d.; row 2 was d./s.
        rows = [source_row(129, 312.30, "1",
                           "5 0|2 5|2 6|3 6|2 1|2 2|1 8|1 7|5 2|2 1|2 4".split("|")),
                source_row(129, 318.54, "2",
                           "11 2|2 5|2 6|2 9|1 8|1 9|1 7|1 11|3 3|1 11|2 1".split("|"))]
        observed = assemble(62, rows)
        self.assertEqual(amounts(observed["1"], RIGHT_AREAS[:2]), [("5", "0"), ("2", "5")])
        self.assertEqual(amounts(observed["2"], RIGHT_AREAS[:3]),
                         [("2", "11"), ("2", "5"), ("2", "6")])

    def test_sixteen_rooms_has_federal_rent_and_all_three_totals(self):
        # PDF p.129 y=403.50: trailing room label is not a currency cell.
        # Federal Territory prints 6s. 0d., unlike unavailable rows 13–15.
        rows = [source_row(129, 385.26, "11",
                           "3 7 1 11 2 8 2 4 1 6 1 9 .. .. 3 11 1 10 2 9 13".split()),
                source_row(129, 403.50, "14",
                           "5 1 2 6 3 10 2 5 1 3 1 7 1 .. 6 0 4 7 2 0".split() + ["16 and over"])]
        observed = assemble(62, rows)
        self.assertEqual(amounts(observed["13"], RIGHT_AREAS[6:]),
                         [("..", ".."), ("..", ".."), ("3", "11"), ("1", "10"), ("2", "9")])
        self.assertEqual(amounts(observed["16 and over"], RIGHT_AREAS[6:]),
                         [("..", ".."), ("6", "0"), ("4", "7"), ("2", "0"), ("3", "0")])

    def test_rule_fragments_do_not_shift_inmate_rent_into_next_state(self):
        # PDF p.128 y=718.63: a stray rule unit precedes Brisbane and the
        # final South Australia pence is lost. All candidate values are legal.
        row = source_row(128, 718.63, "6",
                         "3 1 1 11 2 5 2 11 1 9 2 3 1 2 2 5 1 10 2 1 3 1 1 9".split())
        observed = assemble(63, [row])["6"]
        self.assertEqual(amounts(observed, LEFT_AREAS[6:]),
                         [("2", "5"), ("1", "10"), ("2", "1"), ("3", "1"), ("1", "9"), ("2", "4")])

    def test_right_panel_rules_do_not_corrupt_tasmania_or_absence_pairs(self):
        # PDF p.129 y=752.70/764.93: rule fragments split currency pairs;
        # NT/FT absence marks must not become digits or steal total columns.
        rows = [source_row(129, 752.70, "12",
                           "6 5 3 7 1 4 9 4 9 3 0 3 7 1 .. .. 6 9 3 0 4 5".split()),
                source_row(129, 764.93, "14",
                           "7 5 4 3 1 5 6 6 5 3 0 3 10 1 .. .. 7 9 3 4 5".split())]
        observed = assemble(63, rows)
        self.assertEqual(amounts(observed["12"], RIGHT_AREAS[2:]),
                         [("4", "9"), ("4", "9"), ("3", "0"), ("3", "7"),
                          ("..", ".."), ("..", ".."), ("6", "9"), ("3", "0"), ("4", "5")])
        self.assertEqual(amounts(observed["14"], RIGHT_AREAS[2:]),
                         [("5", "6"), ("6", "5"), ("3", "0"), ("3", "10"),
                          ("..", ".."), ("..", ".."), ("7", "9"), ("3", "4"), ("5", "1")])


if __name__ == "__main__":
    unittest.main()
