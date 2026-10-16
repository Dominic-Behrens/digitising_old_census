"""Map Dwellings geography tables by printed rows and numeric grids.

Candidate column indexes include label fragments and leader dots. Their tail,
not their inherited column names, is the numeric grid. PDF word coordinates
resolve shortened grids and category identities; no arithmetic is used to
recover a quantity. Candidate digits are retained unless geometry demonstrates
that they belong to another column.
"""
from __future__ import annotations

import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

import pymupdf

PDF = (Path(__file__).resolve().parents[1] /
       "data/raw/abs_1911_census/1911_census_volume_iii_part_xiii_dwellings.pdf")
PRIVATE = "Private Dwellings"
OTHER = "Dwellings Other Than Private"
ALL = "All Dwellings"
OWNERS = "Occupied by Owners"
PURCHASERS = "Occupied by Rent Purchasers"
TENANTS = "Occupied by Tenants"
OTHER_METHOD = "Other and Unspecified Methods of Occupancy"
PLACEHOLDER = re.compile(r"^[\s.,·•—–\-„〃”'\"]*$")
FIGURE = re.compile(r"\d[\d,]*")

# Right edges of the printed quantity columns, in PDF points. They describe
# page layouts, not quantities or row-specific offsets. The 6/114 leaves have
# two different tables and therefore two different grids.
_STATE_EDGES = {
    6: (225, 260, 296, 331, 366, 402, 429, 455, 491),
    7: (190, 225, 261, 296, 332, 367, 403, 438, 474),
    8: (201, 237, 272, 307, 343, 378, 414, 449, 484),
    9: (231, 266, 302, 333, 364, 395, 428, 459, 494),
    10: (194, 233, 273, 309, 344, 379, 406, 442, 477),
    11: (201, 237, 273, 308, 343, 379, 414, 449, 485),
    12: (202, 237, 273, 308, 344, 380, 416, 451, 487),
    13: (198, 238, 278, 313, 349, 384, 420, 455, 495),
    14: (187, 228, 267, 303, 338, 374, 409, 445, 485),
    15: (216, 255, 294, 329, 365, 400, 428, 455, 495),
    110: (204, 240, 275, 311, 346, 382, 417, 455, 489),
    111: (201, 237, 272, 308, 343, 379, 414, 449, 485),
    112: (200, 236, 271, 307, 343, 378, 414, 449, 485),
    113: (195, 230, 266, 301, 336, 372, 407, 448, 478),
}
_METRO_EDGES = {
    114: (271, 306, 342, 378, 413, 449, 484),
    115: (223, 263, 307, 351, 395, 439, 483),
    116: (210, 254, 298, 342, 386, 430, 474),
    117: (217, 261, 305, 349, 393, 437, 481),
    118: (216, 260, 304, 349, 393, 437, 482),
    119: (209, 253, 297, 341, 386, 430, 474),
    120: (219, 263, 308, 352, 396, 440, 485),
    121: (214, 258, 303, 347, 391, 435, 479),
    122: (215, 259, 303, 348, 392, 437, 481),
    123: (207, 251, 296, 340, 384, 429, 473),
    124: (227, 271, 314, 359, 402, 446, 491),
    125: (219, 263, 307, 351, 395, 439, 483),
}


@lru_cache(maxsize=32)
def _page(page: int):
    with pymupdf.open(PDF) as document:
        leaf = document[page - 1]
        words = tuple(leaf.get_text("words"))
        lines = tuple((float(line["bbox"][1]),
                       " ".join(span["text"] for span in line["spans"]))
                      for block in leaf.get_text("dict")["blocks"]
                      for line in block.get("lines", []))
    return words, lines


def _edges(number: int, page: int):
    if number == 1:
        return (264, 333, 403, 473)
    if number == 50:
        return (318, 371, 424, 476)
    if number == 4 and page == 6:
        return (205, 241, 277, 312, 348, 383, 419, 455, 490)
    if number == 9 and page == 14:
        return (207, 247, 286, 322, 358, 393, 421, 448, 489)
    return (_STATE_EDGES if number < 50 else _METRO_EDGES).get(page)


