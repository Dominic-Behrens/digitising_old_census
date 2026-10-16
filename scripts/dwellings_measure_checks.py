"""Source-only checks for non-additive Dwellings measures.

Table 2/67 population includes people in camps without dwellings (Table 3,
PDF p6), whereas the printed inmates averages count dwelling inmates. Their
population/occupied comparison is therefore N/A, not an arithmetic failure.
Shipping and total-population rows have no land/dwelling ratio definition.
Table 68 explicitly prints population per occupied dwelling; its Aboriginal
exclusion applies consistently to the counts (PDF p183). Rent averages are
never added or averaged. Printed dots/dashes mean not applicable, not zero;
a genuinely absent candidate or a half-present currency pair is incomplete.
"""
from __future__ import annotations

import re
from decimal import Decimal

from xlsxwriter.utility import xl_col_to_name
from dwellings_numeric import NO_VALUE, numeric_value, source_conflicted_fields


CheckRows = dict[str, dict[int, tuple[str, float | str]]]


def _number(raw: str) -> tuple[float, float] | None:
    """Return value and half a printed last digit, retaining trailing zeroes."""
    parsed = numeric_value(raw)
    if not isinstance(parsed, (int, float)):
        return None
    text = str(raw).strip().strip("*†‡ ").replace(",", "").replace(" ", "")
    value = Decimal(text)
    return float(parsed), float(Decimal(5).scaleb(value.as_tuple().exponent - 1))


def _marked(raw: str) -> bool:
    text = str(raw).strip()
    return bool(text and NO_VALUE.fullmatch(text))


