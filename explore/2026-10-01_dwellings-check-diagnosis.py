# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf>=1.26", "xlsxwriter>=3.2"]
# ///
"""Investigate Dwellings check failures without changing the workbook or sources.

Inputs: frozen input_snapshot.json, source PDF, current exporter/check rules;
        independently researched room/rent/measure diagnosis JSONs for integration.
Outputs: explore/output/2026-10-01_dwellings-check-diagnosis/ diagnosis records,
         coverage counts, pattern report and formula-dependency evidence.
Run with --parent for generic-table research or --integrate for the complete ledger.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import export_abs_1911_dwellings_workbook as producer
from dwellings_count_checks import _category, _class, _key
from dwellings_numeric import numeric_value

OUT = ROOT / "explore/output/2026-10-01_dwellings-check-diagnosis"
PARENT_TABLES = (set(range(1, 10)) - {2}) | set(range(49, 59))


def decode(value):
    return re.sub(r"_x([0-9a-fA-F]{4})_", lambda m: chr(int(m[1], 16)), str(value))


def references(formula):
    result = set()
    for match in re.finditer(r"\b([A-Z]+)(\d+)(?::([A-Z]+)(\d+))?\b", formula):
        first, row, last, end = match.groups()
        def column(name):
            value = 0
            for char in name:
                value = value * 26 + ord(char) - 64
            return value - 1
        for c in range(column(first), column(last or first) + 1):
            for r in range(int(row), int(end or row) + 1):
                result.add((r, c))
    return sorted(result)


def generic_lineage(data):
    markers, states, areas, panels, methods = producer.read_page_markers()
    raw_rows = defaultdict(dict)
    for cell in data["source_cells"]:
        if not cell["table_id"]:
            continue
        page, y = int(cell["pdf_page"]), float(cell["row_y_pt"])
        fallback = int(cell["table_id"].rsplit("::", 1)[1])
        number = producer.table_at(page, y, markers, fallback)
        if page == 179 and markers.get(page) and y < markers[page][0][0]:
            number = 66
        number = producer.assign_room_table(page, y, number)
        number = producer.assign_rent_table(page, y, number)
        number = producer.assign_state_table(page, y, number)
        if number not in PARENT_TABLES:
            continue
        rows = raw_rows[number]
        row = rows.setdefault(cell["row_id"], {
            "page": page, "y": y, "row_id": cell["row_id"], "label": cell["row_label"],
            "resolved": cell["resolved_row_label"], "cells": {}, "source_text": cell["source_row_text"],
        })
        row["cells"][int(cell["column_index"])] = {
            "label": cell["resolved_column_label"] or cell["column_label"], "value": cell["raw_value"],
        }
    groups = defaultdict(lambda: defaultdict(list))
    for number, rows in raw_rows.items():
        dims, fields, row_field = producer.table_fields(number)
        for row in sorted(rows.values(), key=lambda r: (r["page"], r["y"], r["row_id"])):
            label = (row["label"] or row["resolved"]).strip()
            if not label and all(re.sub(r"\s+", "", c["value"]) in {"", ".", "..", "...", "·", "··", "···", "-", "—"} for c in row["cells"].values()):
                continue
            dimension_values = {field: producer.contextual_value(number, row, field, states, areas, panels, methods) for field in dims}
            if not dimension_values.get(row_field):
                dimension_values[row_field] = label
            key = tuple(dimension_values[d] for d in dims)
            row["dimension_values"] = dimension_values
            row["inflation"] = max(row["cells"], default=0) - len(fields)
            groups[number][key].append(row)
    return groups


def parent_records(data):
    lineage = generic_lineage(data)
    records = []
    for check in data["checks"]:
        number = int(check["table"])
        if number not in PARENT_TABLES:
            continue
        table = data["tables"][str(number)]
        headers = table["headers"]
        body = [[decode(v) for v in row] for row in table["rows"]]
        dims = producer.table_fields(number)[0]
        dim_count = len(dims)
        index = int(check["excel_row"]) - 3
        row = body[index]
        deps = references(check["formula"])
        affected = sorted({r - 3 for r, c in deps if 3 <= r < len(body) + 3}) or [index]
        source = [s for i in affected for s in lineage[number].get(tuple(body[i][:dim_count]), [])]
        own_source = lineage[number].get(tuple(row[:dim_count]), [])
        pages = sorted({s["page"] for s in source})
        row_ids = sorted({s["row_id"] for s in source})
        bad_inputs = []
        for r, c in deps:
            if r < 3 or r - 3 >= len(body) or c >= len(headers):
                continue
            value = body[r - 3][c]
            parsed = numeric_value(value)
            if (parsed is None and not str(value).strip()) or isinstance(parsed, str):
                bad_inputs.append((f"{producer.xl_col_to_name(c)}{r}", value))
        inflated = [s for s in source if s["inflation"] > 0]
        cause, confidence, explanation, evidence, action = "", "supported", "", [], ""
        name = check["check"]
        if check["status"] == "INCOMPLETE" and not deps:
            category_column = next((c for c in range(dim_count) if headers[c] not in ("state", "area_type", "dwelling_class", "method_of_occupancy")), None)
            if number == 1:
                category_column = 0
            if name.startswith("check_private_other_"):
                cls_col = headers.index("dwelling_class")
                category = _category(row[category_column])
                partners = [(i, r) for i, r in enumerate(body) if _category(r[category_column]) == category and all(_key(r[c]) == _key(row[c]) for c in range(dim_count) if c not in (category_column, cls_col))]
                classes = Counter(_class(r[cls_col]) for i, r in partners)
                cause = "missing_or_ambiguous_class_partner"
                explanation = f"Category {row[category_column]!r} has represented class counts {dict(classes)}; the check requires exactly one private, other and all row."
                evidence.append("scripts/dwellings_count_checks.py:217-233; represented worksheet class/category keys")
                if number in (53, 57, 58):
                    explanation += " The PDF class heading is missing from detected page context; private/other rows are blank-labelled or merged into another class."
                    evidence.append(f"page_markers.json: Table {number}; exporter read_page_markers/contextual_value/assemble")
                action = "Recover source class headings and category identities, then rebuild matched-class checks."
                omitted_materials = {"sun_dried_bricks", "pise", "wattle_and_dab", "bark", "bushes_rushes", "calico_canvas_hessian"}
                structural = (
                    category == "wagons" and not classes.get("private")
                    or number == 53 and not classes.get("private") and not classes.get("")
                    or number in (54, 58) and category in omitted_materials and not classes.get("other")
                )
                if structural:
                    cause = "structurally_absent_class_counterpart"
                    explanation = f"Category {row[category_column]!r} has class counts {dict(classes)}. The printed private/nonprivate panel does not list this category, so demanding one printed row in every class is an applicability/structural-absence issue, not evidence that a populated source cell was lost."
                    evidence.append("PDF p115/p116/p117/p125: Private excludes wagons; Table53 Private lists only20–59 ranges; sparse Other material panels omit these material categories.")
                    action = "Document structural absence separately from unreadable data; confirm the published absence convention before treating an unprinted counterpart as zero."
                    if number == 53 and category == "400":
                        explanation += " Only Private is structurally absent here: physical p116 prints Other and All '400 and over', each with Melbourne 1 and total 1. The missing matched Other row is an additional category/assembly defect, not publication absence."
                        evidence.append("Independent image review: physical p116, Table53 Other and All 400-and-over rows.")
                        action += " Recover the printed Other counterpart and its category/class key separately."
            elif name.startswith("check_section_"):
                group = tuple(_key(row[c]) for c in range(dim_count) if c != category_column)
                partners = [r for r in body if tuple(_key(r[c]) for c in range(dim_count) if c != category_column) == group]
                cats = [_category(r[category_column]) for r in partners]
                totals = cats.count("total")
                duplicates = {cat: count for cat, count in Counter(cat for cat in cats if cat not in ("total", "other_camps")).items() if count > 1}
                if 4 <= number <= 9:
                    cause = "collapsed_class_sections"
                    explanation = "The generic schema omits dwelling_class while the printed table has private, other and all sections. Duplicate row labels are merged with first-value precedence; section checks deliberately refuse this collapsed representation."
                    evidence.append("scripts/export_abs_1911_dwellings_workbook.py:288-292,433-450; scripts/dwellings_count_checks.py:197-200")
                elif not all(group):
                    cause = "missing_section_context"
                    explanation = f"Section identity contains a blank dimension: {group}; context lookup cannot identify the printed class/method and the check is a static INCOMPLETE."
                    evidence.append("scripts/export_abs_1911_dwellings_workbook.py:175-188,221-227,375-381; scripts/dwellings_count_checks.py:196")
                elif totals != 1:
                    cause = "missing_or_duplicate_section_total"
                    explanation = f"Section {group} contains {totals} represented total rows, not exactly one; no defensible total-minus-parts identity can be generated."
                    evidence.append("scripts/dwellings_count_checks.py:193-214")
                elif duplicates or "" in cats:
                    cause = "ambiguous_category_identity"
                    explanation = f"Section {group} has duplicate canonical categories {duplicates} or empty category labels; adding these rows could double-count or mix different brackets."
                    evidence.append("scripts/dwellings_count_checks.py:32-63,193-196; source rental labels and represented keys")
                else:
                    cause = "unrepresented_section_identity"
                    explanation = f"Section {group} does not meet complete represented-component requirements; the emitted check has no worksheet input references."
                    evidence.append("scripts/dwellings_count_checks.py:124-130,193-214")
                action = "Restore complete source sections, totals and mutually exclusive labels; do not infer totals."
            else:
                raise ValueError(f"Unclassified static incomplete: {check}")
            confidence = "confirmed"
        elif check["status"] == "INCOMPLETE":
            cause = "missing_or_unreadable_required_cells"
            confidence = "confirmed"
            explanation = "The formula's numeric guard fails for " + "; ".join(f"{cell}={value!r}" for cell, value in bad_inputs) + ". Blank candidates are not printed zero; nonnumeric count readings cannot be used."
            if not bad_inputs:
                raise ValueError(f"Incomplete with no missing inputs: {check}")
            evidence.append("Exact referenced baseline values and current numeric guard; numeric_value/NO_VALUE semantics")
            if inflated:
                explanation += " Related source rows also contain extra candidate columns, so some missing values are downstream of column truncation."
            action = "Inspect the named cells and original row geometry; recover missing values from the source rather than arithmetic residuals."
        elif name == "check_unreadable_numeric_fields":
            nonnumeric = [(f"{producer.xl_col_to_name(c)}{index+3}", value) for c, value in enumerate(row) if c >= dim_count and isinstance(numeric_value(value), str)]
            rental = any(re.search(r"(?:\d+s\.|£)", value, re.I) for cell, value in nonnumeric)
            cause = "rental_label_in_numeric_column" if rental else "unresolved_numeric_transcription"
            explanation = "Numeric field(s) contain " + "; ".join(f"{cell}={value!r}" for cell, value in nonnumeric) + "."
            if rental:
                explanation += " Upper rent-bracket text has been returned as a data cell; remaining counts shift right and later geographies/total may be discarded."
                evidence.append("PDF p118 Table55 24s-under25s row: bracket upper endpoint 25s is not Sydney's dwelling count; source candidate p118::r27")
                confidence = "confirmed"
            else:
                readings = {
                    (49, 172): ("source_glyph_read_error", "confirmed", "PDF p112 £8-under£9: WA prints 1, not letter I."),
                    (52, 11): ("source_glyph_read_error", "confirmed", "PDF p115 Private room9: Hobart prints 261, not 26J."),
                    (53, 40): ("source_reading_or_alignment_disagreement", "supported", "PDF p116 All Dwellings 300-and-under400 row: Brisbane has a printed absence mark, not fraction ½. Brisbane 141 belongs to the separate Total row and is not a replacement for E40. Glyph recognition, column displacement or row assignment remains to be established from the candidate mapping."),
                    (56, 20): ("damaged_printed_count_digit", "unresolved", "PDF p121 printed 17s-under18s owner row shows Melbourne 1, 80 with an unreadable/missing hundreds glyph; the model also labels this row18s. Total2600 suggests1180 but does not establish that digit."),
                }
                cause, confidence, detail = readings[(number, index + 3)]
                explanation += " " + detail
                evidence.append(detail)
            action = "Separate rental-label geometry from numeric cells, or read the damaged digit from its source image."
        elif number == 7:
            cause = "unlabelled_row_merge"
            confidence = "confirmed"
            explanation = "The blank category combines an orphan 1484 fragment on p10 with unrelated p12 camp/total fragments. First-value precedence splices NSW=1484 into the later category, so this is not one printed row."
            evidence.append("source row p10::r4 versus p12::r62/r63; exporter assemble group key and setdefault at433-450")
            action = "Attach each fragment to its actual printed row; never merge all missing labels into one category."
        elif number == 58 and name.startswith("check_section_"):
            cause = "other_class_row_misassigned_to_private"
            confidence = "confirmed"
            explanation = "The Other-than-private heading is absent from page context. Its Wagons row is placed in Private; the private subtotal residual exactly equals the extraneous wagons count (637,5,6,4,0,0,total652)."
            evidence.append("PDF p125 Table58 Other Wagons=637,5,6,4,dots,dots,652; source p125::r48 y632.88; page_markers p125 has Private413.36 and All662.71 but no Other")
            action = "Recover the Other heading and reassign its rows before recalculating section totals."
        elif inflated:
            cause = "leader_or_label_columns_shift_data"
            explanation = f"{len(inflated)} contributing candidate row(s) contain more columns than the {len(headers)-dim_count} printed geography fields. Leader dots/label tokens are mapped as quantities, displacing values and dropping overflow."
            if name.startswith("check_section_") or name.startswith("check_private_other_"):
                explanation += " This is an aggregate/matched-class symptom; it does not establish an independent error in the printed total."
            evidence.append("exporter header_index354-362 and assemble438-450; candidate column indexes/values versus fixed geography schema")
            evidence.append("Image anchors: p8 Table5 private20–24=275,206,65,42,21,26,dot,1,636; p115 Table52 All room1=1438,736,550,452,474,80,3730; p117 Table54 All Stone=5172,2139,115,21342,2039,728,31535; p114 Table51 Total=123234,119562,27532,38742,21897,8082,339049")
            action = "Re-map only the printed numeric grid; discard structural dots and label tokens before assigning geography columns."
        elif number in (5, 8):
            cause = "cross_class_values_merged"
            explanation = "Private/other/all panels share the same category key because the schema omits dwelling_class. First-value precedence selects different panels by column; the represented row is not a coherent printed class row."
            evidence.append("PDF p8/p13–14 class panels; exporter288-292 and433-450")
            action = "Preserve class as a dimension and recover each panel separately."
        elif number == 53:
            cause = "candidate_truncated_after_label_leaders"
            confidence = "confirmed"
            explanation = "Candidate width is already capped at seven fields, but leading rental-range ditto/leader tokens occupy two or four of them. Real geographic quantities shift right and trailing cities/Total never enter the payload. Section checks propagate those malformed rows."
            evidence.append("PDF p116 Other Total=430,374,129,146,157,50,1286; baseline=dot,dot,430,374,129,146,157. All20–24=211,235,60,84,49,34,673; baseline=dot,dot,dot,dot,211,235,60. Other200–300=5,3,dots,dots,dots,dots,8.")
            action = "Recover the complete geographic row from its printed grid; payload length alone cannot detect a previously truncated shift."
        elif number == 55:
            cause = "rent_lower_bound_mislabelled"
            confidence = "confirmed"
            explanation = "The All row labelled13s contains the printed12s-under13s quantities. It is compared with genuine13s-under14s private/other rows; all seven geographic failures are a category-join error, not seven independent digit errors."
            evidence.append("PDF p118 private13s=5424,3982,471,886,461,224,11448; p119 other13s=54,83,9,2,6,5,159; p120 All12s=10922,10254,2738,3220,1921,637,29692 and All13s=5478,4065,480,888,467,229,11607; candidate p120::r14 is mislabelled13s.")
            action = "Identify rental intervals from printed lower and upper bounds, not the model's row label alone."
        elif number == 49 and len(own_source) > 1:
            cause = "duplicate_or_orphan_rent_row_merge"
            confidence = "confirmed"
            explanation = "Different printed rent rows/fragments have the same model label and occupancy context. First-value precedence merges them and ignores later correct values; the result is not one coherent printed bracket."
            evidence.append("PDF p112 and source p112::r52/r54/r60 quote-only labels, r56/r57 both labelled£6, r62/r63 labelled£10-and-over, r64/r65 labelledUnspecified. Printed Unspecified=16627,13321,4619,3016,3256,1813,49,39,42740; baseline keeps preceding fragment dots/SA1/Total3.")
            action = "Restore each row's printed bracket and distinguish fragmented row boxes before key-based assembly."
        elif number == 49 and index + 3 == 113:
            cause = "populated_source_count_omitted"
            confidence = "confirmed"
            explanation = "The rent-purchaser £6-under£7 row has Victoria1 and SouthAustralia1, Total2. The candidate omits SouthAustralia1, giving represented sum1 and delta1."
            evidence.append("PDF p111 y739.64 image; source p111::r50; baseline F113 is a no-value mark although its printed SouthAustralia cell is1.")
            action = "Read the omitted SouthAustralia cell from the source grid; do not fill it from Total2."
        elif number == 49 and index + 3 == 116:
            cause = "candidate_truncated_after_label_leaders"
            confidence = "confirmed"
            explanation = "Two leading label dots precede the actual Unspecified geography counts, but the payload contains only nine fields. Counts are shifted two columns and the genuine total3136 is discarded."
            evidence.append("PDF p111 Unspecified=886,1206,355,332,211,144,dots,2,3136; baseline=dot,dot,886,1206,355,332,211,144,2; source p111::r55.")
            action = "Recover the complete numeric grid and exclude label leaders."
        elif number == 51:
            cause = "interior_punctuation_shifts_geographies"
            confidence = "confirmed"
            explanation = "A standalone dash before Perth296 is treated as a separate no-value field. Perth becomes blank, Hobart receives296 and Total receives142; genuine Total4837 is lost."
            evidence.append("PDF p114 Tenement row=1794,1362,425,818,296,142,4837; candidate/baseline=1794,1362,425,818,dash,296,142.")
            action = "Bind the punctuation and quantity to the actual printed column, not one model token per field."
        elif number == 56 and index + 3 == 63:
            cause = "populated_source_counts_misplaced_and_omitted"
            confidence = "confirmed"
            explanation = "The rent-purchaser Under1s source has Sydney1 and Adelaide1, Total2. The candidate retains only one1, in Brisbane, so both position and a populated cell are wrong."
            evidence.append("PDF p122 first Occupied-by-rent-purchasers row; source p122::r2; baseline C63:D63 blank,E63=1,F63 blank,I63=2.")
            action = "Recover Sydney and Adelaide directly from the source and retain the rent-purchaser context."
        elif number == 56 and index + 3 == 137:
            cause = "source_blank_or_damage_and_candidate_misalignment"
            confidence = "supported"
            explanation = "Source3s-under4s shows9,8,no visible Queensland figure,4,7,3,Total40. Candidate is9,8,4,7,3,3,40: it shifts later cities and duplicates3. Even interpreting the source blank as zero leaves a9 gap; a missing/damaged Queensland glyph or printed arithmetic defect is possible but not established."
            evidence.append("PDF p123 y587.25 source image; p123::r50; source visible populated counts sum31, represented counts sum34. Inferring Queensland9 from Total40 is not a source reading.")
            action = "Check an alternate scan/original for the Queensland glyph; preserve the ambiguity and repair the proven positional mismatch separately."
        elif number == 56 and index + 3 == 161:
            cause = "printed_total_digit_damage_or_original_error"
            confidence = "supported"
            explanation = "The source27s-under28s component cells read6,12,1,3,1,no value, summing23, while the scanned Total shows3. This may be a missing/damaged leading2 or an original total error, not a confirmed model transcription correction."
            evidence.append("PDF p123 y779.60 full-width crop and p123::r74; both candidate and visible Total are3.")
            action = "Seek an alternate source copy before changing the Total; do not manufacture its leading2 from the residual."
        else:
            cause = "numeric_or_row_identity_mismatch"
            explanation = "The represented numeric inputs produce this nonzero residual, but no inflated-width contributor identifies a simple leader shift. Inspect the exact referenced row/category and candidate sequence for digit, omitted-cell, bracket-label or identity errors."
            if number == 55:
                explanation += " Table55 source labels often lag one printed rental bracket (e.g. p120 candidate row labelled24s describes printed23s-under24s), so matched-class rows need lower-bound confirmation."
                evidence.append("p120::r25 source_row_text versus candidate row_label; compare printed lower rent bounds")
            if number == 56:
                explanation += " Table56 has undetected rent-free/rented section context and incorrect bracket labels; the small residual is not proof of a census arithmetic error."
            evidence.append("Explicit formula dependency values and source-row provenance; individual digit/identity diagnosis remains unresolved")
            confidence = "unresolved"
            action = "Review the exact formula inputs on the indicated PDF row; distinguish label identity from digit error before any repair."
        evidence.extend([f"source_rows={','.join(row_ids)}", f"pdf_pages={','.join(map(str,pages))}"])
        records.append({
            "check_id": check["check_id"], "table": number, "excel_row": int(check["excel_row"]),
            "check": name, "status": check["status"], "cause": cause, "confidence": confidence,
            "explanation": explanation, "evidence": "; ".join(evidence), "source_pages": pages,
            "related_cells": [f"{producer.xl_col_to_name(c)}{r}" for r,c in deps],
            "source_row_ids": row_ids, "next_action": action,
        })
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", action="store_true")
    parser.add_argument("--integrate", action="store_true")
    args = parser.parse_args()
    if not args.parent and not args.integrate:
        parser.error("Choose --parent or --integrate.")
    data = json.loads((OUT / "input_snapshot.json").read_text())
    if args.parent:
        records = parent_records(data)
        (OUT / "generic_tables.json").write_text(json.dumps({"records": records, "patterns": [], "summary": dict(Counter(r["cause"] for r in records))}, indent=2))
        print("Generic-table check coverage:", len(records), dict(Counter(r["status"] for r in records)))
        print("Causes:", dict(Counter(r["cause"] for r in records)))
    if args.integrate:
        records = []
        for filename in ("generic_tables.json", "room_tables.json", "rent_tables.json", "measure_tables.json"):
            records.extend(json.loads((OUT / filename).read_text())["records"])
        expected = {r["check_id"] for r in data["checks"]}
        actual = Counter(r["check_id"] for r in records)
        missing = sorted(expected - actual.keys())
        extra = sorted(actual.keys() - expected)
        duplicates = [key for key,count in actual.items() if count != 1]
        if missing or extra or duplicates:
            raise ValueError({"missing": missing, "extra": extra, "duplicates": duplicates})
        originals = {r["check_id"]:r for r in data["checks"]}
        for row in records:
            original = originals[row["check_id"]]
            for field in ("table", "excel_row", "check", "status"):
                if str(row[field]) != str(original[field]):
                    raise ValueError(f"Identity mismatch {row['check_id']}/{field}")
            for field in ("cause", "confidence", "explanation", "evidence", "next_action"):
                if not row.get(field):
                    raise ValueError(f"Missing {field}: {row['check_id']}")
            row["result"] = original["result"]
            row["formula"] = original["formula"]
            row["row_label"] = original["row_label"]
        records.sort(key=lambda r:r["check_id"])
        fields = ["check_id", "table", "excel_row", "check", "status", "result", "row_label", "cause", "confidence", "explanation", "evidence", "source_pages", "related_cells", "next_action", "formula"]
        with (OUT / "diagnosis.csv").open("w",newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for row in records:
                writer.writerow({k: json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()})
        counts = Counter((r["status"],r["cause"],r["confidence"]) for r in records)
        with (OUT / "patterns.csv").open("w",newline="") as stream:
            writer = csv.writer(stream); writer.writerow(["status","cause","confidence","checks"])
            writer.writerows([(*key,count) for key,count in sorted(counts.items())])
        with (OUT / "table_summary.csv").open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["table", "title", "failed_checks", "incomplete_checks", "primary_patterns"])
            for number in range(1, 69):
                rows = [r for r in records if int(r["table"]) == number]
                status = Counter(r["status"] for r in rows)
                causes = Counter(r["cause"] for r in rows)
                writer.writerow([number, data["tables"][str(number)]["title"], status["FAIL"], status["INCOMPLETE"],
                                 "; ".join(f"{cause}: {count}" for cause, count in causes.most_common(4))])
        summary = {"reviewed":len(records),"expected":len(expected),"missing":len(missing),"extra":len(extra),"duplicates":len(duplicates),"status":dict(Counter(r["status"] for r in records)),"confidence":dict(Counter(r["confidence"] for r in records))}
        (OUT / "coverage.json").write_text(json.dumps(summary,indent=2))
        print(json.dumps(summary,indent=2))


if __name__ == "__main__":
    main()
