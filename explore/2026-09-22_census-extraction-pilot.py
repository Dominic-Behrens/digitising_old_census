# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf>=1.24"]
# ///
"""Pilot: extract source table fragments with DeepSeek V4.1 Flash, not production data.

Inputs: reviewed page/index CSVs, original PDFs, and verified NSW CSV (checks only).
Outputs: explore/output/2026-09-22_census-extraction-pilot/ (requests, cells, checks).
Run: uv run explore/2026-09-22_census-extraction-pilot.py --run --max-cost-usd 5
Without --run, prepare images and rebuild reports from cached responses, offline.
"""
from __future__ import annotations

import argparse
import base64
import copy
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import shlex
import sys
import time
import urllib.error
import urllib.request

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from classify_pdf_pages_openrouter import get_api_key, post_openrouter, extract_json_object

MODEL = "deepseek/deepseek-v4.1-flash"
DEFAULT_OUT = Path("explore/output/2026-09-22_census-extraction-pilot")
REVIEWED = ROOT / "output/build_abs_1911_table_spans"
# Token-price caps are enforced by OpenRouter; reserve a full context per attempt.
PRICE_CAP = {"prompt": 0.30, "completion": 1.20, "request": 0, "image": 0}
CONTEXT_LIMIT = 1048576
REASONING = {"enabled": False}
SYSTEM = "You transcribe historical census tables from page images. Return only JSON. Never repair values to balance totals."
PROMPT = """Transcribe ONLY the requested analytical table from these source images.
The reviewed mapping is evidence, not proof of completeness. Examine adjacent images.
Never borrow numbers from a different table stacked on the same page. Match title,
sex, row labels, geography and column headings across horizontal spreads. Preserve
left/right halves as separate fragments, with stable column IDs; do not duplicate
or fill missing cells. Preserve a visible printed number even if it differs from
the contents number (especially 7 versus 8). Do not silently renumber a heading.

Extract relevant table fragments on target pages AND relevant fragments found on
context pages. Label their membership accurately: target or context. Context-only
cells will be quarantined, not added to the accepted map. A context page with no
part of this table must contribute no fragment. Flag any mapping discrepancy.

Keep raw printed values as strings, including dots, dashes, decimals and footnote
marks. Blank = null. Illegible = null with that column ID in uncertain_columns.
Never interpret dots/blanks/dashes as zero, and never infer a digit from a total.
Read all rows, totals and footnotes. Keep grouping headings separate from data;
summary rows that duplicate detailed rows are not additional observations.
Split fragments when page, section or units change. Preserve historical exclusion
wording without endorsing it. Units must come from the source; unknown = null.
For NSW LGA sections use section municipality, shire or summary. Otherwise retain
the printed section. Keep LGA names separate from leader dots/footnote marks.

Output this exact JSON shape (no markdown):
{"complete":true,"warnings":[],"context_findings":[],"fragments":[
 {"pdf_page":1,"membership":"target","region":"top",
  "bbox":[0,0,1000,1000],"printed_page":"1","printed_table_number":null,
  "title":"verbatim title when visible","section":"printed section",
  "notes":["source footnotes/exclusions, verbatim"],
  "columns":[{"id":"stable_key","label":"full hierarchical printed header","unit":"persons"}],
  "rows":[{"label":"printed row label","kind":"data","values":["123"],"uncertain_columns":[]}]
 }]}
Use kind data, heading, subtotal or total. Each values array must have exactly one
entry per column, in column order (all null for a pure heading). bbox is an
approximate source table rectangle in 0–1000 page coordinates, not a precision
measurement. The enclosing page, fragment, row and column identify each cell.
context_findings is a list of {pdf_page, reason} for relevant omitted table parts.
complete is false if ANY supplied target portion cannot be fully transcribed.
Do not truncate a table or replace rows with ellipses. Use the supplied column IDs
where applicable; other genuinely printed columns need distinct descriptive IDs.
"""


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temp.replace(path)


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def numeric(raw):
    if raw is None or not str(raw).strip():
        return None, "blank"
    text = str(raw).strip()
    # Grouping commas and the historical centred decimal point are typographic.
    if not re.fullmatch(r"[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:[.·]\d+)?|[.·]\d+", text):
        return None, "uninterpreted_mark_or_text"
    return str(Decimal(text.replace(",", "").replace("·", "."))), "numeric"


def make_jobs():
    catalogue = {(r["doc_id"], r["table_number"]): r for r in read_csv(REVIEWED / "abs_1911_reviewed_table_index.csv")}
    mapped = {(r["doc_id"], int(r["pdf_page"])): r for r in read_csv(REVIEWED / "abs_1911_reviewed_pages.csv")}
    ages = "1911_census_volume_ii_part_i_ages"
    dwellings = "1911_census_volume_iii_part_xiii_dwellings"
    summary = "1911_census_volume_iii_part_xiv_summary"
    ages_columns = [f"age_{n}_{n+4}" for n in range(0, 100, 5)] + ["age_100_plus", "unspecified", "total"]
    specs = [
        ("summary_27", summary, "27", [33], [32, 34],
         [f"{region}_{sex}" for region in ["adelaide", "remainder", "state"] for sex in ["males", "females", "total"]], "single-page hierarchical columns; 7/8 heading"),
        ("ages_33", ages, "33", [60, 61], [59, 62], ages_columns, "horizontal spread; shared pages"),
        ("ages_34", ages, "34", [60, 62], [59, 61, 63], ages_columns, "interrupted accepted mapping; context completeness check"),
    ]
    for page in range(183, 188):
        context = sorted({183, page-1, page+1} - {page})
        specs.append((f"nsw_lga_{page}", dwellings, "68", [page], context,
                      ["area", "males", "females", "persons", "persons_per_area", "occupied_dwellings", "dwellings_per_area", "population_per_dwelling"],
                      "NSW subsection benchmark; mixed area units and printed 69"))
    jobs = []
    for job_id, doc, number, targets, context, columns, purpose in specs:
        entry = catalogue[(doc, number)]
        expected = {int(p) for p in entry["observed_pdf_pages"].split(" | ")}
        if not set(targets) <= expected:
            raise ValueError(f"Pilot target no longer matches reviewed map: {job_id}")
        jobs.append({"job_id": job_id, "doc_id": doc, "table_number": number,
                     "table_title": entry["table_title"], "source_pdf": entry["local_path"].replace("\\", "/"),
                     "target_pages": targets, "context_pages": context, "column_ids": columns,
                     "purpose": purpose, "scope": "NSW only, not all Table 68" if number == "68" else "mapped table portions",
                     "mapped_printed_labels": {str(p): mapped[(doc, p)]["final_table_numbers"] for p in targets}})
    return jobs


