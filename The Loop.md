# The Loop

## Current decisions — 22 September 2026

- All 108 accepted human decisions are archived outside the disposable dashboard
  in `data/intermediate/page_inventory/abs_1911_manual_page_overrides.csv`.
  Human decisions take priority over separately attributed source inspections
  and accepted model QA. The completed dashboard batch stays saved.
- The completed coverage reviews are promoted. Retain their separate working
  ledger and human provenance; do not fabricate classifier results for omitted
  pages. Future dashboard saves still require explicit promotion.
- Preserve exact many-to-many page/table membership. A discontinuity is confirmed
  only after every gap page and both boundaries have been reviewed; do not fill gaps.
- Use the reviewed page map/index/spans in `output/build_abs_1911_table_spans/`
  for analysis. Original contents-derived spans remain candidate-generation inputs.
- Preserve printed Table 69 on Dwellings page 186. Link the continuation to the
  contents' LGA sequence through separate metadata; do not invent another
  analytical table or silently renumber the page.
- NSW extraction uses source geometry plus explicit image-backed corrections,
  never residual adjustments to force totals. Keep printed ratios in their source
  area units, and retain row-level provenance.
- `README.md` gives offline regeneration commands. `data-notes.md` records current
  counts, validation, source exclusions and remaining mapping gaps.
- Earlier entries below are historical; their missing-data and review-queue
  statements are superseded by the current outputs.

## 2026-06-19

- Downloaded City of Sydney historical council and ward boundary extracts into
  `data/raw/city_of_sydney_historical_boundaries/`.
- Interpreted "1901 onwards" as including the boundary regime active at 1901.
  For council boundaries, that means the first included period is `1870-1908`.
  For ward boundaries, the first included ward period is the one active around
  1901.
- Important limitation: the City of Sydney council-boundary layer does not give
  standalone historical polygons for every surrounding municipality before
  absorption; it is mainly useful for City of Sydney itself.

## 2026-06-19 (continued): NSW 1911 LGA dwelling data extraction

- Discovered the 1911 census PDF (Volume III Part XIII) has a text layer, so
  no OCR needed — used PyMuPDF word-level coordinates to reconstruct tables.
- **Key correction**: page 149 (PDF index) is Table 65 (counties by wall
  material), NOT LGA-level data. The actual LGA data is Table 68 on pages
  182-186 (PDF index): municipalities on 182-184, shires on 184-186.
- Table 68 columns: LGA name, area, males, females, persons, persons/area,
  occupied dwellings, dwellings/area, population/dwelling.
- The PDF text layer is noisy (OCR artifacts in names like "Glen InllEls" for
  "Glen Innes", "MurWl 'llumbah" for "Murwillumbah").
- Used name-anchored extraction: find LGA name y-positions, collect values
  within ±4px band. Page-specific column boundaries needed because pages 182-185
  and page 186 have different x-positions.
- Installed PyMuPDF via `pip install pymupdf` (Python 3.13.7).

### Extraction quality (first pass)
- 323 rows extracted: 190 municipalities + 133 shires.
- Municipality dwelling total: 206,312 (exact match with published total).
- Shire dwelling total: 119,489 vs published 120,517 (0.9% off).
- 11 rows with missing values (mostly truncated names from OCR noise).
- 7 rows with column misalignment (M+F ≠ P).
- Municipality males total: 479,668 vs 514,873 published (6.8% low — due to
  missing values and some column misalignment).

### Remaining issues to fix
- Truncated/mangled LGA names need manual correction.
- 11 rows with missing data need manual fill from page images.
- 7 rows with column misalignment need correction.
- Scripts in `scripts/` (extract_table68.py, validate.py, check_issues.py).

## 2026-06-24: OpenRouter page-inventory scaffold

- Added `scripts/classify_pdf_pages_openrouter.py` to classify every page of a
  census PDF with an OpenRouter vision model and write audit-friendly outputs:
  raw JSONL responses, a page-level CSV, and a table-level CSV.
