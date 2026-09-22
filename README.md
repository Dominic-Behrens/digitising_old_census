# Digitising old census tables

This project maps tables in the Australian 1911 census PDFs and extracts the NSW local-government-area population and occupied-dwelling table. Raw PDFs remain untouched.

The numbered-table inventory is not a complete inventory of unnumbered tables. The NSW LGA extraction is reconciled to its published totals. All 876 indexed tables have mapped pages, and all 2,292 source pages are represented. The 43 pages omitted from the guided classifier were reviewed by the user and confirmed to contain no data tables. No review-required flags remain. See [data-notes.md](data-notes.md).

## Rebuild current outputs

Run from the repository root. Python 3.10+ and [uv](https://docs.astral.sh/uv/) are required. These commands use existing local source PDFs and cached classification CSVs; they make no model API calls.

```bash
python3 scripts/build_abs_1911_table_spans.py
uv run --with pymupdf python scripts/extract_table68.py
uv run --with pymupdf python scripts/validate.py
uv run --with pymupdf python scripts/check_issues.py
```

The first `uv` run may download PyMuPDF. Validation returns a non-zero exit status on a failed check.

### Main outputs

| Output | Purpose |
|---|---|
| `data/intermediate/nsw_1911_lga_dwellings.csv` | Corrected 324-row NSW LGA dataset, with source units and row provenance |
| `output/build_abs_1911_table_spans/abs_1911_reviewed_pages.csv` | Page assignments after existing QA and accepted human overrides |
| `output/build_abs_1911_table_spans/abs_1911_reviewed_table_index.csv` | Contents table catalogue with mapped pages and printed-number variants |
| `output/build_abs_1911_table_spans/abs_1911_reviewed_table_spans.csv` | Explicit contiguous page runs; gaps are not filled |
| `output/build_abs_1911_table_spans/abs_1911_override_audit.csv` | Assignment changes, source files/rows and decision evidence |
| `output/build_abs_1911_table_spans/abs_1911_reviewed_issues.csv` | Remaining coverage/continuity checks and recorded source discrepancy |
| `output/extract_table68/` | Cell audit, source-backed corrections, transcribed published totals and page images |
| `output/validate/validation.json` | Reconciliation result and check counts |
| `output/check_issues/issues.csv` | Unresolved extraction/data failures; header only when none remain |

The original contents-derived index and candidate spans under `data/intermediate/table_index/` remain inputs to the guided classifier. They are not the reviewed analysis map.

## Human decisions and printed numbering

The 108 accepted dashboard decisions (8 initial + 57 follow-up + 43 coverage exclusions) are archived in `data/intermediate/page_inventory/abs_1911_manual_page_overrides.csv`. They override accepted model QA and the separate assistant source-inspection records in `data/intermediate/page_inventory/abs_1911_source_page_overrides.csv`. The latter currently corrects Summary page 168 to Table 138, verified directly from the scan. Both snapshots remain available if dashboard working results are later reset; future dashboard edits are not automatically promoted.

Dwellings physical page 186 really prints **69**. Its neighbouring pages and the contents identify the continuing LGA sequence as **68**. In the reviewed map, `final_table_numbers` preserves 69, while `contents_table_numbers` and `table_ids` link the continuation to the contents sequence. The evidence is in `data/intermediate/table_index/abs_1911_table_numbering_evidence.csv`. No extra analytical table is counted.

The legacy extractor filename `extract_table68.py` is retained because it extracts that whole NSW sequence, physical pages 183–187, not just the page headed 69.

## Local review dashboard

Open an already-running dashboard at <http://localhost:8765>. If it is not running:

```bash
uv run explore/2026-09-20_census-qa-dashboard.py --batch coverage
```

Do not launch another copy on the same port. Both review batches are complete and promoted; the dashboard shows a completion screen. The 43 coverage decisions remain in `explore/output/2026-09-20_census-qa-dashboard/coverage_review_decisions.csv`, separate from the 57-page follow-up in `mapping_review_decisions.csv`. Use `--batch mapping` for the mapping queue. Saving future decisions does not automatically update the reviewed mapping.

## Layout

- `data/raw/`: immutable source material.
- `data/intermediate/`: generated data and accepted correction records.
- `scripts/`: existing Python pipeline (legacy location; extended rather than duplicated or moved).
- `output/<script-name>/`: generated mapping, extraction and validation evidence. The older `output/diagnostics/` holds the original review bundle.
- `explore/`: the local review dashboard and its working output.
- `The Loop.md`: decisions; `data-notes.md`: source definitions, caveats and validation.
