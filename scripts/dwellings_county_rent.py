"""Assemble Table 66 from its paired, printed county rental panels.

The transcription alternates between amounts, separate currency units, and
compressed rows. PDF character geometry is therefore authoritative for placement;
well-aligned candidate amounts fill OCR gaps without shifting later currencies.
"""
from __future__ import annotations

from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
import re

import pymupdf

PDF = (Path(__file__).resolve().parents[1] / "data/raw/abs_1911_census/"
       "1911_census_volume_iii_part_xiii_dwellings.pdf")
# Diagnostic provenance only; these are not workbook rows or metadata sheets.
UNMAPPABLE_CELLS: list[dict[str, str | int]] = []

# Label limits, printed data limits, and centres of the first shilling/penny
# subcolumns. The nine currency groups repeat at approximately 40 PDF points.
# Image transcriptions for p174's absent text grid and p177's fused currencies.
# Tokens are printed shillings:pence; ".." is the no-value mark, not a zero.
_IMAGE_AMOUNTS = {
    174: {
        "Maryborough": "2:8 4:2 4:3 5:2 6:9 8:1 9:11 11:8 13:1",
        "Moreton, East": "2:7 4:10 6:0 7:7 9:2 11:2 13:1 15:11 17:11",
        "Moreton, West": "2:5 3:8 4:11 6:6 7:5 9:0 10:0 11:2 13:3",
        "Mount Morgan": "2:5 4:4 6:4 8:5 9:11 11:1 12:4 14:4 17:9",
        "Nundah": "4:10 5:6 6:8 7:5 9:8 12:8 17:5 21:3 24:10",
        "Oxley": "2:9 4:8 4:6 6:11 9:0 11:0 13:8 16:5 19:9",
        "Palmer": "1:9 2:2 3:2 3:11 6:5 5:0 5:3 6:6 ..",
        "Peak Downs": "2:0 5:6 4:9 3:3 5:6 11:6 12:6 .. ..",
        "Rockhampton": "4:4 5:7 6:7 7:6 9:7 11:8 13:8 15:8 19:6",
        "St. Lawrence": "1:6 .. 2:11 4:7 6:8 5:6 .. 10:6 ..",
        "Somerset": "4:1 5:11 7:5 8:3 11:10 10:9 15:5 14:6 ..",
        "Springsure": "2:0 4:0 5:4 6:2 7:5 9:2 10:7 11:6 15:3",
        "Stanley": "2:0 3:0 4:2 5:9 7:7 9:0 10:0 12:0 13:8",
        "Stanthorpe": "1:9 3:7 4:10 6:3 8:8 10:7 12:11 12:7 17:9",
        "Taroom": "2:7 3:9 5:2 4:1 6:4 8:3 7:1 12:6 16:0",
        "Tiaro": "1:11 3:2 3:11 5:3 5:11 7:1 7:11 9:9 10:3",
        "Toowong": "4:9 6:5 6:2 7:10 10:5 13:3 16:11 19:7 25:7",
        "Toowoomba": "3:2 6:4 7:2 7:6 9:6 10:10 13:6 16:2 19:9",
        "Townsville": "3:7 5:1 6:8 8:7 10:1 11:10 14:1 16:7 18:11",
        "Warrego": "3:6 4:3 4:2 5:11 8:1 9:3 9:0 10:6 10:6",
        "Warwick": "3:11 4:10 7:5 7:9 9:10 12:4 15:9 17:11 19:10",
        "Westwood": "1:10 3:3 4:5 6:4 7:7 9:2 10:6 13:3 13:11",
        "Wide Bay": "2:4 3:8 5:1 6:2 7:5 9:8 11:4 12:8 13:8",
        "Winton": "2:5 5:11 5:11 8:11 10:10 12:5 11:5 17:3 15:8",
        "WHOLE STATE": "2:4 4:3 5:8 7:3 9:1 10:10 13:2 15:5 17:7",
    },
    177: {
        "Beverley": "16:8 .. 20:6 .. .. .. 82:6 14:6 8:3",
        "Coolgardie": "26:10 21:4 12:10 34:3 35:6 82:6 .. 5:6 10:2",
        "Coolgardie, North": "13:6 .. .. .. .. .. .. .. 5:6",
        "Esperance": ".. 8:6 7:0 20:6 .. .. .. .. 7:1",
        "Eucla": ".. .. .. .. .. .. .. .. 6:7",
        "Gascoyne": "29:6 27:2 52:6 .. 22:6 62:6 62:6 .. 11:8",
        "Katanning": "24:8 29:6 .. 42:6 62:6 .. 72:6 .. 9:10",
        "Kimberley, East": ".. .. .. .. .. .. 30:6 .. 12:7",
        "Kimberley, West": "52:6 .. 13:6 .. .. .. .. .. 16:2",
        "Magnet": "20:6 .. 31:6 .. 20:6 .. .. .. 6:6",
        "Margaret": "17:2 .. 12:6 .. .. 20:6 .. 2:6 7:1",
        "Murchison": ".. .. 30:6 .. .. .. .. .. 6:2",
        "Murchison, East": ".. .. .. .. .. .. .. .. 5:11",
        "Narrogin": "20:6 .. .. 20:6 .. 20:6 .. 18:0 9:3",
        "Northam": "21:5 31:0 36:0 34:0 25:6 .. 25:6 16:6 10:0",
        "North-West": ".. .. .. .. .. .. .. .. 8:4",
        "Phillips River": ".. .. .. .. .. .. .. .. 8:5",
        "Pingelly": "15:0 10:6 29:9 .. .. .. .. 8:0 9:0",
        "Plantagenet": "18:0 24:8 25:6 25:0 27:0 20:6 .. .. 8:2",
        "Sussex": "20:11 22:10 19:3 30:6 52:6 .. 23:0 .. 6:6",
        "Swan": "35:10 39:6 42:10 45:3 50:4 49:6 86:10 16:11 13:3",
        "Tambellup": "20:6 .. 25:6 23:0 .. .. .. .. 7:4",
        "Victoria": "24:0 35:1 30:5 18:10 52:3 31:6 52:3 10:0 9:11",
        "Wagin": "29:0 .. .. .. .. .. .. 10:6 9:3",
        "Wellington": "21:5 22:6 29:9 19:9 .. .. 23:0 40:6 7:10",
        "Yilgarn": ".. .. .. .. .. .. .. 8:0 4:11",
        "York": "19:6 22:0 19:3 20:6 25:6 .. 56:6 .. 8:9",
        "WHOLE STATE": "29:1 31:11 34:2 34:2 42:4 44:0 70:3 15:6 10:7",
        "Beaconsfield": "14:9 10:6 .. .. .. .. .. 5:6 6:5",
    },
}
# Individually checked source-image units still absent from aligned PDF text.
# Indices refer to the documented 36-field currency schema, not OCR columns.
_IMAGE_UNITS = {
    (168, "New South Wales", "Clarence"): "9:9",
    (168, "New South Wales", "Clarendon"): "9:9",
    (168, "New South Wales", "Clarke"): "7:2",
    (169, "New South Wales", "Cowper"): "32:. 33:.",
    (168, "New South Wales", "Cunningham"): "13:3",
    (169, "New South Wales", "Cunningham"): "27:6",
    (169, "New South Wales", "Darling"): "26:. 27:.",
    (168, "New South Wales", "Delalah"): "13:6",
    (169, "New South Wales", "Delalah"): "18:. 19:. 20:. 21:.",
    (169, "New South Wales", "Dowling"): "24:. 25:. 26:. 27:.",
    (169, "New South Wales", "Drake"): "24:. 25:. 26:. 27:.",
    (169, "New South Wales", "Fitzroy"): "21:1",
    (168, "New South Wales", "Gordon"): "7:5",
    (168, "New South Wales", "Gough"): "17:1",
    (169, "New South Wales", "Gresham"): "20:. 21:. 22:. 23:.",
    (169, "New South Wales", "Gunderbooka"): "26:. 27:.",
    (169, "New South Wales", "Hawes"): "27:6",
    (169, "New South Wales", "Hume"): "27:6",
    (169, "New South Wales", "Hunter"): "27:6",
    (170, "New South Wales", "Napier"): "0:3",
    (170, "New South Wales", "Narran"): "0:1 7:9",
    (171, "New South Wales", "Narran"): "24:7 35:1",
    (170, "New South Wales", "Pottinger"): "13:4",
    (170, "New South Wales", "Ularara"): "5:6",
    (170, "New South Wales", "Wentworth"): "5:1",
    (171, "New South Wales", "White"): "32:1 33:6",
    (173, "Victoria", "Dundas"): "23:1 24:24",
    (172, "Victoria", "Kara Kara"): "6:5",
    (172, "Victoria", "Karkarooc"): "3:0",
    (172, "Victoria", "Lowan"): "3:7",
    (172, "Victoria", "Weeah"): "7:5",
    (172, "Victoria", "WHOLE STATE"): "0:2 1:2 2:3 3:11 4:6 5:7 6:7 7:10 8:9 9:9 10:11 11:5 12:13 13:11 14:16 15:10 16:19 17:4",
    (173, "Queensland", "Brisbane, South"): "25:9",
    (173, "Queensland", "Bundaberg"): "25:0",
    (173, "Queensland", "Charleville"): "25:6",
    (173, "Queensland", "Clermont"): "25:2",
    (173, "Queensland", "Cook"): "24:12 25:6",
    (173, "Queensland", "Darling Downs, E."): "19:5 20:17",
    (173, "Queensland", "Darling Downs, N."): "19:2",
    (172, "Queensland", "Herberton"): "1:6 2:4",
    (172, "Queensland", "Highfields"): "2:3",
    (175, "Queensland", "Maryborough"): "21:4 31:6",
    (175, "Queensland", "Mount Morgan"): "31:0",
    (175, "Queensland", "Oxley"): "33:6",
    (175, "Queensland", "Peak Downs"): "33:6",
    (175, "Queensland", "Rockhampton"): "31:3",
    (175, "Queensland", "St. Lawrence"): "32:1",
    (175, "Queensland", "Stanley"): "26:. 27:.",
    (175, "Queensland", "Tiaro"): "31:6",
    (175, "Queensland", "Toowong"): "31:6",
    (175, "Queensland", "Toowoomba"): "31:1",
    (175, "Queensland", "Townsville"): "31:4 32:16",
    (175, "Queensland", "Warwick"): "26:. 27:.",
    (175, "Queensland", "Westwood"): "31:6",
    (175, "Queensland", "Wide Bay"): "30:52 31:6",
    (175, "Queensland", "WHOLE STATE"): "20:22",
    (175, "South Australia", "Le Hunte"): "34:8",
    (175, "South Australia", "Musgrave"): "19:6",
    (176, "Western Australia", "Yilgarn"): "0:1 1:8 2:4 3:1 4:5 5:11 6:9 7:11 8:11 9:2 10:16 11:11 12:20 13:0",
    (176, "Western Australia", "WHOLE STATE"): "3:11 7:11",
    (176, "Tasmania", "Beaconsfield"): "9:11",
    (176, "Tasmania", "Bothwell"): "9:8",
    (177, "Tasmania", "Bruni"): "24:. 25:.",
    (177, "Tasmania", "Clarence"): "30:. 31:.",
    (177, "Tasmania", "Deloraine"): "22:11",
    (177, "Tasmania", "Evandale"): "32:. 33:.",
    (177, "Tasmania", "Flinders Island"): "30:. 31:.",
    (177, "Tasmania", "Kentish"): "28:. 29:.",
    (176, "Tasmania", "Port Cygnet"): "7:11 9:1",
    (176, "Tasmania", "Portland"): "0:1",
    (176, "Tasmania", "Queenborough"): "5:1",
    (177, "Tasmania", "Ringarooma"): "28:. 29:.",
    (176, "Tasmania", "St. Leonards"): "3:1",
    (177, "Tasmania", "Table Cape"): "28:. 29:.",
    (176, "Tasmania", "Waratah"): "9:8",
    (176, "Tasmania", "Westbury"): "9:3",
    (178, "Northern Territory", "Gladstone"): "6:. 7:.",
    (178, "Northern Territory", "REMAINDER OF TERRITORY"): "7:8 8:15 9:6 10:10 11:6 14:23 15:0",
    (179, "Northern Territory", "REMAINDER OF TERRITORY"): "30:. 31:.",
    (179, "Federal Territory", "Jervis Bay"): "22:. 23:. 28:. 29:. 32:. 33:. 34:12 35:10",
    (178, "Federal Territory", "WHOLE TERRITORY"): "5:11",
    (179, "Federal Territory", "WHOLE TERRITORY"): "26:. 27:. 28:. 29:.",
}
_LAYOUT = {
    168: (35, 125, 193, 835, 140, 162),
    169: (419, 540, 195, 835, 68, 90),
    170: (35, 127, 166, 835, 143, 163),
    171: (428, 540, 160, 835, 78, 101),
    172: (35, 118, 154, 835, 130, 152),
    173: (437, 540, 150, 835, 88, 111),
    174: (35, 118, 155, 835, 130, 152),
    175: (425, 540, 150, 835, 78, 100),
    176: (35, 133, 153, 835, 145, 166),
    177: (423, 540, 148, 835, 75, 97),
    178: (35, 135, 150, 280, 142, 164),
    179: (409, 540, 150, 280, 64, 85),
}


