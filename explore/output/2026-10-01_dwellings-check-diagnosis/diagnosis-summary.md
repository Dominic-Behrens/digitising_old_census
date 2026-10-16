# Dwellings check diagnosis — 1 October 2026

## Outcome and scope

Every build-snapshot inconsistency has a diagnosis record: **4,206 failed checks and 6,761 incomplete checks**, 10,967 records in total. No missing, duplicate or extra check IDs. This is an investigation, not a corrected dataset. Production formulas, source candidates, PDFs and workbooks were not edited.

- [diagnosis.csv](diagnosis.csv): every check, worksheet row, original result/formula, cause, evidence, source pages, related cells, confidence and next action.
- [table_summary.csv](table_summary.csv): all 68 tables and their dominant patterns.
- [patterns.csv](patterns.csv): exact primary-cause counts by status and confidence.
- [coverage.json](coverage.json): coverage reconciliation.
- `generic_tables.json`, `room_tables.json`, `rent_tables.json`, `measure_tables.json`: detailed family investigations.

The ledger covers the export snapshot behind `mathematical_checks.csv`, not subsequent manual Excel edits. A failed aggregate can depend on the same malformed cell as many other failed aggregates. Counts are **check instances, not independent bad cells**.

## Main patterns

| Pattern | Evidence and interpretation |
|---|---|
| **Numeric columns shifted by label/leader tokens** | 2,825 FAIL records have alignment-related primary diagnoses, including mixed/suspected alignment cases. Printed dots in the label gutter, ditto marks, upper rent bounds and stray punctuation become data columns. Real figures move into another geography/room/inmate field, and trailing values or totals disappear. Some candidate payloads already have the nominal column count despite being truncated. |
| **Facing rows and class/category joins are wrong** | Unlabelled rows, omitted material labels, different rent lower bounds, or missing private/other/all headings cause adjacent source rows to be paired or merged. First-value precedence then hides later correct values. This also explains many incomplete identities. |
| **Total recovery selects a neighbouring source row** | 522 FAIL records are classified under rent-total recovery baseline shift. The selection compares PDF word-top coordinates with candidate row coordinates; a nearby next bracket's total can win. These are supported mechanism diagnoses, not 522 independently image-verified total corrections. |
| **Source-reading and hardcoded-correction errors** | Some original model cells and later manual recovery literals are wrong. These need direct source correction, not residual balancing. Multiple linked checks can expose one bad literal. |
| **A mathematical identity is not justified** | 68 FAIL records primarily involve the cross-average identity, with two further mixed outlier/read-error cases. Average inmates per dwelling, rooms per dwelling and inmates per room need matching coverage before their quotient is an identity. The printed tables include unspecified-room categories; compatible cohorts are not established by the existing check. |
| **Printed precision or source damage remains** | Some image-verified printed ratios do not meet nearest half-last-digit rounding; truncation or historical calculation conventions can explain a subset. Other cells have damaged/missing glyphs. These are not permission to change a source figure or infer a missing digit. |

Alignment-related count includes these explicit causes: leader columns/labels, propagated or mixed positional errors, source-column displacement, truncated leaders, facing-row mispairing, right-panel label shifts, sparse offsets, braced-group misalignment and misplaced source counts. Each record keeps its own confidence and secondary limitations.

## Concrete source-backed examples

1. **Table 52, first All-dwellings room row, physical PDF p115.** Printed: `1,438, 736, 550, 452, 474, 80, 3,730`. Workbook: four city cells blank, then `1,438, 736, 550` in the last three fields. One shifted row produces the geography and several private-plus-other failures.
2. **Table 18, All Concrete, p35.** The production image-recovery literal is `39`; the source prints `89`. This is a wrong hardcoded reading, not a census balancing adjustment. Its row, matched-class and section checks share the defect.
3. **Table 40, Under 1s, p77.** Bounded total-selection replay chose the next bracket's `6,776` instead of the printed `1,484`. Fixing individual totals without correcting row-coordinate selection would repeat the error.
4. **Table 55, All row labelled 13s, pp118–120.** Its values `10,922, 10,254, 2,738, 3,220, 1,921, 637, 29,692` belong to printed **12s-under-13s**. Comparing them with genuine private/other **13s-under-14s** rows produces seven false category joins.
5. **Table 58, private section totals, p125.** The Other-class heading is not detected. The Other-only Wagons row is placed in Private. Five private subtotal residuals exactly match the misplaced counts `637, 5, 6, 4`, total `652`. Perth and Hobart have printed `..` marks, not numeric zero glyphs; the count checks evaluate those printed marks as zero.
6. **Table 66's ten currency incompletes.** Seven source pairs are printed no-values that were returned as half-present numeric pairs. Three readable amounts are White `1s6d`, Cook `12s6d`, and Wide Bay `52s6d`. Different remedies are required for false absence versus a missing readable unit.
7. **Table 68.** Individual source checks identify malformed area readings for Orange East and Terania, and digit errors for York, Tinaroo and Nullagine. Burra's current hardcoded `4.47` also conflicts with the inspected printed `4.46`. These are individual reading/override issues, not a reason to loosen every density check.
8. **Table 48, Other occupancy, pp108–109.** Printed £2–£2 5s has total `128`, and £4 10s–£4 15s has total `3`. Both totals survive in assembled rows with wrong rent labels. An initial diagnosis called these omitted rows; direct source/worksheet comparison contradicted that claim. The five related section residuals remain hypotheses pending operand-level review. Adding those rows again would double-count them.

