"""Assemble Table 68 from its printed grid on physical PDF pages 183–199.

Candidate rows supply council aliases and vertical anchors, not column indices:
leaders were mistaken for four extra numeric columns on several pages. Grid
coordinates and image-backed exceptions below refer to the unchanged raw PDF.
Area and density strings retain the printed units in an explicit area_unit
dimension; no conversion, balancing, or calculated replacement is performed.
"""
from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import defaultdict
from pathlib import Path
import re

import pymupdf

PDF = Path(__file__).resolve().parents[1] / "data/raw/abs_1911_census/1911_census_volume_iii_part_xiii_dwellings.pdf"

# Left name/area rule, followed by the eight numeric cell right edges.
GRID = {
    183: (212, 248, 284, 320, 355, 390, 425, 461, 500),
    184: (205, 241, 276, 312, 348, 383, 419, 454, 492),
    185: (213, 248, 284, 320, 355, 391, 426, 461, 500),
    186: (204, 240, 275, 311, 347, 382, 418, 454, 491),
    187: (232, 268, 303, 339, 375, 410, 446, 482, 518),
    188: (191, 227, 263, 299, 334, 370, 405, 441, 479),
    189: (233, 269, 304, 340, 375, 411, 446, 482, 519),
    190: (191, 227, 263, 298, 334, 370, 405, 441, 480),
    191: (217, 253, 289, 325, 360, 396, 432, 468, 507),
    192: (204, 240, 276, 311, 347, 382, 418, 453, 491),
    193: (214, 247, 287, 322, 358, 394, 429, 465, 503),
    194: (206, 242, 278, 313, 349, 385, 420, 456, 496),
    195: (199, 235, 271, 306, 342, 378, 413, 449, 488),
    196: (217, 253, 289, 324, 360, 396, 431, 467, 504),
    197: (198, 234, 270, 305, 341, 376, 412, 447, 486),
    198: (222, 260, 294, 330, 365, 400, 435, 472, 510),
    199: (205, 241, 276, 312, 347, 383, 418, 454, 495),
}
SLOPES = {185: .006, 186: .003, 187: -.002, 189: -.005, 190: -.005, 193: .002, 196: .002}

# Printed section cutovers, including summary panels and the mid-page state
# change on page 191. These avoid damaged/split OCR headings and state leakage.
SECTIONS = {
    183: ((0, "New South Wales", "Municipalities"),),
    184: ((0, "New South Wales", "Municipalities"),),
    185: ((0, "New South Wales", "Municipalities"), (715, "New South Wales", "Shires")),
    186: ((0, "New South Wales", "Shires"),),
    187: ((0, "New South Wales", "Shires"), (720, "New South Wales", "Summary")),
    188: ((0, "Victoria", "Cities, Towns and Boroughs"),),
    189: ((0, "Victoria", "Shires"),),
    190: ((0, "Victoria", "Shires"),),
    191: ((0, "Victoria", "Shires"), (325, "Victoria", "Summary"),
          (450, "Queensland", "Cities"), (555, "Queensland", "Towns"),
          (795, "Queensland", "Cities and Towns")),
    192: ((0, "Queensland", "Shires"),),
    193: ((0, "Queensland", "Shires"), (725, "Queensland", "Summary")),
    194: ((0, "South Australia", "Corporations"), (510, "South Australia", "District Councils")),
    195: ((0, "South Australia", "District Councils"),),
    196: ((0, "South Australia", "District Councils"), (700, "South Australia", "Summary")),
    197: ((0, "Western Australia", "Municipalities"), (660, "Western Australia", "Road Board Districts")),
    198: ((0, "Western Australia", "Road Board Districts"),),
    199: ((0, "Western Australia", "Road Board Districts"), (490, "Western Australia", "Summary")),
}

