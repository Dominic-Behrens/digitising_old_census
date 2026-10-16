# Digitising Historic Australian census tables

This repo is a work in progress to digitise old census data out of PDFs. Big work in progress. Don't trust anything here yet. 

Historical municipal map scans and a native boundary export are in
[`data/raw/historical_boundary_maps/`](data/raw/historical_boundary_maps/README.md).
The collection and source register are still being expanded. Check each map's
edition and boundary date before linking it to census data.

## NSW census LGA coverage panel

The panel has 2,558 council-year rows for all 10 NSW censuses from 1911 to 1981.
1981 is the first digital boundary edition verified in this work. Published
rosters define the rows; statistical parts are merged and source conflicts are
flagged. Name review and individual map-outline checks remain open.
Run `python3 explore/2026-10-14_nsw-lga-census-panel.py` from the repository root.
The builder requires PyMuPDF and Shapely 2 or later.
See [`panel outputs and status`](explore/output/2026-10-14_nsw-lga-census-panel/README.md).
The unchanged official1981 boundary GeoPackage is in
[`panel raw sources`](data/raw/nsw_lga_census_panel/README.md).

The same builder now produces the [Sydney panel](explore/output/2026-10-14_nsw-lga-census-panel/sydney_lga_census_panel.csv):
424 council-year entries, using each census's published Sydney region. It also
builds a [map preview pack](explore/output/2026-10-14_nsw-lga-census-panel/sydney_map_preview.pdf)
and a [1981 GIS layer](explore/output/2026-10-14_nsw-lga-census-panel/sydney_lga_1981.gpkg)
with 44 original ABS polygons. Historical polygons are not yet digitised;
full-outline and boundary-identity checks remain open.

## Other-state census LGA panel

The same panel method now covers Victoria, Queensland, South Australia, Western
Australia, Tasmania, the Northern Territory and the ACT for the ten census years
1911-1981. Raw sources are ABS per-state LGA census volumes, the national
Statistician's Reports (1911-1961), 1971 Field Count Statements and the ANU 1976
preliminary volumes; 1981 also uses the official ABS GeoPackage for the digital
check. Every roster row links to a candidate map source for its state and census
year, and the 1981 rows match 96-100% of the ABS 1981 whole-LGA names by state.

Run `python3 explore/2026-10-16_download-other-states-lga-census-maps.py` then
`python3 explore/2026-10-16_other-states-lga-census-panel.py` from the repository
root. See [`other-state panel outputs and status`](explore/output/2026-10-16_other-states-lga-census-panel/README.md).

## What is here

- `data/raw/`: downloaded source material, including Australian Bureau of Statistics census PDFs and historical City of Sydney boundary data.
- `data/intermediate/`: generated inventories, review decisions, correction records and the extracted NSW dataset.
- `scripts/`: Python scripts for mapping, extraction and validation.
- `explore/`: an optional local review dashboard and its working outputs.
- `output/`: generated mapping, extraction and validation evidence.
- [`data-notes.md`](data-notes.md): source definitions, caveats and validation notes.
- [`The Loop.md`](The%20Loop.md): project decisions and development history.

## What Git keeps

`.gitignore` excludes generated `output/` files, exploratory results, rendered
page caches, Python caches/environments and local credentials. It retains code,
script lock files, raw inputs, intermediate review/correction records, dashboard
decision CSVs and selected small pilot provenance records.

Ignored does not mean disposable. Back up the large extraction response ledgers,
source-cell caches and frozen investigation inputs separately. A fresh clone
does not contain these local inputs; copying the saved response ledger permits
offline replay without paying to extract the source again.

Ignore rules do not remove files already tracked by Git. No tracked data is
removed by this policy.

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

## Table-cell extraction pilot

The exploratory pilot uses `deepseek/deepseek-v4.1-flash` on eight requests:
Summary Table 27, Ages Tables 33–34, and five NSW LGA pages from Dwellings Table 68.
It uses neighbouring images, keeps source fragments separate, and quarantines
table cells found outside the accepted mapping. It does not replace reviewed data.