def _registered_row(number: int, row: dict, count: int) -> dict:
    """Register a proposal on its printed total, not a nearby label fragment."""
    edges = _edges(number, row["page"])
    candidates = [cell["value"] for _, cell in sorted(row["cells"].items())]
    if not edges or len(candidates) < count:
        return row
    total = _normal(candidates[-1])
    anchors = [word for word in _page(row["page"])[0]
               if FIGURE.fullmatch(word[4]) and _normal(word[4]) == total
               and edges[-1] - 32 <= word[0] <= edges[-1]
               and abs((word[1] + word[3]) / 2 - row["y"]) <= 20]
    if len(anchors) != 1:
        return row
    slope = {110: 0.010, 112: 0.012}.get(row["page"], 0.0) if number == 49 else 0.0
    registered = {**row, "y": (anchors[0][1] + anchors[0][3]) / 2,
                  "baseline_slope": slope, "baseline_x": (anchors[0][0] + anchors[0][2]) / 2}
    if number in {49, 56} and (
            _category(number, row, "weekly_rental_value") == row["label"].strip()
            and _category(number, row, "weekly_rental_value")
            != _category(number, registered, "weekly_rental_value")):
        # Protect the original bin only when its other printed figures also
        # corroborate the proposal; a label alone can belong to a fragment.
        source = _printed_values(number, row)
        if all(i in source and _normal(candidates[-count + i]) == _normal(source[i])
               for i in range(count - 1)):
            return row
    return registered


def _nearby_words(number: int, row: dict):
    edges = _edges(number, row["page"])
    if not edges:
        return (), ()
    words = _page(row["page"])[0]
    # Printed labels and figures share a baseline; candidate row_y is near
    # the centre of the glyphs rather than the PDF's top coordinate.
    nearby = [word for word in words
              if abs((word[1] + word[3]) / 2 - row["y"]
                     - row.get("baseline_slope", 0.0)
                     * ((word[0] + word[2]) / 2 - row.get("baseline_x", 0.0))) <= 4]
    return nearby, edges


def _printed_values(number: int, row: dict) -> dict[int, str]:
    words, edges = _nearby_words(number, row)
    if not edges:
        return {}
    buckets = [[] for _ in edges]
    for word in words:
        x = (word[0] + word[2]) / 2
        if x < edges[0] - 32:
            continue
        index = min(range(len(edges)), key=lambda i: abs(x - (edges[i] - 10)))
        if abs(x - (edges[index] - 10)) <= 21:
            buckets[index].append(word)
    result = {}
    for index, bucket in enumerate(buckets):
        tokens = [word[4].strip() for word in sorted(bucket, key=lambda w: w[0])]
        figures = [token for token in tokens if FIGURE.fullmatch(token)]
        if len(figures) == 1:
            result[index] = figures[0]
        elif tokens and all(PLACEHOLDER.fullmatch(token) for token in tokens):
            result[index] = ".."
    # Image-read recoveries of OCR-damaged tokens. Each is tied to the
    # printed page, row baseline and column; none is inferred from totals.
    recoveries = _source_readings()
    for table, page, lower, upper, figures in recoveries:
        if number == table and row["page"] == page and lower <= row["y"] < upper:
            result.update(figures)
    return result

def _source_readings():
    """Image-confirmed readings: physical page, row baseline and column."""
    return (
        (4, 6, 703, 711, {4: "56"}),  # Private room13, WA, x325–348
        (4, 6, 799, 807, {2: "121,753", 3: "82,108", 6: "1,194"}),  # Private Total
        (53, 116, 758, 762, {6: "8"}),  # All 200–300, total
        (53, 116, 766, 772, {0: "2", 1: "1", 2: "..", 3: ".."}),  # All 300–400
        (4, 7, 535, 540, {7: "138"}),  # All room1, FT, x428–438
        (5, 8, 565, 580, {2: "1"}),  # Other 200–300/300–400, Qld, x268–272
        (6, 9, 525, 532, {5: "10"}),  # Other Unspecified, Tas, x385–395
        (6, 9, 444, 454, {7: "1"}),  # Other Iron, FT, x453–459
        (7, 10, 753, 762, {2: "..", 3: "4", 4: "3", 5: ".."}),  # Private £8
        (7, 12, 295, 304, {7: ".."}),  # All 14s., FT printed dots
        (7, 12, 585, 595, {6: "2", 7: ".."}),  # All £3, NT/FT
        (7, 12, 665, 675, {6: "1", 7: ".."}),  # All £5, NT/FT
        (7, 12, 775, 790, {2: "125,836"}),  # All Total, registered rightmost baseline
        (7, 12, 802, 812, {2: "998"}),  # Camps, not the preceding Total
        (8, 14, 280, 287, {0: "18,788"}),  # All room11, NSW, x165–192
        (52, 115, 258, 267, {5: "269"}),  # Private room9, Hobart, x425–439
        (52, 115, 570, 578, {1: "2", 2: "2", 3: "2"}),  # Other Wagons
        (56, 123, 205, 214, {6: "2,070"}),  # Tenants 21s., total, x462–474
        (56, 123, 583, 592, {3: "4", 4: "7"}),  # Other 3s., Adelaide/Perth
        (56, 124, 272, 280, {0: "4", 1: "4", 2: "1", 3: "1", 4: "1", 5: ".."}),  # Other £5
        (56, 124, 280, 288, {0: "6", 1: "2"}),  # Other £6
        (56, 124, 288, 296, {2: "..", 3: "1"}),  # Other £8, Adelaide, x354–358
        (56, 124, 296, 305, {1: "1"}),  # Other £10+, Melbourne, x265–269
        (49, 112, 750, 760, {4: "1"}),  # Tenants £8, WA, x338–342
        (49, 112, 760, 765, {0: "2", 1: "..", 2: "..", 3: "..", 4: "..",
                             5: "..", 6: "..", 7: "..", 8: "2"}),  # Tenants £9
        (49, 112, 768, 775, {0: "2", 1: "..", 2: "1", 3: "..", 4: "..",
                             5: "..", 6: "..", 7: "..", 8: "3"}),  # Tenants £10+
    )



