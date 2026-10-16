"""Map Table 67's printed numeric grid without trusting candidate column indices.

Inputs: unchanged Dwellings PDF and source-region rows supplied by the exporter.
Output: county rows; shared Outside Counties area/densities are separate metadata.
No count is calculated from a total or a neighbouring county.
"""
from __future__ import annotations

from bisect import bisect_right
from functools import lru_cache
from pathlib import Path
import re

import pymupdf

PDF = Path(__file__).resolve().parents[1] / "data/raw/abs_1911_census/1911_census_volume_iii_part_xiii_dwellings.pdf"
# Physical rules, with a virtual split between the final shilling/pence figures.
GRIDS = {
    178: (104.8, 134.4, 163.9, 193.6, 223.1, 252.6, 282.3, 311.9, 341.4, 371.3, 401.2, 430.7, 460.3, 475.2, 491.0),
    179: (94.5, 124.2, 154.2, 184.0, 213.3, 243.3, 272.8, 302.8, 332.3, 360.4, 388.7, 418.9, 448.9, 470.0, 490.0),
    180: (127.6, 157.1, 188.7, 217.7, 247.3, 277.3, 306.3, 336.4, 366.3, 395.7, 425.3, 454.7, 484.5, 501.0, 520.0),
    181: (114.5, 144.3, 173.8, 203.4, 232.9, 262.7, 292.2, 321.7, 351.3, 380.9, 410.7, 440.3, 469.9, 486.0, 506.0),
    182: (127.0, 156.4, 185.9, 215.7, 245.2, 274.9, 304.5, 334.3, 363.6, 393.7, 423.5, 453.0, 482.9, 499.0, 519.0),
}
GROUP_NAMES = frozenset({"Northern Division", "North Eastern Div.", "North Western Div.", "Western Division"})
GROUP_FIELDS = ("area_group_square_miles", "area_group_persons_per_square_mile", "area_group_occupied_dwellings_per_square_mile")

# Physical-page, state and county scoped image readings. Numeric indices follow
# the fourteen printed fields; commas/precision below are visible source marks,
# not digits recovered from a density or count residual.
CELL_CORRECTIONS = {
    (178, "New South Wales", "Gipps"): {9: "4.00"},  # y740, x371–401
    (178, "New South Wales", "Hawes"): {13: "5"},  # y807, x475–491
    (179, "New South Wales", "Landsborough"): {6: ".."},  # y411, x283–303
    (179, "New South Wales", "Woore"): {12: "..", 13: ".."},  # y759, x449–490
    (182, "Western Australia", "North West"): {0: "117,344"},  # y168, x127–156
    (182, "Tasmania", "Brighton"): {8: "2.354"},  # y326, x364–394
    (182, "Tasmania", "Esperance"): {0: "2235.94"},  # y381, x127–156
    (182, "Tasmania", "Longford"): {9: "6.81"},  # y502, x394–424; printed discrepancy
    (182, "Northern Territory", "Disraeli"): {0: "3,500"},  # y697, x127–156
    (182, "Federal Territory", "Jervis Bay"): {8: ".214"},  # y795, x364–394
}

# Physical p182, Western Australia summary, y273.6, x156–245: the complete
# Shipping row is absent from both candidate rows and searchable PDF text.
ROW_CORRECTIONS = {
    (182, "Western Australia", "Shipping"):
        ("..", "5,846", "1,170", "7,016", "..", "..", "..", "..", "..", "..", "..", "..", "..", ".."),
}


def _number_token(value):
    value = str(value).strip().replace(",", "").replace(" ", "")
    return value if re.fullmatch(r"[0-9]+(?:\.[0-9]*)?|\.[0-9]+", value) else None


@lru_cache(maxsize=5)
def _characters(page):
    with pymupdf.open(PDF) as document:
        blocks = document[page - 1].get_text("rawdict")["blocks"]
    return tuple((float(char["bbox"][0]), (char["bbox"][0] + char["bbox"][2]) / 2,
                  (char["bbox"][1] + char["bbox"][3]) / 2, char["c"])
                 for block in blocks for line in block.get("lines", [])
                 for span in line["spans"] for char in span["chars"])


def _printed_cells(page, y):
    grid = GRIDS[page]
    cells = [[] for _ in range(14)]
    for x0, x, cy, char in _characters(page):
        col = bisect_right(grid, x) - 1
        if 0 <= col < 14 and grid[col] + 1.0 < x < grid[col + 1] - 1.0 and abs(cy - y) < 2.8:
            cells[col].append((x0, char))
    return [re.sub(r"\s+", "", "".join(char for _, char in sorted(cell))) for cell in cells]