```bash
# Offline: render evidence and rebuild reports from cached responses.
uv run explore/2026-09-22_census-extraction-pilot.py
# Paid: run only requests not already attempted, within the US$5 pilot ceiling.
uv run explore/2026-09-22_census-extraction-pilot.py --run --max-cost-usd 5
```

Paid runs use `OPENROUTER_API_KEY` or the existing OpenCode credential. In WSL,
`--auth-file /mnt/c/Users/CIE-AJAX/.local/share/opencode/auth.json` selects the
existing Windows credential without copying it. Never commit credentials.

Outputs are under `explore/output/2026-09-22_census-extraction-pilot/`:
`cells.csv`, quarantined `context_cells.csv`, `checks.csv`, `metrics.csv`,
`review_findings.csv`, source evidence and `requests.jsonl`.
`status.json` records progress, actual/unknown cost and a resume command.
Failed or interrupted attempts are not retried automatically.
Reasoning is disabled: the first default-reasoning call exhausted its token
limit and was rejected. Blank cells and printed dots are never converted to zero.
The verified NSW dataset and independent source references are used only for checks,
never supplied as answers to the model.

First-pass result: eight responses completed; **US$0.074746344** total including the
rejected initial call. **2,459/2,592 NSW numeric cells (94.9%)** matched uniquely by
source page, row name and column. Only **2/10 published-subtotal checks** passed.
The result is **not ready for bulk extraction**: row identities, unit changes and
horizontal continuation completeness need tighter handling. See `data-notes.md`.

The second pass uses source-reviewed crops, row-ID gutters and explicit unit
boundaries. Its input plan is `refined/source_regions.json` under the pilot output
folder. The row markers contain no numeric answers. Units and sections are supplied
from source inspection, so this is assisted extraction, not an unassisted model test.

```bash
# Offline second-pass replay; leaves the first-pass outputs untouched.
uv run explore/2026-09-22_census-extraction-pilot.py --refine
# Paid second pass; the US$5 ceiling includes BOTH passes and failed attempts.
uv run explore/2026-09-22_census-extraction-pilot.py --refine --run --max-cost-usd 5
```

Second-pass outputs live in `refined/`, with a separate request ledger.
`comparison.csv` reports resolved checks, regressions and checks not repeated.
`row_id_benchmark.csv` separately tests NSW values by source-row ID and records
row-name matches. This does not replace the exact-name benchmark.
The combined cell files retain each cell's actual request hash and source image:
unchanged Summary rows and NSW published summaries remain first-pass results.
The pilot's saved input manifest labels female age-table fragments on pages 61
and 63 as context, so both remain in `context_cells.csv` although the corrected
reviewed map assigns Table 34 to all pages 60–63. Offline replay preserves the
historical request labels and makes no new call. Changing the original request
manifest or settings would create a new fingerprint and could incur another charge.

Second-pass result: **2,543/2,592 (98.1%)** NSW cells match by exact source page,
normalised name and column. Source-row-ID checks match **2,591/2,592 (99.96%)**;
the remaining value is correctly read `4,416*`, which the strict parser leaves
unparsed. Six model-spelled names still need review. Published subtotals improve
to **9/10**, and Summary/Ages reference checks to **105/106**.
All 507 previously missing female-continuation cells are present in the pilot's
quarantine (234 on page 61; 273 on page 63). Both page assignments are corrected;
the pilot still has 66 failed checks and zero remaining mapping findings.
One female age total remains wrong; retained summary units and an omitted printed
table label also need review. These are exploratory results, not replacement data.