def _normal(value: str) -> str:
    if PLACEHOLDER.fullmatch(value):
        return "0"
    return value.replace(",", "").strip()


def _values(number: int, row: dict, count: int) -> list[str]:
    candidates = [cell["value"] for _, cell in sorted(row["cells"].items())]
    if len(candidates) >= count:
        values = candidates[-count:]
    else:
        values = candidates + [""] * (count - len(candidates))
    printed = _printed_values(number, row)
    # Two displaced nonzero tokens establish a shift. A solitary small digit
    # may instead be OCR damage (e.g. an "84" read as "1").
    displaced = sum(_normal(value) != "0" and _normal(value) != _normal(values[i])
                    and any(_normal(value) == _normal(candidate)
                            for candidate in candidates)
                    for i, value in printed.items() if i < count) >= 2
    # A correctly placed total does not validate the interior grid. A lost
    # leading quantity can shift every city while leaving that total intact.
    if len(printed) == count and Counter(map(_normal, printed.values())) == Counter(map(_normal, values)):
        displaced = any(_normal(printed[i]) != _normal(values[i]) for i in range(count))
    if displaced or len(candidates) < count:
        corrected = [""] * count
        used = set()
        for index, value in printed.items():
            if index >= count:
                continue
            matches = [i for i, candidate in enumerate(candidates)
                       if i not in used and _normal(candidate) == _normal(value)]
            if matches:
                used.add(matches[-1])
                corrected[index] = candidates[matches[-1]]
            else:
                # A clean printed token is source evidence, not a balancing
                # residual. An unreadable PDF token never enters this map.
                corrected[index] = value
        values = corrected
    for table, page, lower, upper, figures in _source_readings():
        if number == table and row["page"] == page and lower <= row["y"] < upper:
            for index, value in figures.items():
                values[index] = value
    return values


def _context(items, y):
    result = ""
    for location, value in sorted(items):
        if location > y:
            break
        result = value
    return result


@lru_cache(maxsize=32)
def _printed_headings(page: int):
    classes, methods = [], []
    for y, text in _page(page)[1]:
        canonical = re.sub(r"[^A-Z]", "", text.upper().replace("1", "T"))
        for fragment, label in (("DWELLINGSOTHERTHANPRIVATE", OTHER),
                                ("ALLDWELLINGS", ALL), ("PRIVATEDWELLINGS", PRIVATE)):
            if fragment in canonical and not re.match(r"^\s*\d", text):
                classes.append((y, label))
                break
        for fragment, label in (("OCCUPIEDBYRENTPURCHASERS", PURCHASERS),
                                ("OCCUPIEDBYOWNERS", OWNERS),
                                ("OCCUPIEDBYTENANTS", TENANTS),
                                ("OTHERANDUNSPECIFIEDMETHODS", OTHER_METHOD)):
            if fragment in canonical:
                methods.append((y, label))
                break
    # PDF page 125's Other heading is a damaged OCR run, not searchable
    # text. Its printed location is between the Private Total (y556.6)
    # and Other Stone (y576.9); no quantity is recovered by this anchor.
    if page == 125:
        classes.append((564.0, OTHER))
    return tuple(sorted(classes)), tuple(sorted(methods))


