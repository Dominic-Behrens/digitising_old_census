"""Source-column arithmetic for the count panels of the Dwellings workbook.

A delta is printed total minus its disjoint components. No source figure is
altered. Missing/unreadable figures produce INCOMPLETE, not an inferred zero.
Tables 8/9/57/58 contain inmate counts, despite not counting dwellings.
"""
from __future__ import annotations

from collections import defaultdict
import re
import unicodedata

from xlsxwriter.utility import xl_col_to_name
from dwellings_numeric import NO_VALUE, numeric_value


_STATES = (
    "new_south_wales", "victoria", "queensland", "south_australia",
    "western_australia", "tasmania", "northern_territory", "federal_territory",
)
_METROS = (
    "sydney_and_suburbs", "melbourne_and_suburbs", "brisbane_and_suburbs",
    "adelaide_and_suburbs", "perth_and_suburbs", "hobart_and_suburbs",
)


def _key(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return "_".join(re.findall(r"[a-z0-9]+", value.lower().replace("&", " and ")))


def _category(value: str) -> str:
    key = _key(value)
    if key.startswith("total_population"):
        return "total_population"
    if key.startswith("shipping"):
        return "shipping_population"
    if key.startswith("total") or key in ("all", "all_dwellings"):
        return "total"
    if "camps" in key.split("_") and "aboriginal" not in key and "half_cast" not in key and "whites" not in key:
        return "other_camps"
    if key in ("living", "were_living", "half_castes_were_living") or "aboriginal_camp" in key:
        return "aboriginal_camps"
    if "wagon" in key:
        return "wagons"
    if key.startswith("bushes_rushes"):
        return "bushes_rushes"
    if key.startswith("ruberoid"):
        return "ruberoid"
    if key.startswith("pis") and len(key) <= 7:
        return "pise"
    if "unspecif" in key or key == "un_specified":
        return "unspecified"
    if key == "20" or (re.search(r"\b20\b", str(value)) and any(word in key for word in ("over", "upwards"))):
        return "20_and_over"
    # Printed rent labels abbreviate the upper end with ditto marks. Their
    # lower bound is the category identity, not a monetary data value.
    rental = str(value).lower().replace("is.", "1s.").replace("ios.", "10s.")
    if rental.strip().startswith("under") and re.search(r"\b1s", rental):
        return "rent_under_1s"
    pounds = re.search(r"£\s*(\d+)(?:\s+(\d+)s)?", rental)
    if pounds:
        return f"rent_pounds_{pounds[1]}_{pounds[2] or '0'}"
    shillings = re.search(r"(?<!\d)(\d+)s\.", rental)
    if shillings:
        return f"rent_shillings_{shillings[1]}"
    return key


# Full printed-panel reviews establish these finite class/category omissions.
# They permit checking an existing All row against its published partner;
# they never create a data row or treat an arbitrary missing extraction as zero.
# Physical PDF pages: 6–15, 22–56, 60–71 and 114–125.
_PUBLISHED_ABSENCES = {
    number: {("private", "wagons"), ("private", "aboriginal_camps")}
    for number in (4, 6, 7, 8, 9)
}
for _table in (52, 54, 55, 57, 58):
    _PUBLISHED_ABSENCES[_table] = {("private", "wagons")}
for _table, _ranges_absent in (
    (5, ("70–79", "80–89", "90–99", "100 and under 200", "200 and under 300",
         "300 and under 400", "400 and over")),
    (53, ("60–69", "70–79", "80–89", "90–99", "100 and under 200",
          "200 and under 300", "300 and under 400", "400 and over")),
):
    _PUBLISHED_ABSENCES[_table] = {("private", _category(label)) for label in _ranges_absent}
for _table in (54, 58):
    _PUBLISHED_ABSENCES[_table].update(
        ("other", _category(label)) for label in
        ("Sun-dried Bricks", "Pisé", "Wattle and Dab", "Bark",
         "Bushes, Rushes, Spinifex, etc.", "Calico, Canvas, Hessian")
    )
_PUBLISHED_ABSENCES[55].update({("other", "rent_under_1s"), ("other", "rent_shillings_1")})
for _table in (*range(12, 30), *range(33, 39)):
    _PUBLISHED_ABSENCES.setdefault(_table, set()).update(
        {("private", "wagons"), ("private", "aboriginal_camps")}
    )
for _tables, _kind, _labels in (
    ((13,), "other", ("bushes rushes",)),
    ((14,), "other", ("bark", "bushes rushes", "pise", "wattle and dab")),
    ((15,), "other", ("lath and plaster", "ruberoid", "wattle and dab")),
    ((16, 25), "other", ("bark", "bushes rushes", "pise", "ruberoid")),
    ((17, 26), "other", ("bark", "bushes rushes", "lath and plaster", "pise", "wattle and dab")),
    ((18, 27), "private", ("wattle and dab",)),
    ((18, 27), "other", ("bark", "bushes rushes", "calico canvas hessian", "pise",
                        "ruberoid", "sun dried bricks", "wattle and dab", "aboriginal camps")),
    ((19, 28), "private", ("lath and plaster", "ruberoid", "sun dried bricks", "wattle and dab")),
    ((19, 28), "other", ("bark", "brick", "calico canvas hessian", "concrete", "lath and plaster",
                        "pise", "ruberoid", "sun dried bricks", "wattle and dab", "wagons")),
    ((20, 29), "private", ("bushes rushes", "lath and plaster", "ruberoid", "wattle and dab")),
    ((20, 29), "other", ("bark", "bushes rushes", "concrete", "lath and plaster", "pise",
                        "ruberoid", "sun dried bricks", "unspecified", "wattle and dab",
                        "aboriginal camps", "wagons")),
    ((22,), "other", ("bushes rushes",)),
    ((23,), "other", ("bark", "bushes rushes", "pise", "wattle and dab")),
    ((24,), "other", ("lath and plaster", "ruberoid", "wattle and dab")),
    ((37,), "private", ("11", "12", "13", "14", "15", "16", "17", "18", "19", "20_and_over")),
    ((37,), "other", ("7", "12", "14", "17", "18", "19", "wagons")),
    ((38,), "private", ("13", "15", "17", "18")),
    ((38,), "other", ("3", "4", "7", "9", "10", "11", "12", "14", "15", "16", "17", "18",
                      "19", "unspecified", "wagons", "aboriginal_camps")),
):
    for _table in _tables:
        _PUBLISHED_ABSENCES.setdefault(_table, set()).update(
            (_kind, _category(label)) for label in _labels
        )


def _class(value: str) -> str:
    key = _key(value)
    if "other_than_private" in key:
        return "other"
    if "all_dwellings" in key:
        return "all"
    if "private_dwellings" in key:
        return "private"
    return key


def _value(value: str, printed_blank: bool) -> tuple[float | None, bool]:
    """Return the numeric value and whether an Excel blank is source-allowed."""
    text = str(value).strip()
    if not text:
        return (0.0, True) if printed_blank else (None, False)
    if NO_VALUE.fullmatch(text):
        return 0.0, True
    result = numeric_value(value)
    return (result, False) if isinstance(result, (int, float)) else (None, False)


def _ranges(cells: list[tuple[int, int]]) -> list[str]:
    """Compact column runs; this keeps county formulas well below Excel limits."""
    by_column: dict[int, list[int]] = defaultdict(list)
    for row, column in sorted(set(cells)):
        by_column[column].append(row)
    result = []
    for column, rows in sorted(by_column.items()):
        start = end = rows[0]
        for row in rows[1:] + [None]:
            if row is not None and row == end + 1:
                end = row
                continue
            first = f"{xl_col_to_name(column)}{start + 3}"
            result.append(first if start == end else f"{first}:{xl_col_to_name(column)}{end + 3}")
            start = end = row
    return result


def build_count_checks(number, headers, body, dimension_count):
    """Build all applicable additive identities once for one assembled table.

    Returns check heading -> body row -> (Excel formula without '=', cache).
    Formula guards refer only to original cells. Printed absence marks count as
    zero while remaining blank in Excel. Only direct-PDF Tables 64/65 permit
    genuine printed empty cells. All other empty strings require numeric data.
    """
    if number not in {1, *range(3, 59), 64, 65} or not body:
        return {}
    checks: dict[str, dict[int, tuple[str, float | str]]] = {}
    columns = {header: index for index, header in enumerate(headers)}
    data_columns = list(range(dimension_count, len(headers)))
    parsed = {
        (row, column): _value(values[column], number in (64, 65))
        for row, values in enumerate(body) for column in data_columns
    }

    def incomplete(name, row, references=()):
        checks.setdefault(name, {})[row] = ('"INCOMPLETE"', "INCOMPLETE")

    def delta(name, row, target, components, complete=True):
        references = [target] + list(components)
        if not complete or not components or len(set(references)) != len(references):
            incomplete(name, row, references)
            return
        required, blanks = [], []
        values = []
        for cell in references:
            value, blank_allowed = parsed[cell]
            values.append(value)
            (blanks if blank_allowed else required).append(cell)
        guards = []
        if required:
            guards.append(f'COUNT({",".join(_ranges(required))})={len(required)}')
        if blanks:
            ranges = _ranges(blanks)
            blank_count = "+".join(f"COUNTBLANK({ref})" for ref in ranges)
            guards.append(f'COUNT({",".join(ranges)})+{blank_count}={len(blanks)}')
        target_ref = _ranges([target])[0]
        formula = f'IF(AND({",".join(guards)}),{target_ref}-SUM({",".join(_ranges(list(components)))}),"INCOMPLETE")'
        expected = "INCOMPLETE" if any(value is None for value in values) else values[0] - sum(values[1:])
        checks.setdefault(name, {})[row] = (formula, expected)

    # Horizontal disjoint count columns.
    if number in (1, 50):
        fields = ("occupied", "unoccupied", "being_built")
        for row in range(len(body)):
            delta("check_occupancy_total_delta", row, (row, columns["total"]),
                  [(row, columns[field]) for field in fields])
    for prefix in ("rooms", "inmates"):
        total = columns.get(f"{prefix}_total")
        if total is None:
            continue
        components = [column for column in data_columns if headers[column].startswith(prefix + "_") and column != total]
        for row, values in enumerate(body):
            if prefix == "rooms" and any(_category(value) == "other_camps" for value in values[:dimension_count]):
                continue
            delta(f"check_{prefix}_row_total_delta", row, (row, total), [(row, column) for column in components])
    if number in (64, 65):
        for kind in ("private", "other"):
            total = columns[f"total_{kind}"]
            components = [column for column in data_columns if headers[column].endswith("_" + kind) and column != total]
            for row in range(len(body)):
                delta(f"check_{kind}_row_total_delta", row, (row, total), [(row, column) for column in components])

    geography_total = "commonwealth" if "commonwealth" in columns else "total_metropolitan_areas"
    if geography_total in columns:
        geographies = _STATES if geography_total == "commonwealth" else _METROS
        components = [columns[field] for field in geographies if field in columns]
        for row in range(len(body)):
            delta("check_geography_total_delta", row, (row, columns[geography_total]),
                  [(row, column) for column in components], len(components) == len(geographies))

    # Vertical sections: class/state/method dimensions are kept separate.
    category_column = next((column for column in range(dimension_count)
                            if headers[column] not in ("state", "area_type", "dwelling_class", "method_of_occupancy")), None)
    if number == 1:
        category_column = columns["state"]
    if category_column is None:
        return checks
    groups: dict[tuple[str, ...], list[int]] = defaultdict(list)
    categories = [_category(values[category_column]) for values in body]
    for row, values in enumerate(body):
        group = tuple(_key(values[column]) for column in range(dimension_count) if column != category_column)
        groups[group].append(row)
    for group, rows in groups.items():
        totals = [row for row in rows if categories[row] == "total"]
        parts = [row for row in rows if categories[row] not in
                 ("total", "other_camps", "shipping_population", "total_population")]
        unique = len({categories[row] for row in parts}) == len(parts)
        complete = bool(parts) and unique and all(categories[row] for row in parts) and all(group)
        if number in range(4, 10) and "dwelling_class" not in columns:
            # The legacy single-dimension assembly collapses repeated labels
            # across three printed panels. No defensible section sum survives.
            complete = False
        if number in (1, 50):
            expected = _STATES if number == 1 else _METROS
            index = {_key(body[row][category_column]): row for row in parts}
            parts = [index[name] for name in expected if name in index]
            complete = unique and len(parts) == len(expected)
        # Population includes the separately printed camps without dwellings
        # and shipping. Neither is a dwelling-category constituent.
        if number in (8, 9, 57, 58):
            population = [part for part in rows if categories[part] == "total_population"]
            camps = [part for part in rows if categories[part] == "other_camps"]
            shipping = [part for part in rows if categories[part] == "shipping_population"]
            for target in population:
                components = totals + camps + shipping
                population_complete = len(population) == len(totals) == len(camps) == len(shipping) == 1
                for column in data_columns:
                    delta(f"check_population_{headers[column]}_delta", target, (target, column),
                          [(part, column) for part in components], population_complete)
        if len(totals) != 1:
            for row in totals or rows[:1]:
                for column in data_columns:
                    incomplete(f"check_section_{headers[column]}_delta", row, [(row, column)])
            continue
        row = totals[0]
        for column in data_columns:
            delta(f"check_section_{headers[column]}_delta", row, (row, column),
                  [(part, column) for part in parts], complete)

    # Matched printed categories, never sums across unlike classes.
    if "dwelling_class" in columns:
        class_column = columns["dwelling_class"]
        matches: dict[tuple[str, ...], dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
        for row, values in enumerate(body):
            key = tuple(categories[row] if column == category_column else _key(values[column])
                        for column in range(dimension_count) if column != class_column)
            matches[key][_class(values[class_column])].append(row)
        published_absences = _PUBLISHED_ABSENCES.get(number, ())
        for classes in matches.values():
            for row in classes.get("all", []):
                if categories[row] in ("other_camps", "shipping_population", "total_population"):
                    continue
                partners = classes.get("private", []) + classes.get("other", [])
                complete = len(classes.get("all", [])) == 1 and all(
                    len(classes.get(kind, [])) == 1 or
                    (not classes.get(kind) and (kind, categories[row]) in published_absences)
                    for kind in ("private", "other")
                )
                for column in data_columns:
                    delta(f"check_private_other_{headers[column]}_delta", row, (row, column),
                          [(partner, column) for partner in partners], complete)

    return checks