def build_measure_checks(number: int, headers: list[str], body: list[list[str]],
                         dimension_count: int) -> CheckRows:
    """Build each check once; formulas reference original worksheet cells only.

    Exact sums return zero deltas. Ratios use half-last-digit tolerance of
    the printed ratio; ratios of rounded averages propagate both input
    rounding intervals. Zero denominators are N/A. Non-numeric or absent
    candidates are INCOMPLETE, never silently converted to zero.
    """
    if number not in {2, 8, 9, 57, 58, 59, 60, 61, 62, 63, 66, 67, 68}:
        return {}
    columns = {heading: i for i, heading in enumerate(headers)}
    conflicts = {row: fields for row, record in enumerate(body)
                 if (fields := source_conflicted_fields(number, columns, record))} if number == 68 else {}
    checks: CheckRows = {}

    def put(title: str, row: int, formula: str, cached: float | str) -> None:
        checks.setdefault(title, {})[row] = formula, cached

    def literal(title: str, row: int, status: str) -> None:
        put(title, row, f'"{status}"', status)

    def values(row: int, names: list[str]):
        refs = [f"{xl_col_to_name(columns[name])}{row + 3}" for name in names]
        parsed = [None if name in conflicts.get(row, ()) else _number(body[row][columns[name]])
                  for name in names]
        guard = ",".join(f"ISNUMBER({ref})" for ref in refs)
        return refs, parsed, guard

    def sum_check(title: str, names: list[str]) -> None:
        if not all(name in columns for name in names):
            return
        for row in range(len(body)):
            label = " ".join(str(value) for value in body[row][:dimension_count]).lower()
            if "private + other" in title and ("shipping" in label or "total population" in label):
                literal(title, row, "N/A")
                continue
            refs, nums, guard = values(row, names)
            guards, amounts = [], []
            for ref, parsed, name in zip(refs, nums, names):
                marked = _marked(body[row][columns[name]])
                guards.append(f"OR(ISNUMBER({ref}),COUNTBLANK({ref})=1)" if marked else f"ISNUMBER({ref})")
                amounts.append(parsed[0] if parsed is not None else 0 if marked else None)
            cached = amounts[0] + amounts[1] - amounts[2] if all(value is not None for value in amounts) else "INCOMPLETE"
            put(title, row, f'IF(AND({",".join(guards)}),SUM({refs[0]},{refs[1]})-SUM({refs[2]}),"INCOMPLETE")', cached)

    def ratio_check(title: str, names: list[str], *, rounded_inputs: bool = False,
                    excluded: bool = False) -> None:
        if not all(name in columns for name in names):
            return
        for row, record in enumerate(body):
            label = " ".join(str(v) for v in record[:dimension_count]).lower()
            if excluded or "shipping" in label or "total population" in label:
                literal(title, row, "N/A")
                continue
            if number == 67 and "area_group" in columns and record[columns["area_group"]] and names[1] == "area_square_miles":
                # The published braced denominator belongs to four divisions,
                # not to this row's individual population/dwelling counts.
                literal(title, row, "N/A")
                continue
            refs, nums, guard = values(row, names)
            a, b, target = nums
            if target is None or (rounded_inputs and (a is None or b is None)):
                # Unreadable printed precision cannot be guessed. Rebuild
                # after the source reading has been corrected.
                status = "N/A" if _marked(record[columns[names[2]]]) else "INCOMPLETE"
                literal(title, row, status)
                continue
            tolerance = target[1]
            if rounded_inputs:
                if b[0] <= b[1]:
                    literal(title, row, "N/A")
                    continue
                low = f'({refs[0]}-{a[1]:.16g})/({refs[1]}+{b[1]:.16g})'
                high = f'({refs[0]}+{a[1]:.16g})/({refs[1]}-{b[1]:.16g})'
                condition = f'AND({refs[2]}+{tolerance:.16g}+1E-12>={low},{refs[2]}-{tolerance:.16g}-1E-12<={high})'
                ok = target[0] + tolerance + 1e-12 >= (a[0]-a[1])/(b[0]+b[1]) and target[0]-tolerance-1e-12 <= (a[0]+a[1])/(b[0]-b[1])
            else:
                condition = f'ABS({refs[0]}/{refs[1]}-{refs[2]})<={tolerance:.16g}+1E-12'
                ok = a is not None and b is not None and b[0] != 0 and abs(a[0]/b[0]-target[0]) <= tolerance+1e-12
            formula = f'IF(AND({guard}),IF({refs[1]}=0,"N/A",IF({condition},"PASS","FAIL")),"INCOMPLETE")'
            cached = "INCOMPLETE" if a is None or b is None else "N/A" if b[0] == 0 else "PASS" if ok else "FAIL"
            put(title, row, formula, cached)

    if number in {2, 67, 68}:
        person = "population_total" if number == 2 else "population_persons"
        sum_check("Check: males + females - persons", ["population_males", "population_females", person])
        if number == 2:
            area, occupied = "area_in_acres_or_square_miles", "total_dwellings"
            pop_density, dwelling_density = "population_per_acre_or_square_mile", "dwellings_per_acre_or_square_mile"
            inmates, rooms, per_room = "inmates_per_dwelling", "rooms_per_occupied_dwelling", "inmates_per_room"
            sum_check("Check: private + other - occupied", ["private_dwellings", "other_than_private_dwellings", occupied])
        elif number == 67:
            area, occupied = "area_square_miles", "occupied_dwellings_total"
            pop_density, dwelling_density = "persons_per_square_mile", "occupied_dwellings_per_square_mile"
            inmates, rooms, per_room = "average_inmates_per_occupied_dwelling", "average_rooms_per_occupied_dwelling", "average_inmates_per_room"
            sum_check("Check: private + other - occupied", ["occupied_dwellings_private", "occupied_dwellings_other_than_private", occupied])
        else:
            area, occupied = "area", "occupied_dwellings"
            pop_density, dwelling_density = "population_per_area_unit", "occupied_dwellings_per_area_unit"
            inmates = "population_per_occupied_dwelling"
        ratio_check("Check: persons / area (printed precision)", [person, area, pop_density])
        ratio_check("Check: occupied / area (printed precision)", [occupied, area, dwelling_density])
        ratio_check("Check: persons / occupied (definition)", [person, occupied, inmates], excluded=number in {2, 67})
        if number in {2, 67}:
            # These three means include different unspecified-room/rental
            # populations; their quotient is not a source-established identity.
            ratio_check("Check: inmates / rooms (mixed cohorts: not applicable)",
                        [inmates, rooms, per_room], rounded_inputs=True, excluded=True)

    if number in {8, 9, 57, 58, 59, 60}:
        for col in range(dimension_count, len(headers)):
            title = f"Check: {headers[col]} nonnegative"
            for row, record in enumerate(body):
                raw = record[col]
                if _marked(raw):
                    literal(title, row, "N/A")
                    continue
                ref = f"{xl_col_to_name(col)}{row+3}"
                parsed = _number(raw)
                cached = "INCOMPLETE" if parsed is None else "PASS" if parsed[0] >= 0 else "FAIL"
                put(title, row, f'IF(ISNUMBER({ref}),IF({ref}>=0,"PASS","FAIL"),"INCOMPLETE")', cached)

    if number in {2, 61, 62, 63, 66, 67}:
        for heading in headers[dimension_count:]:
            if not heading.endswith("_shillings"):
                continue
            pence = heading.removesuffix("_shillings") + "_pence"
            if pence not in columns:
                continue
            title = f"Check: {heading.removesuffix('_shillings')} currency units"
            for row, record in enumerate(body):
                refs, nums, guard = values(row, [heading, pence])
                raw = [record[columns[name]] for name in [heading, pence]]
                if any(_marked(v) for v in raw) and all(_marked(v) or not str(v).strip() for v in raw):
                    literal(title, row, "N/A")
                    continue
                if any(n is None for n in nums):
                    cached = "INCOMPLETE"
                else:
                    s, d = nums[0][0], nums[1][0]
                    cached = "PASS" if s >= 0 and s.is_integer() and 0 <= d <= 11 and d.is_integer() else "FAIL"
                s, d = refs
                condition = f'AND({s}>=0,{s}=INT({s}),{d}>=0,{d}<=11,{d}=INT({d}))'
                put(title, row, f'IF(AND({guard}),IF({condition},"PASS","FAIL"),"INCOMPLETE")', cached)
    return checks


