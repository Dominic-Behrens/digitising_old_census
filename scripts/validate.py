"""Validate NSW LGA completeness and every independently published NSW total.

No blanks become zero and no values are adjusted to balance. A source-backed
publication discrepancy is recorded separately from extraction/data failures.
Inputs: data/intermediate/nsw_1911_lga_dwellings.csv and
        output/extract_table68/published_totals.csv.
Outputs: output/validate/validation_checks.csv, validation.json,
         and publication_inconsistencies.csv.
"""
import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import re

from extract_table68 import (AUDIT_DIR, CSV_FIELDS, EXPECTED_COUNTS, INTEGER_FIELDS,
                             NUMERIC_FIELDS, OUT, PUBLISHED_TOTALS, ROOT, write_csv)

CHECK_FIELDS = ["status", "check", "scope", "field", "observed", "expected",
                "source_pdf_page", "source_printed_page", "detail"]
VALIDATION_DIR = ROOT / "output/validate"


def to_int(s):
    """Parse an integer strictly: absent/broken observations are not zero."""
    if not re.fullmatch(r"\d+", s):
        raise ValueError(f"Not a non-negative integer observation: {s!r}")
    return int(s)


def load_rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def collect_checks(rows, totals):
    checks = []

    def add(kind, scope, field, observed, expected, source=None, detail=""):
        source = source or {}
        checks.append({"status": "pass" if observed == expected else "error",
                       "check": kind, "scope": scope, "field": field,
                       "observed": str(observed), "expected": str(expected),
                       "source_pdf_page": source.get("source_pdf_page", ""),
                       "source_printed_page": source.get("source_printed_page", ""),
                       "detail": detail})

    def numeric(row, scope, fields):
        parsed = {}
        for field in fields:
            value = row.get(field) or ""
            try:
                if field in INTEGER_FIELDS:
                    parsed[field] = Decimal(to_int(value))
                else:
                    if not re.fullmatch(r"\d+(?:\.\d+)?", value):
                        raise ValueError("Invalid decimal observation")
                    parsed[field] = Decimal(value)
            except (ValueError, InvalidOperation):
                add("numeric_cell", scope, field, value, "non-negative numeric observation", row)
        return parsed

    def arithmetic(values, scope, source):
        if all(field in values for field in ("males", "females", "persons")):
            add("sex_additivity", scope, "persons", values["males"] + values["females"],
                values["persons"], source, "Males + females must equal persons exactly.")
        for field, numerator, denominator, quantum in [
            ("persons_per_area", "persons", "area", "0.01"),
            ("dwellings_per_area", "occupied_dwellings", "area", "0.001"),
            ("population_per_dwelling", "persons", "occupied_dwellings", "0.01"),
        ]:
            if not all(key in values for key in (field, numerator, denominator)):
                continue
            if values[denominator] == 0:
                add("ratio_denominator", scope, denominator, 0, "positive", source)
                continue
            calculated = (values[numerator] / values[denominator]).quantize(
                Decimal(quantum), rounding=ROUND_HALF_UP)
            add("printed_ratio", scope, field, calculated, values[field], source,
                f"Recomputed at printed precision; per-area denominator is {source.get('area_unit', '')}.")

    keys = [(r.get("section"), r.get("lga_name")) for r in rows]
    add("unique_lga", "all_lgas", "section+lga_name", len(set(keys)), len(keys))
    row_ids = [(r.get("source_page_index"), r.get("source_row_number")) for r in rows]
    add("unique_source_row", "all_lgas", "page_index+row_number", len(set(row_ids)), len(row_ids))
    add("row_count", "all_lgas", "rows", len(rows), sum(EXPECTED_COUNTS.values()))
    expected_groups = {(str(page), section) for page, section in EXPECTED_COUNTS}
    observed_groups = {(r.get("source_page_index") or "", r.get("section") or "") for r in rows}
    add("source_extent", "all_lgas", "page_index+section", sorted(observed_groups), sorted(expected_groups))
    for (page, section), count in EXPECTED_COUNTS.items():
        selected = [r for r in rows if r.get("source_page_index") == str(page) and r.get("section") == section]
        add("row_count", f"index_{page}/{section}", "rows", len(selected), count,
            {"source_pdf_page": page + 1, "source_printed_page": page + 1849})
    parsed_rows = []
    for row in rows:
        scope = f"{row.get('section', '')}/{row.get('lga_name', '')}"
        missing = [field for field in CSV_FIELDS if not (row.get(field) or "").strip()]
        add("row_completeness", scope, "required_fields", ",".join(missing), "", row)
        unit = "acres" if row.get("section") == "municipality" else "square_miles"
        add("area_unit", scope, "area_unit", row.get("area_unit"), unit, row)
        try:
            page = int(row.get("source_page_index") or "")
            add("page_numbering", scope, "source_pdf_page", row.get("source_pdf_page"), str(page + 1), row)
            add("page_numbering", scope, "source_printed_page", row.get("source_printed_page"), str(page + 1849), row)
            add("printed_table_number", scope, "source_table_number_printed",
                row.get("source_table_number_printed"), "69" if page == 185 else "68", row)
        except ValueError:
            add("page_numbering", scope, "source_page_index", row.get("source_page_index"), "integer", row)
        values = numeric(row, scope, NUMERIC_FIELDS)
        arithmetic(values, scope, row)
        parsed_rows.append((row, values))

    expected_total_ids = sorted(total[0] for total in PUBLISHED_TOTALS)
    add("published_total_completeness", "published_totals", "total_ids",
        sorted(row.get("total_id") or "" for row in totals), expected_total_ids)
    parsed_totals = {}
    for total in totals:
        total_id = total.get("total_id") or ""
        applicable = ["males", "females", "persons"] if total_id in (
            "shipping_summary", "total_population") else NUMERIC_FIELDS
        values = numeric(total, total_id, applicable)
        arithmetic(values, total_id, total)
        parsed_totals[total_id] = (total, values)
        if total.get("group") not in ("municipality", "shire"):
            continue
        selected = [(r, v) for r, v in parsed_rows if r.get("section") == total["group"]]
        for field in sorted(INTEGER_FIELDS):
            if field not in values or any(field not in v for _, v in selected):
                add("published_total", total_id, field, "incomplete observations", total.get(field), total)
                continue
            calculated = sum((v[field] for _, v in selected), Decimal(0))
            add("published_total", total_id, field, calculated, values[field], total,
                "Independent printed subtotal/summary compared with extracted LGA rows.")

    # State total adds municipal area in acres only after converting at 640 acres
    # per square mile. Not-incorporated and shipping are not LGA rows.
    for total_id, components, fields in [
        ("whole_state_summary", ["municipality_summary", "shire_summary", "not_incorporated_summary"],
         sorted(INTEGER_FIELDS)),
        ("total_population", ["whole_state_summary", "shipping_summary"], ["males", "females", "persons"]),
    ]:
        if total_id not in parsed_totals:
            continue
        total, target = parsed_totals[total_id]
        for field in fields:
            if field not in target or any(c not in parsed_totals or field not in parsed_totals[c][1] for c in components):
                add("published_summary_additivity", total_id, field, "incomplete observations", total.get(field), total)
                continue
            calculated = Decimal(0)
            for component in components:
                source, values = parsed_totals[component]
                value = values[field]
                if field == "area" and source["area_unit"] == "acres":
                    value /= 640
                calculated += value
            add("published_summary_additivity", total_id, field, calculated, target[field], total,
                " + ".join(components) + ("; municipal acres / 640" if field == "area" else ""))
    return checks