def _letters(text: str) -> str:
    return re.sub("[^a-z]", "", text.lower())


def _chars(page) -> list[dict]:
    return [char for block in page.get_text("rawdict")["blocks"]
            for line in block.get("lines", []) for span in line["spans"]
            for char in span["chars"]]


def _printed_rows(chars: list[dict], page: int, candidates: list[dict]) -> list[dict]:
    x0, x1, y0, y1, _, _ = _LAYOUT[page]
    groups: list[tuple[float, list[dict]]] = []
    for char in sorted(chars, key=lambda c: ((c["bbox"][1] + c["bbox"][3]) / 2,
                                           c["bbox"][0])):
        x, y, right, bottom = char["bbox"]
        centre = (y + bottom) / 2
        if not (x >= x0 and right <= x1 and y0 < centre < y1):
            continue
        if not groups or centre - groups[-1][0] > 2:
            groups.append((centre, []))
        groups[-1][1].append(char)
    rows = []
    for centre, group in groups:
        label = "".join(c["c"] for c in sorted(group, key=lambda c: c["bbox"][0])).strip()
        label = re.sub(r"^[^A-Za-z]*|[^A-Za-z]*$", "", label)
        letters = _letters(label)
        if len(letters) < 3 or letters in {
            "countyor division".replace(" ", ""), "ordivision", "yordivision", "municipality",
            "unicipality", "censusdistrict", "censusdistric", "nsusdistrict", "district",
        }:
            continue
        near = [r for r in candidates if abs(r["y"] - centre) <= 3]
        candidate = min(near, key=lambda r: abs(r["y"] - centre)) if near else None
        # A whole-state rule is sometimes fused with its name in the PDF OCR.
        if letters.startswith("wholesta"):
            label = "WHOLE STATE"
        elif letters.endswith("holeterritory"):
            label = "WHOLE TERRITORY"
        elif candidate:
            source_label = (candidate["label"] or candidate["resolved"]).strip()
            if source_label and SequenceMatcher(None, letters, _letters(source_label)).ratio() >= .9:
                label = source_label
        if rows and (letters in {"territory", "state"}) and "remainder" in _letters(rows[-1]["label"]):
            rows[-1]["label"] = "REMAINDER OF " + label.upper()
            # The amount is aligned with the second line of the printed label.
            rows[-1]["y"] = centre
            continue
        rows.append({"page": page, "y": centre, "label": label, "candidate": candidate})
    return rows