- First target model is `qwen/qwen3.5-flash-02-23`, with rendered page images
  sent directly from PyMuPDF as JPEGs; no page images are saved by default.
- Intended first run command:
  `python scripts/classify_pdf_pages_openrouter.py --model "qwen/qwen3.5-flash-02-23" --max-workers 4`
- Output prefix defaults to
  `data/intermediate/page_inventory/abs_1911_census_volume_iii_part_xiii_dwellings_qwen_qwen3_5_flash_02_23_*`.
- The script now falls back to OpenCode's stored OpenRouter credential when
  `OPENROUTER_API_KEY` is not set. It compiled and a dry-run verified rendering
  and CSV writing.
- One-page smoke test with `qwen/qwen3.5-flash-02-23` failed before inference:
  OpenRouter reported no endpoint matched current guardrail/privacy policy. This
  model routes through Alibaba, so using it may require changing OpenRouter
  privacy settings or explicitly allowing the provider data-collection route.

## 2026-06-24 (continued): Gemini page inventory run

- Switched to `google/gemini-3.1-flash-lite` after the Qwen/Alibaba provider
  route was blocked by OpenRouter privacy policy.
- Full run completed for all 200 pages of
  `data/raw/abs_1911_census/1911_census_volume_iii_part_xiii_dwellings.pdf`:
  200/200 pages classified, no request failures.
- Runtime was about 3.5 minutes with `--max-workers 4`.
- OpenRouter-reported cost was approximately US$0.1815.
- Outputs:
  - `data/intermediate/page_inventory/abs_1911_census_volume_iii_part_xiii_dwellings_google_gemini_3_1_flash_lite_raw.jsonl`
  - `data/intermediate/page_inventory/abs_1911_census_volume_iii_part_xiii_dwellings_google_gemini_3_1_flash_lite_pages.csv`
  - `data/intermediate/page_inventory/abs_1911_census_volume_iii_part_xiii_dwellings_google_gemini_3_1_flash_lite_tables.csv`
- The first-pass table inventory has 111 table-like rows: 69 rows with table
  numbers plus unnumbered continuation/subtable rows. Treat this as a scaffold,
  not a final authoritative table of contents.
- Known issue: Gemini labelled PDF page index 185 (PDF page 186, printed 2034)
  as Table 69, but neighbouring pages and the title indicate it is a continuation
  of Table 68. Do not treat Table 69 as confirmed without manual verification.

## 2026-06-24 (continued): Contents/index extraction with Gemini 3.5 Flash

- Ran `google/gemini-3.5-flash` on the three contents pages (PDF page indices
  1-3) using `scripts/extract_contents_openrouter.py`.
- Extracted 68 indexed tables, matching the apparent true numbered range of the
  volume and confirming that Gemini 3.1's `Table 69` page-level label is not in
  the source index.
- OpenRouter-reported cost for the index extraction was US$0.125085. Most of the
  cost was completion/reasoning tokens, so future runs should consider disabling
  or limiting reasoning if exact transcription remains good enough.
- Outputs:
  - `data/intermediate/page_inventory/abs_1911_census_volume_iii_part_xiii_dwellings_google_gemini_3_5_flash_index_raw.json`
  - `data/intermediate/page_inventory/abs_1911_census_volume_iii_part_xiii_dwellings_google_gemini_3_5_flash_index.csv`
  - `data/intermediate/page_inventory/gemini_3_5_index_vs_gemini_3_1_inventory_comparison.csv`
- Comparison result: all index tables 1-68 are present in the Gemini 3.1 page
  inventory and all start on the expected PDF page index when using
  `expected_page_index = index_start_printed_page - 1849`. The only numbered
  Gemini 3.1 inventory row not present in the index is `Table 69`.

## 2026-06-24 (continued): Downloaded 1911 census PDFs and contents detection

- Downloaded PDFs from the ABS 1911 catalogue page:
  `https://www.abs.gov.au/AUSSTATS/abs@.nsf/DetailsPage/2112.01911?OpenDocument`.