def _aligned_values(row, printed):
    candidates = [cell["value"].strip() for _, cell in sorted(row["cells"].items())]
    numbers = [_number_token(value) for value in printed]
    candidate_numbers = [_number_token(value) for value in candidates]
    # A token must be unique in both readings to anchor an ordered run:
    # Millewa's private/total 19 must not both target the sole OCR 19.
    # Interior gutter/group tokens can change the offset of each run.
    anchors = []
    for index, token in enumerate(candidate_numbers):
        if token is not None and numbers.count(token) == 1 and candidate_numbers.count(token) == 1:
            anchors.append((index, numbers.index(token)))
    paths = []
    for index, col in anchors:
        previous = [path for path in paths if path[-1][0] < index and path[-1][1] < col]
        paths.append(max(previous, key=len, default=[]) + [(index, col)])
    path = max(paths, key=len, default=[])
    if len(path) < 3:
        values = candidates[:14] + [""] * max(0, 14 - len(candidates))
    else:
        values = [""] * 14
        boundaries = [(-1, -1)] + path + [(len(candidates), 14)]
        for (lower_index, lower_col), (upper_index, upper_col) in zip(boundaries, boundaries[1:]):
            width = upper_col - lower_col - 1
            run = candidates[lower_index + 1:upper_index]
            # Extra leading marks or repeated group figures have no slot.
            # Right-align shorter prefixes; preserve interior reading strings.
            run = run[-width:] if width else []
            start = upper_col - len(run)
            values[start:upper_col] = run
        for index, col in path:
            values[col] = candidates[index]
    for col, source in enumerate(printed):
        candidate = values[col]
        token = _number_token(candidate)
        misplaced = token is not None and token != numbers[col] and token in (numbers[:col] + numbers[col + 1:])
        absent = not candidate or not re.search(r"[0-9A-Za-z]", candidate)
        # Rule fragments and damaged PDF OCR do not supersede candidate marks
        # or an explicitly unreadable source character (Lowan's shillings).
        if numbers[col] is not None and (absent or misplaced):
            values[col] = source
    return values


def _printed_baseline(page, y, label):
    """Locate the named printed row before recovering its numeric cells."""
    wanted = re.sub(r"[^a-z0-9]", "", label.lower())
    chars = [part for part in _characters(page) if part[1] < GRIDS[page][0] - 1]
    matches = []
    for baseline in sorted({round(part[2], 2) for part in chars if abs(part[2] - y) <= 12}):
        text = "".join(part[3] for part in sorted(chars) if abs(part[2] - baseline) < 2.8)
        if re.sub(r"[^a-z0-9]", "", text.lower()) == wanted:
            matches.append(baseline)
    return min(matches, key=lambda baseline: abs(baseline - y)) if matches else y


def _context(items, y):
    return next((value for start, value in reversed(sorted(items)) if start <= y), "")


def assemble_county_measures(source_rows, schema, states, area_types):
    dimensions, fields, row_field = schema
    source_rows = list(source_rows)
    western_summary = [row for row in source_rows if row["page"] == 182 and 260 <= row["y"] <= 286]
    labels = {(row["label"] or row["resolved"]).strip().upper() for row in western_summary}
    if "WHOLE STATE" in labels and "TOTAL POPULATION" in labels and "SHIPPING" not in labels:
        # Require the actual summary panel, not merely another p182 county
        # supplied by an isolated consumer. The added values are image reads.
        values = ROW_CORRECTIONS[182, "Western Australia", "Shipping"]
        source_rows.append({
            "page": 182, "y": 273.6, "row_id": "pdf::p182::western-australia-shipping",
            "label": "Shipping", "resolved": "",
            "cells": {index: {"label": "", "value": value} for index, value in enumerate(values, 1)},
        })
    body = []
    seen = {}
    for row in sorted(source_rows, key=lambda r: (r["page"], r["y"], r["row_id"])):
        page, y = row["page"], row["y"]
        label = (row["label"] or row["resolved"]).strip()
        if page not in GRIDS or not label or not row["cells"]:
            continue
        y = _printed_baseline(page, y, label)
        state = _context(states.get(page, []), y)
        area_type = _context(area_types.get(page, []), y)
        key = state, area_type, label, page, round(y, 1)
        printed = _printed_cells(page, y)
        values = _aligned_values(row, printed)
        # These printed population-only rows have no area, dwellings, room or
        # rental readings. Do not import numeric OCR from the adjacent land
        # summary (notably both Shipping lines on physical p182).
        if label == "Shipping" or re.sub(r"[^A-Z]", "", label.upper()) == "TOTALPOPULATION":
            for col in (0, *range(4, 14)):
                values[col] = ".."
        elif label == "Outside Statistical Districts":
            values[1:] = [".."] * 13
        for col, value in CELL_CORRECTIONS.get((page, state, label), {}).items():
            values[col] = value
        if (page, state, label) in ROW_CORRECTIONS:
            values = list(ROW_CORRECTIONS[page, state, label])
        if seen.get(key) == tuple(values):
            # Overlapping crops can propose the same named physical row.
            continue
        seen[key] = tuple(values)
        group = ""
        group_values = [""] * 3
        if page == 181 and label in GROUP_NAMES:
            group = "South Australia / Outside Counties / four divisions"
            # The braces on physical p181, y610–645 span all four divisions.
            # These are published group readings, not per-division denominators.
            group_values = ["297,967", ".01", ".003"]
            for col in (0, 4, 8):
                values[col] = ""
        record = dict(zip(fields[:14], values))
        record.update(zip(GROUP_FIELDS, group_values))
        identifiers = {"state": state, "area_type": area_type, row_field: label, "area_group": group}
        body.append([identifiers.get(name, "") for name in dimensions] + [record.get(name, "") for name in fields])
    return dimensions + fields, body