def _jurisdiction(page: int, y: float) -> tuple[str, str]:
    if page <= 171:
        return "New South Wales", "County"
    if page == 172:
        return ("Victoria", "County") if y < 480 else ("Queensland", "Census District")
    if page == 173:
        return ("Victoria", "County") if y < 480 else ("Queensland", "Census District")
    if page in (174, 175):
        return (("Queensland", "Census District") if y < 375
                else ("South Australia", "County or Division"))
    if page in (176, 177):
        return (("Western Australia", "Statistical District") if y < 390
                else ("Tasmania", "Municipality"))
    return (("Northern Territory", "County") if y < 230
            else ("Federal Territory", "District"))


def _image_marks(page, rows: list[dict], page_no: int) -> None:
    """Recover printed dot pairs absent from OCR, never numeric defaults.

    A mark requires at least two complete, dot-sized ink components and no
    complete digit-sized component in the currency box. Clipped neighbouring
    row glyphs and the bordering rules cannot establish a no-value mark.
    """
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(3, 3), colorspace=pymupdf.csGRAY)
    pixels, width = pixmap.samples, pixmap.width
    shillings, pence = _LAYOUT[page_no][-2:]
    for row in rows:
        row["image_marks"] = []
        for group in range(9):
            s, d = shillings + group * 39.9, pence + group * 39.9
            centre = (s + d) / 2
            y = row["y"]
            if page_no == 177:
                y += max(0., (428 - centre) / 358 * 3.8)
            x0, x1 = int((s - 12) * 3), int((d + 8) * 3)
            y0, y1 = int((y - 4.5) * 3), int((y + 6) * 3)
            ink = {(x, y) for y in range(y0, y1) for x in range(x0, x1)
                   if pixels[y * width + x] < 130}
            components = []
            while ink:
                stack = [ink.pop()]
                points = []
                while stack:
                    x, y = stack.pop()
                    points.append((x, y))
                    for neighbour in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                        if neighbour in ink:
                            ink.remove(neighbour)
                            stack.append(neighbour)
                xs, ys = zip(*points)
                if (len(points) < 2 or min(xs) <= x0 + 2 or max(xs) >= x1 - 2
                        or min(ys) <= y0 or max(ys) >= y1 - 1):
                    continue
                components.append((max(xs) - min(xs), max(ys) - min(ys)))
            if len(components) >= 2 and all(w <= 7 and h <= 5 for w, h in components):
                row["image_marks"].append(group)