- Excluded the two requested files: `Notes of the Commonwealth Statistician` and
  `Volume I - Statistician's Report`.
- Downloaded 17 included PDFs to `data/raw/abs_1911_census/` and wrote the
  source/download manifest to
  `data/raw/abs_1911_census/abs_1911_download_manifest.csv`.
- Added `scripts/download_abs_1911_pdfs.py` for reproducible downloading. It
  preserves source URLs, exclusion reasons, local filenames, and byte counts.
- Added `scripts/detect_contents_pages_openrouter.py` to scan the first pages of
  each downloaded PDF with `google/gemini-3.1-flash-lite` and identify
  contents/index pages.
- Ran contents detection over the first 10 pages of each included PDF; small
  index PDFs had fewer than 10 pages, so 152 pages were classified in total.
  There were no request failures and OpenRouter-reported cost was US$0.084498.
- Outputs:
  - `data/intermediate/page_inventory/abs_1911_contents_detection_raw.jsonl`
  - `data/intermediate/page_inventory/abs_1911_contents_detection_pages.csv`
  - `data/intermediate/page_inventory/abs_1911_contents_detection_summary.csv`
- All 17 included PDFs had at least one detected contents/index page and no
  summary rows were flagged as needing review.

## 2026-06-24 (continued): 1911 cross-document table index dataset

- Added `scripts/build_abs_1911_table_index.py` to run a stronger VLM
  (`google/gemini-3.5-flash`) on each document's detected contents pages and
  build a cross-document table index dataset.
- The first pass failed on Volume III Part XIV Summary due to malformed/truncated
  JSON; reran only that document with a larger `--max-tokens 32000`, which
  succeeded.
- Normalised outputs were regenerated from cached raw responses, so the final
  rerun did not make additional API calls.
- Final OpenRouter-reported cost across latest successful extraction records was
  US$1.069539.
- Outputs:
  - `data/intermediate/table_index/abs_1911_table_index_raw.jsonl`
  - `data/intermediate/table_index/abs_1911_table_index.csv`
  - `data/intermediate/table_index/abs_1911_numbered_table_index.csv`
  - `data/intermediate/table_index/abs_1911_table_index_subentries.csv`
  - `data/intermediate/table_index/abs_1911_table_index_summary.csv`
- `abs_1911_numbered_table_index.csv` is the main numbered-table dataset: 876
  numbered tables across 14 Volume II/III part PDFs. The 3 index-only PDFs are
  included in the summary/raw outputs but excluded from the numbered-table CSV.
- Validation: all 14 part PDFs with numbered tables have contiguous numeric table
  ranges with no missing table numbers according to the extracted contents.

## 2026-06-24 (continued): 1911 table page spans

- Added `scripts/build_abs_1911_table_spans.py` to derive page spans from
  `data/intermediate/table_index/abs_1911_numbered_table_index.csv`.
- Span rule: table start comes from the contents-derived
  `start_page_index_estimate`; table end is the page before the next later
  physical table start in the same document. This uses physical page order, not
  table-number order, because some contents pages have non-monotonic table starts
  by table number (e.g. Volume II Part I Ages lists Table 2 starting before
  Table 1).
- Same-page starts are kept as one-page overlaps and flagged for review rather
  than forcing a single table-page assignment.
- Outputs:
  - `data/intermediate/table_index/abs_1911_table_page_spans.csv`
  - `data/intermediate/table_index/abs_1911_table_page_spans_review.csv`
- Built 876 table spans across 14 table-part PDFs. The review file has 195 rows,
  mostly same-page table-start boundaries; ordinary final-table-in-document flags
  are not treated as review issues by themselves.

## 2026-06-24 (continued): Index-guided page classification

- Added `scripts/classify_abs_1911_pages_guided.py` to classify only pages from
  the contents-derived table spans, with candidate table numbers supplied to the
  VLM for each page.
