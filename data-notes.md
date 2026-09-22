# Data notes

## 1911 census page mapping — 22 September 2026

- `pdf_page` is one-based. `page_index` is zero-based. Printed page numbers are a separate field.
- The contents-derived index has 876 numbered tables across 14 part PDFs. This is not a census of all unnumbered tables.
- The reviewed map contains all 2,292 source pages: 2,249 guided-classifier pages plus 43 user-reviewed coverage pages. Assignments use the guided classifier, then accepted Flash Lite QA, Flash QA, GPT-5.5 adjudication, direct source inspection, and finally 108 human overrides. An uncertain later model pass does not erase an earlier assignment; it marks the page unresolved until adjudicated.
- Human overrides are preserved in `data/intermediate/page_inventory/abs_1911_manual_page_overrides.csv`, independent of the dashboard's working CSV. All 108 were matched exactly against the generated map. The 43 coverage decisions are all `exclude_page`: no data table (front matter, contents or blank), without a more specific page-type claim. Their original classifier fields remain empty; only the reviewed role is `non_table`. Assistant source-inspection corrections are separate and are not counted as human reviews.
- `final_table_numbers` records the final assigned page labels. `contents_table_numbers` and `table_ids` identify the corresponding contents sequence. A model-assigned number on a continuation page is not a claim that a number is visibly printed there.
- `assignment_source`, `review_status`, `assignment_evidence`, and `confirmed_page_title` retain the evidence level. Human confirmation applies only to the reviewed page, not every page of its table.
- Current issue register: **no review-required flags**. All 876 indexed tables have mapped pages, and every source page is represented. The two informational records are the printed Table 69 discrepancy and the confirmed non-contiguous membership of Ages Table 34. This completes the flagged review queues, not a human review of every model-assigned table.
- Reviewed spans preserve explicit contiguous page runs. No gaps are filled by taking the minimum and maximum page alone. No additional API calls were used.

## Dwellings page 186: printed Table 69

- The user confirmed the heading: **69 - Area, Population, Density, Occupied Dwellings, Etc. In Each Local Government Area - continued**.
- This is physical PDF page 186, zero-based index 185, printed page 2034.
- The contents lists the LGA sequence as Table 68, starting on physical page 183 / printed page 2031. Adjacent pages use 68; the NSW sequence continues through physical page 187 / printed page 2035. Victoria starts on physical page 188 / printed page 2036.
- The reviewed map therefore retains `final_table_numbers = 69` on page 186 and links it to `contents_table_numbers = 68`. This does not relabel the page as 68, renumber neighbouring pages, or count the continuation as an extra analytical table.
- The exact source discrepancy and reference are in `data/intermediate/table_index/abs_1911_table_numbering_evidence.csv`. The mapped LGA sequence runs from physical pages 183–199; page 200 is classified as non-table.

## NSW LGA extraction: source units and published totals

Source: `data/raw/abs_1911_census/1911 Census - Volume III - Part XIII Dwellings.pdf`, physical pages 183–187 (printed 2031–2035). The lowercase-named PDF copy used by the original extractor is byte-identical.

- Municipality areas are **acres**. Shire areas are **square miles**. The printed population/area and dwellings/area columns use those respective denominators. Do not sum mixed-unit areas.
- The opening heading on physical page 183 says “Exclusive of all Details relative to Full-blooded Aboriginals” (historical source wording). Population totals inherit that exclusion; they are not counts of every resident under a modern inclusive definition.
- Physical page 187 contains both the shire total and the NSW summary. Independent inspection of this scan gives:

| Section | Area | Area unit | Males | Females | Persons | Occupied dwellings |
|---|---:|---|---:|---:|---:|---:|
| Municipalities | 1,916,800 | acres | 514,873 | 526,886 | 1,041,759 | 206,312 |
| Shires | 181,201 | square miles | 323,759 | 255,204 | 578,963 | 120,517 |

