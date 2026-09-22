# Digitising Historic Australian census tables

This repo is a work in progress to digitise old census data out of PDFs. Big work in progress. Don't trust anything here yet. 

## What is here

- `data/raw/`: downloaded source material, including Australian Bureau of Statistics census PDFs and historical City of Sydney boundary data.
- `data/intermediate/`: generated inventories, review decisions, correction records and the extracted NSW dataset.
- `scripts/`: Python scripts for mapping, extraction and validation.
- `explore/`: an optional local review dashboard and its working outputs.
- `output/`: generated mapping, extraction and validation evidence.
- [`data-notes.md`](data-notes.md): source definitions, caveats and validation notes.
- [`The Loop.md`](The%20Loop.md): project decisions and development history.

## Rebuild the reviewed outputs

Requirements: Python 3.10 or later and [`uv`](https://docs.astral.sh/uv/). Run these commands from the repository root:

```bash
python3 scripts/build_abs_1911_table_spans.py
uv run --with pymupdf python scripts/extract_table68.py
uv run --with pymupdf python scripts/validate.py
uv run --with pymupdf python scripts/check_issues.py
```

The first `uv` run may install PyMuPDF. The validation scripts return a non-zero exit status when a check fails. These commands use the existing local PDFs and cached classification outputs; they do not make model API calls.

## Main outputs

| File | Description |
|---|---|
| `data/intermediate/nsw_1911_lga_dwellings.csv` | Reviewed 324-row NSW local-government-area dataset, with source units and row provenance |
| `output/build_abs_1911_table_spans/abs_1911_reviewed_pages.csv` | Reviewed page assignments, including accepted manual overrides |
| `output/build_abs_1911_table_spans/abs_1911_reviewed_table_index.csv` | Contents-derived table catalogue and mapped pages |
| `output/build_abs_1911_table_spans/abs_1911_reviewed_table_spans.csv` | Explicit contiguous page runs; gaps are not filled |
| `output/build_abs_1911_table_spans/abs_1911_override_audit.csv` | Audit trail for assignment changes and evidence |
| `output/extract_table68/` | Cell-level extraction audit, corrections, published totals and source-page images |
| `output/validate/validation.json` | Reconciliation results and check counts |
| `output/check_issues/issues.csv` | Extraction and coverage issues; header-only when no issues remain |

The file name `extract_table68.py` is retained for historical reasons. It extracts the full NSW sequence, including the continuation page printed as Table 69, rather than only one physical page.

## Optional local review dashboard

The dashboard is for local review only. It listens on `localhost` and does not make model API calls.

```bash
uv run explore/2026-09-20_census-qa-dashboard.py --batch coverage
```

Open <http://localhost:8765>. Use `--batch mapping` to inspect the mapping queue. Do not start a second copy on the same port.

## Provenance and limitations

- The numbered-table inventory is not a complete inventory of unnumbered tables.
- The reviewed map preserves printed table-number differences and does not infer page spans across gaps.
- The extracted values include source page, row and image provenance. Corrections are recorded rather than silently folded into balancing totals.
- Review decisions are archived in `data/intermediate/page_inventory/` and `explore/output/`.
- Source files retain their original provenance. Check the source metadata and applicable terms before redistributing or reusing downloaded material.

See [`data-notes.md`](data-notes.md) for detailed definitions, validation results and known caveats.