def main():
    rows = load_rows(OUT)
    totals = load_rows(AUDIT_DIR / "published_totals.csv")
    checks = collect_checks(rows, totals)
    errors = [check for check in checks if check["status"] == "error"]
    write_csv(VALIDATION_DIR / "validation_checks.csv", CHECK_FIELDS, checks)
    # Source headings really disagree; this is not a numeric extraction failure.
    # No numerical publication inconsistencies were found in the image-backed
    # reconstruction. Unexplained numerical failures remain errors, not waivers.
    publication = [{
        "kind": "printed_table_number_discrepancy", "numeric": False,
        "source_page_index": 185, "source_pdf_page": 186, "source_printed_page": 2034,
        "observed": "69", "comparison": "68 in contents and adjacent NSW continuation headings",
        "action": "Retain the printed 69 and the same NSW analytical table; do not alter any numeric data.",
    }]
    write_csv(VALIDATION_DIR / "publication_inconsistencies.csv", list(publication[0]), publication)
    summary = {"status": "pass" if not errors else "fail", "rows": len(rows),
               "municipalities": sum(r["section"] == "municipality" for r in rows),
               "shires": sum(r["section"] == "shire" for r in rows),
               "checks": len(checks), "failed_checks": len(errors),
               "independent_published_rows": len(totals),
               "confirmed_numerical_publication_inconsistencies": 0,
               "printed_heading_discrepancies": len(publication),
               "data": OUT.relative_to(ROOT).as_posix(),
               "checks_file": "output/validate/validation_checks.csv",
               "errors": errors}
    (VALIDATION_DIR / "validation.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"{summary['municipalities']} municipalities + {summary['shires']} shires = {len(rows)} LGAs")
    for check in checks:
        if check["check"] in ("published_total", "published_summary_additivity"):
            print(f"{check['status'].upper()}: {check['scope']} {check['field']}: "
                  f"{check['observed']} vs printed {check['expected']}")
    print(f"{len(checks) - len(errors)}/{len(checks)} checks passed; {len(errors)} errors.")
    print("Source publication discrepancy: physical page 186/index 185 prints 69, not the contents' 68.")
    for error in errors:
        print(f"ERROR: {error['scope']} {error['check']} {error['field']}: "
              f"{error['observed']!r} vs {error['expected']!r}")
    print(f"Reports: {VALIDATION_DIR}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