- Initial smoke test showed that strict span-only candidates miss real boundary
  pages where the next or previous table is visibly present but outside the
  derived span. Updated the task builder so each page includes the span table plus
  adjacent table numbers from the same document. This keeps the model constrained
  while allowing boundary pages to match both visible tables.
- Ran full guided classification with `google/gemini-3.1-flash-lite`:
  2,249 unique pages classified, no request failures, no candidate mismatches.
- OpenRouter-reported cost for the full guided classification was US$1.536070.
- Outputs:
  - `data/intermediate/page_inventory/abs_1911_index_guided_pages_raw.jsonl`
  - `data/intermediate/page_inventory/abs_1911_index_guided_pages.csv`
  - `data/intermediate/page_inventory/abs_1911_index_guided_pages_review.csv`
- Page-role distribution: 1,130 `continues`, 377 `ends`, 268
  `complete_on_page`, 253 `boundary_multiple_tables`, 171 `starts`, 48
  `non_table`, and 2 `contents_or_index`.
- Review CSV now has 304 focused rows: 253 boundary pages, 48 non-table pages,
  2 contents/index pages, and 1 continuation warning row.
- Important caveat: Dwellings PDF page 186 remains flagged because the model says
  the visible header appears to indicate `Table 69`, while the authoritative
  contents-derived index only runs to `Table 68`. Treat this as a review item, not
  as evidence that a real `Table 69` exists.

## 2026-06-24 (continued): Flagged-page review bundle

- Added `scripts/render_flagged_pages_review.py` to turn the guided-classifier
  review CSV into a manual QA bundle.
- Rendered all 304 flagged pages at zoom 2.0 into
  `output/diagnostics/flagged_pages/`, grouped by `doc_id`.
- Outputs:
  - `output/diagnostics/flagged_pages/index.html`
  - `output/diagnostics/flagged_pages/review_index.csv`
  - `output/diagnostics/flagged_pages/<doc_id>/*.png`
- `review_index.csv` has blank `review_decision` and `review_notes` columns for
  manual review. Suggested decision values are: `accept_model`,
  `previous_table_only`, `next_table_only`, `both_tables`, `exclude_page`, and
  `needs_manual_extraction_check`.
- Rendered image counts by document: Non-European Races 57, Summary 48, Ages 34,
  Life Tables 26, Birthplaces 25, Dwellings 24, Occupations 17, Religions 16,
  Education 15, Schooling 15, Families 11, Length of Residence 9, Conjugal
  Condition 6, Blindness and Deaf Mutism 1.

## 2026-06-24 (continued): Automated first-pass QA of flagged pages

- Used a subagent to stress-test the flagged-page QA design. Recommendation was
  to use `google/gemini-3.1-flash-lite` for cheap triage, constrained to candidate
  table numbers, then escalate uncertain/candidate-set failures.
- Added `scripts/qa_flagged_pages_openrouter.py` to read
  `output/diagnostics/flagged_pages/review_index.csv`, send each rendered page to
  a VLM, and write first-pass QA outputs without overwriting the manual review
  CSV.
- Smoke test on 10 rows succeeded with no failures and cost US$0.007027.
- Full run covered all 304 flagged rows with no request failures and total
  OpenRouter-reported cost US$0.231212.
- Outputs:
  - `data/intermediate/page_inventory/abs_1911_flagged_page_qa_raw.jsonl`
  - `data/intermediate/page_inventory/abs_1911_flagged_page_qa.csv`
  - `data/intermediate/page_inventory/abs_1911_flagged_page_qa_human_review.csv`
- First-pass QA reduced the manual queue from 304 rows to 37 rows. Decisions:
  185 `boundary_confirmed`, 55 `accept_current_match`, 36 `candidate_set_wrong`,
  15 `correct_match_from_candidates`, 11 `non_table_confirmed`, and 2
  `contents_or_index_confirmed`.
