"""
Build page spans for indexed 1911 census tables.

Input:
- data/intermediate/table_index/abs_1911_numbered_table_index.csv
- data/intermediate/table_index/abs_1911_table_numbering_evidence.csv
- data/intermediate/page_inventory/abs_1911_index_guided_pages.csv
- Existing flagged-page QA CSVs (Flash Lite, Flash, GPT-5.5), in that order
- data/intermediate/page_inventory/abs_1911_source_page_overrides.csv
- data/intermediate/page_inventory/abs_1911_manual_page_overrides.csv (highest priority)

Outputs:
- data/intermediate/table_index/abs_1911_table_page_spans.csv
- data/intermediate/table_index/abs_1911_table_page_spans_review.csv
- output/build_abs_1911_table_spans/abs_1911_reviewed_*.csv
- output/build_abs_1911_table_spans/abs_1911_override_audit.csv
Reviewed outputs combine existing QA passes and accepted human overrides; they
never overwrite model responses or the original contents-derived index.

Original candidate-span logic:
- Start page comes from the contents-derived start_page_index_estimate.
- End page is the page before the next later physical table start in the same
  document. This is intentionally based on page order, not table-number order,
  because a few contents pages list tables whose printed starts are not strictly
  monotonic by table number.
- If the next table starts on the same page, keep a one-page span and flag it as
  a same-page boundary. This avoids falsely assigning only one table to a page.
- The final table in each document ends at page_count - 1.

Reviewed spans contain only contiguous runs of assigned pages, never filled gaps.
final_table_numbers preserves confirmed page labels. contents_table_numbers and
table_ids link them to the contents sequence using explicit numbering evidence.
"""

from __future__ import annotations

import csv
import pathlib
import re
from typing import Any


INPUT = pathlib.Path("data/intermediate/table_index/abs_1911_numbered_table_index.csv")
OUTPUT = pathlib.Path("data/intermediate/table_index/abs_1911_table_page_spans.csv")
REVIEW_OUTPUT = pathlib.Path(
    "data/intermediate/table_index/abs_1911_table_page_spans_review.csv"
)
PAGE_DIR = pathlib.Path("data/intermediate/page_inventory")
REVIEWED_DIR = pathlib.Path("output/build_abs_1911_table_spans")
MANUAL_PATH = PAGE_DIR / "abs_1911_manual_page_overrides.csv"
SOURCE_PATH = PAGE_DIR / "abs_1911_source_page_overrides.csv"
NUMBERING_PATH = pathlib.Path("data/intermediate/table_index/abs_1911_table_numbering_evidence.csv")