# Page 199's row names were lost from the candidate CSV; the scan explicitly
# supplies these five summary rows. The 555.21 candidate is an OCR rule fragment.
SUMMARY_NAMES = {511.75: "Municipalities", 527.83: "Road Districts", 551.83: "TOTAL", 560.0: "Shipping", 593.24: "TOTAL POPULATION"}
NAME_CORRECTIONS = {(183, "Ermington and Ryde"): "Ermington and Rydalmere", (196, "Onauga"): "Onaunga"}

# Zero-based numeric column exceptions read from row images. In particular,
# misplaced OCR bounding boxes at Tenterfield/Terania and Warrnambool/Werribee
# cannot be repaired by widening row tolerance without borrowing adjacent digits.
CELL_CORRECTIONS = {
    183: {
        "Bowral": {6: ".110"}, "Brewarrina": {6: ".011"},
        "Cabramatta and Canley Vale": {7: "4.51"}, "Cowra": {6: ".114"}, "Glebe": {0: "521"},
    },
    184: {
        "Grafton, South": {1: "610"}, "Kempsey": {7: "5.04"}, "Lambton, New": {2: "894"},
        "Lane Cove": {2: "1,667"}, "Mosman": {1: "5,836"}, "Narrandera": {2: "1,163", 6: ".306"},
        "Narromine": {2: "628"}, "Orange": {0: "640"}, "Orange, East": {0: "685"},
        "Leichhardt": {5: "4,909"},
    },
    185: {
        "Sydney": {5: "18,463"}, "Ulladulla": {6: ".011"}, "Wickham": {7: "4.79"},
        "TOTAL, MUNICIPALITIES": {0: "1,916,800", 3: "1,041,759"}, "Ashford": {6: ".255"},
    },
    186: {"Cessnock": {5: "4,312"}, "Colo": {4: "3.46"}, "Macleay": {3: "6,679"}},
    187: {"Tenterfield": {2: "2,230"}, "Terania": {0: "347", 2: "2,421"}, "Tintenbar": {6: "5.725"}, "Sutherland": {6: "4.535"}},
    188: {
        "Essendon": {1: "11,037"}, "Footscray": {1: "11,906"}, "Kew": {3: "11,152"},
        "Majorca": {4: ".11"}, "Portland": {2: "1,114"}, "Warrnambool": {6: ".287"},
        "Williamstown": {6: "1.152"},
    },
    189: {"Braybrook": {4: "25.79"}, "Bulla": {7: "7.64"}},
    190: {"Ripon": {2: "2,010"}, "Towong": {1: "3,566"}},
    191: {
        "Warrnambool": {2: "4,147"}, "Werribee": {2: "1,703"},
        "TOTAL, SHIRES": {0: "86,856.25"}, "Shires": {0: "86,856.25"},
        "Whole State": {4: "14.91", 5: "272,683"}, "Gayndah": {6: ".011", 7: "4.57"},
        "Goondiwindi": {1: "734"}, "Hamilton": {1: "2,334"},
        "Rockhampton": {0: "15,082.67", 1: "7,376"},
        "TOTAL, CITIES AND TOWNS": {1: "113,490"},
    },
    192: {"Adavale": {0: "17,430"}, "Croydon": {0: "11,140"}},
    193: {
        "Middle Ridge": {0: "12.75"}, "Pioneer": {6: "1.164"}, "Proserpine": {1: "1,118"},
        "Rawbelle": {6: ".110"}, "Southport": {0: "44.75", 2: "1,010"},
        "Stanthorpe": {1: "1,511"}, "Tarampa": {2: "3,115"}, "Tingalpa": {0: "120"},
        "Waggamba": {2: "588"}, "Wangaratta": {4: ".11"},
        "Noosa": {3: "2,008"}, "Torres": {2: "638"}, "Walloon": {1: "2,211"},
        "Cities and Towns": {0: "233,280", 1: "113,490"}, "Shires": {0: "669894.5"},
        "Whole State": {0: "670,500"}, "Total Population": {3: "605,813", 7: ".."},
    },
    194: {
        "Adelaide": {4: "11.19"}, "Edithburgh": {6: ".112"}, "Hindmarsh": {3: "11,335"},
        "Laura": {4: ".66"}, "Petersburg": {7: "5.11"}, "Port Wakefield": {6: ".111"},
        ("Corporations", "Burra"): {7: "4.46"}, ("District Councils", "Burra"): {7: "4.47"},
        "Crafers": {4: "110.18"},
    },
    195: {"Echunga": {3: "1,332"}, "Gilbert": {7: "4.96"}, "Hall": {7: "4.60"}, "Hutt and Hill Rivers": {5: "111"}, "Kanyaka": {7: "5.12"}},
    196: {
        "Rhynie": {1: "118"}, "Streaky Bay": {6: ".114"}, "Tatiara": {1: "1,114"},
        "Tungkillo": {0: "118"}, "Yatala, South": {4: "112.17"}, "Yongala": {7: "5.11"},
        "TOTAL, DISTRICT COUNCILS": {1: "112,484"}, "District Councils": {1: "112,484"},
    },
    197: {"Total": {4: "1.91"}, "Armadale-Kelmscott": {6: "1.653"}},
    198: {
        "Bulong": {0: "1132.76"}, "Capel": {4: "4.11"}, "Coolgardie": {0: "11,749"},
        "Coolgardie, North-East": {2: "110", 5: "238"}, "Cottesloe Beach": {0: "1.25"},
        "Dandaragan": {2: "110"}, "Esperance": {5: "113"}, "Geraldton": {7: "3.95"},
        "Drakesbrook": {6: ".834"},
        "Goomalling": {7: "3.11"}, "Greenhills": {5: "442"}, "Meckering": {3: "2,115"},
        "Mount Margaret": {6: ".018", 7: "2.33"}, "Northampton": {0: "10,700"}, "Nullagine": {0: "93,438"},
        "Peppermint Grove": {7: "5.11"}, "Plantagenet": {6: ".112"},
    },
    199: {"Port Hedland": {2: "105"}, "Shark Bay": {4: ".04", 7: "4.04"}, "Tableland": {1: "111"}, "Wagin": {0: "625"}, "Wanneroo": {2: "71"}, "York": {2: "491"}},
}