def _category(number: int, row: dict, row_field: str) -> str:
    label = (row["label"] or row.get("resolved", "")).strip()
    words, edges = _nearby_words(number, row)
    left = sorted((w for w in words if w[0] < edges[0] - 33
                   and not PLACEHOLDER.fullmatch(w[4])
                   and w[4] not in {"I", "1-", "[", "|"}), key=lambda w: w[0]) if edges else []
    printed = " ".join(w[4] for w in left)
    lower = printed.lower()
    if row_field in {"state", "metropolitan_area"}:
        return label
    if "total" in lower or label.lower().startswith("total"):
        if "population" in lower:
            return "Total Population"
        return "Total"
    if "wagons" in lower or "wagons" in label.lower():
        return "Wagons, Trains, etc."
    if "shipping" in lower:
        return "Shipping Population"
    if ("aboriginal" in lower or "aboriginal" in label.lower() or "living" in lower
            or label in {"Living", "were Living", "Half-castes were Living"}):
        return "Aboriginal Camps in which Whites or Half-castes were Living"
    if ("camps" in lower or "without dwellings" in label.lower()
            or (not label and (re.search(r"dwelling[s8]", lower) or lower.startswith("lings")))):
        return "Camps without Dwellings"
    if "unspecified" in lower or label.lower() == "unspecified":
        return "Unspecified"
    if row_field == "weekly_rental_value":
        if "under" in lower and (printed.lower().startswith("under") or printed.startswith("U ")):
            return "Under 1s."
        # Only the left-hand lower bound establishes identity. Right-hand
        # upper bounds and ditto tokens cannot advance a row by one shilling.
        currency = [w[4] for w in left if w[0] < 101]
        first = " ".join(currency)
        first = first.translate(str.maketrans({"I": "1", "l": "1", "O": "0"}))
        first = re.sub(r"^£g\b", "£8", first)
        # OCR can split a lower-bound numeral: "2 Os.", "2 18.", "2 2s.".
        # Join only its digit prefix, leaving pounds/shillings spacing intact.
        first = re.sub(r"^(\d)\s+(?=\d+[sS8B](?:[._]|\b))", r"\1", first)
        match = re.match(r"^(\d{1,2})[sS8B](?:[._]|\b)", first)
        if match:
            return match.group(1) + "s."
        joined = re.match(r"^£([1-9])(5|10|15)[sS8]", first)
        if joined:
            return f"£{joined.group(1)} {joined.group(2)}s."
        match = re.match(r"^£\s*(\d+)(?:\s+(\d+)[sS8](?:[._]|\b))?", first)
        if match:
            pounds, shillings = match.group(1), match.group(2)
            if pounds == "10" and ("over" in lower or "upwards" in lower
                                   or "and over" in label.lower()):
                return "£10 and over"
            return "£" + pounds + (" " + shillings + "s." if shillings else "")
        match = re.match(r"^(\d+)s\.", label)
        if match:
            return match.group(1) + "s."
        return label
    if row_field == "number_of_rooms":
        if "and over" in lower or "and upwards" in lower:
            return "20 and over"
        for word in left:
            if word[0] < 85 and re.fullmatch(r"[1-9]|1\d|20", word[4]):
                return "20 and over" if word[4] == "20" else word[4]
        if re.fullmatch(r"[1-9]|1\d|20", label):
            return "20 and over" if label == "20" else label
        return label
    if row_field == "room_range":
        match = re.match(r"(\d+)[—–-]+(\d+)", label or printed)
        if match:
            return f"{match.group(1)}–{match.group(2)}"
        match = re.match(r"(100|200|300|400)\b", printed or label)
        if match:
            start = int(match.group(1))
            return "400 and over" if start == 400 else f"{start} and under {start + 100}"
    if row_field == "wall_material":
        if label.lower().startswith("pis"):
            return "Pisé"
        if label.lower().startswith("bushes"):
            return "Bushes, Rushes, Spinifex, etc."
        if label.lower().startswith("ruberoid"):
            return "Ruberoid and other Compositions"
    # Multiline type labels must not become the final line ('Living',
    # 'Offices, etc.') of the printed category.
    if row_field == "dwelling_type" and label == "Offices, etc.":
        return "Caretaker's Quarters in Store, Offices, etc."
    return label or printed