def prepare(jobs, out, dpi):
    if jobs and "regions" in jobs[0]:
        return prepare_regions(jobs, out, dpi)
    evidence = out / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for job in jobs:
        source = ROOT / job["source_pdf"]
        if source not in hashes:
            hashes[source] = hashlib.sha256(source.read_bytes()).hexdigest()
        job["source_sha256"] = hashes[source]
        job["images"] = {}
        with pymupdf.open(source) as pdf:
            for page in sorted(set(job["target_pages"] + job["context_pages"])):
                image = evidence / f"{job['doc_id']}_{page}_{dpi}dpi.jpg"
                # Regenerate from immutable source; no stale image cache assumptions.
                pix = pdf[page-1].get_pixmap(matrix=pymupdf.Matrix(dpi/72, dpi/72), alpha=False)
                image.write_bytes(pix.tobytes("jpeg", jpg_quality=92))
                job["images"][str(page)] = {"path": image.relative_to(out).as_posix(),
                    "sha256": hashlib.sha256(image.read_bytes()).hexdigest()}
    write_json(out / "manifest.json", jobs)
    (out / "prompt.txt").write_text(SYSTEM + "\n\n" + PROMPT)


def payload(job, out, max_tokens):
    metadata = {k: v for k, v in job.items() if k != "images"}
    prompt = REGION_PROMPT if "regions" in job else PROMPT
    metadata = {k: v for k, v in metadata.items() if not k.startswith("baseline_")}
    content = [{"type": "text", "text": prompt + "\nTask metadata:\n" + json.dumps(metadata)}]
    for page, image in job["images"].items():
        if image.get("role") == "provenance_only":
            continue
        if "regions" in job:
            label = image["label"]
        else:
            role = "TARGET" if int(page) in job["target_pages"] else "CONTEXT ONLY"
            label = f"Physical PDF page {page}; {role}."
        content.append({"type": "text", "text": label})
        content.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode((out / image["path"]).read_bytes()).decode()}})
    provider = {"max_price": PRICE_CAP, "require_parameters": True}
    if "regions" in job:
        sorts = {r.get("provider_sort") for r in job["regions"]}
        if sorts not in ({None}, {"throughput"}):
            raise ValueError("A region job must use one consistent supported provider policy")
        if sorts == {"throughput"}:
            provider["sort"] = "throughput"
    return {"model": MODEL, "temperature": 0, "max_tokens": max_tokens,
            "reasoning": REASONING,
            "response_format": {"type": "json_object"}, "provider": provider,
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": content}]}


def fingerprint(job, max_tokens):
    prompt = REGION_PROMPT if "regions" in job else PROMPT
    return hashlib.sha256(json.dumps([job, SYSTEM, prompt, MODEL, max_tokens, PRICE_CAP, REASONING], sort_keys=True).encode()).hexdigest()


def validate_response(parsed, job):
    if not isinstance(parsed.get("complete"), bool) or not isinstance(parsed.get("fragments"), list) or not parsed["fragments"]:
        raise ValueError("Missing completeness flag or table fragments")
    for fragment in parsed["fragments"]:
        page = fragment["pdf_page"]
        if type(page) is not int or str(page) not in job["images"]:
            raise ValueError("Fragment refers to an unsupplied source page")
        expected = "target" if page in job["target_pages"] else "context"
        if fragment["membership"] != expected:
            raise ValueError("Context fragment mislabelled as target, or reverse")
        columns = fragment["columns"]
        ids = [c["id"] for c in columns]
        if not ids or len(set(ids)) != len(ids) or not fragment["rows"]:
            raise ValueError("Empty fragment or duplicate column keys")
        for column in columns:
            if not isinstance(column["label"], str) or not isinstance(column["unit"], (str, type(None))):
                raise ValueError("Invalid column metadata")
        if len(fragment["bbox"]) != 4 or not all(isinstance(n, (int, float)) and 0 <= n <= 1000 for n in fragment["bbox"]):
            raise ValueError("Invalid source region")
        for row in fragment["rows"]:
            if row["kind"] not in {"data", "heading", "subtotal", "total"} or not isinstance(row["label"], str):
                raise ValueError("Invalid row label/type")
            if len(row["values"]) != len(columns) or any(v is not None and not isinstance(v, str) for v in row["values"]):
                raise ValueError("Ragged row or non-string raw cell")
            if not set(row["uncertain_columns"]) <= set(ids):
                raise ValueError("Uncertainty refers to an unknown column")
    for page in job["target_pages"]:
        if not any(f["pdf_page"] == page for f in parsed["fragments"]):
            raise ValueError(f"No transcription for target page {page}")


def flatten(job, record, out):
    cells = []
    for fi, fragment in enumerate(record["parsed"]["fragments"], 1):
        preceding_heading = ""
        for ri, row in enumerate(fragment["rows"], 1):
            if row["kind"] == "heading":
                preceding_heading = row["label"]
            for ci, (column, raw) in enumerate(zip(fragment["columns"], row["values"]), 1):
                value, state = numeric(raw)
                if column["id"] in row["uncertain_columns"]:
                    value, state = None, "uncertain"
                cells.append({"job_id": job["job_id"], "doc_id": job["doc_id"], "table_number": job["table_number"],
                    "membership": fragment["membership"], "pdf_page": fragment["pdf_page"], "page_index": fragment["pdf_page"]-1,
                    "printed_page": fragment["printed_page"], "printed_table_number": fragment["printed_table_number"],
                    "fragment": fi, "region": row.get("_region", fragment["region"]), "bbox_approx": json.dumps(row.get("_bbox", fragment["bbox"])),
                    "section": fragment["section"], "row_index": ri, "row_label": row["label"], "row_kind": row["kind"],
                    "preceding_heading": preceding_heading,
                    "source_row_id": row.get("source_row_id", ""), "source_row_y": row.get("_source_row_y", ""),
                    "label_uncertain": row.get("label_uncertain"),
                    "column_index": ci, "column_id": column["id"], "column_label": column["label"], "unit": column["unit"],
                    "raw_value": raw, "value": value, "parse_status": state, "notes": " | ".join(fragment["notes"]),
                    "source_pdf": job["source_pdf"], "source_sha256": job["source_sha256"],
                    "source_image": row.get("_source_image", str(out / job["images"][str(fragment["pdf_page"])]["path"])),
                    "request_hash": row.get("_request_hash", record["request_hash"]), "model": MODEL})
    return cells


def normal_name(value):
    return re.sub(r"[^a-z0-9]", "", value.lower())


def lga_section(cell):
    """Use source headings or reviewed region sections, never benchmark values."""
    heading = str(cell.get("preceding_heading") or cell.get("section") or "").lower()
    groups = [name for name, token in [("municipality", "municipalit"), ("shire", "shire")]
              if token in heading]
    return groups[0] if len(groups) == 1 else "unresolved"


def report(jobs, records, out, max_tokens, state="prepared", resume_command=None):
    if jobs and "regions" in jobs[0]:
        records = compose_region_records(jobs, records)
    checks, cells, findings, metrics = [], [], [], []
    completed = failed = in_flight = 0
    references = read_csv(ROOT / DEFAULT_OUT / "source_references.csv")
    def check(job_id, name, passed, expected="", actual="", source=""):
        checks.append(dict(job_id=job_id, check=name, passed=bool(passed), expected=expected, actual=actual, source=source))
    for job in jobs:
        key = fingerprint(job, max_tokens)
        record = records.get(key)
        if record is None:
            continue
        if record.get("status") != "complete":
            if record.get("status") == "in_flight":
                in_flight += 1
            else:
                failed += 1
                check(job["job_id"], "request_completed", False, "complete", record.get("status"))
            continue
        completed += 1
        parsed = record["parsed"]
        check(job["job_id"], "model_reports_complete", parsed["complete"], True, parsed["complete"])
        extracted = flatten(job, record, out)
        cells.extend(extracted)
        context_pages = sorted({c["pdf_page"] for c in extracted if c["membership"] == "context"})
        # Adjacent NSW pages are intentional context, not missing pages from this table.
        mapped = next(r for r in read_csv(REVIEWED / "abs_1911_reviewed_table_index.csv") if r["doc_id"] == job["doc_id"] and r["table_number"] == job["table_number"])
        mapped_pages = {int(p) for p in mapped["observed_pdf_pages"].split(" | ")}
        for page in context_pages:
            if page not in mapped_pages:
                details = ("Source-reviewed target-table region is outside the accepted map. Cells quarantined; ledger unchanged."
                           if "regions" in job else "Model found target-table cells on a context page. Quarantined; source review required.")
                findings.append({"job_id": job["job_id"], "pdf_page": page, "issue": "context_fragment_outside_accepted_mapping", "details": details})
        for warning in parsed.get("warnings", []):
            findings.append({"job_id": job["job_id"], "pdf_page": "", "issue": "model_warning", "details": str(warning)})
        for observation in parsed.get("context_findings", []):
            findings.append({"job_id": job["job_id"], "pdf_page": observation["pdf_page"],
                             "issue": "model_context_observation", "details": observation["reason"]})
        target = [c for c in extracted if c["membership"] == "target" and c["row_kind"] != "heading"]
        metrics.append({
            "job_id": job["job_id"], "target_cells": len(target),
            "target_rows": len({(c["fragment"], c["row_index"]) for c in target}),
            "numeric_cells": sum(c["parse_status"] == "numeric" for c in target),
            "blank_cells": sum(c["parse_status"] == "blank" for c in target),
            "uninterpreted_cells": sum(c["parse_status"] == "uninterpreted_mark_or_text" for c in target),
            "uncertain_cells": sum(c["parse_status"] == "uncertain" for c in target),
            "context_cells": sum(c["membership"] == "context" for c in extracted),
        })
        uncertain = [c for c in target if c["parse_status"] == "uncertain"]
        check(job["job_id"], "no_explicitly_uncertain_cells", not uncertain, 0, len(uncertain))
        if "regions" in job:
            uncertain_labels = {(c["request_hash"], c["source_row_id"]) for c in extracted if c["label_uncertain"]}
            check(job["job_id"], "no_explicitly_uncertain_row_labels", not uncertain_labels, 0, len(uncertain_labels))
            uncertain_context = sum(c["membership"] == "context" and c["parse_status"] == "uncertain" for c in extracted)
            check(job["job_id"], "no_explicitly_uncertain_context_cells", not uncertain_context, 0, uncertain_context)
            if job["job_id"].startswith("ages_"):
                paired_rows = {}
                for cell in extracted:
                    paired_rows.setdefault(cell["source_row_id"], []).append(cell)
                for row_id, row_cells in paired_rows.items():
                    labels = {normal_name(c["row_label"]) for c in row_cells}
                    columns = [c["column_id"] for c in row_cells]
                    check(job["job_id"], f"spread_row_label_agreement:{row_id}", len(labels) == 1,
                          "same county label on both halves", " | ".join(sorted({c["row_label"] for c in row_cells})))
                    check(job["job_id"], f"spread_row_column_coverage:{row_id}",
                          len(columns) == len(job["column_ids"]) and set(columns) == set(job["column_ids"]),
                          len(job["column_ids"]), len(columns))
        for reference in (r for r in references if r["job_id"] == job["job_id"]):
            matches = [c for c in extracted if c["pdf_page"] == int(reference["pdf_page"])
                       and normal_name(c["row_label"]) == normal_name(reference["row_label"])
                       and c["column_id"] == reference["column_id"]]
            expected, _ = numeric(reference["raw_value"])
            passed = len(matches) == 1 and matches[0]["value"] is not None and Decimal(matches[0]["value"]) == Decimal(expected)
            check(job["job_id"], f"source_reference:{reference['pdf_page']}:{reference['row_label']}:{reference['column_id']}",
                  passed, expected, matches[0]["raw_value"] if len(matches) == 1 else f"{len(matches)} matching cells",
                  reference["source"])
        if job["job_id"].startswith("ages_"):
            totals = [c for c in extracted if normal_name(c["row_label"]) == "total"
                      and c["column_id"] in job["column_ids"]]
            complete_totals = len(totals) == len(job["column_ids"]) and all(c["value"] is not None for c in totals) and len({c["column_id"] for c in totals}) == len(totals)
            check(job["job_id"], "all_age_total_columns_in_supplied_images", complete_totals, len(job["column_ids"]), len(totals))
            if complete_totals:
                by_column = {c["column_id"]: Decimal(c["value"]) for c in totals}
                summed = sum(v for k, v in by_column.items() if k != "total")
                check(job["job_id"], "age_groups_plus_unspecified_equal_total", summed == by_column["total"], str(by_column["total"]), str(summed))
        if job["job_id"].startswith("nsw_lga_"):
            gold = [r for r in read_csv(ROOT / "data/intermediate/nsw_1911_lga_dwellings.csv") if int(r["source_pdf_page"]) in job["target_pages"]]
            actual = {}
            duplicates = set()
            for cell in target:
                if "regions" in job and not cell["source_row_id"]:
                    continue  # Retained published summaries are not LGA-body regions.
                # Compare numbers independently of the model's section metadata.
                # Page + printed name is unique in the verified NSW benchmark.
                if cell["row_kind"] == "data":
                    k = (cell["pdf_page"], normal_name(cell["row_label"]), cell["column_id"])
                    if k in actual:
                        check(job["job_id"], "unique_benchmark_cell", False, "unique", str(k))
                        duplicates.add(k)
                    actual[k] = cell
            expected_keys = set()
            for row in gold:
                for field in job["column_ids"]:
                    k = (int(row["source_pdf_page"]), normal_name(row["lga_name"]), field)
                    expected_keys.add(k)
                    got = {} if k in duplicates else actual.get(k, {})
                    same = got.get("value") is not None and Decimal(got["value"]) == Decimal(row[field])
                    check(job["job_id"], f"benchmark:{row['section']}:{row['lga_name']}:{field}", same, row[field],
                          "AMBIGUOUS_DUPLICATE" if k in duplicates else got.get("raw_value", "MISSING"),
                          f"verified NSW CSV; PDF {row['source_pdf_page']}")
                    if field == "area":
                        unit = str(got.get("unit", "")).lower().replace(" ", "_")
                        check(job["job_id"], f"area_unit:{row['lga_name']}", unit == row["area_unit"], row["area_unit"], got.get("unit"))
                        check(job["job_id"], f"section_metadata:{row['lga_name']}",
                              lga_section(got) == row["section"], row["section"], lga_section(got))
            check(job["job_id"], "unmatched_data_cells_need_review", not(set(actual)-expected_keys), 0, len(set(actual)-expected_keys),
                  "Unmatched names or non-LGA summary rows; inspect rather than silently drop")
        # Sex additivity is only evaluated when all three source cells are numeric.
        grouped = {}
        for c in target:
            grouped.setdefault((c["fragment"], c["row_index"]), {})[c["column_id"]] = c
        for group in grouped.values():
            for names in [("males", "females", "persons")] + [(f"{r}_males", f"{r}_females", f"{r}_total") for r in ["adelaide", "remainder", "state"]]:
                if all(n in group and group[n]["value"] is not None for n in names):
                    a, b, total = [Decimal(group[n]["value"]) for n in names]
                    check(job["job_id"], f"sex_additivity:{next(iter(group.values()))['row_label']}:{names[2]}", a+b == total, str(total), str(a+b))
            for sex in ["males", "females", "total"]:
                names = [f"{region}_{sex}" for region in ["adelaide", "remainder", "state"]]
                if all(n in group and group[n]["value"] is not None for n in names):
                    a, b, total = [Decimal(group[n]["value"]) for n in names]
                    check(job["job_id"], f"region_additivity:{next(iter(group.values()))['row_label']}:{sex}", a+b == total, str(total), str(a+b))
    nsw_complete = all(records.get(fingerprint(j, max_tokens), {}).get("status") == "complete"
                       for j in jobs if j["job_id"].startswith("nsw_lga_"))
    if nsw_complete:
        for total in read_csv(ROOT / "output/extract_table68/published_totals.csv"):
            if total["total_id"] not in {"municipality_subtotal", "shire_subtotal"}:
                continue
            for field in ["area", "males", "females", "persons", "occupied_dwellings"]:
                selected = [c for c in cells if c["job_id"].startswith("nsw_lga_")
                            and c["membership"] == "target" and c["row_kind"] == "data"
                            and lga_section(c) == total["group"] and c["column_id"] == field]
                value = sum((Decimal(c["value"]) for c in selected if c["value"] is not None), Decimal(0))
                valid = bool(selected) and all(c["value"] is not None for c in selected)
                check("nsw_lga_all", f"published_subtotal:{total['group']}:{field}",
                      valid and value == Decimal(total[field]), total[field], str(value) if valid else "missing/uncertain cell",
                      f"Published subtotal, PDF {total['source_pdf_page']}; never used to adjust values")
    inspection_path = out / "source_inspections.csv"
    if inspection_path.exists():
        for inspection in read_csv(inspection_path):
            findings.append({"job_id": inspection["job_id"], "pdf_page": inspection["pdf_page"],
                             "issue": "source_inspected_" + inspection["issue"],
                             "details": inspection["source_reading"] + "; " + inspection["action"]})
    fields = ["job_id", "doc_id", "table_number", "membership", "pdf_page", "page_index", "printed_page", "printed_table_number", "fragment", "region", "bbox_approx", "section", "preceding_heading", "row_index", "row_label", "row_kind", "source_row_id", "source_row_y", "label_uncertain", "column_index", "column_id", "column_label", "unit", "raw_value", "value", "parse_status", "notes", "source_pdf", "source_sha256", "source_image", "request_hash", "model"]
    write_csv(out / "cells.csv", fields, [r for r in cells if r["membership"] == "target"])
    write_csv(out / "context_cells.csv", fields, [r for r in cells if r["membership"] == "context"])
    write_csv(out / "checks.csv", ["job_id", "check", "passed", "expected", "actual", "source"], checks)
    write_csv(out / "review_findings.csv", ["job_id", "pdf_page", "issue", "details"], findings)
    write_csv(out / "metrics.csv", ["job_id", "target_cells", "target_rows", "numeric_cells", "blank_cells", "uninterpreted_cells", "uncertain_cells", "context_cells"], metrics)
    known_cost = sum(r.get("cost_usd") or 0 for r in records.values())
    budget_used = sum(r.get("cost_usd") if r.get("cost_usd") is not None else r["reserved_usd"] for r in records.values())
    if state == "prepared" and completed == len(jobs):
        state = "complete"
    status = {"updated_at": stamp(), "state": state, "model": MODEL, "unit": "extraction request", "completed": completed, "total": len(jobs), "failed": failed, "in_flight": in_flight, "skipped": 0, "remaining": len(jobs)-completed-failed-in_flight,
              "reported_cost_usd": known_cost, "unknown_cost_attempts": sum(r.get("cost_usd") is None for r in records.values()), "budget_used_or_reserved_usd": budget_used,
              "attempts_total": len(records), "historical_failed_attempts": sum(r["status"] == "failed" for r in records.values()),
              "checks_passed": sum(r["passed"] for r in checks), "checks_failed": sum(not r["passed"] for r in checks),
              "mapping_findings": len({(r["job_id"], str(r["pdf_page"])) for r in findings
                                      if r["issue"] in {"context_fragment_outside_accepted_mapping", "source_inspected_possible_mapping_omission"}}),
              "checkpoint": str(out / "requests.jsonl"), "last_successful_job": next((r["job_id"] for r in reversed(list(records.values())) if r["status"] == "complete"), None),
              "resume_command": resume_command, "eta_seconds": None,
              "last_request_seconds": next((r.get("elapsed_seconds") for r in reversed(list(records.values())) if r.get("elapsed_seconds")), None)}
    write_json(out / "status.json", status)
    if jobs and "regions" in jobs[0]:
        compare_passes(jobs, checks, cells, out)
    print(json.dumps(status), flush=True)
    return status


REGION_PROMPT = """Transcribe only the labelled extraction regions in this request.
This is a bounded second pass, NOT a request for the entire numbered table.
Each extraction image has artificial row IDs in a separate left gutter. These IDs
are navigation aids, not census values. Transcribe exactly those labelled rows,
once each, in their supplied order. Ignore unlabelled neighbouring row fragments.
Return one fragment per region_id, using only its supplied column_ids in order.
Header images establish printed headings and units; do not extract their data rows.
Regions marked membership=context MUST still be extracted: that field means the
accepted page map is disputed, NOT that the image is optional or context-only.
Right-hand age-table regions contain ages 50 upwards, unspecified and TOTAL;
their county labels are at the RIGHT edge. Pair them with left-hand regions by
the supplied row IDs. Never substitute adjacent male, female or persons tables.
Read every numeric cell directly from the image. Do not use arithmetic, totals,
neighbouring rows or expectations to repair it. Preserve commas, decimal marks,
printed dots, dashes and footnote marks in raw strings. A blank is null, never 0.
If a glyph is ambiguous, return the visible raw string and mark its column ID
uncertain. Do not omit the row or fabricate a value. Preserve source row spelling.
Set label_uncertain=true when a row label is unclear. Printed table/page labels
must follow the image, including printed 69 where the mapping calls it table 68.
The supplied section, membership, units, row kinds and source coordinates are
source-reviewed metadata; software attaches them. Do not infer or override them.
complete means all requested region rows and columns were transcribed, including
uncertain/blank/marked cells; it does NOT claim the whole source table is complete.
Return JSON only:
{"complete":true,"warnings":[],"context_findings":[],"fragments":[
 {"region_id":"supplied ID","printed_page":"verbatim label or empty",
  "printed_table_number":null,"title":"source title","notes":[],
  "columns":[{"id":"supplied column_id","label":"source column heading"}],
  "rows":[{"source_row_id":"supplied gutter ID","label":"verbatim row label",
           "label_uncertain":false,"values":["raw string",null],
           "uncertain_columns":[]}]}]}
"""


def prepare_regions(jobs, out, dpi):
    """Render immutable-source crops; the added gutter contains no reference values."""
    evidence = out / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for job in jobs:
        source = ROOT / job["source_pdf"]
        if source not in hashes:
            hashes[source] = hashlib.sha256(source.read_bytes()).hexdigest()
        job["source_sha256"] = hashes[source]
        job["images"] = {}
        with pymupdf.open(source) as pdf:
            for pn in sorted({r["pdf_page"] for r in job["regions"]}):
                job["images"][str(pn)] = {"path": job["baseline_images"][str(pn)],
                                         "role": "provenance_only"}
            for region in job["regions"]:
                pn = region["pdf_page"]
                clip = pymupdf.Rect(region["clip"])
                if clip.is_empty or not pdf[pn-1].rect.contains(clip):
                    raise ValueError(f"Crop outside source page: {region['region_id']}")
                region["bbox"] = [round(1000*clip.x0/pdf[pn-1].rect.width),
                                  round(1000*clip.y0/pdf[pn-1].rect.height),
                                  round(1000*clip.x1/pdf[pn-1].rect.width),
                                  round(1000*clip.y1/pdf[pn-1].rect.height)]
                with pymupdf.open() as guide:
                    canvas = guide.new_page(width=clip.width+54, height=clip.height)
                    canvas.show_pdf_page(pymupdf.Rect(54, 0, clip.width+54, clip.height),
                                         pdf, pn-1, clip=clip)
                    canvas.draw_line((51, 0), (51, clip.height), color=(0.6, 0.6, 0.6))
                    for row in region["rows"]:
                        if not clip.y0 < row["y"] < clip.y1:
                            raise ValueError(f"Row marker outside crop: {row['id']}")
                        canvas.insert_text((2, row["y"]-clip.y0+2), row["id"], fontsize=5)
                    image = evidence / f"{region['region_id']}_{dpi}dpi.jpg"
                    image.write_bytes(canvas.get_pixmap(dpi=dpi, alpha=False).tobytes("jpeg", jpg_quality=95))
                job["images"][region["region_id"]] = {
                    "path": image.relative_to(out).as_posix(),
                    "sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
                    "label": f"EXTRACT region {region['region_id']}; physical PDF page {pn}; "
                             f"extract ALL gutter-labelled rows, including membership={region['membership']}."}
                for hi, header in enumerate(region["header_clips"]):
                    image = evidence / f"{region['region_id']}_header{hi}_{dpi}dpi.jpg"
                    image.write_bytes(pdf[header["pdf_page"]-1].get_pixmap(
                        dpi=dpi, clip=pymupdf.Rect(header["clip"]), alpha=False).tobytes("jpeg", jpg_quality=95))
                    job["images"][f"{region['region_id']}_header{hi}"] = {
                        "path": image.relative_to(out).as_posix(),
                        "sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
                        "label": f"HEADER/UNIT EVIDENCE ONLY for {region['region_id']}; "
                                 f"physical PDF page {header['pdf_page']}. Do not transcribe data rows here."}
    write_json(out / "manifest.json", jobs)
    (out / "prompt.txt").write_text(SYSTEM + "\n\n" + REGION_PROMPT)


def materialize_regions(parsed, job, out):
    """Attach reviewed metadata, keeping the unmodified model text in the API ledger."""
    expected = {r["region_id"]: r for r in job["regions"]}
    actual = [f["region_id"] for f in parsed["fragments"]]
    if len(actual) != len(expected) or set(actual) != set(expected):
        raise ValueError("Missing, extra or duplicated extraction regions")
    for fragment in parsed["fragments"]:
        region = expected[fragment["region_id"]]
        if [r["source_row_id"] for r in fragment["rows"]] != [r["id"] for r in region["rows"]]:
            raise ValueError(f"Missing, extra, duplicated or reordered rows in {region['region_id']}")
        if [c["id"] for c in fragment["columns"]] != region["column_ids"]:
            raise ValueError(f"Incorrect column coverage in {region['region_id']}")
        fragment.update(pdf_page=region["pdf_page"], membership=region["membership"],
                        region=region["region_id"], bbox=region["bbox"], section=region["section"])
        for column, unit in zip(fragment["columns"], region["units"]):
            column["unit"] = unit
        for row, source_row in zip(fragment["rows"], region["rows"]):
            if not isinstance(row.get("label_uncertain"), bool):
                raise ValueError("Missing row-label uncertainty flag")
            row.update(kind=source_row["kind"], _source_row_y=source_row["y"],
                       _source_image=str(out / job["images"][region["region_id"]]["path"]))
            if row["label_uncertain"]:
                fragment["notes"].append(f"Uncertain source row label: {row['source_row_id']}")
    return parsed


def compose_region_records(jobs, records):
    """Overlay selected regions without presenting retained first-pass cells as new."""
    combined = records.copy()
    for job in jobs:
        key = fingerprint(job, job["refinement_max_tokens"])
        record = records.get(key)
        if not record or record["status"] != "complete":
            continue
        record = copy.deepcopy(record)
        baseline = records[job["baseline_request_hash"]]
        old_fragments = copy.deepcopy(baseline["parsed"]["fragments"])
        for fragment in old_fragments:
            for row in fragment["rows"]:
                row["_request_hash"] = baseline["request_hash"]
                row["_source_image"] = job["baseline_images"][str(fragment["pdf_page"])]
        if job["job_id"] == "summary_27":
            new_fragment = record["parsed"]["fragments"][0]
            new_row = new_fragment["rows"][0]
            matches = [(f, i) for f in old_fragments for i, r in enumerate(f["rows"])
                       if r["label"] == "Norway"]
            if len(matches) != 1 or new_row["label"] != "Norway":
                raise ValueError("Norway overlay requires an unambiguous source row")
            fragment, index = matches[0]
            new_row["_bbox"] = new_fragment["bbox"]
            new_row["_region"] = new_fragment["region"]
            fragment["rows"][index] = new_row
            record["parsed"]["fragments"] = old_fragments
        elif job["job_id"].startswith("nsw_lga_"):
            # Keep published totals and the separate state summary from pass one.
            # They are not LGA-body extraction targets in this second pass.
            for fragment in old_fragments:
                retained, in_summary = [], False
                for row in fragment["rows"]:
                    if normal_name(row["label"]) == "summary" and row["kind"] == "heading":
                        in_summary = True
                    if in_summary or row["kind"] in {"subtotal", "total"}:
                        retained.append(row)
                if retained:
                    fragment["rows"] = retained
                    record["parsed"]["fragments"].append(fragment)
        record["composition"] = {"kind": "derived region overlay",
                                 "baseline_request_hash": baseline["request_hash"],
                                 "refinement_request_hash": key}
        combined[key] = record
    return combined


def compare_passes(jobs, checks, cells, out):
    old = read_csv(Path(jobs[0]["baseline_dir"]) / "checks.csv")
    groups = {}
    for stage, rows in [("baseline", old), ("refined", checks)]:
        for row in rows:
            key = (row["job_id"], row["check"])
            groups.setdefault(key, {}).setdefault(stage, []).append(str(row["passed"]).lower() == "true")
    comparison = []
    for (job_id, name), stages in sorted(groups.items()):
        before, after = stages.get("baseline"), stages.get("refined")
        change = ("not_repeated" if after is None else "new_check" if before is None else
                  "resolved" if not all(before) and all(after) else
                  "regression" if all(before) and not all(after) else "unchanged")
        comparison.append({"job_id": job_id, "check": name, "baseline_passed": all(before) if before else "",
                           "refined_passed": all(after) if after else "", "change": change,
                           "baseline_count": len(before or []), "refined_count": len(after or [])})
    write_csv(out / "comparison.csv", ["job_id", "check", "baseline_passed", "refined_passed",
                                      "change", "baseline_count", "refined_count"], comparison)
    # This separate score uses source geometry IDs, not model-spelled names.
    # The independent numeric reference is read only AFTER model extraction.
    reference = {(int(r["source_pdf_page"]), int(r["source_row_number"])): r
                 for r in read_csv(ROOT / "data/intermediate/nsw_1911_lga_dwellings.csv")}
    row_checks = []
    for cell in cells:
        if not cell["job_id"].startswith("nsw_lga_") or not cell["source_row_id"]:
            continue
        source_row = int(cell["source_row_id"].split("-r")[-1])
        gold = reference[(cell["pdf_page"], source_row)]
        expected = numeric(gold[cell["column_id"]])[0]
        row_checks.append({"job_id": cell["job_id"], "source_row_id": cell["source_row_id"],
                           "row_label": cell["row_label"], "reference_label": gold["lga_name"],
                           "column_id": cell["column_id"], "expected": expected,
                           "actual": cell["value"], "passed": expected is not None and cell["value"] == expected,
                           "label_matches": normal_name(cell["row_label"]) == normal_name(gold["lga_name"]),
                           "source_image": cell["source_image"]})
    write_csv(out / "row_id_benchmark.csv", ["job_id", "source_row_id", "row_label", "reference_label",
              "column_id", "expected", "actual", "passed", "label_matches", "source_image"], row_checks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Make paid calls for unattempted jobs; otherwise offline")
    parser.add_argument("--refine", action="store_true", help="Use source-reviewed regions; retain baseline and cumulative budget")
    parser.add_argument("--max-cost-usd", type=float, default=5)
    parser.add_argument("--case", action="append", help="Run only these job IDs; reports still cover all jobs")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--dpi", type=int)
    parser.add_argument("--max-tokens", type=int, default=32768)
    parser.add_argument("--timeout", type=int, default=600, help="Socket inactivity timeout, not a whole-request deadline")
    parser.add_argument("--api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument("--auth-file", type=Path, help="Explicit existing OpenCode auth file; key is never logged")
    parser.add_argument("--no-opencode-auth", action="store_true")
    args = parser.parse_args()
    args.dpi = args.dpi or (300 if args.refine else 180)
    if not 0 < args.max_cost_usd <= 5 or not 1 <= args.max_tokens <= 65536 or not 100 <= args.dpi <= 300:
        parser.error("Pilot limits: cost >0 and <=US$5; max tokens 1–65536; DPI 100–300")
    out = args.output_dir / "refined" if args.refine else args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    jobs = make_jobs()
    # A later reviewed-map correction must not turn a cached request into a new
    # paid request. Preserve the labels actually supplied in the first-pass prompt.
    baseline_manifest = args.output_dir / "manifest.json"
    if baseline_manifest.exists():
        original_jobs = {j["job_id"]: j for j in json.loads(baseline_manifest.read_text())}
        if {j["job_id"] for j in jobs} != set(original_jobs):
            parser.error("Pilot cases differ from the saved request manifest")
        for job in jobs:
            original = original_jobs[job["job_id"]]
            for field in ("doc_id", "table_number", "source_pdf", "target_pages", "context_pages", "column_ids"):
                if job[field] != original[field]:
                    parser.error(f"Pilot case changed since the saved request: {job['job_id']} {field}")
            job["mapped_printed_labels"] = original["mapped_printed_labels"]
    records = {}
    if args.refine:
        baseline_jobs = {j["job_id"]: j for j in json.loads((args.output_dir / "manifest.json").read_text())}
        for line in (args.output_dir / "requests.jsonl").read_text().splitlines():
            record = json.loads(line)
            records[record["request_hash"]] = record
        regions = json.loads((out / "source_regions.json").read_text())
        for job in jobs:
            baseline = [r for r in records.values() if r["job_id"] == job["job_id"] and r["status"] == "complete"]
            if len(baseline) != 1:
                parser.error(f"Refinement requires one completed baseline for {job['job_id']}")
            job.update(regions=[r for r in regions if r["job_id"] == job["job_id"]],
                       baseline_request_hash=baseline[0]["request_hash"],
                       baseline_dir=str(args.output_dir), refinement_max_tokens=args.max_tokens,
                       baseline_images={p: str(args.output_dir / image["path"])
                                        for p, image in baseline_jobs[job["job_id"]]["images"].items()})
            if not job["regions"]:
                parser.error(f"No source-reviewed regions for {job['job_id']}")
    if args.case and not set(args.case) <= {j["job_id"] for j in jobs}:
        parser.error("Unknown pilot case")
    prepare(jobs, out, args.dpi)
    resume_args = ["uv", "run", "explore/2026-09-22_census-extraction-pilot.py",
                   "--run", "--max-cost-usd", str(args.max_cost_usd),
                   "--output-dir", str(args.output_dir), "--dpi", str(args.dpi),
                   "--max-tokens", str(args.max_tokens)]
    if args.refine:
        resume_args.append("--refine")
    if args.auth_file:
        resume_args += ["--auth-file", str(args.auth_file)]
    if args.no_opencode_auth:
        resume_args.append("--no-opencode-auth")
    resume_args += ["--api-key-env", args.api_key_env]
    resume_command = shlex.join(resume_args)
    path = out / "requests.jsonl"
    if path.exists():
        for line in path.read_text().splitlines():
            record = json.loads(line)
            records[record["request_hash"]] = record
    def save(record):
        with path.open("a") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            handle.flush()
        records[record["request_hash"]] = record
    status = report(jobs, records, out, args.max_tokens, resume_command=resume_command)
    if not args.run or status["completed"] == len(jobs):
        return
    with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as response:
        catalogue = json.load(response)["data"]
    model = next(m for m in catalogue if m["id"] == MODEL)
    if "image" not in model["architecture"]["input_modalities"] or model["context_length"] > CONTEXT_LIMIT:
        raise RuntimeError("Model capability/context changed; inspect before spending")
    write_json(out / "model_metadata.json", model)
    if args.auth_file:
        with args.auth_file.open() as handle:
            api_key = json.load(handle)["openrouter"]["key"]
    else:
        api_key, _ = get_api_key(args)
    reserve = CONTEXT_LIMIT * PRICE_CAP["prompt"]/1_000_000 + args.max_tokens * PRICE_CAP["completion"]/1_000_000
    for job in jobs:
        if args.case and job["job_id"] not in args.case:
            continue
        key = fingerprint(job, args.max_tokens)
        if key in records:
            continue  # Failed/ambiguous paid attempts are not automatically retried.
        if status["budget_used_or_reserved_usd"] + reserve > args.max_cost_usd:
            report(jobs, records, out, args.max_tokens, "budget_blocked", resume_command)
            raise SystemExit("Budget would be exceeded; no request sent")
        record = {"job_id": job["job_id"], "request_hash": key, "started_at": stamp(), "status": "in_flight", "reserved_usd": reserve, "cost_usd": None}
        record["request_settings"] = {"model": MODEL, "reasoning": REASONING,
                                      "max_tokens": args.max_tokens, "provider_price_cap": PRICE_CAP}
        if args.refine:
            record["input_manifest"] = job
        request = payload(job, out, args.max_tokens)
        record["request_settings"]["provider"] = request["provider"]
        save(record)
        report(jobs, records, out, args.max_tokens, "running", resume_command)
        started = time.monotonic()
        try:
            response = post_openrouter(api_key, request, args.timeout)
            # Cache model response, never credentials, request image URLs or headers.
            record["response"] = response
            usage = response.get("usage", {})
            record["cost_usd"] = usage.get("cost")
            choice = response["choices"][0]
            if choice.get("finish_reason") != "stop":
                raise ValueError("Model response did not finish cleanly")
            parsed = extract_json_object(choice["message"]["content"])
            if args.refine:
                parsed = materialize_regions(parsed, job, out)
                record["metadata_source"] = str(out / "source_regions.json")
            validate_response(parsed, job)
            record.update(status="complete", parsed=parsed)
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, IndexError, TypeError) as error:
            record.update(status="failed", error_type=type(error).__name__)
            if isinstance(error, urllib.error.HTTPError):
                record["http_status"] = error.code
            elif isinstance(error, ValueError):
                record["validation_error"] = str(error)
        record["elapsed_seconds"] = round(time.monotonic()-started, 2)
        record["finished_at"] = stamp()
        save(record)
        status = report(jobs, records, out, args.max_tokens, "running", resume_command)
        if record["status"] != "complete":
            report(jobs, records, out, args.max_tokens, "blocked_request_failure", resume_command)
            raise SystemExit("Request failed; inspect cached record before any further spending")
    report(jobs, records, out, args.max_tokens, "complete" if status["completed"] == len(jobs) else "partial", resume_command)


if __name__ == "__main__":
    main()