def _candidate_values(row: dict) -> dict[int, str]:
    candidate = row["candidate"]
    if not candidate or abs(candidate["y"] - row["y"]) > 3:
        return {}
    cells = candidate["cells"]
    page = row["page"]
    if page == 176 and row["y"] > 390:
        source_label = candidate["label"] or candidate["resolved"]
        if _letters(source_label) != _letters(row["label"]):
            return {}  # Candidate municipality names and amounts are shifted.
    result = {}
    # Only fixed-width unit transcriptions are safe to place positionally.
    units = (page in (169, 171, 173, 175, 176, 177) or
             (page == 174 and row["y"] > 375)) and set(cells) == set(range(1, 19))
    offset = 2 if page == 168 else 0
    for column, cell in cells.items():
        value = cell["value"].strip()
        if units:
            if re.fullmatch(r"\d+|[.·\-— ]+", value):
                result[column - 1] = value
            continue
        group = column - 1 - offset
        if not 0 <= group < 9:
            continue
        amount = re.fullmatch(r"(\d+)\s*s\.?\s*(\d+)\s*d\.?", value, re.I)
        amount = amount or re.fullmatch(r"(\d+)\s+(\d+)", value)
        if amount:
            result[group * 2] = amount.group(1)
            result[group * 2 + 1] = amount.group(2)
        elif page in (168, 170, 172, 169, 173, 175, 179) and len(cells) <= 11 and re.fullmatch(r"[.· \-—]+", value):
            result[group * 2] = value
            result[group * 2 + 1] = value
        elif page == 169 and re.fullmatch(r"\d+", value):
            result[group * 2] = value
        elif page == 179 and column == 9 and re.fullmatch(r"\d+", value):
            result[16] = value
    if page == 179 and 10 in cells and re.fullmatch(r"\d+", cells[10]["value"].strip()):
        result[17] = cells[10]["value"].strip()
    return result