# Physical p193, Tinaroo y553, x429–465 visibly prints "3,279" with a comma,
# unlike adjacent decimal densities. Retain this printed inconsistency. On
# p195, Dublin y218, x342–378 prints a damaged final glyph in "5.3)": neither
# its digit nor Tinaroo's punctuation is reconstructed from persons/area.

# Merged OCR tokens crossing the rules in these summaries are replaced by direct
# full-row image observations, not totals calculated from component councils.
ROW_CORRECTIONS = {
    (187, "Municipalities"): ("1,916,800", "514,873", "526,886", "1,041,759", "*.54", "206,312", "*.108", "5.05"),
    (187, "Shires"): ("181,201", "323,759", "255,204", "578,963", "3.20", "120,517", ".665", "4.80"),
    (187, "Not Incorporated"): ("125,264", "11,589", "6,372", "17,961", ".14", "4,147", ".033", "4.33"),
    (187, "Whole State"): ("309,460", "850,221", "788,462", "1,638,683", "5.30", "330,976", "1.070", "4.95"),
    (187, "Shipping"): ("..", "7,477", "574", "8,051", "..", "..", "..", ".."),
    (187, "Total, Population"): ("..", "857,698", "789,036", "1,646,734", "..", "..", "..", ".."),
    (191, "Shipping"): ("..", "4,082", "723", "4,805", "..", "..", "..", ".."),
    (191, "TOTAL POPULATION"): ("..", "655,591", "659,960", "1,315,551", "..", "..", "..", ".."),
    (199, "Municipalities"): ("75,430", "73,176", "70,632", "143,808", "*1.91", "31,370", "*.416", "4.58"),
    (199, "Road Districts"): ("975802.14", "82,543", "48,747", "131,290", ".13", "37,500", ".038", "3.50"),
    (199, "Shipping"): ("..", "5,846", "1,170", "7,016", "..", "..", "..", ".."),
    (199, "TOTAL POPULATION"): ("..", "161,565", "120,549", "282,114", "..", "..", "..", ".."),
}


