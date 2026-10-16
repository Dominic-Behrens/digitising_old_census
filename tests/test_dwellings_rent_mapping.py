"""Behavioural regressions for source-located facing-page rent mapping."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import dwellings_rent_panels as rent


def candidate(page, y, label, values, headings=()):
    return {"page": page, "y": y, "row_id": f"p{page}-{y}", "label": label,
            "resolved": label, "cells": {
                index: {"label": headings[index - 1] if index <= len(headings) else "",
                        "value": value} for index, value in enumerate(values, 1)}}


def printed(page, y, label, values, context=rent.PRIVATE, start=0, width=11):
    return {"page": page, "y": y, "label": label,
            "identity": rent._identity(label, page < 72), "values": values,
            "context": context, "start": start,
            "edges": tuple(60 + index * 31.3 for index in range(width))}


class RentMappingTests(unittest.TestCase):
    def test_leader_tokens_do_not_truncate_last_two_room_columns(self):
        # p76's 12s row contains the upper-bound token, a leader and all eleven
        # figures under misleading headings. The last figures are 148 and 59.
        values = ("14", "37", "295", "3,888", "6,916", "4,384", "1,546", "699", "291", "148", "59")
        row = candidate(76, 351.43, "12s.", ("13s.", "..") + values)
        source = printed(76, 351.44, "12s.", dict(enumerate(values)))
        mapped = rent._values(row, source)
        self.assertEqual(mapped[0], "14")
        self.assertEqual(mapped[9], "148")
        self.assertEqual(mapped[10], "59")


    def test_aligned_candidate_digits_survive_corrupted_pdf_text(self):
        source = printed(109, 776.8, "Unspecified", {10: "28,94i"}, start=11)
        row = candidate(109, 776.96, "Unspecified", ("..",) * 10 + ("28,945",))
        self.assertEqual(rent._values(row, source)[10], "28,945")
        damaged = candidate(109, 776.96, "Unspecified", ("..",) * 10 + ("28,94i",))
        self.assertEqual(rent._values(damaged, source)[10], "28,94i")

    def test_padded_rent_run_does_not_duplicate_surviving_figures(self):
        # p74 £2: candidate padding moved the four surviving figures into
        # rooms8-11. Printed rooms4-11 are 7,11,11,23,43,89,112,117.
        values = ("·",) * 7 + ("7", "11", "11", "23")
        row = candidate(74, 572.44, "£2", values)
        source = printed(74, 571.24, "£2", {
            3: "7", 4: "11", 5: "11", 6: "23",
            7: "43", 8: "89", 9: "112", 10: "117"})
        mapped = rent._values(row, source)
        self.assertEqual({slot: mapped[slot] for slot in range(3, 7)},
                         {3: "7", 4: "11", 5: "11", 6: "23"})
        self.assertNotIn(7, mapped)
        self.assertNotIn(10, mapped)


    def test_sparse_split_page_keeps_the_eleventh_room_column(self):
        edges = rent._column_edges(100, False)
        values = rent._source_values(100, 168.51, edges)
        self.assertEqual(values[0], "86")
        self.assertEqual(values[1], "4")

    def test_malformed_pound_lower_bound_uses_the_printed_upper_endpoint(self):
        rows = rent._printed_rows(45, 96)
        lower = [row for row in rows if abs(row["y"] - 712.91) < 1]
        self.assertEqual([row["label"] for row in lower], ["£3"])

    def test_damaged_upper_shilling_token_does_not_duplicate_lower_rent(self):
        # Printed upper5s/10s/15s can be OCR'd58_/lOB./15B. Their
        # missing shillings used to relabel the lower row as the previous one.
        cases = ((41, 80, 638.95, "£3"), (41, 81, 654.56, "£3 5s."),
                 (43, 88, 733.99, "£4 10s."), (48, 105, 689.52, "£3 5s."))
        for number, page, y, expected in cases:
            rows = [row for row in rent._printed_rows(number, page)
                    if abs(row["y"] - y) < 1]
            self.assertEqual([row["label"] for row in rows], [expected])

    def test_distant_equal_labels_are_not_joined_or_discarded(self):
        left = printed(54, 200, "1", {0: "7"}, width=10)
        right = printed(55, 235, "1", {10: "9"}, start=10)
        with patch.object(rent, "_printed_rows", side_effect=lambda number, page: (left,) if page == 54 else (right,)):
            headers, body = rent.assemble_rent_panels(30, [], (["dwelling_class", "number_of_rooms"], [], "number_of_rooms"), {}, {})
        rows = [dict(zip(headers, row)) for row in body]
        self.assertEqual(rows[0]["inmates_1"], "7")
        self.assertEqual(rows[0]["inmates_total"], "")
        self.assertEqual(rows[1]["inmates_1"], "")
        self.assertEqual(rows[1]["inmates_total"], "9")

    def test_physical_split_leaf_owns_only_its_printed_table(self):
        self.assertEqual(rent.assign_rent_table(77, 240.56, 39), 40)
        self.assertEqual(rent.assign_rent_table(59, 400, 31), 32)
        self.assertEqual(rent.assign_rent_table(100, 600, 46), 47)
        self.assertIsNone(rent._layout(46, 100, 600))

    def test_table40_under_one_total_uses_word_midpoint_not_next_bbox_top(self):
        # Physical p77 has 1,484 on the Under1s baseline, then 6,776 one row
        # below. Candidate row_y_pt is a box midpoint, not its top edge.
        rows = [candidate(76, 238.63, "Under 1s.", ("1,048", "263", "78", "55", "26", "13", "1", "..", "..", "..", "..")),
                candidate(77, 240.56, "Under 1s.", ("..",) * 10 + ("6,776",))]
        headers, body = rent.assemble_rent_panels(40, rows, (["weekly_rental_value", "dwelling_class"], [], "weekly_rental_value"), {}, {})
        matches = [dict(zip(headers, row)) for row in body if row[:2] == ["Under 1s.", rent.PRIVATE]]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["rooms_total"], "1,484")
        self.assertEqual(matches[0]["rooms_1"], "1,048")

    def test_table48_existing_mislabelled_rows_are_relabelled_not_duplicated(self):
        # Snapshot rows213/224 are the existing £2 and £4 10s source brackets,
        # not omitted rows to append. £4's nearby 3,1,2 belong to its own row.
        rows = [candidate(108, 631.88, "£2 5s.", ("..", "..", "..", "..", "1", "..", "7", "9", "22", "23", "13")),
                candidate(109, 640.52, "58.", ("15", "14", "7", "4", "5", "..", "2", "1", "5", "..", "128")),
                candidate(108, 712.76, "£4", ("£4 10s.", "”", "£4 15s.") + ("..",) * 10 + ("3", "1", "2")),
                candidate(109, 728.72, "£4 10s.", ("..", "..", "..", "..", "1", "1", "..", "1", "..", "..", "3"))]
        headers, body = rent.assemble_rent_panels(48, rows, (["method_of_occupancy", "weekly_rental_value"], [], "weekly_rental_value"), {}, {})
        other = [dict(zip(headers, row)) for row in body if row[0] == rent.METHODS[3]]
        pound_two = [row for row in other if row["weekly_rental_value"] == "£2"]
        four_ten = [row for row in other if row["weekly_rental_value"] == "£4 10s."]
        four = [row for row in other if row["weekly_rental_value"] == "£4"]
        self.assertEqual(len(pound_two), 1)
        self.assertEqual(pound_two[0]["rooms_total"], "128")
        self.assertEqual(len(four_ten), 1)
        self.assertEqual(four_ten[0]["rooms_total"], "3")
        self.assertEqual(four[0]["rooms_9"], "3")
        self.assertEqual(four[0]["rooms_10"], "1")
        self.assertEqual(four[0]["rooms_11"], "2")
        self.assertEqual(four[0]["rooms_total"], "15")


if __name__ == "__main__":
    unittest.main()