def _panel_values(chars: list[dict], row: dict, rows: list[dict]) -> dict[int, str]:
    page = row["page"]
    image = _IMAGE_AMOUNTS.get(page, {}).get(row["label"])
    if image and not (row["label"] == "WHOLE STATE" and row["y"] > 390):
        return {2 * group + unit: amount.split(":")[unit] if ":" in amount else amount
                for group, amount in enumerate(image.split()) for unit in range(2)}
    _, _, _, _, shillings, pence = _LAYOUT[page]
    buckets: dict[int, list[dict]] = defaultdict(list)
    marks: dict[int, list[dict]] = defaultdict(list)
    for char in chars:
        x0, y0, x1, y1 = char["bbox"]
        x, y = (x0 + x1) / 2, (y0 + y1) / 2
        group = round((x - (shillings + pence) / 2) / 39.9)
        if not 0 <= group < 9:
            continue
        s, d = shillings + group * 39.9, pence + group * 39.9
        if not s - 13 <= x <= d + 8:
            continue
        # On p177 the horizontal baselines slope down to the left by four
        # points. Correct only the evidenced skew, not neighbouring row data.
        if page == 177:
            y -= max(0., (428 - x) / 358 * 3.8)
        if abs(row["y"] - y) > 4:
            continue
        closest = min(rows, key=lambda r: abs(r["y"] - y))
        if closest is not row:
            continue
        unit = group * 2 + int(x > (s + d) / 2)
        if char["c"].isdigit() or char["c"] in "oO":
            buckets[unit].append(char)
        elif char["c"] in ".·":
            marks[group].append(char)
    values = {}
    for unit, group in buckets.items():
        value = "".join(c["c"] for c in sorted(group, key=lambda c: c["bbox"][0]))
        # PDF OCR uses the letter o for the printed zero in the pence columns.
        if unit % 2 and value in {"o", "O"}:
            value = "0"
        if value.isdigit() and (unit % 2 == 0 or int(value) < 12):
            values[unit] = value
    for group, chars_in_group in marks.items():
        if group * 2 not in values and group * 2 + 1 not in values:
            value = "".join(c["c"] for c in sorted(chars_in_group, key=lambda c: c["bbox"][0]))
            values[group * 2] = value
            values[group * 2 + 1] = value
    for unit, value in _candidate_values(row).items():
        values.setdefault(unit, value)
    if page == 176 and row["y"] < 185:
        values.update(_candidate_values(row))
    return values


