"""Source-backed room/inmate mapping, independent of arithmetic residuals."""

import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from dwellings_room_panels import assemble_room_panels, assign_room_table
from export_abs_1911_dwellings_workbook import read_page_markers

DOC = "1911_census_volume_iii_part_xiii_dwellings"


def schema(number):
    prefix = "inmates" if number >= 21 else "rooms"
    bins = [str(i) for i in range(1, 20)] + ["20_and_over"]
    if prefix == "rooms":
        bins.append("unspecified")
    bins.append("total")
    dimensions = (["dwelling_type"] if number == 10 else
                  ["state", "dwelling_type"] if number == 11 else
                  ["wall_material", "dwelling_class"])
    return dimensions, [f"{prefix}_{value}" for value in bins], dimensions[-1] if number <= 11 else "wall_material"


class RoomMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.states, _, cls.panels, _ = read_page_markers()
        cls.source = {}
        with (ROOT / "output/extract_abs_1911_source_regions/cells.csv").open(
                encoding="utf-8", newline="") as stream:
            for cell in csv.DictReader(stream):
                if cell["doc_id"] != DOC or not 16 <= int(cell["pdf_page"]) <= 53:
                    continue
                row = cls.source.setdefault(cell["row_id"], {
                    "page": int(cell["pdf_page"]), "y": float(cell["row_y_pt"]),
                    "row_id": cell["row_id"], "label": cell["row_label"],
                    "resolved": cell["resolved_row_label"], "cells": {},
                })
                row["cells"][int(cell["column_index"])] = {
                    "label": cell["resolved_column_label"] or cell["column_label"],
                    "value": cell["raw_value"],
                }

    def rows(self, *locations):
        return [self.source[f"{DOC}::p{page}::r{row}"] for page, row in locations]

    def assemble(self, number, rows, states=None, panels=None):
        headers, body = assemble_room_panels(
            number, rows, schema(number),
            states if states is not None else self.states,
            panels if panels is not None else self.panels)
        return [dict(zip(headers, row)) for row in body]

    def test_numeric_headings_do_not_hide_label_leaders(self):
        # PDF p16 Police Barracks: four structural dots precede rooms1.
        rows = self.assemble(10, self.rows((16, 15), (17, 15)))
        barracks = next(row for row in rows if row["dwelling_type"] == "Police Barracks")
        self.assertEqual([barracks[f"rooms_{i}"] for i in range(1, 12)],
                         ["2", "4", "6", "5", "14", "9", "5", "4", "3", "3", "1"])
        self.assertEqual(barracks["rooms_total"], "69")

    def test_truncated_leader_vector_recovers_only_printed_tail(self):
        # PDF p44 Other Stone, y443–453: proposal ends at inmates8;
        # the source grid independently prints inmates9/10/11 = 3/2/2.
        stone = next(row for row in self.assemble(24, self.rows((44, 20), (45, 20)))
                     if row["wall_material"] == "Stone"
                     and row["dwelling_class"] == "Dwellings Other Than Private")
        self.assertEqual([stone[f"inmates_{i}"] for i in range(1, 12)],
                         ["2", "1", "5", "6", "2", "1", "3", "5", "3", "2", "2"])

    def test_sparse_offsets_follow_pdf_not_private_other_difference(self):
        # PDF p32 Other Total at y569: two leader marks, eleven actual bins.
        rows = self.assemble(17, self.rows((32, 28), (33, 30)))
        total = next(row for row in rows if row["wall_material"] == "Total"
                     and row["dwelling_class"] == "Dwellings Other Than Private")
        self.assertEqual([total[f"rooms_{i}"] for i in range(1, 12)],
                         ["13", "26", "62", "154", "172", "169", "142", "159", "139", "139", "98"])

    def test_compressed_facing_y_does_not_pair_stone_with_concrete(self):
        # PDF pp24–25 All: p25's candidate Concrete y635.6 is nearer
        # p24 Stone y633.92, but printed Concrete is a different category.
        rows = self.assemble(13, self.rows((24, 33), (24, 34), (24, 35),
                                          (25, 36), (25, 37), (25, 38)))
        by_material = {row["wall_material"]: row for row in rows
                       if row["dwelling_class"] == "All Dwellings"}
        self.assertEqual(by_material["Stone"]["rooms_1"], "174")
        self.assertEqual(by_material["Stone"]["rooms_total"], "9,980")
        self.assertEqual(by_material["Concrete"]["rooms_1"], "6")
        self.assertEqual(by_material["Concrete"]["rooms_total"], "907")

    def test_right_panel_successor_labels_are_not_category_evidence(self):
        # PDF p49 Private: Concrete84, Iron10,109, Wood20,611;
        # candidate r8 labels the printed Iron vector as Concrete.
        rows = self.assemble(26, self.rows((48, 6), (48, 7), (48, 8),
                                          (49, 7), (49, 8), (49, 9)))
        by_material = {row["wall_material"]: row for row in rows
                       if row["dwelling_class"] == "Private Dwellings"}
        self.assertEqual(by_material["Concrete"]["inmates_total"], "84")
        self.assertEqual(by_material["Iron"]["inmates_total"], "10,109")
        self.assertEqual(by_material["Wood"]["inmates_total"], "20,611")

    def test_printed_total_without_candidate_label_is_retained(self):
        # PDF pp46–47 Other Total: label omitted from both candidates.
        rows = self.assemble(25, self.rows((46, 31), (47, 30)))
        total = next(row for row in rows if row["wall_material"] == "Total"
                     and row["dwelling_class"] == "Dwellings Other Than Private")
        self.assertEqual(total["inmates_1"], "56")
        self.assertEqual(total["inmates_total"], "2,071")


    def test_source_concrete_total_cannot_be_overwritten_with_39(self):
        rows = self.assemble(18, self.rows((34, 28), (35, 26)))
        concrete = next(row for row in rows if row["wall_material"] == "Concrete"
                        and row["dwelling_class"] == "All Dwellings")
        # PDF p35 x365–378/y456–467 visibly prints89, not a residual inference.
        self.assertEqual(concrete["rooms_total"], "89")

    def test_affected_private_inmate_cells_keep_source_coordinates(self):
        rows = self.assemble(29, self.rows((53, 25), (53, 29)))
        by_material = {row["wall_material"]: row for row in rows
                       if row["dwelling_class"] == "Private Dwellings"}
        self.assertEqual(by_material["Stone"]["inmates_13"], "1")
        self.assertEqual(by_material["Stone"]["inmates_total"], "30")
        self.assertEqual(by_material["Wood"]["inmates_14"], "2")
        self.assertEqual(by_material["Wood"]["inmates_total"], "183")

    def test_unidentified_vector_is_not_merged_into_nearest_label(self):
        rows = [{"page": 24, "y": 633.92, "row_id": "unidentified", "label": "", "resolved": "",
                 "cells": {1: {"label": "1", "value": "174"}}},
                {"page": 25, "y": 635.6, "row_id": "concrete", "label": "Concrete", "resolved": "",
                 "cells": {11: {"label": "Total", "value": "907"}}}]
        body = self.assemble(13, rows, panels={24: [(608.0, "All Dwellings")],
                                             25: [(601.0, "All Dwellings")]})
        unknown = next(row for row in body if not row["wall_material"])
        concrete = next(row for row in body if row["wall_material"] == "Concrete")
        self.assertEqual(unknown["rooms_1"], "174")
        self.assertEqual(unknown["rooms_total"], "")
        self.assertEqual(concrete["rooms_1"], "")
        self.assertEqual(concrete["rooms_total"], "907")

    def test_repeated_private_house_categories_join_within_printed_state(self):
        # PDF pp18–19 prints Victoria at y143 and South Australia at y597.
        # The repeated category must not borrow the other state's total.
        rows = self.assemble(11, self.rows((18, 2), (19, 5), (18, 35), (19, 45)))
        houses = {row["state"]: row for row in rows if row["dwelling_type"] == "Private House"}
        self.assertEqual(houses["Victoria"]["rooms_1"], "9,347")
        self.assertEqual(houses["Victoria"]["rooms_total"], "261,977")
        self.assertEqual(houses["South Australia"]["rooms_1"], "3,053")
        self.assertEqual(houses["South Australia"]["rooms_total"], "80,990")

    def test_hospital_and_charitable_institution_are_distinct_printed_categories(self):
        rows = [{"page": 16, "y": 307.19, "row_id": "charitable", "resolved": "",
                 "label": "Charitable Institution (other than Hospital)",
                 "cells": {1: {"label": "1", "value": "21"}}},
                {"page": 17, "y": 307.0, "row_id": "hospital", "resolved": "",
                 "label": "Hospital", "cells": {11: {"label": "Total", "value": "1,126"}}}]
        body = self.assemble(10, rows)
        charitable = next(row for row in body if row["dwelling_type"].startswith("Charitable"))
        hospital = next(row for row in body if row["dwelling_type"] == "Hospital")
        self.assertEqual(charitable["rooms_total"], "")
        self.assertEqual(hospital["rooms_1"], "")
        self.assertEqual(hospital["rooms_total"], "1,126")

    def test_wrapped_charitable_label_does_not_duplicate_hospital(self):
        # p16/p17 r12's final "Hospital)" is a continuation of Charitable,
        # while r11 is the separate Hospital immediately above it.
        body = self.assemble(10, self.rows((16, 11), (17, 11), (16, 12), (17, 12)))
        hospitals = [row for row in body if row["dwelling_type"] == "Hospital"]
        charitable = [row for row in body if row["dwelling_type"].startswith("Charitable")]
        self.assertEqual(len(hospitals), 1)
        self.assertEqual(len(charitable), 1)
        self.assertEqual(charitable[0]["rooms_total"], "431")
        self.assertEqual(charitable[0]["rooms_1"], "21")

    def test_lost_leading_cell_keeps_remaining_bins_in_their_source_columns(self):
        original = self.rows((24, 33))[0]
        intact = next(row for row in self.assemble(13, [original])
                      if row["wall_material"] == "Stone" and row["dwelling_class"] == "All Dwellings")
        truncated = dict(original, cells={
            column - 1: cell for column, cell in original["cells"].items() if column > 1
        })
        shifted = next(row for row in self.assemble(13, [truncated])
                       if row["wall_material"] == "Stone" and row["dwelling_class"] == "All Dwellings")
        self.assertEqual(shifted["wall_material"], "Stone")
        for field in (f"rooms_{i}" for i in range(2, 12)):
            self.assertEqual(shifted[field], intact[field])

    def test_header_height_proposal_recovers_its_unique_printed_row(self):
        # p51 r1 is the Private/Stone vector proposed at y52.8 instead of
        # its physical y201 baseline. Its distinct digit vector locates it.
        body = self.assemble(27, self.rows((51, 1)))
        stone = next(row for row in body if row["wall_material"] == "Stone"
                     and row["dwelling_class"] == "Private Dwellings")
        self.assertEqual(stone["inmates_12"], "10")
        self.assertEqual(stone["inmates_total"], "1,575")


    def test_sparse_federal_police_row_does_not_become_a_second_military_row(self):
        body = self.assemble(11, self.rows((20, 46), (21, 53), (20, 47), (21, 54)))
        military = [row for row in body if row["state"] == "Federal Territory"
                    and row["dwelling_type"] == "Military and Naval Establishment"]
        police = [row for row in body if row["state"] == "Federal Territory"
                  and row["dwelling_type"] == "Police Station and Quarters"]
        self.assertEqual(len(military), 1)
        self.assertEqual(len(police), 1)
        self.assertEqual(military[0]["rooms_total"], "4")
        self.assertEqual(police[0]["rooms_5"], "1")
        self.assertEqual(police[0]["rooms_total"], "1")

    def test_shared_page_cutovers_apply_to_both_panels(self):
        for page, boundary, earlier in ((16, 459, 10), (34, 601, 18), (36, 425, 19),
                                       (50, 639, 27), (52, 423, 28)):
            for panel in (page, page + 1):
                self.assertEqual(assign_room_table(panel, boundary - 0.01, 1), earlier)
                self.assertEqual(assign_room_table(panel, boundary, 1), earlier + 1)


if __name__ == "__main__":
    unittest.main()