- **Wollondilly** appears on physical page 187: area 931 square miles; males 2,561; females 2,288; persons 4,849; occupied dwellings 1,028. Its omission exactly explains the original shire dwelling shortfall of 1,028. These are source readings, not residual balancing adjustments.
- The NSW summary also lists unincorporated territory and shipping. These are not LGAs and must not be added as municipality/shire rows. The LGA-only totals will therefore differ from whole-state population and dwelling totals.

### Repaired output and checks

- Regenerated `data/intermediate/nsw_1911_lga_dwellings.csv`: **324 LGAs = 190 municipalities + 134 shires**. All eight numeric columns are populated; numeric values use plain digits/decimal points without thousands separators.
- Full-width name reconstruction recovers one-letter OCR fragments. Numeric extraction uses character centres, page-specific column grids and scan-skew adjustments instead of token starts and narrow name bands.
- Thirty residual name/cell corrections are explicitly transcribed from page images, not calculated as balancing residuals. `output/extract_table68/corrections.csv` records raw, automatic and corrected values with source page/row coordinates and evidence. `extraction_cells.csv` preserves every cell's extraction path.
- Every output row includes area unit, source PDF filename/SHA-256, zero-based index, physical and printed page numbers, printed table number, row number/y position and image path. The PDF/text-layer-specific geometry and corrections must be re-inspected if the source scan changes.
- `output/extract_table68/published_totals.csv` contains eight independently printed subtotal/summary rows, transcribed from scans. These do not feed adjustments into extracted LGA values.
- `output/validate/validation.json` reports **2,981 checks passed, zero failures**. Checks cover missing cells, source extent/counts, duplicate rows, strict numeric parsing, male-plus-female identities, printed ratios at their published precision, municipality/shire totals, whole-state totals with acre conversion, and shipping population.
- `output/check_issues/issues.csv` has no unresolved extraction/data issues. No numerical publication inconsistency was found. The printed 69/contents 68 discrepancy is retained separately in `output/validate/publication_inconsistencies.csv`.
- Smoke checks confirmed that removing Wollondilly reproduces the original 119,489 versus 120,517 dwelling mismatch; a shifted population cell fails additivity; a blank dwelling cell fails rather than becoming zero.

## Review observations — horizontal spreads and 7/8 confusion

- The user reports a recurring 7-to-8 table-number reading error. The next-batch review CSV records Summary physical page 33 as Table 27 (previous model assignment 28), and page 167 as Table 137 (previous assignment 138). This supports targeted checking, not a global replacement of 8 with 7.
- The user also confirms horizontal table continuations across pages, with another table beneath the first on a shared page. A page can therefore contain parts of several tables, and one table can occupy several pages without repeating its number on every part.
- The completed follow-up CSV contains 57 decisions, 33 with multiple table numbers. All were promoted alongside the original eight, retaining their exact page assignments and timestamps.
- The guided classifier currently sends one page image per request (`build_payload` in `scripts/classify_abs_1911_pages_guided.py`). Neighbouring table-number candidates are supplied, but neighbouring images are not. Candidates alone do not reveal the other half of a horizontal spread.
- Future reclassification needs neighbouring-page visual evidence, while assigning only table parts present on the target page. Table position, row labels, geography and column headings should support the linkage; do not copy every table from a neighbouring page or treat every interrupted page range as a confirmed error.
- Ages Table 34 remains mapped to physical pages 60 and 62, not 61. The user reviewed all three pages: 60 = 33 | 34; 61 = 33; 62 = 34 | 35. Preserve this exact membership. It is a confirmed gap, not an unresolved assignment; no specific left/right region geometry has been inferred.
- A gap is only marked confirmed when every intervening page and both boundaries have a human-confirmed or directly source-verified assignment. A smoke check removing the review for Ages page 61 kept the gap open.
- Applying the human correction on Summary page 167 exposed a separate model error on page 168. The contents, page text and rendered heading all identify page 168 (index 167, printed 2216) as **138.—TOTAL POPULATION OF THE NORTHERN TERRITORY**, not the model's 139. This is archived in `abs_1911_source_page_overrides.csv` with assistant-inspection provenance; page 169 remains 139.