def _missing_source_rows(number: int, source_rows: list[dict]) -> list[dict]:
    """Recover omitted printed rows only during a full source-table rebuild."""
    if len(source_rows) < 10 or not all(
            row["row_id"].startswith("1911_census_volume_iii_part_xiii_dwellings::")
            for row in source_rows):
        return []
    recovered = []
    if number == 4:
        # The page-6 candidate region ends at room12. Printed row-label
        # coordinates identify the remainder without assuming a count sum.
        for word in _page(6)[0]:
            if not (60 <= word[0] <= 100 and 580 < word[1] < 840):
                continue
            if not (re.fullmatch(r"[1-9]|1\d|20", word[4])
                    or word[4].lower() in {"unspecified", "total"}):
                continue
            y = (word[1] + word[3]) / 2
            if any(row["page"] == 6 and abs(row["y"] - y) < 4 for row in source_rows):
                continue
            row = {"page": 6, "y": y, "row_id": f"pdf::p6::{y:.2f}",
                   "label": word[4], "resolved": "", "cells": {}}
            values = _printed_values(number, row)
            row["cells"] = {i + 1: {"label": "", "value": values.get(i, "")}
                            for i in range(9)}
            recovered.append(row)
    if number == 58 and not any(row["page"] == 125 and 570 < row["y"] < 582
                               for row in source_rows):
        # Manual reading of PDF p125, Stone at y576.9, x190–480. The row
        # is merged into the damaged heading by the PDF OCR and entirely
        # absent from cells.csv. Values are transcribed, never calculated.
        recovered.append({
            "page": 125, "y": 576.9, "row_id": "pdf::p125::other-stone",
            "label": "Stone", "resolved": "", "cells": {
                i: {"label": "", "value": value} for i, value in enumerate(
                    ("11,723", "6,411", "382", "9,379", "2,600", "949", "31,444"), 1)}})
    return recovered


def assemble_geography_panels(number: int, source_rows: list[dict], schema,
                              panels, methods) -> tuple[list[str], list[list[str]]]:
    dimension_fields, data_fields, row_field = schema
    grouped = {}
    locations = {}
    last_method = ""
    last_class = ""
    printed_rows = source_rows + _missing_source_rows(number, source_rows)
    printed_rows = [_registered_row(number, row, len(data_fields)) for row in printed_rows]
    for row in sorted(printed_rows, key=lambda r: (r["page"], r["y"], r["row_id"])):
        if not row["cells"]:
            continue
        # Single-cell OCR fragments are duplicates of the adjacent full
        # rent row, not additional unlabeled categories.
        if len(row["cells"]) == 1 and len(data_fields) > 1:
            continue
        category = _category(number, row, row_field)
        if not category or PLACEHOLDER.fullmatch(category):
            continue
        printed_classes, printed_methods = _printed_headings(row["page"])
        dwelling_class = _context(printed_classes, row["y"])
        if not dwelling_class:
            dwelling_class = _context(panels.get(row["page"], []), row["y"]) or last_class
        method = _context(printed_methods, row["y"]) or last_method
        if not method:
            method = _context(methods.get(row["page"], []), row["y"])
        if dwelling_class:
            last_class = dwelling_class
        if method:
            last_method = method
        dimensions = {row_field: category, "dwelling_class": dwelling_class,
                      "method_of_occupancy": method}
        key = tuple(dimensions.get(field, "") for field in dimension_fields)
        values = _values(number, row, len(data_fields))
        if key in grouped and any(
                value and grouped[key][index] and _normal(value) != _normal(grouped[key][index])
                for index, value in enumerate(values, len(dimension_fields))):
            # Resolve a column-shift proposal only against a complete grid
            # corroborated by the other proposal. A one-digit disagreement
            # remains ambiguous even when the PDF OCR matches one candidate.
            source = _printed_values(number, row)
            location = (row["page"], row["y"])
            if locations.get(key) == location and len(source) == len(data_fields):
                previous = grouped[key][len(dimension_fields):]
                old_matches = all(value and _normal(value) == _normal(source[i])
                                  for i, value in enumerate(previous))
                new_matches = all(value and _normal(value) == _normal(source[i])
                                  for i, value in enumerate(values))
                disputed = values if old_matches else previous
                source_counts = Counter(_normal(value) for value in source.values() if _normal(value) != "0")
                disputed_counts = Counter(_normal(value) for value in disputed if _normal(value) != "0")
                shifted = disputed_counts <= source_counts and any(
                    _normal(value) != "0" and _normal(value) != _normal(source[i])
                    and _normal(value) in source_counts for i, value in enumerate(disputed)
                )
                if old_matches and not new_matches and shifted:
                    continue
                if new_matches and not old_matches and shifted:
                    grouped[key] = [dimensions.get(field, "") for field in dimension_fields] + values
                    continue
            # A contradictory proposal is not resolved by first-value
            # precedence. Preserve duplicate dimensions for ambiguity checks.
            key += (row["page"], row["y"], row["row_id"])
        if key not in grouped:
            grouped[key] = [dimensions.get(field, "") for field in dimension_fields] + values
            locations[key] = (row["page"], row["y"])
        else:
            existing = grouped[key]
            for index, value in enumerate(values, len(dimension_fields)):
                if not existing[index] and value:
                    existing[index] = value
    return dimension_fields + data_fields, list(grouped.values())