All PDF pages above are physical one-based pages, not printed page numbers. Exact check IDs and worksheet coordinates are in the ledger.

## Why INCOMPLETE is not one problem

Of 6,761 incomplete checks, **3,888 are static literal INCOMPLETE results** and **2,873 are numeric guards or other incomplete formulas**.

- **Static literals:** missing/duplicate totals, ambiguous categories, unmatched facing rows, missing headings or collapsed panels can prevent construction of an identity. Missing/malformed measure operands can also freeze a literal result because their precision is unavailable at build time: Narrogin's missing average-rooms value and Dublin's damaged density are examples. The 3,888/2,873 split describes formula formats, not structural versus numeric causes. Resolve the relevant source or assembly defect and regenerate the checks; editing an Excel cell alone cannot change a literal result.
- **Structural applicability:** 999 incomplete records have explicit nonprivate-only/structurally absent-counterpart diagnoses. For example, Private has no wagon/camp row, and sparse printed panels omit some categories. This is not automatically missing numeric data. Confirm the publication's absence convention before treating an unprinted counterpart as zero.
- **Dynamic input guards:** blank candidates, malformed numbers, absent no-value marks, shifted columns and half-present currency pairs prevent calculation. The ledger names the precise blockers.

Table 53's “400 and over” category has no printed Private counterpart, but p116 does print Other and All counterparts. Its seven diagnoses retain structural Private absence as the primary cause and now identify the additional missing Other match as an assembly/category defect.

## Confidence and unresolved source readings

- **Confirmed:** mechanism demonstrated by code/state or an individual source reading. It does **not** mean every operand in the check was independently digit-audited.
- **Supported:** provenance and numerical signatures support the diagnosis, with stated unverified readings or secondary causes.
- **Hypothesis:** a specific, falsifiable reading/alignment explanation remains to be adjudicated from the source.
- **Unresolved:** the exact missing source information is named; no digit is invented.

The integrated classification contains 7,141 confirmed, 3,423 supported, 398 hypothesis and five unresolved records. The five unresolved records refer to three source-reading problems: Melbourne's damaged count in Table 56's printed 17s-under-18s owner row, Lowan's shilling glyph, and Dublin's density final glyph. Two Table 56 p123 rows also have supported source-damage/original-error explanations; no missing digit is reconstructed from their totals.

Area-based density disagreements are conditional on treating displayed area as exact. The current checks account for target precision, not the printed area's possible rounding interval. For Glenorchy, printed `730 / 43.75` narrowly misses printed `16.685`; a **hypothetical**, unobserved area `43.752` lies within the displayed area's rounding interval and yields `16.68495`, compatible with that density. This establishes a competing joint-rounding explanation, not a recovered area or historical convention. Keep confirmed source digits separate from confidence in the historical arithmetic explanation.

Independent review also corrected Table 53 cell E40: its `½` candidate belongs to the All-dwellings 300–399-room row, whose printed Brisbane entry is an absence mark. The printed `141` is in the separate Total row, not a replacement for E40. This record is a supported source-reading/alignment disagreement, not a confirmed 141-versus-½ glyph error.

## Recommended repair order — not applied

1. Repair grid/row/class/rent-interval alignment and preserve all printed sections. Then rebuild, rather than patching thousands of dependent totals.
2. Repair total-selection coordinates and recheck every hardcoded source recovery against its image.
3. Separate supported mathematical identities from diagnostic cross-average comparisons; distinguish structural absence from unreadable quantities.
4. Re-run checks and adjudicate remaining individual readings and genuine printed discrepancies. Keep damaged readings and unresolved publication conventions explicit.

The existing all-column population and formula-recalculation checks were not sufficient to establish source correctness. Balanced matrices can share the same wrong alignment. Passing arithmetic is not a source digit audit.

## Verification and replay

- Ran `uv run explore/2026-10-01_dwellings-check-diagnosis.py --parent --integrate` against the frozen investigation inputs. All 10,967 check IDs reconcile; no missing, extra or duplicate IDs.
- Verified the 68-table summary totals and corrected source-review cases. Independent source-image and economic/inference reviews informed the qualifications above.
- `source_review.json` records bounded visual verification and review corrections. `incomplete_formula_causes.csv` separates literal/guarded formula formats by cause. `source_fingerprints.json` identifies the source/build artifacts; their recorded hashes remained unchanged.
- To regenerate only the integrated ledger, counts and table summary from the saved family diagnoses: `uv run explore/2026-10-01_dwellings-check-diagnosis.py --integrate`.
- No production repair, permanent regression test or paid extraction was performed. This investigation does not verify unflagged cells or establish historical rounding conventions.