def _rows(source_rows):
    pages = defaultdict(list)
    for source in sorted(source_rows, key=lambda row: (row["page"], row["y"], row["row_id"])):
        page = source["page"]
        if page not in GRID:
            continue
        label = (source["label"] or source["resolved"]).strip()
        if not label and page == 199:
            label = next((name for y, name in SUMMARY_NAMES.items() if abs(source["y"] - y) < .1), "")
        if not label:
            continue
        label = NAME_CORRECTIONS.get((page, label), label)
        prior = pages[page]
        # Williamstown is printed once: the second candidate is its displaced
        # numeral/leader OCR, not another council or a second panel.
        if prior and prior[-1][1] == label and source["y"] - prior[-1][0] < 5:
            continue
        prior.append((source["y"], label))
    return pages


# These sections print Acres; shires, district councils and road districts
# print Square miles. Summary panels explicitly repeat Acres on their urban
# first row and sq. miles on the next row, which carries through the state total.
ACRE_SECTIONS = frozenset({
    "Municipalities", "Cities, Towns and Boroughs", "Cities and Towns",
    "Cities", "Towns", "Corporations",
})


def assemble_council_panels(source_rows, schema, states, area_types):
    """Return the supplied schema and one row per printed council/summary row."""
    dimension_fields, data_fields, row_field = schema
    if len(data_fields) != 8:
        raise ValueError("Table 68 requires its eight printed numeric fields")
    body = []
    with pymupdf.open(PDF) as document:
        for page_no, rows in sorted(_rows(source_rows).items()):
            grid = GRID[page_no]
            ys = [y for y, _ in rows]
            cells = [[[] for _ in data_fields] for _ in rows]
            slope = SLOPES.get(page_no, 0)
            for block in document[page_no - 1].get_text("rawdict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        for char in span["chars"]:
                            x0, y0, x1, y1 = char["bbox"]
                            x = (x0 + x1) / 2
                            col = bisect_right(grid, x) - 1
                            if not 0 <= col < len(data_fields) or not grid[col] + 2 < x < grid[col + 1] - 2:
                                continue
                            cy = (y0 + y1) / 2 - slope * (x - 100)
                            pos = bisect_left(ys, cy)
                            index = min((i for i in (pos - 1, pos) if 0 <= i < len(rows)), key=lambda i: abs(ys[i] - cy))
                            if abs(ys[index] - cy) < 3.6:
                                cells[index][col].append((x0, char["c"]))
            for (y, council), raw in zip(rows, cells):
                values = [re.sub(r"\s+", "", "".join(c for _, c in sorted(cell))).strip() for cell in raw]
                _, state, area_type = next(section for section in reversed(SECTIONS[page_no]) if section[0] <= y)
                corrections = CELL_CORRECTIONS.get(page_no, {})
                # Burra occurs in both printed sections on physical p194.
                # A page/name override must not overwrite the corporation
                # reading (4.46) with the district council reading (4.47).
                for col, value in corrections.get((area_type, council), corrections.get(council, {})).items():
                    values[col] = value
                if (page_no, council) in ROW_CORRECTIONS:
                    values = list(ROW_CORRECTIONS[page_no, council])
                # The two page-199 TOTAL lines are distinct printed rows, not
                # duplicate OCR; only the second is the whole-state summary.
                if page_no == 199 and council == "TOTAL":
                    values = (["975802.14", "82,543", "48,747", "131,290", ".13", "37,500", ".038", "3.50"] if y < 490 else
                              ["975,920", "155,719", "119,379", "275,098", ".28", "68,870", ".071", "3.99"])
                unit_section = council if area_type == "Summary" else area_type
                area_unit = "Acres" if unit_section in ACRE_SECTIONS else "Square miles"
                dimensions = {"state": state, "area_type": area_type, row_field: council, "area_unit": area_unit}
                body.append([dimensions.get(field, "") for field in dimension_fields] + values)
    return dimension_fields + data_fields, body
