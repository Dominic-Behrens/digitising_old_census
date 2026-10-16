# /// script
# requires-python = "==3.13.15"
# dependencies = ["pymupdf==1.28.2", "xlsxwriter==3.2.9"]
# ///
"""Rebuild the 1911 Dwellings tables as one worksheet per indexed table.

Inputs: output/extract_abs_1911_source_regions/cells.csv and table_coverage.csv;
       data/raw/abs_1911_census/1911_census_volume_iii_part_xiii_dwellings.pdf.
Output: output/export_abs_1911_dwellings_workbook/dwellings_numeric_checked.xlsx
        and mathematical_checks.csv. Source figures are not corrected to pass checks.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
import sys
import re
from pathlib import Path

import pymupdf
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name

from dwellings_room_panels import assemble_room_panels, assign_room_table
from dwellings_rent_panels import assemble_rent_panels, assign_rent_table
from dwellings_state_panels import assemble_state_panels, assign_state_table
from dwellings_county_panels import TABLE65_FIELDS, assemble_county_panels
from dwellings_county_rooms import assemble_county_rooms
from dwellings_county_rent import assemble_county_rent
from dwellings_council_panels import assemble_council_panels
from dwellings_county_measures import GROUP_FIELDS, assemble_county_measures
from dwellings_geography_panels import assemble_geography_panels
from dwellings_numeric import numeric_value, numeric_format, source_conflicted_fields
from dwellings_count_checks import build_count_checks
from dwellings_measure_checks import build_measure_checks, build_fixed_room_checks

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "output/extract_abs_1911_source_regions"
PDF = ROOT / "data/raw/abs_1911_census/1911_census_volume_iii_part_xiii_dwellings.pdf"
OUT = ROOT / "output/export_abs_1911_dwellings_workbook"
DOC = "1911_census_volume_iii_part_xiii_dwellings"
DOC_PREFIX = DOC + "::"

STATES = {
    "NEW SOUTH WALES": "New South Wales",
    "VICTORIA": "Victoria",
    "QUEENSLAND": "Queensland",
    "SOUTH AUSTRALIA": "South Australia",
    "WESTERN AUSTRALIA": "Western Australia",
    "TASMANIA": "Tasmania",
    "NORTHERN TERRITORY": "Northern Territory",
    "FEDERAL TERRITORY": "Federal Territory",
}
AREA_TYPES = {
    "COUNTY": "County", "COUNTIES": "Counties", "COUNTY OR": "County or Division",
    "COUNTY OR DIVISION": "County or Division",
    "CENSUS": "Census District", "CENSUS DISTRICT": "Census District",
    "CENSUS DISTRICTS": "Census Districts",
    "MUNICIPALITY": "Municipality", "MUNICIPALITIES": "Municipalities",
    "MUNICIPA": "Municipality", "MUNLCIP ALITY": "Municipality",
    "SHIRE": "Shire", "SHIRES": "Shires", "BOROUGH": "Borough",
    "BOROUGHS": "Boroughs", "TOWN": "Town", "TOWNS": "Towns",
    "MUNICIPAL DISTRICT": "Municipal District",
    "MUNICIPAL DISTRICTS": "Municipal Districts",
    "STATISTICAL": "Statistical District",
    "STATISTICAL DISTRICT": "Statistical District",
    "STATISTICAL DI TRICT": "Statistical District",
    "CITIES TOWNS AND BOROUGHS": "Cities, Towns and Boroughs",
    "CORPORATION": "Corporation", "CORPORATIONS": "Corporations",
    "DISTRICT COUNCIL": "District Council", "DISTRICT COUNCILS": "District Councils",
    "DISTRICT": "District",
    "ROAD BOARD DISTRICT": "Road Board District",
    "ROAD BOARD DISTRICTS": "Road Board Districts",
    "ROAD BOARD DISTRICTH": "Road Board Districts",
}
PANEL_PATTERNS = (
    ("PRIVATE DWELLINGS", "Private Dwellings"),
    ("DWELLINGS OTHER THAN PRIVATE", "Dwellings Other Than Private"),
    ("ALL DWELLINGS", "All Dwellings"),
)
METHOD_PATTERNS = (
    ("OCCUPIED BY OWNERS", "Occupied by Owners"),
    ("OCCUPIED BY TENANTS", "Occupied by Tenants"),
    ("OCCUPIED BY RENT PURCHASERS", "Occupied by Rent Purchasers"),
    ("OTHER AND UNSPECIFIED METHODS", "Other and Unspecified Methods of Occupancy"),
    ("OTHER METHODS OF OCCUPANCY", "Other Methods of Occupancy"),
    ("UNSPECIFIED METHODS OF OCCUPANCY", "Unspecified Methods of Occupancy"),
)
ROOMS = [str(i) for i in range(1, 20)] + ["20 and over", "Unspecified", "Total"]
INMATES = [str(i) for i in range(1, 20)] + ["20 and over", "Total"]
GEOGRAPHIES = [
    "New South Wales", "Victoria", "Queensland", "South Australia",
    "Western Australia", "Tasmania", "Northern Territory", "Federal Territory",
    "Commonwealth",
]
METRO_AREAS = [
    "Sydney and Suburbs", "Melbourne and Suburbs", "Brisbane and Suburbs",
    "Adelaide and Suburbs", "Perth and Suburbs", "Hobart and Suburbs",
    "Total Metropolitan Areas",
]
STATE_AREA_COLUMNS = [
    "new_south_wales_sydney_and_suburbs", "new_south_wales_remainder_of_state",
    "new_south_wales_whole_state", "victoria_melbourne_and_suburbs",
    "victoria_remainder_of_state", "victoria_whole_state",
    "queensland_brisbane_and_suburbs", "queensland_remainder_of_state",
    "queensland_whole_state", "south_australia_adelaide_and_suburbs",
    "south_australia_remainder_of_state", "south_australia_whole_state",
    "western_australia_perth_and_suburbs", "western_australia_remainder_of_state",
    "western_australia_whole_state", "tasmania_hobart_and_suburbs",
    "tasmania_remainder_of_state", "tasmania_whole_state", "northern_territory",
    "federal_territory", "commonwealth_total_metropolitan",
    "commonwealth_remainder_of_commonwealth", "commonwealth_whole_commonwealth",
]


def slug(value: str) -> str:
    value = value.strip().lower().replace("’", "'").replace("&", " and ")
    value = value.replace("q'land", "queensland").replace("melb.", "melbourne")
    value = value.replace("vic.", "victoria").replace("n.s.w.", "new south wales")
    value = value.replace("s.a.", "south australia").replace("w.a.", "western australia")
    value = value.replace("tas.", "tasmania").replace("n.t.", "northern territory")
    value = value.replace("f.t.", "federal territory")
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    value = value.replace("common_wealth", "commonwealth")
    value = value.replace("_subs", "_suburbs") if value.endswith("_subs") else value
    return {
        "n_s_w": "new_south_wales", "n_t": "northern_territory", "f_t": "federal_territory",
        "melbourne_suburbs": "melbourne_and_suburbs",
        "total_metropolis": "total_metropolitan_areas",
        "total_metropolitan": "total_metropolitan_areas",
        "sydney": "sydney_and_suburbs", "melbourne": "melbourne_and_suburbs",
        "brisbane": "brisbane_and_suburbs", "adelaide": "adelaide_and_suburbs",
        "perth": "perth_and_suburbs", "hobart": "hobart_and_suburbs",
    }.get(value, value)


def read_tables() -> list[dict[str, str]]:
    with (SOURCE / "table_coverage.csv").open(encoding="utf-8", newline="") as stream:
        tables = [row for row in csv.DictReader(stream) if row["table_id"].startswith(DOC_PREFIX)]
    tables.sort(key=lambda row: int(row["table_id"].rsplit("::", 1)[1]))
    if [int(row["table_id"].rsplit("::", 1)[1]) for row in tables] != list(range(1, 69)):
        raise ValueError("Expected the 68 contents-indexed Dwellings tables")
    return tables


def upper_line(text: str) -> str:
    text = text.upper().replace("—", " ").replace("–", " ").replace("-", " ")
    return " ".join(re.sub(r"[^A-Z0-9 ]+", " ", text).split())


def read_page_markers() -> tuple[dict[int, list[tuple[float, int]]], dict[int, list[tuple[float, str]]],
                                  dict[int, list[tuple[float, str]]], dict[int, list[tuple[float, str]]],
                                  dict[int, list[tuple[float, str]]]]:
    markers: dict[int, list[tuple[float, int]]] = defaultdict(list)
    states: dict[int, list[tuple[float, str]]] = defaultdict(list)
    area_types: dict[int, list[tuple[float, str]]] = defaultdict(list)
    panels: dict[int, list[tuple[float, str]]] = defaultdict(list)
    methods: dict[int, list[tuple[float, str]]] = defaultdict(list)
    table_heading = re.compile(r"^\s*(\d{1,2})\s*[.;\-~–—]+")
    with pymupdf.open(PDF) as document:
        for page_no in range(5, min(len(document), 199) + 1):
            page = document[page_no - 1]
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    text = " ".join(span["text"] for span in line["spans"]).strip()
                    if not text:
                        continue
                    y = float(line["bbox"][1])
                    upper = text.upper()
                    match = table_heading.match(text)
                    if match and any(word in upper for word in ("DWELLING", "INMATE", "AVERAGE", "AREA", "POPULATION", "OCCUPIED")):
                        number = int(match.group(1))
                        # The contents index and the headings on the pages around it identify one Table 68.
                        if page_no == 186 and number == 69:
                            number = 68
                        if 1 <= number <= 68:
                            markers[page_no].append((y, number))
                    canonical = upper_line(text).replace("PRIV ATE", "PRIVATE").replace("TENAN1 S", "TENANTS")
                    if text == upper or re.match(r"^[IVXLC]+[. ]", text.upper()):
                        state_heading = canonical.removesuffix(" CONTINUED")
                        for state, label in STATES.items():
                            if state_heading == state or state_heading.endswith(" " + state):
                                states[page_no].append((y, label))
                        if canonical in AREA_TYPES:
                            area_types[page_no].append((y, AREA_TYPES[canonical]))
                    for fragment, label in PANEL_PATTERNS:
                        if fragment in canonical:
                            panels[page_no].append((y, label))
                    for fragment, label in METHOD_PATTERNS:
                        if fragment in canonical:
                            methods[page_no].append((y, label))
            # The printed "MUNICIPALITY" heading is split across OCR lines on these pages.
            if page_no in (146, 147, 148):
                area_types[page_no].append((0.0, "Municipality"))
            if page_no == 167:
                states[page_no].append((0.0, "Tasmania"))
                area_types[page_no].append((0.0, "Municipality"))
            if page_no == 179:
                # OCR misses the NSW heading at the start of Table 67's lower panel.
                states[page_no].append((345.0, "New South Wales"))
            if page_no == 17:
                markers[page_no].append((458.0, 11))
            if page_no == 18:
                states[page_no].append((371.0, "Queensland"))
            if page_no == 21:
                states[page_no].append((555.0, "Northern Territory"))
            if page_no == 125:
                # Physical p125: Other heading is visible at y564 but absent
                # from the PDF text; Private Total is above it at y556.6.
                panels[page_no].append((564.0, "Dwellings Other Than Private"))
            if page_no == 180:
                states[page_no].append((152.0, "Victoria"))
            if page_no == 181:
                states[page_no].append((687.0, "Western Australia"))
            if page_no == 182:
                states[page_no].append((0.0, "Western Australia"))
                area_types[page_no].append((295.0, "Municipality"))
                states[page_no].append((679.0, "Northern Territory"))
                area_types[page_no].append((679.0, "County"))
            markers[page_no].sort()
            states[page_no].sort()
            area_types[page_no].sort()
            panels[page_no].sort()
            methods[page_no].sort()
    return markers, states, area_types, panels, methods


def context_at(items: list[tuple[float, str]], y: float) -> str:
    result = ""
    for row_y, value in items:
        if row_y > y:
            break
        result = value
    return result


def table_at(page: int, y: float, markers: dict[int, list[tuple[float, int]]], fallback: int) -> int:
    number = fallback
    for title_y, visible_number in markers.get(page, []):
        if title_y > y:
            break
        number = visible_number
    return number


def read_rows(tables: list[dict[str, str]], markers: dict[int, list[tuple[float, int]]]) -> dict[int, list[dict]]:
    known = {row["table_id"] for row in tables}
    rows: dict[int, dict[str, dict]] = {i: {} for i in range(1, 69)}
    with (SOURCE / "cells.csv").open(encoding="utf-8", newline="") as stream:
        for cell in csv.DictReader(stream):
            if cell["doc_id"] != DOC or not cell["table_id"]:
                continue
            if cell["table_id"] not in known:
                raise ValueError(f"Unknown indexed Dwellings table: {cell['table_id']}")
            fallback = int(cell["table_id"].rsplit("::", 1)[1])
            page = int(cell["pdf_page"])
            y = float(cell["row_y_pt"])
            number = table_at(page, y, markers, fallback)
            # Page 179 continues Table 66 above the lower-page Table 67 heading.
            if page == 179 and markers.get(page) and y < markers[page][0][0]:
                number = 66
            number = assign_room_table(page, y, number)
            number = assign_rent_table(page, y, number)
            number = assign_state_table(page, y, number)
            key = cell["row_id"]
            table_rows = rows[number]
            if key not in table_rows:
                table_rows[key] = {
                    "page": page, "y": y, "row_id": key,
                    "label": cell["row_label"], "resolved": cell["resolved_row_label"],
                    "cells": {},
                    "source_row_text": cell["source_row_text"],
                }
            row = table_rows[key]
            col = int(cell["column_index"])
            if col in row["cells"]:
                raise ValueError(f"Duplicate candidate cell at {number}/{key}/{col}")
            row["cells"][col] = {
                "label": cell["resolved_column_label"] or cell["column_label"],
                "value": cell["raw_value"],
            }
    return {number: list(table_rows.values()) for number, table_rows in rows.items()}


def table_fields(number: int) -> tuple[list[str], list[str], str]:
    if number == 1:
        return ["state"], ["occupied", "unoccupied", "being_built", "total"], "state"
    if number == 2:
        return ["section", "area", "area_unit"], [
            "area_in_acres_or_square_miles", "population_males", "population_females",
            "population_total", "population_per_acre_or_square_mile", "private_dwellings",
            "other_than_private_dwellings", "total_dwellings", "dwellings_per_acre_or_square_mile",
            "inmates_per_dwelling", "rooms_per_occupied_dwelling", "inmates_per_room",
            "average_weekly_rent_shillings", "average_weekly_rent_pence",
        ], "area"
    if 3 <= number <= 9:
        row_field = {3: "dwelling_type", 4: "number_of_rooms", 5: "room_range",
                     6: "wall_material", 7: "weekly_rental_value", 8: "number_of_rooms",
                     9: "wall_material"}[number]
        dims = [row_field, "dwelling_class"] if number >= 4 else [row_field]
        return dims, [slug(value) for value in GEOGRAPHIES], row_field
    if number in (10, 11):
        dims = ["state", "dwelling_type"] if number == 11 else ["dwelling_type"]
        return dims, [f"rooms_{value.lower().replace(' ', '_')}" for value in ROOMS], "dwelling_type"
    if 12 <= number <= 20:
        return ["wall_material", "dwelling_class"], [f"rooms_{value.lower().replace(' ', '_')}" for value in ROOMS], "wall_material"
    if 21 <= number <= 29:
        return ["wall_material", "dwelling_class"], [f"inmates_{value.lower().replace(' ', '_')}" for value in INMATES], "wall_material"
    if 30 <= number <= 38:
        return ["dwelling_class", "category"], [f"inmates_{value.lower().replace(' ', '_')}" for value in INMATES], "category"
    if 39 <= number <= 47:
        return ["weekly_rental_value", "dwelling_class"], [f"rooms_{value.lower().replace(' ', '_')}" for value in ROOMS], "weekly_rental_value"
    if number == 48:
        return ["weekly_rental_value", "method_of_occupancy"], [f"rooms_{value.lower().replace(' ', '_')}" for value in ROOMS], "weekly_rental_value"
    if number == 49:
        return ["weekly_rental_value", "method_of_occupancy"], [slug(value) for value in GEOGRAPHIES], "weekly_rental_value"
    if number == 50:
        return ["metropolitan_area"], ["occupied", "unoccupied", "being_built", "total"], "metropolitan_area"
    if number == 51:
        return ["dwelling_type"], [slug(value) for value in METRO_AREAS], "dwelling_type"
    if 52 <= number <= 58:
        row_field = {52: "number_of_rooms", 53: "room_range", 54: "wall_material",
                     55: "weekly_rental_value", 56: "weekly_rental_value",
                     57: "number_of_rooms", 58: "wall_material"}[number]
        dims = [row_field, "method_of_occupancy"] if number == 56 else [row_field, "dwelling_class"]
        if number == 53:
            dims = [row_field, "dwelling_class"]
        return dims, [slug(value) for value in METRO_AREAS], row_field
    if number in (59, 60):
        return ["number_of_rooms"], STATE_AREA_COLUMNS, "number_of_rooms"
    if number in (61, 62, 63):
        currency = [f"{geography}_{unit}" for geography in STATE_AREA_COLUMNS for unit in ("shillings", "pence")]
        return ["number_of_rooms"], currency, "number_of_rooms"
    if 64 <= number <= 67:
        if number == 64:
            values = [f"rooms_{room}_{kind}" for room in list(range(1, 20)) + ["20_and_over", "unspecified"]
                      for kind in ("private", "other")]
            values += ["total_private", "total_other", "other_camps_without_dwellings"]
        elif number == 65:
            values = list(TABLE65_FIELDS)
        elif number == 66:
            categories = list(range(1, 16)) + ["16_and_over", "unspecified"]
            values = [f"rooms_{room}_{unit}" for room in categories for unit in ("shillings", "pence")]
            values += ["total_shillings", "total_pence"]
        else:
            values = [
                "area_square_miles", "population_males", "population_females", "population_persons",
                "persons_per_square_mile", "occupied_dwellings_private", "occupied_dwellings_other_than_private",
                "occupied_dwellings_total", "occupied_dwellings_per_square_mile",
                "average_inmates_per_occupied_dwelling", "average_rooms_per_occupied_dwelling",
                "average_inmates_per_room", "average_weekly_rental_shillings", "average_weekly_rental_pence",
            ]
        dims = ["state", "area_type", "area"]
        if number == 67:
            dims.append("area_group")
            values += list(GROUP_FIELDS)
        return dims, values, "area"
    if number == 68:
        return ["state", "area_type", "council", "area_unit"], [
            "area", "population_males", "population_females", "population_persons",
            "population_per_area_unit", "occupied_dwellings", "occupied_dwellings_per_area_unit",
            "population_per_occupied_dwelling",
        ], "council"
    raise ValueError(f"No table schema for table {number}")


def header_index(number: int, cell_col: int, heading: str, fields: list[str], page: int) -> int | None:
    key = slug(heading)
    if key in fields:
        return fields.index(key)
    if 1 <= cell_col <= len(fields):
        return cell_col - 1
    return None


def contextual_value(number: int, row: dict, field: str, states, area_types, panels, methods) -> str:
    page, y = row["page"], row["y"]
    if number == 2 and field in {"section", "area_unit"}:
        # Physical p5 has three printed sections. Geography-only keys merge
        # the six repeated states and the two unlabelled printed totals.
        section = "Metropolitan" if y < 600 else "Remainder of States" if y < 690 else "Whole States and Territories"
        if field == "section":
            return section
        label = (row["label"] or row["resolved"]).lower()
        if "shipping" in label or "total population" in label:
            return ""
        return "Acres" if section == "Metropolitan" else "Square miles"
    if field == "state" and number == 1:
        return (row["label"] or row["resolved"]).strip()
    if field == "state" and number == 11:
        return context_at(states.get(page, []), y)
    if field == "state" and 64 <= number <= 68:
        return context_at(states.get(page, []), y)
    if field == "area_type" and 64 <= number <= 68:
        return context_at(area_types.get(page, []), y)
    if field == "dwelling_class":
        return context_at(panels.get(page, []), y)
    if field == "method_of_occupancy":
        return context_at(methods.get(page, []), y)
    if field in ("state", "area_type", "dwelling_class", "method_of_occupancy"):
        return ""
    return (row["label"] or row["resolved"]).strip()


def assemble(number: int, source_rows: list[dict], schemas, states, area_types, panels, methods) -> tuple[list[str], list[list[str]]]:
    dimension_fields, data_fields, row_field = schemas[number]
    if 10 <= number <= 29:
        return assemble_room_panels(number, source_rows, schemas[number], states, panels)
    if 30 <= number <= 48:
        return assemble_rent_panels(number, source_rows, schemas[number], panels, methods)
    if number in {1, *range(3, 10), *range(49, 59)}:
        return assemble_geography_panels(number, source_rows, schemas[number], panels, methods)
    if 59 <= number <= 63:
        return assemble_state_panels(number, source_rows, schemas[number])
    if number == 64:
        return assemble_county_rooms(source_rows, schemas[number], states, area_types)
    if number == 65:
        return assemble_county_panels(source_rows, schemas[number], states, area_types)
    if number == 66:
        return assemble_county_rent(source_rows, schemas[number], states, area_types)
    if number == 67:
        return assemble_county_measures(source_rows, schemas[number], states, area_types)
    if number == 68:
        return assemble_council_panels(source_rows, schemas[number], states, area_types)
    grouped: dict[tuple[str, ...], dict] = {}
    placeholder_values = {"", ".", "..", "...", "·", "··", "···", "-", "—"}
    for row in sorted(source_rows, key=lambda value: (value["page"], value["y"], value["row_id"])):
        label = (row["label"] or row["resolved"]).strip()
        if not row["cells"]:
            continue
        if not label and all(
            re.sub(r"\s+", "", cell["value"]) in placeholder_values
            for cell in row["cells"].values()
        ):
            continue
        dimensions = {
            field: contextual_value(number, row, field, states, area_types, panels, methods)
            for field in dimension_fields
        }
        if row_field not in dimensions:
            dimensions[row_field] = label
        elif not dimensions[row_field]:
            dimensions[row_field] = label
        key = tuple(dimensions[field] for field in dimension_fields)
        if key not in grouped:
            grouped[key] = {"dimensions": dimensions, "order": (row["page"], row["y"]), "values": {}}
        target = grouped[key]
        target["order"] = min(target["order"], (row["page"], row["y"]))
        for cell_col, cell in sorted(row["cells"].items()):
            index = header_index(number, cell_col, cell["label"], data_fields, row["page"])
            if index is None or not 0 <= index < len(data_fields):
                continue
            target["values"].setdefault(data_fields[index], cell["value"])
    headers = dimension_fields + data_fields
    result = []
    for item in sorted(grouped.values(), key=lambda value: value["order"]):
        result.append([item["dimensions"].get(field, "") for field in dimension_fields] +
                      [item["values"].get(field, "") for field in data_fields])
    return headers, result


def build_checks(number: int, headers: list[str], body: list[list[str]], dimension_count: int):
    checks = build_count_checks(number, headers, body, dimension_count)
    checks.update(build_measure_checks(number, headers, body, dimension_count))
    readable, nonnegative, integral = {}, {}, {}
    first, last = xl_col_to_name(dimension_count), xl_col_to_name(len(headers) - 1)
    conflict_columns = {name: index for index, name in enumerate(headers)} if number == 68 else None
    for index, row in enumerate(body):
        span = f"{first}{index + 3}:{last}{index + 3}"
        conflicts = source_conflicted_fields(number, conflict_columns, row) if conflict_columns else ()
        values = [value if name in conflicts else numeric_value(value)
                  for name, value in zip(headers[dimension_count:], row[dimension_count:])]
        readable[index] = (f"COUNTA({span})-COUNT({span})", sum(isinstance(value, str) for value in values))
        nonnegative[index] = (f'COUNTIF({span},"<0")', sum(isinstance(value, (int, float)) and value < 0 for value in values))
        if number in {1, *range(3, 59), 64, 65}:
            integral[index] = (
                f"SUMPRODUCT(IFERROR(--(MOD({span},1)<>0),0))",
                sum(isinstance(value, (int, float)) and value % 1 != 0 for value in values),
            )
    checks["check_unreadable_numeric_fields"] = readable
    checks["check_negative_numeric_fields"] = nonnegative
    if integral:
        checks["check_noninteger_count_fields"] = integral
    return checks


def export(tables: list[dict[str, str]], source_rows: dict[int, list[dict]], contexts) -> Path:
    markers, states, area_types, panels, methods = contexts
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "dwellings_numeric_checked.xlsx"
    temporary = OUT / ".dwellings_numeric_checked.xlsx.tmp"
    book = xlsxwriter.Workbook(str(temporary), {
        "constant_memory": True, "strings_to_formulas": False, "strings_to_urls": False,
    })
    book.use_zip64()
    # Fixed metadata makes repeated offline builds byte-reproducible.
    created = datetime.fromtimestamp(int(os.environ.get("SOURCE_DATE_EPOCH", "0")), timezone.utc).replace(tzinfo=None)
    book.set_properties({"created": created})
    title_format = book.add_format({
        "font_name": "Franklin Gothic Demi", "font_size": 12, "bold": True,
        "font_color": "#FFFFFF", "bg_color": "#006B7A", "valign": "vcenter",
        "text_wrap": True,
    })
    header_format = book.add_format({
        "font_name": "Franklin Gothic Book", "font_size": 9, "bold": True,
        "bg_color": "#E9E8E5", "bottom": 2, "bottom_color": "#006B7A",
        "valign": "vcenter", "text_wrap": True,
    })
    body_format = book.add_format({
        "font_name": "Franklin Gothic Book", "font_size": 9, "border": 7,
        "border_color": "#BFBFBF", "valign": "top",
        "text_wrap": True,
    })
    numeric_formats = {}
    review_format = book.add_format({
        "font_name": "Franklin Gothic Book", "font_size": 9, "border": 7,
        "border_color": "#BFBFBF", "valign": "top", "text_wrap": True,
        "bg_color": "#FFF2CC",
    })
    check_format = book.add_format({
        "font_name": "Franklin Gothic Book", "font_size": 9, "border": 7,
        "border_color": "#BFBFBF", "num_format": "0.########",
    })
    failure_format = book.add_format({"bg_color": "#FDD0CE", "font_color": "#9C0006"})
    check_records = []
    row_headers = {}
    assembled_tables = {}
    schema_by_number = {number: table_fields(number) for number in range(1, 69)}
    for table in tables:
        number = int(table["table_id"].rsplit("::", 1)[1])
        sheet_name = f"Table {number}"
        headers, body = assemble(number, source_rows[number], schema_by_number, states,
                                 area_types, panels, methods)
        if not body:
            raise ValueError(f"No table rows were assembled for {sheet_name}")
        dimension_count = len(schema_by_number[number][0])
        conflict_columns = {name: index for index, name in enumerate(headers)} if number == 68 else None
        assembled_tables[str(number)] = {"title": table["table_title"], "headers": headers,
                                        "dimension_count": dimension_count, "rows": body}
        checks = build_checks(number, headers, body, dimension_count)
        if number in (60, 62):
            checks.update(build_fixed_room_checks(number, headers, body,
                                                  assembled_tables[str(number - 1)]))
        all_headers = headers + list(checks)
        sheet = book.add_worksheet(sheet_name)
        sheet.hide_gridlines(2)
        sheet.set_zoom(85)
        sheet.set_landscape()
        sheet.set_margins(0.25, 0.25, 0.4, 0.4)
        sheet.freeze_panes(2, len(schema_by_number[number][0]))
        sheet.repeat_columns(0, len(schema_by_number[number][0]) - 1)
        sheet.set_row(0, 38)
        title = table["table_title"]
        if 59 <= number <= 63:
            title += "\n(Exclusive of Dwellings occupied solely by Full-blooded Aboriginals)."
        if len(headers) == 1:
            sheet.write_string(0, 0, title, title_format)
        else:
            sheet.merge_range(0, 0, 0, len(headers) - 1, title, title_format)
        for col, header in enumerate(all_headers):
            sheet.write_string(1, col, header, header_format)
            sheet.set_column(col, col, 30 if col >= len(headers) else 24 if header in headers[:dimension_count] else 18)
        header_lines = max((len(header) + (28 if col >= len(headers) else 22 if col < dimension_count else 16) - 1)
                           // (28 if col >= len(headers) else 22 if col < dimension_count else 16)
                           for col, header in enumerate(all_headers))
        sheet.set_row(1, max(45, 12 * header_lines + 8))
        for row_num, values in enumerate(body, start=2):
            conflicts = source_conflicted_fields(number, conflict_columns, values) if conflict_columns else ()
            label_lines = max((len(str(value)) + 21) // 22
                              for value in values[:len(schema_by_number[number][0])])
            sheet.set_row(row_num, max(15, 12 * label_lines + 3))
            for col, value in enumerate(values):
                numeric = col >= dimension_count or headers[col] in ("number_of_rooms", "category")
                parsed = numeric_value(value) if numeric and headers[col] not in conflicts else value
                if parsed is None or parsed == "":
                    sheet.write_blank(row_num, col, None, body_format)
                elif isinstance(parsed, (int, float)):
                    code = numeric_format(value)
                    if code not in numeric_formats:
                        numeric_formats[code] = book.add_format({
                            "font_name": "Franklin Gothic Book", "font_size": 9, "border": 7,
                            "border_color": "#BFBFBF", "valign": "top", "num_format": code,
                        })
                    sheet.write_number(row_num, col, parsed, numeric_formats[code])
                else:
                    sheet.write_string(row_num, col, parsed, review_format if numeric else body_format)
                if numeric and value and (parsed is None or isinstance(parsed, str) or re.search(r"[*†‡]", value)):
                    sheet.write_comment(row_num, col, f"Printed/source reading: {value}")
            for offset, (check_name, check_rows) in enumerate(checks.items(), start=len(headers)):
                result = check_rows.get(row_num - 2)
                if result is None:
                    continue
                formula, cached = result
                if check_name == "check_noninteger_count_fields":
                    # MOD consumes the entire row vector. A scalar formula
                    # lets Excel insert @ and inspect only its first field.
                    sheet.write_array_formula(row_num, offset, row_num, offset,
                                              "=" + formula, check_format, cached)
                else:
                    sheet.write_formula(row_num, offset, "=" + formula, check_format, cached)
                check_records.append({
                    "table": number, "excel_row": row_num + 1, "check": check_name,
                    "result": cached, "formula": "=" + formula,
                    "row_label": " | ".join(values[:dimension_count]),
                })
        for col in range(len(headers), len(all_headers)):
            cell = f"{xl_col_to_name(col)}3"
            sheet.conditional_format(2, col, len(body) + 1, col, {
                "type": "formula",
                "criteria": f'OR(AND(ISNUMBER({cell}),ABS({cell})>0.00000001),{cell}="FAIL",{cell}="INCOMPLETE")',
                "format": failure_format,
            })
        sheet.repeat_rows(0, 1)
        sheet.print_area(0, 0, len(body) + 1, len(all_headers) - 1)
        row_headers[sheet_name] = (len(body), len(headers))
    book.close()
    temporary.replace(path)
    with (OUT / "mathematical_checks.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["table", "excel_row", "check", "result", "formula", "row_label"])
        writer.writeheader()
        writer.writerows(check_records)
    with (OUT / "assembled_tables.json").open("w", encoding="utf-8") as stream:
        json.dump(assembled_tables, stream, ensure_ascii=False, indent=2)
    print(f"{path.relative_to(ROOT)}: {len(row_headers)} tables; "
          f"{sum(row_count for row_count, _ in row_headers.values()):,} rows")
    return path


def write_build_manifest() -> None:
    """Record actual immutable inputs, mapping code, runtime and outputs."""
    code_paths = {Path(__file__).resolve()}
    for name, module in sys.modules.items():
        if name.startswith("dwellings_") and getattr(module, "__file__", None):
            code_paths.add(Path(module.__file__).resolve())
    lock = Path(__file__).with_suffix(".py.lock")
    if lock.exists():
        code_paths.add(lock)
    inputs = [PDF, SOURCE / "cells.csv", SOURCE / "table_coverage.csv"]
    outputs = [OUT / name for name in (
        "dwellings_numeric_checked.xlsx", "mathematical_checks.csv", "assembled_tables.json")]

    def fingerprints(paths):
        result = {}
        for path in sorted(paths):
            with path.open("rb") as stream:
                result[path.relative_to(ROOT).as_posix()] = hashlib.file_digest(stream, "sha256").hexdigest()
        return result

    counts = Counter()
    with (OUT / "mathematical_checks.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            value = row["result"]
            status = value if value in {"PASS", "FAIL", "INCOMPLETE", "N/A"} else (
                "PASS" if abs(float(value)) <= 1e-8 else "FAIL")
            counts[status] += 1
    manifest = {
        "schema_version": 1,
        "command": "uv run --offline --locked scripts/export_abs_1911_dwellings_workbook.py",
        "source_date_epoch": int(os.environ.get("SOURCE_DATE_EPOCH", "0")),
        "runtime": {"python": platform.python_version(), "implementation": platform.python_implementation(),
                    "platform": sys.platform, "pymupdf": pymupdf.VersionBind, "xlsxwriter": xlsxwriter.__version__},
        "inputs_sha256": fingerprints(inputs),
        "code_sha256": fingerprints(code_paths),
        "outputs_sha256": fingerprints(outputs),
        "check_instances": dict(sorted(counts.items())),
        "limitations": ["No arithmetic balancing or guessed source digits.",
                        "Passing checks do not independently verify every source digit.",
                        "Historical rounding assumptions remain unchanged."],
    }
    with (OUT / "build_manifest.json").open("w", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2, sort_keys=True)


def main() -> None:
    tables = read_tables()
    contexts = read_page_markers()
    markers = contexts[0]
    rows = read_rows(tables, markers)
    export(tables, rows, contexts)
    write_build_manifest()


if __name__ == "__main__":
    main()