def build_fixed_room_checks(number, headers, body, source_table):
    """Compare published per-room measures only within finite fixed-room bins.

    These checks use Tables 59/60 or 61/62's matching geography and measure,
    not the unsupported rental/all-inmate quotient across mixed populations.
    Both published amounts retain their original rounding intervals.
    """
    if number not in (60, 62):
        return {}
    source_number = 59 if number == 60 else 61
    source_headers = source_table["headers"]
    source_columns = {name: index for index, name in enumerate(source_headers)}
    columns = {name: index for index, name in enumerate(headers)}
    source_rows = {}
    for index, record in enumerate(source_table["rows"]):
        source_rows.setdefault(record[0], []).append((index, record))
    checks = {}
    for name in headers[1:]:
        if number == 62 and not name.endswith("_shillings"):
            continue
        fields = [name] if number == 60 else [name, name.removesuffix("_shillings") + "_pence"]
        if not all(field in source_columns and field in columns for field in fields):
            continue
        check_name = f"Check: Table {source_number} / fixed rooms {name}"
        results = checks.setdefault(check_name, {})
        for index, record in enumerate(body):
            room = str(record[0]).strip()
            if not room.isdecimal() or not 1 <= int(room) <= 15:
                results[index] = ('"N/A"', "N/A")
                continue
            matches = source_rows.get(room, [])
            if len(matches) != 1:
                results[index] = ('"INCOMPLETE"', "INCOMPLETE")
                continue
            source_index, source_record = matches[0]
            raw_source = [source_record[source_columns[field]] for field in fields]
            raw_target = [record[columns[field]] for field in fields]
            if all(_marked(value) for value in raw_source + raw_target):
                results[index] = ('"N/A"', "N/A")
                continue
            parsed = [_number(value) for value in raw_source + raw_target]
            if any(value is None for value in parsed):
                results[index] = ('"INCOMPLETE"', "INCOMPLETE")
                continue
            refs_source = [f"'Table {source_number}'!{xl_col_to_name(source_columns[field])}{source_index + 3}" for field in fields]
            refs_target = [f"{xl_col_to_name(columns[field])}{index + 3}" for field in fields]
            if number == 60:
                amount_source, amount_target = parsed
                source_expression, target_expression = refs_source[0], refs_target[0]
            else:
                s, d, ts, td = parsed
                amount_source, amount_target = (12 * s[0] + d[0], d[1]), (12 * ts[0] + td[0], td[1])
                source_expression = f"(12*{refs_source[0]}+{refs_source[1]})"
                target_expression = f"(12*{refs_target[0]}+{refs_target[1]})"
            rooms = int(room)
            tolerance = amount_source[1] / rooms + amount_target[1]
            difference = abs(amount_source[0] / rooms - amount_target[0])
            guard = ",".join(f"ISNUMBER({ref})" for ref in refs_source + refs_target)
            formula = f'IF(AND({guard}),IF(ABS({source_expression}/{rooms}-{target_expression})<={tolerance:.16g}+1E-12,"PASS","FAIL"),"INCOMPLETE")'
            results[index] = (formula, "PASS" if difference <= tolerance + 1e-12 else "FAIL")
    return checks
