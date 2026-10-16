"""Source-backed geography regressions; no candidate CSV or paid service needed."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from dwellings_geography_panels import assemble_geography_panels

METRO = ["sydney_and_suburbs", "melbourne_and_suburbs", "brisbane_and_suburbs",
         "adelaide_and_suburbs", "perth_and_suburbs", "hobart_and_suburbs",
         "total_metropolitan_areas"]
STATES = ["new_south_wales", "victoria", "queensland", "south_australia",
          "western_australia", "tasmania", "northern_territory", "federal_territory",
          "commonwealth"]


def source_row(page, y, label, values, row_id="fixture"):
    return {"page": page, "y": y, "label": label, "resolved": label,
            "row_id": row_id, "cells": {
                i: {"label": "", "value": value}
                for i, value in enumerate(values, 1)}}


def assemble(number, rows, category, columns=METRO):
    headers, body = assemble_geography_panels(
        number, rows, ([category, "dwelling_class"], columns, category), {}, {})
    return [dict(zip(headers, row)) for row in body]


class GeographyMappingTests(unittest.TestCase):
    def test_all_room_one_ignores_four_leader_columns(self):
        # PDF115 / candidate r48: all seven figures are after four leaders.
        rows = [source_row(115, 620.61, "1", [".."] * 4 +
                           ["1,438", "736", "550", "452", "474", "80", "3,730"])]
        observed = assemble(52, rows, "number_of_rooms")[0]
        self.assertEqual(observed["dwelling_class"], "All Dwellings")
        self.assertEqual([observed[column] for column in METRO],
                         ["1,438", "736", "550", "452", "474", "80", "3,730"])

    def test_repeated_room_labels_keep_private_other_and_all_separate(self):
        rows = [source_row(115, y, "1", values, str(y)) for y, values in (
            (197.8, ["1,404", "688", "543", "446", "469", "78", "3,628"]),
            (405.4, ["34", "48", "7", "6", "5", "2", "102"]),
            (620.61, ["1,438", "736", "550", "452", "474", "80", "3,730"]))]
        observed = {row["dwelling_class"]: row for row in assemble(52, rows, "number_of_rooms")}
        self.assertEqual(observed["Private Dwellings"]["sydney_and_suburbs"], "1,404")
        self.assertEqual(observed["Dwellings Other Than Private"]["sydney_and_suburbs"], "34")
        self.assertEqual(observed["All Dwellings"]["sydney_and_suburbs"], "1,438")

    def test_printed_rent_lower_bound_overrides_next_bracket_candidate(self):
        # PDF120 r14 is 12s. under 13s., not candidate label 13s.
        rows = [source_row(120, 321.36, "13s.",
                           ["10,922", "10,254", "2,738", "3,220", "1,921", "637", "29,692"])]
        observed = assemble(55, rows, "weekly_rental_value")[0]
        self.assertEqual(observed["weekly_rental_value"], "12s.")
        self.assertEqual(observed["sydney_and_suburbs"], "10,922")
        self.assertEqual(observed["dwelling_class"], "All Dwellings")

    def test_split_lower_bound_digits_do_not_shift_adjacent_rental_bins(self):
        # PDF113 splits 20s./21s./22s. into two OCR words.
        rows = [
            source_row(113, 468.48, "21s.", ["264", "191", "100", "66", "97", "7", "3", "..", "738"]),
            source_row(113, 476.64, "22s.", ["19", "9", "1", "2", "..", "..", "..", "..", "31"]),
            source_row(113, 484.79, "23s.", ["37", "23", "3", "6", "5", "..", "..", "..", "74"]),
        ]
        observed = assemble(49, rows, "weekly_rental_value", STATES)
        self.assertEqual(
            [(r["weekly_rental_value"], r["new_south_wales"], r["commonwealth"]) for r in observed],
            [("20s.", "264", "738"), ("21s.", "19", "31"), ("22s.", "37", "74")])

    def test_repeated_total_does_not_move_a_row_to_another_rental_bin(self):
        # PDF123 prints 3 for both totals, but OCR recognises only the second.
        rows = [
            source_row(123, 779.60, "27s.", ["6", "12", "1", "3", "1", "..", "3"], "27"),
            source_row(123, 787.65, "28s.", ["1", "1", "..", "1", "..", "..", "3"], "28"),
        ]
        observed = assemble(56, rows, "weekly_rental_value")
        self.assertEqual(
            [(r["weekly_rental_value"], r["sydney_and_suburbs"], r["melbourne_and_suburbs"],
              r["total_metropolitan_areas"]) for r in observed],
            [("27s.", "6", "12", "3"), ("28s.", "1", "1", "3")])

    def test_missing_other_heading_does_not_put_wagons_in_private(self):
        rows = [source_row(125, 632.88, "Wagons, Trains, etc.",
                           ["637", "5", "6", "4", "..", "..", "652"])]
        observed = assemble(58, rows, "wall_material")[0]
        self.assertEqual(observed["dwelling_class"], "Dwellings Other Than Private")
        self.assertEqual(observed["sydney_and_suburbs"], "637")
        self.assertEqual(observed["total_metropolitan_areas"], "652")

    def test_short_400_room_grids_keep_melbourne_and_total(self):
        rows = [source_row(116, 571.17, "400 and over",
                           ["·", "·", "··", "··", "1", "1", "··"], "other"),
                source_row(116, 775.94, "400",
                           ["· ·", "· ·", "· ·", "1", "· ·", "· ·", "1"], "all")]
        observed = {row["dwelling_class"]: row for row in assemble(53, rows, "room_range")}
        for dwelling_class in ("Dwellings Other Than Private", "All Dwellings"):
            self.assertEqual(observed[dwelling_class]["room_range"], "400 and over")
            self.assertEqual(observed[dwelling_class]["melbourne_and_suburbs"], "1")
            self.assertEqual(observed[dwelling_class]["total_metropolitan_areas"], "1")
        self.assertNotEqual(observed["All Dwellings"]["adelaide_and_suburbs"], "1")

    def test_state_room_range_leaders_do_not_truncate_commonwealth(self):
        # PDF8 r5, Private 20–24, includes a zero NT and a one FT.
        rows = [source_row(8, 316.3, "20–24", ["· ·"] * 3 +
                           ["275", "206", "65", "42", "21", "26", "· ·", "1", "636"])]
        observed = assemble(5, rows, "room_range", STATES)[0]
        self.assertEqual(observed["new_south_wales"], "275")
        self.assertEqual(observed["federal_territory"], "1")
        self.assertEqual(observed["commonwealth"], "636")

    def test_unlabelled_multiline_camp_row_remains_distinct_from_total(self):
        rows = [source_row(12, 764.95, "", ["21", "1", "50", "18", "80", "..", "21", "..", "191"])]
        observed = assemble(7, rows, "weekly_rental_value", STATES)[0]
        self.assertEqual(observed["weekly_rental_value"],
                         "Aboriginal Camps in which Whites or Half-castes were Living")
        self.assertEqual(observed["commonwealth"], "191")

    def test_tenant_heading_applies_before_page_continuation(self):
        # Page122's OCR spells TENAN1'S; this row is already Tenants,
        # not the preceding Rent Purchasers panel.
        row = source_row(122, 665.6, "Under 1s. .. ..", ["24", "2", "5", "5", "2", "2", "40"])
        schema = (["weekly_rental_value", "method_of_occupancy"], METRO, "weekly_rental_value")
        headers, body = assemble_geography_panels(56, [row], schema, {}, {})
        observed = dict(zip(headers, body[0]))
        self.assertEqual(observed["method_of_occupancy"], "Occupied by Tenants")
        self.assertEqual(observed["weekly_rental_value"], "Under 1s.")
        self.assertEqual(observed["total_metropolitan_areas"], "40")


    def test_complete_printed_grid_resolves_duplicate_regardless_of_arrival_order(self):
        correct = source_row(110, 768.92, "£8", ["7", "8", "..", "3", "2", "..", "..", "..", "20"], "correct")
        shifted = source_row(110, 766.05, "£8", ["..", "8", "..", "3", "..", "2", "..", "..", "20"], "shifted")
        schema = (["weekly_rental_value", "method_of_occupancy"], STATES, "weekly_rental_value")
        for rows in ([correct, shifted], [shifted, correct]):
            headers, body = assemble_geography_panels(49, rows, schema, {}, {})
            records = [dict(zip(headers, row)) for row in body]
            self.assertEqual([(r["new_south_wales"], r["western_australia"], r["tasmania"]) for r in records],
                             [("7", "2", "..")])

    def test_complete_pdf_ocr_does_not_adjudicate_a_single_digit_conflict(self):
        figures = ["1,438", "736", "550", "452", "474", "80", "3,730"]
        alternate = ["1,439"] + figures[1:]
        rows = [source_row(115, 620.61, "1", figures, "a"),
                source_row(115, 620.61, "1", alternate, "b")]
        records = assemble(52, rows, "number_of_rooms")
        self.assertEqual({r["sydney_and_suburbs"] for r in records}, {"1,438", "1,439"})

    def test_incomplete_source_grid_does_not_resolve_conflicting_digits(self):
        figures = ["1,438", "736", "550", "452", "474", "80", "3,730"]
        alternate = ["1,439"] + figures[1:]
        rows = [source_row(115, 60, "1", figures, "a"),
                source_row(115, 60, "1", alternate, "b")]
        schema = (["number_of_rooms", "dwelling_class"], METRO, "number_of_rooms")
        headers, body = assemble_geography_panels(52, rows, schema, {115: [(0, "All Dwellings")]}, {})
        records = [dict(zip(headers, row)) for row in body]
        self.assertEqual({r["sydney_and_suburbs"] for r in records}, {"1,438", "1,439"})

    def test_printed_twenty_plus_qualifier_overrides_truncated_two_label(self):
        row = source_row(124, 770.74, "2", ["17,058", "14,630", "4,392", "3,875", "4,870", "1,572", "46,397"])
        observed = assemble(57, [row], "number_of_rooms")[0]
        self.assertEqual(observed["number_of_rooms"], "20 and over")
        self.assertEqual(observed["dwelling_class"], "Dwellings Other Than Private")

    def test_matching_total_does_not_preserve_shifted_tenant_cities(self):
        rows = [source_row(123, 168.2, "16s.",
                           ["2,052", "240", "651", "278", "·", "159", "6,778"])]
        observed = assemble(56, rows, "weekly_rental_value")[0]
        self.assertEqual([observed[column] for column in METRO],
                         ["3,398", "2,052", "240", "651", "278", "159", "6,778"])

    def test_false_fraction_does_not_displace_printed_absences(self):
        rows = [source_row(116, 768.09, "300",
                           ["· ·", "· ·", "½", "1", "· ·", "· ·", "3"])]
        observed = assemble(53, rows, "room_range")[0]
        self.assertEqual([observed[column] for column in METRO],
                         ["2", "1", "..", "..", "· ·", "· ·", "3"])

    def test_readable_hobart_room_nine_is_not_left_as_ocr_letter(self):
        rows = [source_row(115, 262.05, "9",
                           ["2,711", "2,963", "798", "707", "286", "26J", "7,734"])]
        observed = assemble(52, rows, "number_of_rooms")[0]
        self.assertEqual(observed["hobart_and_suburbs"], "269")

    def test_damaged_owner_figure_is_not_balanced_from_total(self):
        row = source_row(121, 372.47, "17s.",
                         ["724", "1,80", "229", "289", "133", "45", "2,600"])
        schema = (["weekly_rental_value", "method_of_occupancy"], METRO, "weekly_rental_value")
        headers, body = assemble_geography_panels(56, [row], schema, {}, {})
        observed = dict(zip(headers, body[0]))
        self.assertEqual(observed["melbourne_and_suburbs"], "1,80")
        self.assertEqual(observed["method_of_occupancy"], "Occupied by Owners")

    def test_rent_figures_register_on_source_row_not_previous_label(self):
        # Candidate figures at y576.25 belong to the printed £2 5s. row
        # at y584, not to the preceding £2 row.
        rows = [source_row(11, 576.25, "£2 5s. to £2 10s.",
                           ["153", "106", "37", "22", "21", "9", "2", "..", "350"])]
        observed = assemble(7, rows, "weekly_rental_value", STATES)[0]
        self.assertEqual(observed["weekly_rental_value"], "£2 5s.")
        self.assertEqual(observed["new_south_wales"], "153")


if __name__ == "__main__":
    unittest.main()