The region plan can set `provider_sort: "throughput"` consistently across all
regions of a case. This [routing preference](https://openrouter.ai/docs/guides/routing/provider-selection)
keeps the original model and price caps, and is included in the request fingerprint.
It was used only for the last two cases after the local runner interrupted a request.
`--timeout` controls socket inactivity, not total request duration. Confirmed charges
across both passes are **US$0.111863931**; including the interrupted-call reserve,
budget used/reserved is **US$0.465758331**. See `data-notes.md` for the cost uncertainty.

## Full-volume source-cell extraction (under review)

The source scope is the 14 Volume II–III detailed-table PDFs, including
numbered and independently confirmed unnumbered analytical tables. Reports,
Notes and index PDFs are outside scope. The reviewed index has 876 numbered
tables across 2,292 physical pages. Source review linked all 209 detected
unnumbered title/grid candidates to numbered-table subsections or
continuations. No independent table was confirmed by this screen.

The reviewed map has 166 source-page overrides. Right-hand pages may continue
two different tables; five visibly misnumbered headings retain both printed
and contents identities. See `data-notes.md`.

The generic whole-page/crop trial in `scripts/extract_abs_1911_tables.py`
failed row and column checks and must **not** be resumed as a bulk run.
Use the source-anchored path instead:

```bash
# Offline: rebuild the reviewed page map, then source-text anchors,
# raster-only candidates on text-limited pages and marked crops.
uv run --with pymupdf python scripts/build_abs_1911_table_spans.py
uv run --with pymupdf python scripts/build_abs_1911_source_rows.py
uv run --with pymupdf python scripts/build_abs_1911_image_rows.py
uv run --with pymupdf python scripts/render_abs_1911_source_regions.py
# Network: one bounded Go region, only while Zen "Use balance" remains off.
# Supply OPENCODE_GO_API_KEY in the environment or use --auth-file.
uv run --with pymupdf python scripts/extract_abs_1911_source_regions.py \
  --run --provider go --go-balance-disabled-confirmed \
  --limit-requests 1 --max-attempts 1
# Offline: reconstitute cells/issues/status without a request or retry.
uv run --with pymupdf python scripts/extract_abs_1911_source_regions.py --replay
```

After checking trial crops, a Go-only batch can add `--workers 4` and set
`--limit-requests` and `--max-attempts` to its authorised batch size.
Reservations are logged before concurrent requests; OpenRouter runs serially.

The ledger and `status.json` give the checkpoint and last run command.
A recorded `running` state does not prove the process is live. Check the
process and any reserved attempts before starting another batch.

Row anchors are candidates, not a proof that every printed row was located.
Fifteen mapped pages lack a usable PDF text layer; image geometry adds 1,210
unverified candidates across those pages. The renderer keeps row-ID crops,
printed header images, hashes and a page review queue in
`output/render_abs_1911_source_regions/`. The network runner keeps an
append-only request ledger and unaccepted `cells.csv`, `issues.csv`,
`table_coverage.csv` (all 876 indexed tables) and `status.json` in its own
output folder. A source row can still have a wrong digit, mark, label or
column heading: no table is accepted without source-backed QA. Failed or
interrupted attempts are not retried automatically. `--retry-stale` explicitly
reissues only finished attempts with changed source-region images/mapping or
missing manifest fingerprints; it will not retry an unknown reserved attempt.
`--retry-changed-request` explicitly reissues finished attempts after a
changed prompt/model/token bound. `--retry-failed` selects only regions whose
latest finished attempt failed (for example, use `--max-tokens 16384` for
truncated JSON); add `--retry-failed-provider go` when falling back so a
previous failed paid response is not retried unchanged. Each retry gets a
new ledger fingerprint. None of these options retries unknown reservations.
The US$5 OpenRouter ceiling includes settled provider-reported charges and
full $0.50 reservations for unknown bills; the Go usage-equivalent limit is
separate. Do not enable Zen balance use.

`column_label` is the local transcription. A unique candidate heading from
another page of the same numbered table is shown separately in
`resolved_column_label`, with its source page and region; it remains unverified.

`resolved_row_label` can link a facing-page row to a uniquely aligned label
on the previous page of the same table; its source row is recorded and the
link remains unverified. The raw local `row_label` is never overwritten.

OpenRouter fallback for the other documents retains its US$5 cumulative cap.
The separate Dwellings Part XIII Luna run was authorised up to US$20 project-wide;
that permission does not extend to the other documents.

## Dwellings tables workbook

Generate the workbook from the unchanged source-cell transcription and PDF.
The script pins Python 3.13.15, PyMuPDF 1.28.2 and XlsxWriter 3.2.9:

```bash
uv run --locked scripts/export_abs_1911_dwellings_workbook.py
```

After the runtime and packages are cached, add `--offline` for a network-free
rebuild. Keep the adjacent `.py.lock` file with the script.

`output/export_abs_1911_dwellings_workbook/dwellings_numeric_checked.xlsx`
has one worksheet for each of the 68 contents-indexed Dwellings tables.
Unambiguous quantities are real Excel numbers; damaged readings remain text.
Each sheet has the printed title, standardised dimension headings and visible
formula-check columns beside the data. No separate QA or provenance sheet is added.
The exporter joins facing-page panels before writing the grid.
It uses the source candidates, printed PDF coordinates and documented direct
image reads to recover shifted or missing cells; it makes no paid API calls.
Table 68 includes `area_unit`: urban areas use acres, while rural sections use
square miles. Its area and density headings therefore do not assume one unit.

The 10 October tab-by-tab audit covers all 68 tables. Its source evidence and
coverage limits are in `data/intermediate/abs_1911_dwellings_tab_audit.json`;
`tab_audit.csv` beside the workbook gives one record per tab.
The pre-audit numeric workbook is preserved in `audit_baseline_2026-10-10/`.
These are source-review outputs, not an accepted analytical dataset.
Damaged readings, printed contradictions and unresolved categories remain visible.
The audit results and reusable extraction protocol are in `data-notes.md`.

Checks cover row/section totals, matched private-plus-other counts, population
identities, density ratios at source-reading precision, and shillings/pence
bounds where the source definitions permit them. Count deltas should be zero;
ratio/currency checks show `PASS` or `FAIL`. `INCOMPLETE` means a required value
or unambiguous grouping is missing; `N/A` means the identity does not apply.
Nonzero deltas, `FAIL` and `INCOMPLETE` have a failure fill. Checks do not change
source values to make totals agree, and rent averages are never added together.
The noninteger-count check uses an Excel array formula so every count field is
checked; implicit intersection must not reduce it to the first field.
Fixed-room comparisons use only rooms 1–15 with matching printed cohorts and
precision. Open-ended bins and unsupported average identities are `N/A`.
Source-conflicted punctuation, such as Table 68 Tinaroo's `3,279` density,
stays text rather than becoming a validated number.

`mathematical_checks.csv` in the same output folder records every generated
check, formula, source-row label and build-time result. Excel formulas respond
to numeric edits; the CSV is a build snapshot, not a live workbook export.
Rebuild after source corrections that change grouping or printed precision.
The earlier text-only `dwellings_source_tables.xlsx` is retained as the baseline.

`assembled_tables.json` records the mapped dimensions and original reading
strings before Excel conversion. `build_manifest.json` records SHA-256 hashes
of source inputs, mapping code, lock file and outputs, plus actual runtime versions.
Workbook timestamps default to a fixed epoch; `SOURCE_DATE_EPOCH` may override it.
Byte-identical builds require the same inputs, code, pinned runtime and epoch.

Run the source-backed mapping regressions:

```bash
uv run --offline --python 3.13.15 --with pymupdf==1.28.2 --with xlsxwriter==3.2.9 python -m unittest discover -s tests -p 'test_dwellings*.py'
```

Mapping uses printed column grids, category/class identities and facing-page
baselines, not arithmetic agreement. Table 67 keeps shared Outside Counties
area/density in separate group fields; those denominators do not belong to each
division's population or dwelling count. Unmatched or contradictory fragments
remain visible. A passing total or valid currency amount does not prove digit
accuracy. The audit record distinguishes full row/grid coverage, direct visual
readings and bounded independent samples.


## Review model output locally

Run `python3 explore/2026-09-24_extraction-qa-dashboard.py` from the project
root, then open `http://localhost:8766`. Choose a PDF, table or QA flag; use
**Random region** to inspect an unselected crop. The page shows the original
marked crop, its printed heading, raw model cells, source-linked labels shown
separately, and issue flags. A direct region link uses the URL fragment, for
example `#1911_census_volume_iii_part_xi_life_tables%3A%3Ap27%3A%3Ag3`.

This dashboard is read-only. Its rebuildable browsing cache lives in
`explore/output/2026-09-24_extraction-qa-dashboard/review.sqlite`; restart
the server after an extraction replay to refresh the snapshot. Neither
unflagged rows nor the displayed counts measure transcription accuracy.

## Historical map GIS pilot

Target: **1911 NSW local government area boundaries first**, including
municipalities and shires. Keep a georeferenced source image and complete LGA
polygons, including any separate parts and holes supported by the source.
Ward boundaries are context only and their extraction is deferred. Distinguish
the LGA perimeter from internal ward divisions and parish lines; do not assume
that each coloured region is an LGA or infer a perimeter by joining ward colours.
A map conversion and a census-date boundary
are separate products: neither a catalogue year nor a matching place name
establishes the geography at the census date.

The offline preparation stage is implemented:

```bash
python3 explore/2026-10-10_map-gis-pilot.py
python3 -m unittest discover -s tests -p 'test_map_gis_pilot.py' -v
```

Run from the repository root with Pillow and PyMuPDF installed; tests also use
NumPy. Tested versions
are recorded in the output fingerprint. The script makes no network/model calls.
It freezes the downloader register on its first run, checks every saved source
hash, inventories PDF pages, extracts sole embedded scan images at native
resolution, and makes a 12-case review pack. Other PDF layouts are rendered.
Changing the live download register does not change this pilot. Preserve the
frozen register; a new cohort should be an explicit new experiment.

Open the [pilot contact sheet](explore/output/2026-10-10_map-gis-pilot/contact_sheet.jpg).
The [case register](explore/output/2026-10-10_map-gis-pilot/pilot.csv) records
eight calibration cases and four evaluation cases, including alternate scans,
ward colours, rotated text, rivers, overview maps and retrospective PDF figures.
The circa-1810 land-grant figure is a negative control: processing must not
turn it into a 1911 LGA. The 1926 statewide map is a format stress test.
These cases are not a representative accuracy sample of all NSW LGAs.
Overview maps overlap local sheets; the evaluation split is a method check,
not a geographically independent performance estimate.

All generated files are in `explore/output/2026-10-10_map-gis-pilot/`:

| Output | Use |
|---|---|
| `source_manifest.csv`, `inventory.csv` | Frozen source cohort and page-level inspection |
| `pilot.csv`, `source_regions.json` | Cases, native dimensions, exact source/image hashes and preview transforms |
| `cases/<map_id>/` | Previews and extracted PDF images; ordinary JPEG inputs stay in raw storage |
| `templates/` | Blank map review, control-point, feature-review and census-link CSVs |
| `source_issues.csv`, `status.json` | Failures, file counts, timestamp, checkpoint and offline resume command |
| `source_fingerprints.json` | Code, source-register and runtime fingerprints |

Templates are rebuilt. Before entering decisions, copy the relevant template
to `data/intermediate/map_gis_pilot/` and keep it in Git. Preparation does not
read those completed reviews yet. A `prepared` status means that images and
provenance are ready; it does not mean that any map is georeferenced or accepted.
Old running records do not establish process liveness.

`target_feature_type` is fixed to `lga_boundary` in the pilot and map-review
template. The separate `feature_type` field is the observed source geography
and stays blank until review. This keeps the land-grant negative control from
being labelled an LGA just because that is the extraction target.

### Conversion design and acceptance gates

| Stage | Method to test | Evidence needed to advance |
|---|---|---|
| Identify panels and features | Whole-map review; Astra can propose panel boxes, legends, labels and boundary types | Confirm map frame/insets, distinguish LGA/ward/parish lines, retain printed dates and uncertainty |
| Georeference | Printed grid or reviewed stable landmarks; test an affine fit first, then alternatives only where justified | Verified reference source and CRS; spatially distributed fit points; separate check points; errors in metres and edge inspection |
| Trace LGA boundaries | Compare QGIS manual tracing, colour/line extraction, and Astra-assisted segment selection | Complete LGA geometry where supported; internal ward divisions excluded; source-visible segments, native-pixel coordinates and unresolved sections retained |
| Validate geometry | Overlay on original image; inspect seams, rings and shared edges | No unintended gaps/overlaps within the same dated coverage; valid geometry; no invented closure across unreadable sections |
| Establish 1911 geography | Compare dated maps, change records and the census area list | Evidence that each area version applies at the census date; unresolved areas stay unlinked |
| Export | GeoTIFF images and GeoPackage features/review layers | Separate spatial, historical and join decisions; complete lineage; accepted features separated from candidates |

The user approved NSW Spatial Services reference mapping and GDA2020 / MGA
zone 56 (EPSG:7856) for the Strathfield trial, for LGA-level census maps and
comparisons. The first trial uses an affine fit and a source-visible candidate
perimeter. A positional acceptance tolerance and final boundary review remain
open. Do not silently
use modern boundaries/coastlines as historical truth. Coloured bands may straddle
a boundary; decide which printed line they denote before vectorising them.
An affine fit is a proposed baseline, not an accepted method for every map.
QGIS supports control-point collection and several transformation methods;
compare their results on check points rather than fit residuals alone.
See the [QGIS georeferencer guide](https://docs.qgis.org/3.44/en/docs/user_manual/managing_data_source/georeferencer.html).

Use the **native image** coordinate frame for stored points and traces:
top-left edge `(0, 0)`, x right, y down, first pixel centre `(0.5, 0.5)`.
The preview x/y scale factors are recorded separately. PDF extraction also
retains the image's normalized-image-to-page transform and page rotation;
native-image coordinates are not PDF points. All later crops and overlapping
tiles must record their offsets and scales back to this frame. Insets require
separate transforms. Transform traced vertices through the same fitted mapping
as the image, with controlled densification for nonlinear transformations.

The data model has four separate keys: `map_id` for a source page/panel,
`feature_id` for an observed trace, `area_version_id` for a dated geographic
entity, and the existing census source-row ID. Keep many-to-many evidence links:
several maps can support one area, and one map can contain several areas.
Keep publication date, depicted date and validity interval distinct; unknown
dates remain unknown. Cross-year boundary harmonisation and population
allocation are later analytical tasks, outside this conversion pilot.

### First Strathfield conversion trial

The trial now exports a **candidate georeferenced GeoTIFF and LGA polygon**.
Inputs are the NLA atlas scan, a saved NSW road-reference extract, and the
assistant-inspected points/trace in
`data/intermediate/map_gis_pilot/strathfield_trial.json`. The native source is
unchanged. The raster retains all original pixels with an affine geographic
transform; it is not resampled into a north-up grid.

```bash
# Offline replay in the temporary package cache used for this pilot.
UV_CACHE_DIR=/tmp/map-gis-uv-cache uv run --locked --offline \
  explore/2026-10-10_map-gis-pilot.py \
  --trial data/intermediate/map_gis_pilot/strathfield_trial.json
```

The script requires Python 3.12 or later, declares pinned dependencies, and has
an adjacent dependency lock file. A fresh machine needs `uv run --locked`
once to download them before offline replay can work. The `/tmp`
cache is temporary; it is not part of the deliverable.

Outputs are in
`explore/output/2026-10-10_map-gis-pilot/cases/nla.obj-231128914_p001/georeferencing/`:

- [Review image](explore/output/2026-10-10_map-gis-pilot/cases/nla.obj-231128914_p001/georeferencing/review.jpg):
  candidate perimeter, fit-point coverage and modern reference-road overlay.
- `candidate_georeferenced.tif`: native scan with EPSG:7856 coordinates.
- `candidate_lga.gpkg`: LGA candidate, reference points and reference roads.
  The polygon is explicitly marked as unaccepted for 1911.
- `point_errors.csv`, `report.json`: separate fit/check/diagnostic errors,
  source/config/code hashes and limitations. `trial_status.json` in the pilot
  output root records this stage; preparation counts describe preparation only.

Eight road intersections fit the transform. Three held-out intersections have
RMS error **14.64 m** and maximum error **19.39 m**. One point corrected after
residual-led source reinspection is diagnostic only and excluded from that
summary. These checks do not measure boundary tracing error. Most perimeter
vertices lie outside the fit-point convex hull, especially on the west; the
map's accuracy there has not been established.

The first-pass trace follows the printed municipal line, including the stated
left-bank boundary on the Cooks River. The railway-obscured northern edge and
river-bank placement need review. The council records a Flemington addition
in 1892, later than the atlas's generic 1886 catalogue date. This candidate
therefore needs post-1892 boundary evidence before it can represent 1911.
See `data-notes.md` for sources and the control-point correction record.

### Cost and scaling experiment

Start with the Strathfield atlas image and its alternate scan. Establish a
reviewed manual baseline, then compare automated candidates against it.
Tune on calibration cases; apply fixed settings to the four evaluation cases
and report failures as well as successes. Do not measure quality by agreement
between two model answers. Before treating the resulting census geography as
final, obtain an independent geographic/historical review.

Record API cost, compute time, review minutes, failed attempts, position error,
boundary completeness and label/date errors per case. The main measure is
**total cost per accepted area**, with map-level costs retained for allocation.
No dollar estimate is credible until the pilot measures calls and repair time.
Run a small second batch before extrapolating to the full collection.

Reuse map-series interpretation, cached images and responses. Give Astra a
whole-map overview plus detailed source crops; require cited crop/segment IDs
and an explicit unresolved result. Never accept model-supplied geographic
coordinates without a verified reference. Vision models have documented
[spatial and line-style limitations](https://developers.openai.com/api/docs/guides/images-vision).
Keep model tracing as a benchmark arm until source review establishes its value.

The eventual runner should fingerprint source, crop, prompt, model, reference
data and settings; reserve budget before requests; checkpoint each attempt;
and retry only explicit failed/changed work. Start with a small worker pool and
scale from observed throughput. Use the [Batch API](https://developers.openai.com/api/docs/guides/batch)
for stable supported requests if its turnaround fits. Map API spend has not
been approved and does not inherit the Dwellings extraction budget.

This repository has a legacy `scripts/` pipeline. The new map work remains in
`explore/` while methods and acceptance rules are tested. Promote accepted
report work using the project promotion rule; do not add a second pipeline layout.

## Provenance and limitations

- The numbered-table inventory is not a complete inventory of unnumbered tables.
- The reviewed map preserves printed table-number differences and does not infer page spans across gaps.
- The extracted values include source page, row and image provenance. Corrections are recorded rather than silently folded into balancing totals.
- Review decisions are archived in `data/intermediate/page_inventory/` and `explore/output/`.
- Source files retain their original provenance. Check the source metadata and applicable terms before redistributing or reusing downloaded material.

See [`data-notes.md`](data-notes.md) for detailed definitions, validation results and known caveats.