def assemble_county_rent(source_rows, schema, states, area_types):
    """Return one complete Table 66 row per printed area, joining both leaves.

    Context dictionaries are accepted for the exporter's common interface. The
    printed paired panels determine jurisdiction; inherited page headings cannot
    safely distinguish Queensland from South Australia on pages 174/175.
    Missing, unreadable source units remain blank and are listed with provenance
    in UNMAPPABLE_CELLS rather than being coerced to zero.
    """
    dimensions, fields, _ = schema
    headers = dimensions + fields
    by_page = defaultdict(list)
    for row in source_rows:
        by_page[row["page"]].append(row)
    body = []
    UNMAPPABLE_CELLS.clear()
    with pymupdf.open(PDF) as document:
        for left_page in range(168, 179, 2):
            right_page = left_page + 1
            left_chars = _chars(document[left_page - 1])
            right_chars = _chars(document[right_page - 1])
            left = _printed_rows(left_chars, left_page, by_page[left_page])
            right = _printed_rows(right_chars, right_page, by_page[right_page])
            _image_marks(document[left_page - 1], left, left_page)
            _image_marks(document[right_page - 1], right, right_page)
            remaining = list(left)
            for printed in right:
                jurisdiction = _jurisdiction(right_page, printed["y"])
                matches = [r for r in remaining if _jurisdiction(left_page, r["y"]) == jurisdiction]
                if not matches:
                    raise ValueError(f"Table66 p{right_page}: no left panel for {printed['label']}")
                name = _letters(printed["label"])
                def match_score(row):
                    labels = [row["label"]]
                    if row["candidate"]:
                        labels.extend((row["candidate"]["label"], row["candidate"]["resolved"]))
                    return max(SequenceMatcher(None, name, _letters(value)).ratio() for value in labels)
                partner = max(matches, key=match_score)
                similarity = match_score(partner)
                if similarity < .55:
                    raise ValueError(f"Table66 p{right_page}: unmatched printed area {printed['label']!r}")
                remaining.remove(partner)
                # The source candidate may repair letter-level OCR corruption,
                # but never establishes a new geographic row.
                label = printed["label"]
                if name == "jervisbay":
                    label = "Jervis Bay"  # Printed initial is detached in PDF OCR.
                if similarity < .9:
                    label = partner["label"]
                # Printed county names: p171 Windeyer; p173 Borung. Both OCR
                # leaves can repeat the same corrupt spelling, so agreement
                # between leaves does not establish the source label.
                label = {(171, "windeyor"): "Windeyer",
                         (173, "borlulg"): "Borung"}.get(
                             (right_page, _letters(label)), label)
                printed["label"] = label
                values = _panel_values(left_chars, partner, left)
                if jurisdiction[0] == "South Australia" and "remainder" in _letters(label):
                    continue  # Printed heading for the divisions, not a rent row.
                values.update({18 + k: v for k, v in _panel_values(right_chars, printed, right).items()})
                for offset, panel in ((0, partner), (18, printed)):
                    for group in panel["image_marks"]:
                        values[offset + group * 2] = ".."
                        values[offset + group * 2 + 1] = ".."
                for panel in (partner, printed):
                    corrections = _IMAGE_UNITS.get((panel["page"], jurisdiction[0], label), "")
                    for correction in corrections.split():
                        index, value = correction.split(":")
                        values[int(index)] = value
                context = {"state": jurisdiction[0], "area_type": jurisdiction[1], "area": label}
                body.append([context.get(field, label) for field in dimensions] +
                            [values.get(index, "") for index in range(len(fields))])
                for index, field in enumerate(fields):
                    if index not in values:
                        UNMAPPABLE_CELLS.append({"page": left_page if index < 18 else right_page,
                                                 "state": jurisdiction[0], "area": label, "field": field})
            if remaining:
                raise ValueError(f"Table66 p{left_page}: unpaired printed areas: "
                                 + ", ".join(r["label"] for r in remaining))
    return headers, body