def read_csv(path: pathlib.Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def to_int(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def table_number_sort(value: str) -> tuple[int, str]:
    match = re.search(r"\d+", value or "")
    if match:
        return (int(match.group()), value)
    return (10**9, value or "")


def page_list(start: int | None, end: int | None) -> str:
    if start is None or end is None or end < start:
        return ""
    return " | ".join(str(page) for page in range(start, end + 1))


def build_spans(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_doc: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_doc.setdefault(row["doc_id"], []).append(row)

    spans: list[dict[str, Any]] = []
    for doc_id, doc_rows in sorted(by_doc.items()):
        doc_rows = sorted(doc_rows, key=lambda row: table_number_sort(row["table_number"]))
        starts = [to_int(row.get("start_page_index_estimate")) for row in doc_rows]

        for index, row in enumerate(doc_rows):
            start = starts[index]
            page_count = to_int(row.get("page_count"))
            later_starts = [value for value in starts if value is not None and start is not None and value > start]
            next_later_start = min(later_starts) if later_starts else None
            next_numbered_start = starts[index + 1] if index + 1 < len(starts) else None
            flags: list[str] = []

            if start is None:
                end = None
                flags.append("missing_start_page_index")
            elif next_later_start is None:
                end = (page_count - 1) if page_count is not None else start
                flags.append("final_table_in_document")
            else:
                end = next_later_start - 1

            if next_numbered_start is not None and start is not None:
                if next_numbered_start == start:
                    flags.append("same_page_as_next_table_start")
                elif next_numbered_start < start:
                    flags.append("next_numbered_table_starts_before_this_table")

            if page_count is not None and start is not None:
                if start < 0 or start >= page_count:
                    flags.append("start_outside_pdf_page_range")
                if end is not None and end >= page_count:
                    flags.append("end_outside_pdf_page_range")

            previous_start = starts[index - 1] if index > 0 else None
            if previous_start is not None and start == previous_start:
                flags.append("same_page_as_previous_table_start")

            if end is not None and start is not None and end < start:
                flags.append("end_before_start")

            review_flags = [flag for flag in flags if flag != "final_table_in_document"]

            spans.append(
                {
                    "doc_id": row["doc_id"],
                    "file_name": row["file_name"],
                    "title": row["title"],
                    "local_path": row["local_path"],
                    "page_count": row["page_count"],
                    "table_number": row["table_number"],
                    "table_title": row["table_title"],
                    "start_printed_page": row["start_printed_page"],
                    "start_page_index": start if start is not None else "",
                    "end_page_index": end if end is not None else "",
                    "page_span_count": (end - start + 1)
                    if start is not None and end is not None and end >= start
                    else "",
                    "page_indexes": page_list(start, end),
                    "start_pdf_page": start + 1 if start is not None else "",
                    "end_pdf_page": end + 1 if end is not None else "",
                    "next_table_number": doc_rows[index + 1]["table_number"]
                    if index + 1 < len(doc_rows)
                    else "",
                    "next_table_start_page_index": next_numbered_start
                    if next_numbered_start is not None
                    else "",
                    "next_later_start_page_index": next_later_start
                    if next_later_start is not None
                    else "",
                    "topic": row["topic"],
                    "geography": row["geography"],
                    "part_or_section": row["part_or_section"],
                    "subentry_count": row["subentry_count"],
                    "span_flags": " | ".join(flags),
                    "needs_review": bool(review_flags),
                }
            )
    return spans


def write_csv(rows: list[dict[str, Any]], path: pathlib.Path, fields: list[str] | None = None) -> None:
    if fields is None:
        if not rows:
            raise ValueError(f"Explicit headers required for empty output: {path}")
        fields = list(rows[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def numbers(value: str) -> list[str]:
    """Parse explicit printed numbers, never infer a number from a title."""
    parts = [part.strip() for part in value.split("|") if part.strip()]
    if any(not part.isdigit() or int(part) < 1 for part in parts):
        raise ValueError(f"Invalid table numbers: {value!r}")
    return list(dict.fromkeys(parts))


def reconcile_pages(contents: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pages = read_csv(PAGE_DIR / "abs_1911_index_guided_pages.csv")
    by_key = {}
    for row in pages:
        key = (row["doc_id"], row["pdf_page"])
        if key in by_key or int(row["pdf_page"]) != int(row["page_index"]) + 1:
            raise ValueError(f"Duplicate page or inconsistent page numbering: {key}")
        row.update(
            final_table_numbers=row["matched_table_numbers"],
            final_page_role=row["page_role"],
            assignment_source="guided_classifier",
            assignment_evidence=row["warnings"],
            review_status="model_classified",
            confirmed_page_title="",
        )
        by_key[key] = row

    # Human coverage reviews can add real source pages omitted by the classifier.
    # Leave classifier fields empty: no model inspected these pages.
    documents = {r["doc_id"]: r for r in contents}
    for decision in read_csv(MANUAL_PATH):
        key = (decision["doc_id"], decision["pdf_page"])
        if key in by_key:
            continue
        document = documents.get(key[0])
        page = to_int(key[1])
        if document is None or page is None or not 1 <= page <= int(document["page_count"]):
            raise ValueError(f"Human review target is not a source page: {key}")
        row = dict.fromkeys(pages[0], "")
        row.update({field: document[field] for field in
                    ("doc_id", "file_name", "local_path", "page_count")})
        row.update(pdf_page=str(page), page_index=str(page - 1),
                   review_status="unresolved")
        pages.append(row)
        by_key[key] = row

    audit = []
    layers = [
        ("qa_flash_lite", PAGE_DIR / "abs_1911_flagged_page_qa.csv"),
        ("qa_flash", PAGE_DIR / "abs_1911_flagged_page_qa_gemini_3_5_flash.csv"),
        ("gpt55_adjudication", PAGE_DIR / "abs_1911_flagged_page_qa_gpt55_adjudication.csv"),
        ("source_inspection", SOURCE_PATH),
        ("human_review", MANUAL_PATH),
    ]
    for source, path in layers:
        seen = set()
        for source_row, decision in enumerate(read_csv(path), start=2):
            key = (decision["doc_id"], decision["pdf_page"])
            if key in seen or key not in by_key:
                raise ValueError(f"Duplicate or unknown override target in {path}: {key}")
            seen.add(key)
            row = by_key[key]
            human = source == "human_review"
            direct_review = source in {"human_review", "source_inspection"}
            action = decision.get("decision", decision.get("gpt55_verdict", decision.get("qa_decision", "")))
            accepted = (
                action in {"accept_model", "correct_match", "exclude_page"}
                if direct_review else decision["needs_human_review"].lower() == "false"
                and not decision.get("error")
            )
            proposed = decision.get("table_numbers", decision.get("final_table_numbers", ""))
            proposed = " | ".join(numbers(proposed))
            role = decision.get("final_page_role", "table" if proposed else row["final_page_role"])
            if direct_review:
                role = "non_table" if action == "exclude_page" else "table"
            evidence = decision.get("notes", decision.get("evidence_notes", decision.get("qa_notes", "")))
            before = row["final_table_numbers"]
            if accepted:
                if not proposed and role not in {"non_table", "contents_or_index"}:
                    raise ValueError(f"Accepted table assignment has no number: {path}:{source_row}")
                row.update(
                    final_table_numbers=proposed,
                    final_page_role=role,
                    assignment_source=source,
                    assignment_evidence=evidence,
                    review_status=("human_confirmed" if human else
                                   "source_verified" if source == "source_inspection" else
                                   "model_adjudicated"),
                    confirmed_page_title=decision.get("confirmed_page_title", ""),
                )
            else:
                # An uncertain later pass must not silently clear earlier assignments.
                row["review_status"] = "unresolved"
            audit.append({
                "doc_id": key[0], "pdf_page": key[1], "source": source,
                "source_file": path.as_posix(), "source_row": source_row,
                "decision": action, "accepted": accepted,
                "before_table_numbers": before, "proposed_table_numbers": proposed,
                "after_table_numbers": row["final_table_numbers"],
                "evidence": evidence, "updated_at": decision.get("updated_at", ""),
                "confirmation_source": decision.get("confirmation_source", ""),
            })
    return sorted(pages, key=lambda r: (r["doc_id"], int(r["pdf_page"]))), audit


def build_reviewed_outputs(contents: list[dict[str, str]]) -> None:
    pages, audit = reconcile_pages(contents)
    catalogue = {(r["doc_id"], r["table_number"]): dict(r) for r in contents}
    numbering = {(r["doc_id"], r["pdf_page"]): r for r in read_csv(NUMBERING_PATH)}
    observed = {}
    issues = []
    for row in pages:
        page_key = (row["doc_id"], row["pdf_page"])
        evidence = numbering.get(page_key, {})
        row["numbering_note"] = evidence.get("notes", "")
        flags = []
        if row["review_status"] == "unresolved":
            flags.append("unresolved_assignment")
        assigned = numbers(row["final_table_numbers"])
        if not assigned and row["final_page_role"] not in {"non_table", "contents_or_index"}:
            flags.append("table_page_without_assignment")
        if row["error"]:
            flags.append("original_classifier_error")
        contents_numbers = assigned.copy()
        if evidence:
            printed = evidence["visible_table_number"]
            if printed not in assigned:
                raise ValueError(f"Numbering evidence conflicts with reviewed assignment: {page_key}")
            contents_numbers = [
                evidence["contents_table_number"] if n == printed else n
                for n in assigned
            ]
            flags.append("printed_number_differs_from_contents")
        row["contents_table_numbers"] = " | ".join(contents_numbers)
        row["table_ids"] = " | ".join(f"{row['doc_id']}::{n}" for n in contents_numbers)
        for number in contents_numbers:
            key = (row["doc_id"], number)
            if key not in catalogue:
                flags.append("table_number_absent_from_contents")
            observed.setdefault(key, []).append(row)
        row["review_flags"] = " | ".join(dict.fromkeys(flags))
        for flag in dict.fromkeys(flags):
            issues.append({
                "doc_id": row["doc_id"], "pdf_page": row["pdf_page"],
                "table_number": row["final_table_numbers"], "issue": flag,
                "details": row["numbering_note"] or row["assignment_evidence"],
            })

    confirmed_pages = {
        (r["doc_id"], int(r["pdf_page"])) for r in pages
        if r["review_status"] in {"human_confirmed", "source_verified"}
    }

    reviewed_index, reviewed_spans = [], []
    for key, entry in sorted(catalogue.items(), key=lambda item: (item[0][0], table_number_sort(item[0][1]))):
        assigned_rows = sorted(observed.get(key, []), key=lambda r: int(r["pdf_page"]))
        pdf_pages = [int(r["pdf_page"]) for r in assigned_rows]
        entry.update(
            catalogue_basis="contents",
            printed_number_variants=" | ".join(sorted(
                {key[1]} | {
                    r["visible_table_number"] for r in numbering.values()
                    if r["doc_id"] == key[0] and r["contents_table_number"] == key[1]
                }, key=table_number_sort)),
            observed_pdf_pages=" | ".join(map(str, pdf_pages)),
            observed_page_count=len(pdf_pages),
            human_confirmed_page_count=sum(r["review_status"] == "human_confirmed" for r in assigned_rows),
        )
        reviewed_index.append(entry)
        if not pdf_pages:
            issues.append({"doc_id": key[0], "pdf_page": "", "table_number": key[1],
                           "issue": "indexed_table_without_mapped_pages", "details": entry["table_title"]})
            continue
        runs = []
        for page in pdf_pages:
            if not runs or page != runs[-1][-1] + 1:
                runs.append([])
            runs[-1].append(page)
        if len(runs) > 1:
            gaps_confirmed = all(
                (key[0], page) in confirmed_pages
                for left, right in zip(runs, runs[1:])
                for page in range(left[-1], right[0] + 1)
            )
            issues.append({
                "doc_id": key[0], "pdf_page": entry["observed_pdf_pages"],
                "table_number": key[1],
                "issue": ("confirmed_non_contiguous_assignment" if gaps_confirmed
                          else "non_contiguous_table_assignment"),
                "details": ("All gap pages and both boundaries have confirmed page assignments. "
                            "Retain exact membership; do not fill the gap." if gaps_confirmed else
                            "Explicit page runs retained; gaps were not filled."),
            })
        for run in runs:
            reviewed_spans.append({
                "doc_id": key[0], "table_number": key[1], "table_title": entry["table_title"],
                "start_pdf_page": run[0], "end_pdf_page": run[-1],
                "start_page_index": run[0]-1, "end_page_index": run[-1]-1,
                "page_span_count": len(run), "pdf_pages": " | ".join(map(str, run)),
                "catalogue_basis": entry["catalogue_basis"],
            })

    # Flag omitted source pages, not just conflicts inside the guided-classifier sample.
    docs = {}
    for entry in contents:
        docs[entry["doc_id"]] = int(entry["page_count"])
    classified = {(r["doc_id"], int(r["pdf_page"])) for r in pages}
    for doc_id, count in docs.items():
        for page in range(1, count+1):
            if (doc_id, page) not in classified:
                issues.append({"doc_id": doc_id, "pdf_page": page, "table_number": "",
                               "issue": "page_not_in_guided_inventory",
                               "details": "May be front matter or an unindexed table; not inspected."})

    for issue in issues:
        issue["requires_review"] = issue["issue"] not in {
            "printed_number_differs_from_contents", "confirmed_non_contiguous_assignment",
        }

    write_csv(pages, REVIEWED_DIR / "abs_1911_reviewed_pages.csv")
    write_csv(reviewed_index, REVIEWED_DIR / "abs_1911_reviewed_table_index.csv")
    write_csv(reviewed_spans, REVIEWED_DIR / "abs_1911_reviewed_table_spans.csv")
    write_csv(audit, REVIEWED_DIR / "abs_1911_override_audit.csv")
    write_csv(issues, REVIEWED_DIR / "abs_1911_reviewed_issues.csv",
              ["doc_id", "pdf_page", "table_number", "issue", "details", "requires_review"])
    print(f"Reviewed map: {len(pages)} pages; {sum(r['review_status'] == 'human_confirmed' for r in pages)} human-confirmed")
    print(f"Reviewed catalogue: {len(reviewed_index)} contents tables; {len(issues)} issue records")
    print(f"Reviewed outputs: {REVIEWED_DIR}")


def main() -> None:
    rows = read_csv(INPUT)
    spans = build_spans(rows)
    review = [row for row in spans if row["needs_review"]]
    write_csv(spans, OUTPUT)
    write_csv(review, REVIEW_OUTPUT, list(spans[0]))

    print(f"Input tables: {len(rows)}")
    print(f"Output spans: {len(spans)}")
    print(f"Review rows: {len(review)}")
    print(f"Span output: {OUTPUT}")
    print(f"Review output: {REVIEW_OUTPUT}")
    build_reviewed_outputs(rows)


if __name__ == "__main__":
    main()