- Treat the 37-row human-review output as a triage list, not ground truth. Some
  cheap-model notes are self-contradictory, especially where the page has visible
  row numbers or unnumbered continuation headings that can be mistaken for table
  numbers.

## 2026-06-24 (continued): Gemini 3.5 escalation of flagged-page QA

- Reran the 37-row first-pass human-review shortlist with
  `google/gemini-3.5-flash` using `scripts/qa_flagged_pages_openrouter.py`.
- Updated the QA script to accept either the original manual review CSV schema or
  the first-pass shortlist schema.
- Full escalation run covered 37 rows with no request failures and total
  OpenRouter-reported cost US$0.182390.
- Outputs:
  - `data/intermediate/page_inventory/abs_1911_flagged_page_qa_gemini_3_5_flash_raw.jsonl`
  - `data/intermediate/page_inventory/abs_1911_flagged_page_qa_gemini_3_5_flash.csv`
  - `data/intermediate/page_inventory/abs_1911_flagged_page_qa_gemini_3_5_flash_human_review.csv`
- Gemini 3.5 reduced the unresolved queue from 37 rows to 31 rows. Resolved rows
  include Birthplaces pages 157 and 265, Non-European Races pages 23, 25, and 73,
  and Occupations page 554.
- Remaining 31 rows are still `candidate_set_wrong` according to Gemini 3.5, but
  some notes remain internally inconsistent where the candidate list actually
  includes the model's visible table number. Treat this file as a prioritised
  adjudication list, not final truth.
- Important unresolved conflict: Dwellings PDF page 186 is again labelled by
  Gemini 3.5 as visible `Table 69`, while the contents-derived index currently
  ends at `Table 68`. This needs manual verification against the page image and
  contents page before changing table-index assumptions.

## 2026-06-24 (continued): GPT-5.5 subagent adjudication

- Ran five GPT-5.5 subagents over the 31-row Gemini 3.5 human-review shortlist,
  split by document. This used existing rendered PNGs and did not make additional
  OpenRouter calls.
- Saved the consolidated adjudication to
  `data/intermediate/page_inventory/abs_1911_flagged_page_qa_gpt55_adjudication.csv`.
- GPT-5.5 reduced the unresolved queue from 31 rows to 8 rows: 15 Birthplaces rows
  assigned to candidates, 6 Non-European Races rows assigned to candidates, 2
  Summary rows assigned to candidates, 6 Occupations rows likely assigned to
  candidates but still needing human review because the pages do not visibly print
  table numbers, and 2 Dwellings rows remain true candidate-set conflicts.
- Key interpretation: many Gemini `candidate_set_wrong` claims were caused by
  mistaking row/category numbers (e.g. `Birth-place No.`, occupation order, or
  birthplace codes) for table numbers, or by over-reading unnumbered continuation
  pages.
- Remaining high-priority manual checks: Dwellings PDF page 57 appears to align
  with out-of-candidate Table 33; Dwellings PDF page 186 visibly appears headed
  `69.-AREA, POPULATION, DENSITY, OCCUPIED DWELLINGS, ETC...--continued`, still
  conflicting with the contents-derived index ending at Table 68.

## 2026-09-20: Local manual QA dashboard

- Keep the UI to the eight unresolved pages, one scan at a time: table number,
  notes, Save & next, or skip without saving. Model evidence stays collapsed.
  Previous/Next review revisit the eight-page shortlist. Always-visible PDF
  controls browse adjacent scans without changing the review target.
- Run `uv run explore/2026-09-20_census-qa-dashboard.py`, then open
  `http://localhost:8765`. This local tool makes no model API calls.
- Human decisions are a separate review layer in
  `explore/output/2026-09-20_census-qa-dashboard/review_decisions.csv`.
  Saving does not alter source PDFs, the table index or the page mapping.
- Context navigation does not change the review target. Confirm an assignment
  explicitly; outside-index table numbers require an evidence note.
- On 22 September, discarded saved dashboard decisions at the user's request.
  Model adjudications and source data were retained.
