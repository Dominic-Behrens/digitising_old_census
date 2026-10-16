# Data notes

## Strathfield LGA conversion trial — 10 October 2026

- Source: `nla.obj-231128914`, Strathfield atlas scan, 3,616 × 5,000 px.
  The first trial exports a candidate GeoTIFF and one valid LGA polygon with
  87 distinct ring vertices. No wards are extracted. No census link is accepted.
- Reference: [NSW Spatial Services RoadSegment, multiCRS layer 5](https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Transport_Theme_multiCRS/MapServer/5).
  The saved response contains 371 named-road segments in the bounded Strathfield
  area, returned directly in EPSG:7856. It is not a complete road network.
  Road-intersection coordinates are checked against their cited OBJECTIDs.
  Raw reference snapshots and query parameters are in `data/raw/map_gis_reference/`.
- Eight assistant-inspected intersections fit an affine transform: RMS fit
  residual 8.54 m, maximum 14.91 m. Three held-out intersections have RMS error
  14.64 m, maximum 19.39 m. These are placement errors at selected road points,
  not a survey accuracy estimate or a boundary-error estimate. Present-day
  intersection stability still needs review. No residual threshold accepts data.
- G04 originally marked Oxford Street at source pixel (2055, 2180) while
  labelled Homebush/Albert. A 208.3 m initial residual prompted inspection of a
  wider source crop. The corrected Albert intersection is (2067, 1980).
  Its role is diagnostic, excluded from the held-out score; both readings and
  the correction reason remain in the trial input JSON. The three checks are
  The Boulevarde/Albyn, Bridge/Abbotsford and Cross/High.
- 81 of 87 perimeter vertices are outside the fit-point convex hull. Western
  and southwestern placement needs additional evidence. The valid polygon is
  a first-pass manual trace. The northern line is partly obscured by the railway
  symbol; the river-bank trace is approximate. The printed instruction specifies
  the left bank of the Cooks River; neither the river centreline nor modern
  council boundaries were substituted. The QA overlay was visually inspected.
- [Strathfield Council's 2024–25 Delivery Program](https://www.strathfield.nsw.gov.au/files/assets/public/v/3/council/plans-and-strategies/delivery-program-operational-plan-fy-2024-2025_wip04b.pdf),
  PDF page 14 (printed 13), records annexation of Flemington on 19 February 1892.
  The atlas's catalogue date is generically 1886. Verify the actual edition and
  post-annexation perimeter before treating this traced sheet as 1911 geography.
- GeoTIFF read-back preserves every decoded RGB pixel and the fitted transform.
  GeoPackage read-back verifies the candidate geometry, CRS and reference-layer
  counts. Generated outputs remain under the existing pilot script's folder;
  trial inputs are retained in `data/intermediate/map_gis_pilot/strathfield_trial.json`.
- All 15 preparation/affine regression tests passed, including withheld-point
  separation, corrected-point diagnostics, pixel-edge convention, degenerate
  control geometry and rejection of reused fit/check locations. No map API
  calls were made. An independent geographic/historical review is still needed
  before accepting the layer for census analysis.

## Map GIS pilot preparation — 10 October 2026

- The pilot freezes 148 source-file records from the still-growing download
  register: 153 image/PDF pages. All 148 source hashes and readability checks
  passed. These are file/page counts, not unique maps or boundary regimes.
  The frozen source manifest is in
  `explore/output/2026-10-10_map-gis-pilot/source_manifest.csv`.
- Twelve cases include eight calibration and four evaluation cases. Repeated
  local editions/scans stay in the same comparison group. Overview maps overlap
  local coverage, so this is not a geographically independent accuracy sample.
  Cases were visually inspected for selection; no extraction method has yet
  been tuned or evaluated on them.
- Each Strathfield PDF page has one embedded scan and no PDF text or drawing
  paths. Selected pages 1 and 4 extract to 1,024 by 1,696 pixels. Rendering at
  higher DPI cannot recover missing source detail. Page 1 depicts circa-1810
  land grants; page 4 depicts circa 1910. Both are retrospective heritage-study
  figures, not direct proof of 1911 LGA boundaries.
- Previews retain separate horizontal and vertical scale factors back to native
  pixels. The coordinate origin is the top-left image edge; x increases right,
  y down. PDF image placement and page rotation are recorded separately.
- At preparation: georeferenced maps zero; accepted boundary features and census
  links zero. See the trial entry above for subsequent candidate exports.
  The preparation script makes no API calls. Reference data, control points,
  positional tolerance, boundary interpretation and temporal evidence are still
  needed. The existing City of Sydney layer covers only the City, not all NSW LGAs.
- Nine offline regression tests passed: changed raw sources, changes between
  inspection and preparation, PDF image extraction, mixed/annotated/cropped PDF
  rendering, preview coordinates, unsafe/duplicate manifest entries and frozen
  cohort replay. The generated 12-case contact sheet was visually inspected.

## Historical boundary map downloads — 10 October 2026

- Source scans are in `data/raw/historical_boundary_maps/`. The first batches
  contain 84 boundary map scans, seven cover/reference images, and one
  six-page Strathfield historical-map compilation. These are file counts,
  not unique boundary regimes. Dictionary and NLA copies overlap.
- Dictionary catalogue dates span 1886–1895. Images are mostly about 960 px
  wide; NLA JPEGs have a long edge up to 5,000 px. Preserve each edition.
- The atlas calls the places suburbs, but maps municipalities and often wards.
  Parish boundaries are another distinct geography. Do not infer contemporary
  suburb polygons or 1911 census boundaries from an atlas title.
- NLA parent metadata can give a generic 1886 date. The map leaf, annotations
  and overprints control interpretation; check the actual boundary date.
- Visual review of the 34 NLA leaves found 30 maps, two covers, one title page
  and one statistics page. Strathfield PDF page 1 shows land grants circa 1810;
  it is not a contemporary municipal map. The compilation includes later maps.
- The first 88 files passed local size, SHA-256 and image/PDF checks. Two added
  Sydney overview maps (1877 and circa 1903) passed hash and image checks. The register is
  `explore/output/2026-10-10_download-boundary-maps/manifest.csv`. Scan validity
  does not establish cartographic accuracy or the correct census-date boundary.
- The City of Sydney archive returned HTTP 403 and its old map CDN hostname
  did not resolve. Dictionary and NLA copies are accessible alternatives.
- Trover's browser approach works here with a temporary Chrome setup. Trove's
  correct map search category is `images`, with `l-format=Map`. A `maps` URL
  fell back to results across all categories. Do not treat an “online” filter
  as proof of an accessible scan; verify the record's View links.
- Trove record `244327844` exposed the 1926 statewide map via its View button:
  NLA `nla.obj-2869419748` is the map, and `nla.obj-2869419619` is a separate
  place index and statistics sheet. Both are saved. They are not two maps.
- The 1926 native access map is 35,749 × 29,971 px. Downloaded JPEG is 5,000 ×
  4,192 px; requesting a larger width still returned that size. The native
  master offered by NLA is about 3.2 GB and was not downloaded. Fine tracing
  remains resolution-limited. The 1903 map's catalogue date is `[1903?]`.
- `trove_candidates.csv` records 22 map candidates from the initial searches.
  The 1918 statewide map has a catalogue record but no exposed scan in the
  inspected View record. The 1905 proposed Cumberland shires map and later
  Cumberland municipal maps are now saved. Search remains in progress.
- **Expanded collection:** 537 files, 1,615,799,371 bytes. All passed existence,
  size, SHA-256 and file-readability checks. Images/PDFs also passed dimensions
  or page-count checks. There are
  240 municipal files (233 JPEGs and seven PDFs), eight municipal ward maps, 28 maps with shire boundaries, two proposed-boundary
  maps, one petitioned/proclaimed map, 219 parish maps with LGA lines, two planning-scheme sheets, two
  boundary sheet indexes, 32 other reference images, one cadastral companion
  image, one PDF compilation and one GeoJSON historical boundary set. No registered file matches the known
  NLA unavailable-image placeholder hash.
- Ten more parish scans show municipal or shire lines for Coonamble, Mudgee,
  Lithgow, Uralla, Gulgong, Forbes, Mullumbimby, Cooma and Murwillumbah.
  Murwillumbah has two parish sheets. These also show goldfield, water or
  drainage district lines; do not trace those as LGA boundaries. The catalogue
  dates span 1937–1965 and do not establish census-date boundaries. Parkes
  and North Deniliquin remain candidates: LGA lines were not confirmed in
  this visual pass. Selection is recorded in
  `nla_regional_parish_third_review_candidates.csv`.
- Further parish scans show LGA lines for Dubbo (1957), Narromine (1936),
  Condobolin (`[1954]`), Temora (1925), Junee (1934), Muswellbrook (`[1948]`)
  and Kempsey (1949). Coverage is partial. Narromine and Muswellbrook also
  have coloured annotations; their date and authority are unverified. The
  Wollongong parish sheet remains a candidate because an LGA edge was not
  confirmed in this pass. Review: `nla_regional_parish_fourth_review_candidates.csv`.
- Tamworth (1940) shows suburban lands and part of its municipality. Tenterfield
  (1966) shows municipal and shire lines on a town/suburban-land plan. Five
  more leaves from NLA atlas `231103971` cover West Botany, Canterbury, Ryde,
  Randwick and Waverley, with catalogue date `[189-?]`. Its index `231104092`
  is a finding aid, not a boundary map. The atlas cover and advertisement were
  inspected but not selected for this batch.
- Added parish sheets with LGA lines for Inverell (1941), Narrabri (1960),
  Warren (1936), Taree (catalogue `[1966]`), Wallendbeen via Nubba (1933),
  the Balranald area via Benongal (1920), Shellharbour/Jamberoo via Terragong
  (1946), and Broughtons Vale via Cambewarra (1946). LGA lines coexist with
  water, catchment, mining and cadastral lines. The Benongal sheet labels a
  municipal line near Yanga but its title does not name that municipality.
  Taree has printed map date 9 May 1956, distinct from publication `[1966]`.
  Selection: `nla_regional_parish_fifth_review_candidates.csv`.
- Reviewed 17 town-plan records plus seven companion sheets. Selected Bega
  (1971), Mudgee (1969), Wingham (1970), Mullumbimby (1972) and Cowra (1970)
  for municipal lines, and Casino sheets 3 and 4 (1974) for partial shire
  boundary coverage. Casino county lines and North/South Casino cadastral
  labels are distinct from its LGA boundaries. Unselected sheets contain
  reference tables or cadastral town limits without a confirmed LGA edge
  in this pass; they remain candidates, not unavailable sources.
  Review: `nla_town_boundary_review_candidates.csv`. Bega, Mullumbimby and
  Casino are catalogued in copyright with research-use access notes; Mudgee
  and Wingham are catalogued out of copyright. Cowra is catalogued out of
  copyright but also carries a research-use access note. Preserve these
  record-specific terms. These maps do not establish 1901/1911 lines.
- Nine more parish maps show LGA lines for Balranald (Mamanga, 1928), Moama
  (Tataila, 1936), Murrumburrah (Murrimboola, 1964), Corowa (1940), Maitland
  (Gosforth, 1926), Penrith/St Marys (Mulgoa, 1926), Goulburn (Towrang, 1923),
  Orange (1945) and Bombala (1936 catalogue/base date). Boundary labels and
  symbols were checked on the scans. Coverage is partial. Gosforth, Towrang
  and Orange have coloured additions with unverified dates and authority.
  Keep goldfield, population-area and water/catchment outlines separate from
  LGA edges. Bombala also has a printed `62.315` identifier; the edition and
  boundary-revision date need confirmation before use for a dated claim.
  Ulmarra, Fosterton and Veness remain candidates because an LGA edge was
  not confirmed. Fosterton has a 1925 printed base date and `[1960]` publication.
  Review: `nla_regional_parish_sixth_review_candidates.csv`.
- Fifteen Sydney-area parish scans show LGA lines: Gidley (1964), Bankstown
  (1941), all four Hunters Hill sheets (1961), the Mosman part of Willoughby
  (1969), St George (1924), Bringelly (1953), Gordon (1930), both St Luke map
  sheets (1959), Londonderry (1931), Camden (1945 catalogue/base date) and
  Kiama (1928). Coverage is partial. The Mosman companion sheet contains
  legends, portion tables and small diagrams; its `map_reference_sheet`
  kind excludes it from the boundary-scan count. Hunters Hill includes LGA
  lines at rivers and the railway near Hornsby Shire; do not substitute parish
  edges. St George's printed notes distinguish municipal boundaries from
  proclaimed town/population-area limits. Londonderry and Kiama have coloured
  additions with unverified dates and authority. Camden's `60-102` identifier
  may indicate a later edition; its boundary revision date remains unverified.
  The Botany inventory is now fully inspected: eight map sheets and eight
  reference leaves (1971). LGA edges were not confirmed on the map sheets;
  cadastral/parish, locality and registration-of-buildings-area markings are
  distinct. All sixteen leaves remain unselected. Detailed review is in
  `nla_botany_series_review_candidates.csv`.
  Review: `nla_sydney_parish_review_candidates.csv`.
- Twelve further parish scans show LGA edges in the Illawarra/Southern
  Highlands: Kiama (1957 and 1972), Wonona (1923 catalogue; printed base
  29 December 1922), Coolangatta (1960 and 1973), Cordeaux (1922 and 1942),
  Moollattoo (1972), Calderwood (1968), Mittagong (1968), and Broughton
  (1958 and 1978). Labels and municipal/shire symbols were checked on the
  scans. Keep their distinct editions; coverage is partial. Calderwood labels
  its municipal line at Marshall Mount Creek; Kiama labels Shellharbour beside
  the Minnamurra River edge. Catchment, sanctuary, reserve, land-district and
  transmission-line markings are separate. Cordeaux's 1942 base/catalogue
  record also has a `60.104` identifier; edition and boundary revision date
  remain unverified. Coolangatta 1973 and Mittagong 1968 are sheet 1 maps;
  their sheet 2 companions contain reference tables and town insets,
  saved separately as `map_reference_sheet`.
  Review: `nla_coastal_parish_review_candidates.csv`.
- Cooma Q0982 has two cadastral sheets (`[1977]`) with separate LGA keys
  for Cooma, Monaro and Snowy River. The four Mudgee cadastral sheets (1975)
  distinguish Mudgee municipality from Cudgegong Shire; `1628462679` is
  wholly inside Mudgee and is labelled `cadastral_companion_map`, not counted
  as a boundary scan. Retain the Integration Survey Grid and corner values
  printed on these maps when georeferencing; do not assume a modern grid.
- The 1986 Illawarra agricultural-map catalogue describes shire boundaries,
  but all eleven inspected digitised leaves are `Onsite Only` and return the
  same 400 × 400 unavailable-image placeholder. They were not saved as maps.
  The property series records `395693180`/`556963784` and Illawarra `342135431`
  display library holdings diagrams; none was selected for this batch.
  Review: `nla_cadastral_shire_review_candidates.csv`. Cobar, Bomaderry and
  Crookwell town-improvement scans were deferred pending boundary review.
- Visual review reclassified four NLA downloads as library holdings diagrams:
  `252949302`, `3077494311`, `3077658488`, `3077665757`. They are finding aids,
  not historical municipal-boundary scans. Raw files are retained unchanged.
- The 1905 Cumberland proposal is now downloaded as State Library image
  `FL8787726`, collection `IE8787720`; Trove record `260765836` supplies the
  source link. It does not establish that proposed changes took effect.
- Added Cumberland boundaries dated 1948, 1954 and 1961, and the 1909 Kyogle
  map under the Local Government Act 1906. Kyogle also shows a quarantine
  boundary and tick-discovery markings; distinguish these from shire lines.
- County maps can show partial shires. Clarendon has a printed 1933 base-map
  date but `[1954]` publication; Denison has a 1922 base and `[1957]`
  publication, with shire boundaries highlighted. Overprint currency remains
  unverified. Cabonne's estimated catalogue date is `[between 1960 and 1969?]`;
  confirm chronology before analytical use. The register now preserves MARC
  publication strings, including uncertain decades, instead of normalising
  them to an apparently exact 1 January date where those strings are present.
- Direct NLA catalogue searches exposed more downloads than the initial Trove
  result pages. Candidate CSVs and `additional_sources.csv` preserve discovery
  and selection. Town/parish plans, unrelated books, non-NSW maps and the later
  Illawarra agricultural map set were deferred in these focused batches, not
  established as unavailable or outside the user's full requested collection.

## 1911 census page mapping — 22 September 2026

- `pdf_page` is one-based. `page_index` is zero-based. Printed page numbers are a separate field.
- The contents-derived index has 876 numbered tables across 14 part PDFs. This is not a census of all unnumbered tables.
- The reviewed map contains all 2,292 source pages: 2,249 guided-classifier pages plus 43 user-reviewed coverage pages. Assignments use the guided classifier, then accepted Flash Lite QA, Flash QA, GPT-5.5 adjudication, direct source inspection, and finally 108 human overrides. An uncertain later model pass does not erase an earlier assignment; it marks the page unresolved until adjudicated.
- Human overrides are preserved in `data/intermediate/page_inventory/abs_1911_manual_page_overrides.csv`, independent of the dashboard's working CSV. All 108 are applied to the generated map; the page 61 override was amended with user approval on 23 September, with the original decision retained in its note. The 43 coverage decisions are all `exclude_page`: no data table (front matter, contents or blank), without a more specific page-type claim. Their original classifier fields remain empty; only the reviewed role is `non_table`. Assistant source-inspection corrections are separate and are not counted as human reviews.
- `final_table_numbers` records the final assigned page labels. `contents_table_numbers` and `table_ids` identify the corresponding contents sequence. A model-assigned number on a continuation page is not a claim that a number is visibly printed there.
- `assignment_source`, `review_status`, `assignment_evidence`, and `confirmed_page_title` retain the evidence level. Human confirmation applies only to the reviewed page, not every page of its table.
- The current reviewed catalogue maps all 876 indexed tables and all 2,292 physical pages. Its five issue records document source-printed table numbers that differ from the contents identity; none is an unreviewed gap. Page assignment is still not a human review of every cell or even every page.
- Reviewed spans preserve explicit contiguous page runs. No gaps are filled by taking the minimum and maximum page alone. Rebuilding this mapping uses no additional API calls.

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
- On 22 September, the accepted Ages Table 34 map contained only physical pages 60 and 62: page 61's human review said 33 only, despite a visible female continuation. This historical gap was corrected with user approval on 23 September; see below.
- A gap is only marked confirmed when every intervening page and both boundaries have a human-confirmed or directly source-verified assignment. A smoke check removing the review for Ages page 61 kept the gap open.
- Applying the human correction on Summary page 167 exposed a separate model error on page 168. The contents, page text and rendered heading all identify page 168 (index 167, printed 2216) as **138.—TOTAL POPULATION OF THE NORTHERN TERRITORY**, not the model's 139. This is archived in `abs_1911_source_page_overrides.csv` with assistant-inspection provenance; page 169 remains 139.

## DeepSeek table-cell pilot — first pass, 22 September 2026

- Script: `explore/2026-09-22_census-extraction-pilot.py`; all pilot outputs are in its matching `explore/output/` folder. The pilot is not promoted into the analysis pipeline.
- Scope: Summary Table 27; Ages Tables 33 and 34; NSW only from Dwellings Table 68 (physical pages 183–187). Eight extraction requests, with target and adjacent context images kept distinct.
- Independent checks use 106 source-transcribed numeric cells from Summary/Ages and the verified 324-row NSW dataset. These values are not sent to the model.
- Model: `deepseek/deepseek-v4.1-flash`. The initial default-reasoning request used 27,820 reasoning tokens out of its 32,768-token completion limit and truncated the JSON. It cost US$0.0405126 and was rejected. The non-reasoning Summary rerun finished normally, used zero reasoning tokens, cost US$0.005597004, and matched all 18 selected source reference cells.
- The Summary rerun still read Norway/Adelaide males as 135 rather than the source's 136. Sex and regional additivity both flagged this. `source_inspections.csv` and the high-resolution row crop record the correction evidence; the model result remains unchanged.
- Source inspection and the Ages model response identified Table 34 right-hand continuations on PDF page 61 (bottom) and page 63 (top). At the first-pass date, the accepted map contained only pages 60 and 62. The pilot kept context separate; both mapping conflicts were resolved later without changing the original model response.
- No dot/blank symbol legend was located on the inspected pages or the first five pages of the Ages and Summary volumes. Printed dots remain raw marks with no numeric value; blanks and uncertain cells are also distinct from zero.
- Final run: all eight non-reasoning requests completed, costing US$0.034233744; total spend including the rejected initial attempt was **US$0.074746344**. Nine attempts are retained, all with reported cost. One request took about 8.5 minutes; latency was variable.
- The NSW benchmark is an exact **page + normalised row name + column** match, not a comparison by row position. It scored **2,459/2,592 cells (94.87%)**. Failures comprise 104 cells with no matching row label (13 names), eight ambiguous cells from a duplicated Murrurundi label, and 21 differing, unparsed or uncertain values. Duplicate identities do not get a last-write-wins pass. These counts do not imply 13 source rows were omitted: name transcription can prevent a match even when a row is present.
- Section checks preserve each emitted heading and use the preceding explicit municipality/shire heading where available; they do not borrow grouping from the benchmark. A cached-response check recovered the 56 municipality/10 shire boundary on page 185 without changing numbers. Unit errors remain: the model missed area units on page 183 and carried acre metadata across the page 185 shire boundary.
- Only **2/10** NSW published-subtotal checks passed. Source-inspected numeric errors include Paddington males **1,494 instead of 11,494**, and Bolwarra females **1,457 instead of 1,487**. These remain unchanged in the pilot outputs, with cropped-source evidence in `source_inspections.csv`.
- Independent Summary/Ages reference checks: **82/106** matched. All 18 Summary references and all 44 male-Ages references matched. The 24 failures were female-Ages reference cells on context pages 61 and 63: the model identified the continuation in its notes but did not emit those cells. `context_cells.csv` is therefore empty for this run, not proof that no context fragments exist.
- All eight responses passed the structural request checks, but three reported incomplete transcription. Final validation produced **3,825 passes and 289 failures**, plus two separately source-inspected mapping conflicts. Checks overlap and are not an overall accuracy percentage. An API-completed request is not a validated table.
- Offline replay and the completed `--run` resume command reused all eight results with an unchanged request-ledger checksum and no further paid requests. Blank/dot/zero parsing and the within-page section transition were exercised on source-backed records.

## Source-region refinement — 22 September 2026

- The second pass uses 23 extraction crops at 300 DPI: 16 NSW LGA row bands, six male/female age-table halves, and the Summary Norway row. Separate header images provide column and unit evidence. `refined/source_regions.json` records PDF-point bounds, source row centres, IDs, sections and units.
- NSW row centres come from the existing source-geometric extractor, not from numeric benchmark values. The 324 LGA rows are split into bands of at most 24 rows. Small crop overlaps preserve digits on skewed scans; only gutter-labelled rows are extraction targets.
- On Dwellings page 185, the first 56 LGA rows are municipalities in acres; the last ten are shires in square miles. The lower section explicitly prints `sq. miles.`. Supplied unit and section metadata are source-reviewed controls, not evidence that the model inferred them correctly.
- Ages Table 33 has 39 logical rows across pages 60–61. Table 34 has 18 rows on the lower halves of pages 60–61, then 21 rows, including the total, on the upper halves of pages 62–63. Paired halves share source-row IDs. The pilot's fixed manifest still labels pages 61 and 63 as context; its cells remain quarantined even after the reviewed map was corrected.
- First-pass request and result files are preserved. The second-pass ledger stores raw model responses and the exact input manifest. Derived cells retain the request hash and image that supplied each value. Unchanged Summary rows and NSW published totals/state summaries remain first-pass results.
- Numeric benchmarks and independent reference cells are not sent to the model. The exact-name benchmark remains separate from the new source-row-ID benchmark, which records numeric and name matches independently. The refined LGA benchmark excludes retained state-summary rows using the reviewed region scope, not by dropping unmatched LGA names.
- All eight current second-pass cases completed. Exact page/name/column matches improved to **2,543/2,592 (98.11%)**. There are 48 failed matches caused by six row labels, plus one faithfully transcribed but unparsed annotated number. Source-row-ID checks separately match **2,591/2,592 numeric values (99.96%)**; no parsed NSW numeric value differs from the benchmark.
- Source crops confirm the six name mismatches: `Cobborah` → `Cobbora`, `Eurobodalla` → the printed `Eurobadalla`, `Inlay` → `Imlay`, `Namoï` → `Namoi`, `Talabragar` → `Talbragar`, and `Timbrabungie` → `Timbrebungie`. Raw model names are not overwritten. Eurobadalla is a new spelling regression from the first pass; its ten failed checks concern one name join, not ten numeric errors.
- Queanbeyan's area really prints **`4,416*`**. Both model passes preserved it correctly, but the strict numeric parser leaves the value blank. This is an annotation/parsing issue, not a digit-reading error. It blocks the municipality-area subtotal; the other **9/10** published subtotal checks pass. The asterisk is not silently stripped.
- All 324 LGA body rows have source-reviewed area units: **190 acres, 134 square miles**. Six exact-name unit/section checks fail because the names do not match, not because these provided body units are wrong.
- The combined Summary/Ages output matches **105/106** independent reference cells. The remaining failure is the female age 75–79 total: model **6,034**, source **6,934**. This causes a 900-person age-total discrepancy. The source crop confirms the digit; the model value remains uncorrected.
- Both age tables pass all **156** row-pair/column-coverage checks. The female continuation contributes **507 quarantined cells**: 234 on page 61 and 273 on page 63. Dots remain uninterpreted marks; the completed combined output contains no literal `"0"` strings. These coverage and spot checks do not prove every age-table cell is accurate.
- The targeted source-inspected errors are corrected in the new responses: Norway/Adelaide males **136**, Paddington males **11,494**, and Bolwarra females **1,487**. Other Summary cells retain their first-pass values and provenance.
- Two further metadata limits remain. The retained page 187 municipal summary has first-pass square-mile metadata, but its source explicitly uses acres and per-acre densities before changing to square miles for subsequent rows. The page 187 `* Per acre` legend applies locally and does not establish the meaning of Queanbeyan's area mark. The new page 186 response also omits the printed table number; source, baseline and accepted mapping still preserve **69**, not 68.
- Final automated checks: **4,213 passes, 66 failures**. `comparison.csv` records 226 resolved check keys and ten regressions, all ten from the single Eurobadalla spelling change. Other new or unrepeated checks are labelled separately. Checks overlap and are not an overall accuracy rate. Ten independent residual source inspections are in `refined/source_inspections.csv`.
- The local runner's one-hour deadline interrupted the first page 186 request after six completed cases. Its remote outcome and charge are unknown; the ledger records a stopped client, not a live request, and retains a **US$0.3538944** reserve. Only the two remaining cases were then sent with throughput-prioritised routing under the original model and price caps. The six completed fingerprints were unchanged.
- Confirmed second-pass charges are **US$0.037117587**, plus that unresolved charge. Confirmed charges across both passes are **US$0.111863931**; total used/reserved budget is **US$0.465758331**, below the US$5 ceiling. There are 18 attempts across both passes, including the original truncated response and the interrupted request.
- Serving providers varied. Completed Morph requests took about 13–15 minutes; the two throughput-routed Together requests took about 24 seconds each. `--timeout 600` is a socket inactivity setting, not a whole-request deadline. The run is not a controlled provider comparison, so gains cannot be attributed to cropping alone.
- The original 22 September offline replay left the request-ledger checksum and five result CSV checksums unchanged, with no new paid attempt. Cached-response checks confirmed that metadata attachment and overlays did not change model-read values, names or uncertainty flags. The 23 September mapping correction and manifest-preserving replay are recorded below.

## Ages continuation mapping correction — 23 September 2026

- Direct inspection of physical pages 62–63 confirms female Table 34 continues in the upper half of page 63 and persons Table 35 continues in the lower half. The guided classifier's Table 36-only assignment on page 63 was wrong. `abs_1911_source_page_overrides.csv` now assigns 34 | 35 with source-inspection provenance.
- With user approval, the page 61 human override was amended from 33 to 33 | 34. Its note retains the original decision and its source. Rebuilding the reviewed map assigns Table 34 to pages **60–63**, Table 35 to 62–63 and Table 36 to 64. The map has 2,292 pages, 876 indexed tables and one informational issue record.
- The pilot replays historical request labels from its saved first-pass manifest, not the changed current map; otherwise the corrected page 61 label would create a new paid-request fingerprint. Both offline passes completed from cached responses: 8/8 each, no new calls. The refined pass still has 4,213 passed checks, 66 failed checks and **zero mapping findings**. Its 507 female cells remain in `context_cells.csv` because the original request classified those regions as context. The outstanding numeric, name, unit and annotation errors have not been repaired.

## Full-volume extraction trial — 23 September 2026

- `scripts/discover_abs_1911_unnumbered.py` screened 2,292 source pages in the
  14 detailed-table PDFs. It emitted 209 **unverified** title/grid candidates
  on 170 pages; 26 pages were text-limited. A title-like line can be a column
  band or section heading inside a numbered table. Do not promote candidates
  without inspection of the PDF and its numbered heading.
- `output/discover_abs_1911_unnumbered/review_evidence.csv` now has
  source-backed decisions for all 209 detected title/grid candidates:
  all are subsections or continuations of numbered tables. No independent
  unnumbered analytical table was confirmed by this screen; absence of
  evidence from a detector is not proof that none exists. The separate
  `low_text_review.csv` records 15 mapped numbered continuations and 11
  non-table pages among 26 text-limited pages. One reviewer had incorrectly
  called Religions physical page 50 blank; direct image inspection shows
  numbered Table 17 and corrected that review record.
- `scripts/extract_abs_1911_tables.py` uses the reviewed many-to-many page map,
  four overlapping image crops on each trial page, a durable request ledger,
  and separate unaccepted cell observations. The Go model is
  `deepseek-v4.1-flash`, with `reasoning_effort: none`; it is not given the NSW
  numeric benchmark or the independent spot-check answers. Go usage-equivalent
  estimates in the ledger are **not** OpenRouter charges.
- In the superseded 75-DPI-overview trial, the model emitted 170 cells for each
  of Ages Tables 33 and 34 from the **first crop** of page 60. The crop visibly
  contains Table 33 only; Table 34 begins lower on the whole-page overview.
  Its `[0,0]` cell centres were also unusable. The 35-DPI-overview trial instead
  emitted 170 cells for Table 33 and an empty `no_body` part for Table 34.
  This is a specific improvement, not proof of complete transcription.
- The 35-DPI trial with a 24-point crop margin still misassigned the **female
  Table 34** body on page 60 to **male Table 33** when the printed Table 34
  heading fell just above the crop. A targeted 60-point-margin crop includes
  that heading and returned 180 female cells for Table 34 and `no_body` for
  Table 33. The default extraction session now uses the larger margin in
  `production-v4/`. Older sessions remain preserved as diagnostics and must
  not be merged into accepted data.
- On Dwellings page 185, the 35-DPI first crop emitted 135 observations,
  including 27 with estimated centres outside the crop core. Of the 96 numeric
  cells with centres inside the core, 88 matched the reviewed dataset exactly
  after numeric parsing; eight belonged to one row labelled `Plattsburg` by
  the model versus `Plattsburgh` in the reviewed dataset and could not be
  joined by exact name. The previous 75-DPI trial also misplaced Richmond
  and Rockdale across an artificial band boundary. A model centre is an
  estimate, not source geometry.
- The wider 60-point margin fixes the tested male/female table identity, but
  not row-level accuracy. In Ages page 60's second crop, ten published male
  `TOTAL` values (including `73,061`) were emitted under the row label
  `Shipping`; the corresponding source row is visibly `TOTAL`. A numeric
  spot check alone would miss this error. The replay now flags a majority
  conflict when model-assigned cells fall after a different printed
  table-number heading on the same page; it flagged all 180 misassigned
  female cells in the older 24-point trial.
- No generic crop or mapped table is human-accepted by these trials. Every
  returned response, missing/overlapping table part, uncertain label, invented
  value and core-boundary conflict needs source-backed review before any
  claim that all tables are extracted.

- Direct inspection of Non-European Races physical pages 158–173 found
  a systematic one-page shift on right-hand continuations: pages 159, 161,
  163, 165, 167, 169, 171 and 173 belong to numbered Tables 103–110,
  respectively, not 104–111. Source-page overrides record each correction;
  the reviewed map and row anchors were rebuilt. Table 107's right half
  on page 167 is not an independent unnumbered table.
- Adjacent source headings also corrected Ages physical page 93 from
  Table 62 to the right-hand half of Table 61, and Non-European Races
  pages 17, 21 and 23 to Tables 12 | 13, 16 | 17, and 18 | 19,
  respectively. These were model-assigned, not human-overridden pages.
  The lower grid on Non-European Races page 133 continues Table 90,
  which starts at the bottom of page 132; it is not unnumbered.
- A second source-page audit rendered 235 boundary contact sheets and full-page views where an extra table could start below the top strip. There are 166 direct source-page overrides. A right-hand page can continue **two** tables from the preceding left-hand page: for example, Non-European Races physical pages 24–25 contain Tables 20 and 21 on both halves. Source reviewers who checked only the top strip missed the lower table; the full-page image and adjacent numbered headings control the map.
- Life Tables physical pages 31 and 56 each finish one table at the top and start the next below. Dwellings physical pages 178–179 each finish Table 66 above and print Table 67 below. Occupations physical pages 547–549 continue Table 81, page 550 starts Table 82, page 551 continues 82 and page 552 starts 83. These are page-specific assignments, not a global odd-page offset.
- Five explicit printed-number variants are kept in `abs_1911_table_numbering_evidence.csv`: Ages p72 prints 42 but belongs to contents Table 43; Birthplaces p258 prints 97 but belongs to 98; Occupations p102 prints 20 but belongs to 18; Dwellings p186 prints 69 but belongs to 68; Summary p89 prints 79 but belongs to 80. The printed number remains in `final_table_numbers`, while `table_ids` use the contents identity.
- `build_abs_1911_source_rows.py` generated candidate row coordinates for
  all 2,292 physical pages: 138,180 anchors; 2,221 pages have candidate
  table anchors, 15 mapped pages are text-limited and 56 have no mapped
  table. These counts describe OCR geometry, not complete data rows.
  `render_abs_1911_source_regions.py` marks page-local row IDs on source
  crops and preserves PDF/image hashes. Pages with uncertain anchors or
  absent headings remain a review queue.
- Raster geometry supplies 1,210 **unverified** row positions on the 15
  mapped text-limited pages. These are separate from the PDF-text anchors;
  source crops mark them, but section totals and right-hand row numbers
  still need source review. Birthplaces physical page 71 is the right-hand
  half of a spread: its printed row numbers link to birthplace labels on
  physical page 70. Do not treat a right-hand number alone as the full
  birthplace label. A Go probe of page 71 found the printed
  `Birth-place No.` as the 17th right-hand column but returned empty row
  labels; the source label is on page 70. Earlier output instead used
  added `rN` markers as labels. Both responses remain quarantined.
  On page 70, 75 of 83 PDF-number anchors were initially marked uncertain
  and omitted from model crops; the renderer now includes such marked
  candidates for explicit review.
- On Dwellings page 185 the continuation's column labels precede a
  section heading. A crop starting at that section heading omitted all
  printed column labels; the renderer now includes the page-top header
  through the first source row. A twelve-row Go probe with that corrected
  header returned all eight visible columns per row, but remains unaccepted
  pending source-backed verification across the corpus.
- In the source-anchored Go trial, Ages page 60's male `TOTAL` row kept
  the printed row label but incorrectly added `TOTAL` as a data cell,
  shifting its ten age values one column right and leaving the last
  column heading empty. QA quarantines the row. Dwellings page 185's
  seven Shires rows yielded 56 candidate values, but Ashford's printed
  occupied-dwellings-per-acre mark appears as `255` rather than `.255`;
  536 dwellings / 2,100 acres is about .255. The cross-column check
  flags this mark for image review without changing the raw transcription.
  Both trials remain unaccepted. Seven anchored Go requests have returned;
  their reported usage-equivalent total is 0.0359187 USD, not OpenRouter spend.
- Offline replay now writes `table_coverage.csv` with one row per 876
  catalogue tables, comparing mapped and rendered pages, returned regions,
  candidate cells and QA issues. A covered region is not a verified cell:
  statuses remain `incomplete`, `needs_source_review` or
  `candidate_unverified`, never accepted without source checks.
- A full render first produced 16,603 candidate regions on 2,236 mapped
  pages. Trial requests showed that local heading strips sometimes stopped
  after a title/subtitle, before the column labels. The renderer now includes
  the column-heading band up to the first candidate data row; all pages were
  regenerated. On Dwellings page 179, eleven Table 67 rows produced
  154 candidate cells in 14 printed data columns. The two rent-unit columns
  were both labelled with the shared rental heading, not their distinct
  printed `s.` and `d.` units, so those labels need review. On Life Tables
  page 31, Table 18 data rows have no local column heading; its printed
  heading appears on physical page 32. Nine data columns were transcribed
  per row. Their local labels remain empty; the resolved-label fields link
  to page 32 and require review. Two Ages page-5 heading-only requests
  initially failed strict JSON shape validation; the failures contain no
  accepted cells. The first thirteen Go attempts used 0.0602775 USD in
  reported usage-equivalent tokens, not OpenRouter spend. Later attempts
  are recorded in the append-only ledger.
- The offline cell view now retains the locally transcribed `column_label`
  and a separate `resolved_column_label`. It fills a blank only when one
  candidate heading exists for the same catalogue table and column index;
  `column_label_source_pdf_page` and
  `column_label_source_region_id` identify that heading. For Table 18 on
  Life Tables page 31, all nine labels link to the printed Table 18 heading
  on page 32. Inherited labels remain `needs_source_review`; differing
  source headings are not forced into one label. Adjacent duplicate
  headings, such as Dwellings' shillings/pence columns, are flagged; only
  those duplicate positions are excluded as inheritance sources.
- A facing-page row can have no local name. `resolved_row_label` links
  it to the previous page of the **same** table only when at least three
  distinct printed row numbers match, row heights agree within 12 points,
  and the source label is unique. Totals without a number must align with
  a nearby printed `Total` row. The local `row_label` is not overwritten;
  source page/row and `same_table_paired_page` origin are retained, with
  `needs_source_review` status. Birthplaces pages 70–71 give eleven such
  paired rows, including both totals.
- A bounded 40-region Ages Go batch returned 39 regions and failed one:
  physical page 6 group 4 omitted the visibly printed `Unspecified Adults`
  and `Period not indicated` rows despite mentioning both in ambiguities.
  The strict row-ID check rejected the incomplete response. A separate
  14-document sample returned one region from every volume, but showed
  layouts with absent local headings, facing-page labels, and one Life
  Tables crop where the printed age was duplicated as a data value. A
  revised prompt re-ran that Life region with nine metrics per row rather
  than age plus nine metrics. This does not validate other regions or
  transcribed digits.
- Independent source-image review found a Life Tables error on physical
  page 27, Table 15, age 40: the printed `p_x` mark is `.99056`, but both
  the PDF text layer and candidate cell say `.99066`; printed `q_x` is
  `.00944`. A high-resolution crop and `p_x + q_x = 1` support `.99056`.
  The candidate remains unaccepted. Offline QA now flags numeric
  `p_x + q_x` discrepancies above `.00001` for source review; it does not
  silently replace the cell. Four representative rows in Religions,
  Blindness, Non-European Races, and Conjugal Condition had no mark
  mismatch, but some lack printed local labels/headings. Families and
  Occupations representative rows matched. The Schooling page 44 Private
  School row has an omitted initial `..`, shifted age counts, and a missing
  `1` in `Unspecified`: its printed total is **335**, not 1,335. A 360-dpi
  source crop resolved the independent review's mistaken reading of the
  adjacent `1` as a thousands digit. Five candidate rows on that page fail
  the printed age-column sum; offline QA flags them without rewriting marks.
  Dwellings page 69 has eleven printed row labels in the right margin
  (1–10, `Unspecified`) that the model appended as a twelfth data column.
  Offline QA flags that numeric sequence for source review; it does not
  discard the candidate cell.
- The Go source-region batch stopped after two HTTP 402 (Payment Required)
  responses, with Zen balance use still disabled. Its 23 September checkpoint
  had 2,683 completed regions, 523 failed, zero in flight, and 13,397 still
  unresolved; most failures were 8,192-token JSON truncations. One bounded
  paid fallback for a heading-only region cost US$0.0005475; a 12-row Ages
  region, retried with 16,384 output tokens, cost US$0.008672265. Those
  examples cannot establish a corpus-wide price. OpenRouter fallback has an
  independent cumulative US$5 cap that includes the US$0.465758331 pilot;
  no complete table or corpus can be claimed from this checkpoint.
- The paid fallback then attempted 474 source regions, returning 398 and
  failing 76. Provider-reported settled charges plus the pilot total
  US$4.50050078406; US$0.49949921594 remains, below the US$0.50 reserve
  needed to start another paid request. Failed requests with a known
  provider-reported bill now count that bill, not a retained US$0.50
  reservation; unknown bills still keep the full reserve. On 24 September,
  one bounded Go retry returned after the prior day's two 402 responses.
  Go resumed for untouched regions with 16,384 output tokens; this is
  evidence of availability at that moment, not a guaranteed daily reset.
  Its local US$1,000 usage-equivalent ceiling is **not** authorised paid
  spend; Zen balance use must stay disabled.
- A further Go run stopped on one HTTP 500 and resumed for untouched
  regions, then stopped at another HTTP 402. The latest checkpoint:
  8,198 of 16,603 regions returned; 268 failed, two have stale legacy
  provenance, and 8,137 remain unattempted. `cells.csv` contains 792,395
  **unaccepted candidate** cells, 82,532 issue rows, and no accepted table.
  All 876 indexed tables have a coverage row: 527 incomplete and 349
  needing source review. The 2,242 Schooling age-sum flags show that
  response-shape validation does not establish faithful transcription.
  Paid fallback remains below its cap but cannot reserve another request.
- The user reported a Go cap reset; the resumed 24 September batch
  returned 1,700 further regions before another HTTP 402. That checkpoint
  had 9,897 returned, 287 failed, two stale and 6,419 unattempted.
  Its 951,094 cells and 97,102 issues were unaccepted candidates, not
  certified tables. The later Luna work below changes these counts.

## Dwellings Part XIII Luna extraction — 24 September 2026

- The document has 1,487 source regions over 195 PDF pages. The source
  crop on physical page 69 has its printed rooms row label at the right
  edge. Ten ruled dot/value columns plus the total are data to its left;
  the rightmost room number is not a twelfth data cell. The revised
  source-region prompt preserves these positions. On this crop Luna
  returned eleven cells for each of eleven rows; its first row has room
  label `1` and total `613`. The earlier DeepSeek response copied that
  room label as a twelfth cell.
- On physical page 179 Luna and DeepSeek each returned 154 cells over
  twelve marked rows. The Luna Inglis row starts `872`, `4,572`,
  `4,308`, `8,880`, matching the visible scan. Two inspected layouts
  are not an accuracy estimate for the document.
- The user raised the cumulative project OpenRouter ceiling to US$20.
  All 1,487 Dwellings source regions have Luna-returned responses,
  including 72 initially failed responses retried and the two older
  Go-only regions replaced. No Dwellings region is currently failed,
  untouched or stale against the source manifest. Offline replay contains
  136,349 unaccepted Luna cells from 1,183 data-bearing regions:
  29,172 `candidate_unverified` and 107,177 `needs_source_review`.
  No table is accepted; these are not verified census figures.
- Repeated responses omitted the final marked row of some twelve-row
  crops. Seven affected regions were selectively rerendered with ten
  points of space below the last marker; all other region images and
  manifest hashes remained unchanged. The final row is listed first in
  the prompt to enforce coverage. Page 25 region 7 then returned all
  twelve rows; its last row, `Bushes, Rushes, Spinifex, etc`, has eleven
  candidate cells. Crop and candidate status still require source QA.
- Provider-reported settled Luna charges for Dwellings are
  US$3.0673749380. With the earlier Dwellings DeepSeek pilot, confirmed
  provider-reported charges are US$3.1169287300. Sixteen Luna attempts
  and one pilot attempt have unknown charges. On 25 September the user
  authorised release of their US$8.3538944 budget holds: 16 append-only
  `reserve_released` events in the source ledger and one amended pilot
  record preserve the failed outcomes. Unknown does not mean unbilled.
  Project-wide confirmed provider-reported charges, now also the budget
  amount used, are US$7.21398132206 of the approved US$20 ceiling.
  OpenAI, OpenAI Flex and Bedrock pinned endpoints returned HTTP 404;
  Azure EU/US intermittently returned upstream 429. Serial Azure US
  completed the document after a two-hour cooldown. The run has exited;
  `output/extract_abs_1911_source_regions/ledger.jsonl` is its checkpoint.

## Dwellings workbook export — 25 September 2026

- `output/export_abs_1911_dwellings_workbook/dwellings_source_tables.xlsx`
  has one table-shaped worksheet for each of the 68 contents-indexed tables.
  Headings are standardised for dimensions such as state, area, and council;
  there are no summary, unassigned, QA, or provenance sheets.
- The exporter now combines candidate strings with printed-PDF geometry and
  source-image recoveries. Not every printed figure has an independent check.
- Physical PDF page 186 carries a one-off heading numbered `69`; the contents
  index and neighbouring continuation headings identify it within indexed
  Table 68, so it is not a separate workbook table.

- Physical pages 146–148 and 165–167 place Tasmania municipalities above
  Northern Territory counties and Federal Territory districts; some headings
  are split or marked as continuations. Physical page 179 contains the end
  of Table 66 above the start of Table 67. The export uses those printed
  headings and page positions to keep state and area labels aligned.

## Dwellings workbook repair — 1 October 2026

- Facing-page columns are joined before export. Shared-page table boundaries,
  state/class sections, structural leader cells and duplicate OCR fragments
  are handled separately. Room/inmate columns restart on continuation pages;
  their page-local indexes are not workbook column indexes.
- The all-table smoke audit found no entirely empty numeric column except
  Table 65's printed private-wagon and private-Aboriginal-camp columns.
  No three-letter row-label text was found in numeric fields. These are
  coverage checks, not proof of every digit.
- Tables 64, 65 and 66 each assemble 388 printed geography/total rows:
  NSW 143, Victoria 38, Queensland 65, South Australia 52, Western Australia 28,
  Tasmania 52, Northern Territory 7 and Federal Territory 3.
  Table 67 has 402 rows; Table 68 has 1,055 council/summary rows.
- Table 65 retains all 35 printed data fields, including private/other wagon
  and Aboriginal-camp columns. Canberra's stone/brick figures are 30/31;
  Jervis Bay has 3 concrete private dwellings, not Canberra's material row.
  A source review found a spurious OCR zero at Wonnangatta, stone-other;
  the printed no-value cell is blank in the workbook.
- Table 66 now recovers Argyle's room-10 rent as 18s11d and total rent as 9s0d.
  Missing candidate pence are read from the printed source, not calculated.
  Printed zeros, dots and annotations are kept distinct.
- Table 68 carries `area_unit`, `area`, `population_per_area_unit` and
  `occupied_dwellings_per_area_unit`. Municipal/city/corporation rows use
  acres; shire/district/road-board rows use square miles. Summary panels
  repeat those unit changes. Dublin, physical page 195, retains the damaged
  density string `5.3)`; no final digit is guessed.
- Additional image reads recover Table 36's private room-5, 20-and-over
  inmate cell as 1 (physical page 67), and Table 39's private Under-1s total
  as 3,769 (physical page 73). Numeric totals are not filled from residuals.
- Representative source-value assertions passed for Tables 7, 10, 11, 14,
  27, 36, 39, 64–68. Independent bounded reviews inspected Table 65 material
  lineage and Tables 66/68 currency/unit lineage; the Wonnangatta finding
  was checked against the image and corrected.
- Final rebuild: 68 visible worksheets and 6,429 data rows, confirmed by
  desktop Excel. Six behavioral regression tests passed. Excel-rendered
  panels were inspected for Tables 10, 27, 65, 66 and 68; the final pass
  confirmed wrapped long labels and the recovered inmate-11/12 boundary.
- Raw PDFs and extraction candidates are unchanged. Rebuilds are offline.
  This repair is not a census-wide, cell-by-cell independent digit audit.

## Dwellings numeric cells and mathematical checks — 1 October 2026

- The current export is `output/export_abs_1911_dwellings_workbook/dwellings_numeric_checked.xlsx`:
  68 worksheets, 6,429 data rows and 83,594 numeric source/category cells.
  Cell-by-cell comparison with the retained text-only baseline found no changed
  source quantities or dimension labels. Printed no-value marks become blank;
  unresolved readings, including Dublin's `5.3)`, stay text. Footnote annotations
  on numeric readings remain in number formats and source-reading comments.
- The 54,702 generated checks comprise 41,409 passes, 4,206 discrepancies,
  6,761 incomplete checks and 2,326 not-applicable checks. These count check
  instances, not independent bad cells. Discrepancies require source adjudication;
  arithmetic agreement does not establish that every digit was read correctly.
- Checks use only represented, disjoint components. Ambiguous/collapsed sections
  remain `INCOMPLETE`; missing totals are not inferred. Printed absence can
  contribute zero to count sums without becoming a numeric zero in the sheet.
  Genuine empty printed cells are allowed only in the direct-PDF Tables 64/65.
- Tables 2/67 do not compare total population with average inmates per occupied
  dwelling: the population includes people in camps without dwellings. Ratios of
  rounded averages propagate input rounding intervals; other ratios use half the
  last digit of the source-reading string. Shipping/total-population ratio rows
  are not applicable. Rent averages are not added or averaged.
- Table 2's last two data headings are now shillings and pence, not pounds and
  combined shillings/pence. Currency checks require integral nonnegative shillings
  and pence from 0 through 11; unreadable or half-present pairs are incomplete.
- Campbell Town is a municipality, not an other-camps category. A regression
  guards this distinction. Tables 64/65 now have no nonzero arithmetic deltas.
- Desktop Excel recalculated all checks: every result matched the generated CSV,
  with no Excel error cells. Live edits proved row/national totals, currency bounds,
  density changes, zero denominators, missing inputs and visible failure formatting.
  Test inputs were restored before saving. An Excel-rendered Table 1 was inspected;
  all 13 Dwellings regression tests passed.
- Formula tolerances and groups are fixed at build time. Rebuild after corrections
  to source precision/grouping. The CSV is a build-time snapshot and does not
  update when the user edits Excel. No paid calls or source-value repairs were made.

## Dwellings alignment and reproducible rebuild — 1 October 2026

- This mapping repair supersedes the preceding workbook counts. The rebuilt
  review workbook has 68 worksheets and 6,809 data rows. Raw PDF,
  `cells.csv` and `table_coverage.csv` hashes remained unchanged.
- Physical numeric grids exclude leader dots and rental-label tokens.
  Printed category/class identities and facing-page baselines control joins.
  Tables 4–9 retain Private/Other/All panels; Table 3 remains an overview.
  Contradictory geography proposals retain duplicate dimensions for ambiguity
  checks rather than using first-value precedence.
- Source-backed output scenarios confirmed Table 18 All Concrete total 89;
  Table 40 Private Under-1s total 1,484, not the next bracket's 6,776;
  Table 48 Other occupancy £2 total 128, £4 10s total 3, and the distinct
  £4 row's room-9/10/11 counts 3/1/2. Existing mislabelled rental rows are
  relabelled, not appended as duplicate source rows.
- Table 52 All one-room counts are Sydney 1,438, Melbourne 736, Brisbane 550,
  Adelaide 452, Perth 474, Hobart 80 and total 3,730. This panel was inspected
  in an actual desktop-Excel rendering after recalculation.
- Table 67 uses printed county column geometry. Shared Outside Counties
  area/density values are separate `area_group_*` fields. They are not
  denominators for each division's individual population or dwelling counts;
  individual density checks are not applicable for those grouped rows.
  Independent economic review found interior group tokens still displacing
  three divisions and overlapping crops duplicating York. Both were repaired
  against actual candidate layouts and printed named-row baselines, not an
  enlarged duplicate tolerance. All four division population/dwelling triples
  were checked against physical page 181. York appears once, with 5,836
  persons and 1,249 occupied dwellings; neighbouring Yilgarn is retained.
  A separate source-image review confirmed the four named Tables 18/40/48/52
  examples. Neither review was a full-workbook digit audit.
- Before repair: 54,702 checks — 41,409 PASS, 4,206 FAIL, 6,761 INCOMPLETE,
  2,326 N/A. After repair: 58,625 checks — 47,443 PASS, 1,550 FAIL,
  7,368 INCOMPLETE, 2,264 N/A. Check populations and row identities changed;
  this is not a one-to-one correction count or an independent bad-cell count.
  The exact earlier check snapshot is retained as `pre_mapping_checks.csv`
  in the exporter output folder.
- All 46 Dwellings regressions passed. Two final offline locked rebuilds
  produced byte-identical XLSX, mathematical-check CSV, mapped-table JSON
  and build manifest. Desktop Excel opened all 68 sheets; rendered Table 52
  and Table 67 division panels were inspected after recalculation. This is not
  a full visual audit or a comparison of every formula with its build-time result.
- Python 3.13.15, PyMuPDF 1.28.2 and XlsxWriter 3.2.9 are pinned with the
  adjacent script lock file. `build_manifest.json` records runtime versions
  and SHA-256 input/code/output hashes. `assembled_tables.json` preserves
  mapped dimensions and reading strings before Excel numeric conversion.
  Default workbook timestamps use epoch zero; repeatability assumes the same
  inputs, code, runtime and `SOURCE_DATE_EPOCH`.
- No paid extraction calls, residual balancing or new guesses for damaged
  digits were made. Individual source-reading errors remain: for example,
  Table 30 All room-7/inmate-8 candidate 6,539 versus inspected 6,536;
  Table 30 All Wagons inmate-2 candidate 14 versus inspected 144;
  Table 38 All room-1/inmate-1 candidate 10 versus inspected 110.
  These examples are prior source-inspection findings, not a new full digit
  audit. Historical rounding assumptions remain unchanged.

- The 1949 NSW roads/local-government map is two sheets, saved as
  `nla.obj-232786321` and `nla.obj-232786431`; parent `nla.obj-232786313`.
  Catalogue and printed date both give 1 January 1949. Both sheets were
  visually inspected. Count scans separately from unique maps.
- NLA catalogue format filtering uses `f[format][]=Map`. The attempted
  `f[format_ssim][]=Map` was ignored. Corrected named-shire candidate files
  replace those results. Baradine (`1494743226`) and Coonabarrabran
  (`1589978410`) scheme maps describe planning zones, reserves and allotments;
  metadata was retained, but no LGA boundary scan was confirmed or downloaded.

- ANU `G0039.pdf` is a 1906 Auburn municipality map (item
  `dc61527a-a72d-41d8-bf32-d46bedf7b206`), published by H.E.C. Robinson.
  One page; embedded scan 23,504 × 35,490 pixels; 33,374,489 bytes. The
  PDF passed hash/page/render checks and was visually inspected. It shows
  neighbouring municipalities, with faded print and paper damage. The
  1906 date comes from the catalogue, not a legible printed date in the preview.
  ANU permits research use; prior permission is required for reproduction.
  The 686.8 MB TIFF was not downloaded; the PDF already embeds a large scan.

- The State Library large-scale maps guide links its NSW Department of Lands
  municipality series (Sydney metropolitan area, 1917 onward) to catalogue
  record `74VKPlWXQkwd`. That record returned HTTP 403 on 10 October 2026.
  It remains a discovery lead, not evidence of downloaded scans.
- Visual review of parish scans confirmed labelled LGA lines in Appin
  (`233827404`, 1930) and Hume–Yass (`676584344`, 1942 base with 1962 revisions).
  They are classified separately as `parish_map_with_lga_boundaries`. They
  may show only part of an LGA. Manly Cove, Jamberoo and Caloola remain
  candidates for closer line/legend inspection; their temporary review images
  have not been added to the raw collection.
- Shoalhaven (`229902221`, 1859) shows petitioned and proclaimed boundaries;
  these must be distinguished when tracing. Hurstville (`229979114`,
  `[188-?]`) is a proposed municipality. The Sydney overview `229943868`
  has 1890 in its title but no publication date in the extracted MARC record.

- The latest 11 scans passed size, SHA-256, image decoding and dimension
  checks; all 171 files were rechecked with no failures. Visual contact-sheet
  review found partial Concord (`2115283922`; catalogue holds one sheet) and
  Willoughby (`230552079`) coverage. Sydney `231264239` has missing/damaged
  edges; `229943868` is a more complete 1890 copy. Preserve both source copies.

- Later NLA municipality-title search pages 2–3 each returned 100 records.
  The unfiltered-geography shire-title search returned 100 records. These
  inventories include records outside NSW and cadastral maps; catalogue hits
  are not counts of confirmed historical LGA scans. Candidate CSVs retain
  the query and page.
- Rookwood (`2005472402`) is printed January 1892 and explicitly shows
  boundaries and land holdings. Sydney `231896071` is the 1867 Willis
  overview with municipal and parish boundaries.
- Central Darling (`274859513`) shows shire and riding boundaries; catalogue
  publication estimate is `[between 1960 and 1969?]`. Darling parent
  `327914020` has no image copies. Its four scanned sheets are `327914267`,
  `512000221`, `513696650`, `513696522`, with the same uncertain decade.
  Verify printed/overprint dates before assigning boundaries to a census year.
- Eurobodalla `1513984517` has a shire title but describes a Dalmeny cadastral
  sheet (G40), marked “not a precise survey”. Berry `240949283` is part of
  an 11-sheet cadastral series with sheet 5 absent at NLA. Cobar `2250594982`
  describes 1976 census collection districts. These three remain candidates
  for visual review; no local-government lines have yet been confirmed.

- All 178 files passed size, SHA-256, image/PDF readability and dimension/page
  checks after this batch. Visual review confirmed the seven new scans. The
  Darling sheet with the large title (`513696522`) includes a legend for shire,
  riding and county lines. Library call-number annotations `[196-?]` are not
  printed survey dates. Do not mistake the four sheets for four unique shires.

- Six regional parish maps were saved after visual review of labels/lines:
  Gunnedah (`1371003520`, 1964), Moree (`572142853`, 1959), Quirindi
  (`518891570`, 1965), Molong (`233732229`, 1936), Ballina (`1315090865`,
  publication `[1967]`, printed 21 May 1958), and Wandook (`1220423251`, 1964).
  These show municipal or shire lines within parish coverage, not six complete
  LGA boundary polygons. Wandook also shows irrigation and water-supply areas;
  Gunnedah shows mining limits. Nyngan (`532879943`) remains unconfirmed.
- Hay (`3139821994`) has image copies and catalogue extent 23 sheets, but
  its browse page exposed no leaf links. Gosford (`740922141`, 1963) belongs
  to J.F.N. Murray collection parent `708368901`; its browse response listed
  116 identifiers from the wider collection. Do not treat these as 116 Gosford
  map sheets. The inventory CSV labels this relationship as unverified.

- All 184 saved files passed size, SHA-256, image decoding/dimensions and PDF
  page-count checks after this batch. The six new parish scans were also
  visually inspected at larger scale. No georeferencing or tracing was done.

- Visual review found Hay `3139821994` is a modern library holding diagram
  labelled “NLA holds sheets shown in pink”, not an aerial map leaf. It is
  retained as `library_holding_index_map`; `[1962?]` dates the map series.
  Gosford `740922141` is planning-scheme sheet X (1963), with partial
  Gosford/Hornsby/Colo/Baulkham Hills shire context. It is labelled
  `planning_map_with_lga_boundaries`; coloured planning zones are not LGA lines.
- The second regional parish batch covers Bega (1943), Ulmarra (`[1960]`),
  Wilcannia (publication 1924, printed 8 November 1923), Orange (`[1938]`),
  Mulyan (`[1939]`) and Waradgery (1936). Labels and distinctive lines were
  visually inspected. Coverage can be partial. Orange includes handwritten
  red boundary annotations; annotation date and authority remain unverified.
  These dates and source notes are preserved in the manifest and NLA metadata.
- Calala `1231993517` and Young `874321239` remain candidates, with temporary
  scans only. Their inspected areas contain property/mining and other lines;
  local-government boundary content needs closer confirmation.

- All 192 files passed size, SHA-256, image decoding/dimensions and PDF page
  checks after this batch. Seven new boundary-information scans and one
  additional holdings diagram were saved after visual review. The collection
  includes duplicate editions/copies and partial sheets, not 192 unique LGAs.

- Six further regional parish scans show municipal edges: Narrandera (1938),
  Barraba (`[1965]`), Gunnary/Burrowa (`[1965]`), Cootamundra (1962), Dungog
  (`[1935]`) and Croobyar/Milton (`[1926]`). Barraba has a printed 1936 base
  and `65.503` identifier; Gunnary has a 1940 base and `65.229` identifier.
  Edition dates do not establish boundary revision dates. Coverage can be partial.
  Goldfield, catchment, irrigation and Buildings Act lines are separate.
  Coolangatta 1973 and Mittagong 1968 sheet 2 are reference companions,
  excluded from the boundary-scan count. Manilla, Molroy, Mungadal and Lindsay
  remain deferred: municipal labels alone do not confirm an edge to trace.
  Review: `nla_regional_parish_seventh_review_candidates.csv`.

- Ten more parish scans show LGA edges: Hume/Yass (1972), Yass (catalogue
  1924, 1943 and 1965), Gunnedah (1964), Goulburn (catalogue 1916),
  Tenterfield (1943), Lynch/Nyngan (1958), Kamandra/Parkes (1940) and
  South Condobolin (1975, sheet 2). Labels, lines and legends were inspected.
  Municipal, ward, population-area, catchment, sanctuary and goldfield lines
  differ. The Yass 1924 record includes November 1935 markings; the Goulburn
  1916 record has later annotations, including 1924. Do not date all visible
  boundaries from catalogue publication alone. Yass 1965 retains a 1943 base.
  South Condobolin sheet 1 contains reference tables and is saved separately.
  Tunks Ward/St Leonards (`231636385`) and Yoee (`667629435`) remain deferred
  because a distinct LGA edge was not confirmed in this pass.
  Gunnedah `1371004367` is catalogued as one map on two sheets; its browse
  response exposes no separate leaf links. Complete physical-sheet coverage
  remains unverified.
  Review: `nla_regional_parish_eighth_review_candidates.csv`.

- Ten further parish scans show LGA lines: Camden (1933 and 1968),
  Campbell/Inverell (1961), Wandook/Deniliquin (1923), Gosforth (1917),
  Blaxland (`[1958]`), Yanga/Balranald (1950), Nowra (1942), Currambene (1927)
  and Derrulaman (`[1967]`). Coverage is partial. Gosforth explicitly labels
  annexation to West Maitland; its coloured property annotations have
  unverified date and authority. Blaxland includes the Colo Shire edge.
  Derrulaman shows the Conargo Shire edge with a 1937 base and `67-677`
  identifier. Yanga distinguishes municipal and flood-control/irrigation
  boundaries; Nowra/Currambene also show population, catchment, drainage
  trust and state-forest lines. Do not trace those as LGA lines.
  Aellalong and Coeypolly remain deferred; a title naming a municipality
  does not establish a visible municipal edge.
  Review: `nla_regional_parish_ninth_review_candidates.csv`.

- Eleven additional parish scans show municipal edges: South Jewnee/Junee
  (1965), Dubbo (`[1962]`), Timbrebongie and Wentworth/Narromine (1960),
  Condobolin (1959), Kempsey (1948), Binjura/Cooma (1935), Orange (1934),
  Murrungal/Burrowa (1932), Calala/Tamworth (`[1963]`) and Uralla (`[1963]`).
  Map labels and edge symbols were inspected; coverage can be partial.
  Binjura is faded. Orange has coloured annotations with unverified date
  and authority. Goldfield, urban-area, catchment, drainage, aerodrome and
  classified-area markings are distinct. Uralla's Police Offences Act note
  states that those limits match the town limits; it does not state that
  they match the municipal perimeter. West Waradgery (1919) remains deferred
  because its Hay label did not establish a distinct LGA edge in this pass.
  Review: `nla_regional_parish_tenth_review_candidates.csv`.

- Nine further parish map sheets show LGA edges: Marangaroo/Lithgow (1962),
  Brougham and Rowan/Muswellbrook (`[1961]`), Young (1954, two map sheets),
  Gulgo/Condobolin (1939), Broughton (1937), Demondrille/Wallendbeen (1931),
  and Hume/Yass (`[1962]`). Young has a third reference-to-portions sheet,
  saved as `map_reference_sheet` and excluded from the boundary-scan count.
  Muswellbrook labels municipal lines separately from suburban, town and
  Police Offences Act limits. Broughton shows Berry/Gerringong municipal
  labels, annexation and cancellation/variation notes; coloured annotations
  and revision dates require checking before assigning a census year.
  Taloumbi (`[1960]`) remains deferred because a distinct LGA edge was not
  confirmed. All selected map sheets were visually reviewed; coverage is partial.
  Review: `nla_regional_parish_eleventh_review_candidates.csv`.

- Five additional scans show boundary information: Bowral re-planning scheme
  (1953), Bombala town plan (1944), Windsor town plan (1937), Tonga parish
  (1971), and Wallendoon parish (1971). Bowral shows the adjoining Mittagong
  Shire along the scheme extent; zoning is separate. Bombala and Windsor
  legends distinguish municipal lines from town, suburban and police limits.
  Tonga shows Denman/Singleton shire edges. Wallendoon shows the internal
  Jindalee/Demondrille shire line alongside land and pastures district lines.
  Coverage can be partial. Seven other plans remain deferred: Shellharbour
  sheet 32, central Goulburn, Narrabri flood map, Morisset sheet 1, Nowra,
  Moss Vale and Huskisson. A municipal or shire name in the title does not
  establish that the perimeter appears on the sheet. Review:
  `nla_town_planning_second_review_candidates.csv`.

- Thirteen more boundary scans: Chippendale (1842), Lett/Lithgow (November
  1897), Nowra (1932), Field of Mars (1923), Jamberoo (1978), Berrima
  (1946 and 1968), Wallaya (1939), Manton (`[1930]`), Gamboola (`[1937]`
  and `[1965]`), Quat Quatta (1941), and Bega (1943). Chippendale identifies
  Government Street as Sydney's municipal boundary; it covers a small
  segment. Lett distinguishes Lithgow borough from water catchments and
  mining limits. Field of Mars includes municipal/shires lines around
  Parramatta, Ryde, Hunters Hill and Baulkham Hills; edges are damaged.
  The two Gamboola scans use the same 1937 base but have different catalogue
  publication dates and details. Town, planning, goldfield, catchment,
  land district and state lines are separate from LGA lines. Coverage is
  partial. Richmond's 1919 base, `[1952]` publication and later land-use
  annotations remain deferred because no municipal line was confirmed.
  Review: `nla_regional_parish_twelfth_review_candidates.csv`.

- The additional Sydney municipal atlas browse response exposes 40 IDs.
  All map leaves are already saved. Two IDs are parent/seed records and
  `nla.obj-231108166` is a publisher advertisement, not another map.
  Inventory: `nla_municipal_atlas_remaining_browse_ids.json`; review:
  `nla_additional_atlas_completion_review_candidates.csv`.

- The Murray collection inventory has 117 records. Metadata inspection
  shows a mixed international collection, not 117 Gosford companion sheets.
  Fifteen NSW record views were inspected. Six scans were selected: central
  northern tourist district (`1939?]`, catalogue punctuation retained),
  central southern/Riverina (`[1940]`), north eastern (`[1938]`), south
  eastern (1932), Llangothlin (1941), and Mount Mitchell (1964). The four
  tourist maps show shire lines and names; coloured overlays, roads,
  tourist regions and fishing details must be kept separate. The two parish
  maps show the Severn/Guyra divide along their southern edges. Five parish
  parent views resolve to the same map content as their access leaves;
  only confirmed access leaves are saved. Blair Hill, Marowan and Yarrow
  remain deferred because no LGA edge was confirmed. The Illawarra view
  combines scheme sheets 17 and 18; no municipal edge was confirmed. Its
  extent says 22 sheets, but browse returns the mixed collection rather
  than 22 companion leaves. Metadata inventory:
  `nla_gosford_collection_metadata_review_candidates.csv`; visual review:
  `nla_murray_nsw_visual_review_candidates.csv`.

- Remaining town-plan review: 18 views were checked, including all seven
  Deniliquin series leaves. The Deniliquin outer line matches the suburban
  boundary symbol, not the municipal symbol. Narellan shows village extent;
  the inspected Shoalhaven/Nowra, Greenwell, Sussex Inlet and Oaks Estate
  plans did not confirm LGA edges. These remain deferred. Evidence:
  `nla_remaining_town_plan_review_candidates.csv`.
- Boundary-phrase searches added Sydney municipal ward maps dated 1873
  (`nla.obj-229932645`) and `[1878]` (`nla.obj-229967198`). These show
  divisions within the city, not modern suburb boundaries. The register kind
  is `municipal_ward_boundary_map`. The 1873 scan has holes and damaged edges.
  Both sheets of the fifth-edition Goulburn city plan (1932),
  `nla.obj-1532743240` and `nla.obj-1532743759`, show parts of the city
  perimeter. Distinguish city, suburban, parish and reserve lines using the
  legend on sheet 2. Cooma's inspected 1926 plan remains deferred because
  no LGA line was confirmed. Evidence:
  `nla_boundary_phrase_visual_review_candidates.csv`.

- Suburban-boundary phrase review: both sheets of the fifth-edition
  Environs of Young plan are selected (`nla.obj-2901575786` and
  `nla.obj-2901575954`). Catalogue publication: 1958. They show the
  Young municipality/Burrangong Shire divide. Later annotations are not
  evidence of a revised boundary date. The Gosford town plan is within
  Gosford Shire; no LGA perimeter was confirmed. Heathcote, three Kiandra
  plans, Blackville, Buraja and Nimmitabel remain deferred: town/village
  and suburban-land limits require a distinct interpretation. Evidence:
  `nla_suburban_phrase_review_candidates.csv`.

## Dwellings tab-by-tab audit — 10 October 2026

This audit supersedes the earlier Dwellings workbook counts and open correction
examples. Raw PDFs and paid extraction candidates are unchanged. Repairs are
in the source mappers and check builders, not manual edits to Excel.

- Workbook: 68 tabs, 6,774 rows. The pre-audit numeric workbook had 6,809 rows.
  Removed duplicate/fractured proposals and recovered printed rows; fewer output
  rows is not a count of removed source observations.
- `output/export_abs_1911_dwellings_workbook/tab_audit.csv` is the dated 68-tab
  audit snapshot: source pages, coverage, before/after rows and check counts.
- `data/intermediate/abs_1911_dwellings_tab_audit.json` holds detailed source
  readings, coordinates, corrections, independent reviews and revised claims.
  Temporary render references are not durable files; recreate from PDF coordinates.
- Full grid/section review does not mean every digit received independent
  high-resolution visual transcription. Exact coverage differs by family and
  is recorded per tab. The workbook remains source-review data, not accepted
  analytical data.

### Corrections by table family

- Table 2: retain all 25 printed rows, not 18 collapsed rows. Separate
  Metropolitan, Remainder and Whole sections, including unlabeled totals.
  Metropolitan area is in acres; the other sections use square miles.
- Tables 1, 3–9 and 49–58: correct displaced geography grids, lost figures,
  truncated categories and duplicate fragments. Keep camps, shipping and total
  population separate from dwelling-category subtotals. Table 49's split OCR
  numerals shifted Other lower bounds 12–18 and 20–22 to the next bracket.
  Table 56's Other 27s. row was lost when a repeated total anchored it to 28s.
  Restore the source row; retain its contradictory printed total.
- Tables 10–29: build the printed row/column inventory before mapping proposals.
  All 915 final row identities and values match that inventory. Table 11 has
  132 rows: NSW/Victoria/Queensland/SA/WA 19 each, Tasmania 17, NT 13 and
  Federal Territory 7. There is no Commonwealth block. This supersedes the
  provisional 135-row claim. Table 23 All Total/inmates 5 is 39,199, not the
  earlier audit's mistaken 39,109. Use only 146 reviewed finite category
  omissions in class checks; do not treat all missing categories as zero.
- Tables 30–48: repair room-by-inmate and rental-panel baselines, slanted
  figures, dropped dots, sparse rows and bracket identities. Complete the
  source dispositions for all 496 remaining fields and 105 flagged rows.
  The earlier examples are now corrected: Table 30 All room 7/inmates 8 =
  6,536; All Wagons/inmates 2 = 144; Table 38 All room 1/inmates 1 = 110.
  Table 41 Other 27s./rooms 12 is 17, not .17; Table 43 Private 4s./rooms 5
  is 645, not 64.5. Table 48's £3 15s. bracket ends at £4; the earlier
  supposed £4 5s. endpoint inconsistency was an audit misreading.
- Tables 59–63: correct 93 source fields, including false Federal Territory
  absences, shifted Commonwealth values, reversed currency units and damaged
  rule fragments. All 93 corrections received independent source checks and
  match the final export. Preserve the printed Aboriginal exclusion.
- Tables 64–66: review all county grids and source sections; independently
  verify 12 correction records, including currency absence pairs and labels.
- Tables 67–68: recover source rows, correct quantities/units and separate shared
  group metadata from individual geography measures. Keep Tinaroo's Table 68
  occupied-dwelling density `3,279` as text: punctuation and magnitude conflict.
  It is neither validated 3,279 nor an inferred 3.279.

### Retained source problems

Do not alter these readings to make arithmetic pass:

- Table 9: printed label/figure displacement and two Aboriginal numeric lines
  leave material classification unresolved.
- Table 12 All Wood total: printed 199,653 causes a 300,000 discrepancy.
- Table 22 All Unspecified/inmates 10: printed 3 conflicts with Private 25 +
  Other 8. Table 27 Private Stone/inmates 15 has an unreadable glyph.
- Table 49 Other 20s.: printed total 738 versus component sum 728.
  Table 56 Other 27s.: printed total 3 versus component sum 23.
- Four independently confirmed fixed-room discrepancies remain between
  Tables 59/60 and 61/62. The audit records exact fields and source readings.
- Table 42's obscured leading room-count glyphs, Table 40's damaged count,
  Table 48's `[4,035` occupancy total, Table 56's `1,80` Melbourne reading,
  Table 67 Lowan shillings and Table 68 Dublin density remain explicit
  unreadable/conflicted readings. Table 36's genuinely empty source cell
  stays blank. Visible suffixes are not recovered complete quantities.

Other retained diagnostics are listed by exact tab, row and check in the audit
JSON and `mathematical_checks.csv`. A failed check is not necessarily an extraction
error; an incomplete check is not a licence to fill its operands.

### Verification and reusable protocol

| Check status | Pre-audit | Rebuilt |
|---|---:|---:|
| PASS | 47,443 | 55,821 |
| FAIL / nonzero delta | 1,550 | 128 |
| INCOMPLETE | 7,368 | 327 |
| N/A | 2,264 | 2,811 |

Check counts are diagnostic instances, not unique erroneous cells. Check scope
also changed: unsupported identities became N/A and supported fixed-room
comparisons were added.

- All 83 source-backed regressions pass. Real desktop Excel recalculated all
  59,087 checks with zero cache mismatches and no Excel errors. Seven actual
  Excel-exported panels were visually inspected. Live edits proved both the
  noninteger-count flag and fixed-room FAIL/INCOMPLETE/PASS transitions.
- Two final locked rebuilds produced byte-identical XLSX, assembled JSON,
  mathematical CSV and manifest. All three immutable input hashes match the
  pre-audit manifest. No paid extraction or residual balancing was used.
- Start another document with its own printed row, section, unit and column
  inventory. Bind quantities to physical rows before joining panels.
- Read first, interior and last rows, plus sparse and multiline cases. Passing
  totals and legal currency do not establish correct digits or state alignment.
- Separate printed absence, source-empty cells, missing extraction, source
  damage and publication conflict. Use only source-backed finite omissions.
- A repeated total cannot establish a row identity. A matching label also needs
  independent quantity-grid corroboration before rejecting a changed anchor.
- Apply arithmetic only to matched cohorts, units and printed precision.
  Open-ended room bins are not exact divisors; average rents are not additive.
- Use full real section/state contexts in mapping tests and select rows by
  named dimensions. Partial fixtures selected the wrong class/state after
  complete inventories were added. Retire wording-only/incidental assertions.
- Test the live spreadsheet, not caches alone. Excel implicit intersection
  narrowed `MOD(range,1)` to the first field and missed later fractional counts.
  The noninteger check now uses an array formula over every count field.
- Existing manual corrections can be wrong. Record rejected readings and
  independent review revisions. Prove a source-checked pilot before bulk work;
  do not copy Dwellings-specific geometry or correction constants to new PDFs.

The dated audit snapshots do not regenerate on an ordinary workbook rebuild.
New inputs or mapping changes need a new source review and reconciled snapshot.

- Hunt & Steven's Sydney map (1868) has two access leaves,
  `nla.obj-231531786` (north) and `nla.obj-231531896` (south). Both
  show coloured ward lines; the north sheet has the city-ward colour legend.
  The two sheets must be used together. These are municipal wards, not
  modern suburb areas. Fold marks, stains and fading affect readability.
  Evidence: `nla_hunt_steven_sydney_review_candidates.csv`.

- Municipality catalogue pages 4–5 returned 200 records. A twelve-scan
  parish review selected eleven: Wongawilli (1921), North Casino (`[1963]`),
  Burrill (1962), South Condobolin (1960 and two 1930 source copies),
  Brunswick (`[1959]`), Bulgandramine (1959), Ham Common (1958),
  Napier (1935), and Kahibah (`[1931]`). They show partial municipal or
  shire lines. Warroo (1936) remains deferred: no LGA line was confirmed.
  Keep water catchment, bird sanctuary, goldfield, pasture-protection,
  town-land and land-district lines separate. South Condobolin
  `nla.obj-570997845` is upside down; the raw download remains unchanged.
  The two 1930 copies are overlapping source scans, not separate boundary
  regimes. Evidence: `nla_municipality_pages45_review_candidates.csv`.
- County of King maps add two different shire overprints: `[1954]`
  (`nla.obj-258230442`, 1935 base, shires revised 14 October 1954) and
  `[1967]` (`nla.obj-258241183`, 1936 base, revised 6 April 1967).
  Red lines include outer shire/municipal boundaries and internal ridings;
  use the legend to distinguish them. The 1893 West Maitland map
  (`nla.obj-2053897226`) has a municipal-boundary legend and partial
  municipal coverage. Crown Grant and subdivision boundaries are separate.

- Municipality pages 4–5, second/third visual batches: 20 scans reviewed,
  18 selected. They add Ham Common (1926), Wedderburn (1924 and 1960),
  Warroo (1921), Coeypolly (1963), Braidwood (`[1960]`), Claremont
  (1960), Gosforth (`[1960]`), Tomerong (`[1960]`), Mullumbimby
  (`[1959]`), South Borambil (1959), Weetaliba (1946), South Casino
  (`[1941]`), Cabramatta (1940), North Lismore (`[1937]`), East
  Waradgery (1936), Copper Hill (`[1933]`) and Holsworthy (1931).
  LGA coverage is partial; each publication date remains distinct from
  printed base dates and later annotations. Warroo `nla.obj-232721586`
  shows a Yass municipal edge absent from the confirmed coverage of the
  other inspected Warroo copy. Its later red annotations include a 1973
  label; their authority and complete date are unverified. Ham Common
  has coloured annotations and heavy stains. Weetaliba has tears;
  Cabramatta has a missing upper corner. Raw scans remain unchanged.
- Stockton (`[1932]`) and Scone (1931) remain deferred because municipal
  perimeters were not confirmed separately from population, village and
  suburban limits. Do not trace these limits as LGA edges. Evidence:
  `nla_municipality_pages45_second_review_candidates.csv` and
  `nla_municipality_pages45_third_review_candidates.csv`.

- Municipality pages 4–5, fourth visual batch: 16 scans reviewed; 11 parish
  sheets selected. These are Tomerong (1929), Hume–Yass (1927), Heddon
  (`[1957]`), Jamieson (1926), Narellan (1939, both sheets), Errol (1931),
  Prospect (1930, both sheets), Kalateenee (`[1963]`) and Glen Innes (1948).
  They show partial municipal or shire lines. Narellan sheets cover Camden,
  Campbelltown, Nepean and Wollondilly; Prospect sheets cover Blacktown,
  Baulkham Hills, Holroyd and Fairfield. Town, urban-area and parish limits
  remain separate from LGA lines. Hume–Yass has coloured ward annotations
  with unverified date and authority; Heddon has a damaged right edge.
  Gunnedah (1972) and Port Macquarie (1968), including their reference
  sheets, remain deferred pending independent confirmation of LGA lines.
  Melbourne remains outside the current NSW download scope. Evidence:
  `nla_municipality_pages45_fourth_review_candidates.csv`.

- Municipality pages 4–5, fifth visual batch: 20 sheets inspected and selected.
  Twelve parish sheets show LGA lines: Glen Innes (1940), Rooty Hill (1938),
  Stonehenge (1962), Wollumboola (`[1960]`, 1942 base), Wantiool (1958),
  Macquarie (1953), Wongawilli (1931), Bong Bong (1932), Queanbeyan (1931),
  Minto (1930, both sheets) and Calderwood (1947). Glen Innes town (1971)
  has two map sheets with municipal lines along Beardy Waters; its northern
  sheet also contains the legend and reference tables. Environs of Forbes
  (1977) has four map sheets with municipal edges against Jemalong shire
  and along the Lachlan River, plus two reference-table sheets. The latter
  are `map_reference_sheet`, excluded from the boundary-scan count.
  Catchment, town, reserve and LGA lines use distinct symbols. The 1940
  Glen Innes parish copy has coloured annotations of unverified date and
  authority. Rooty Hill is faded and taped; Macquarie is faded. Queanbeyan
  has a missing upper-left corner and separate Commonwealth acquired-land
  lines. Minto has a damaged lower-right corner. Raw scans remain unchanged.
  Evidence: `nla_municipality_pages45_fifth_review_candidates.csv` and
  `nla_municipality_pages45_fifth_browse_ids.json`.

- Municipality pages 4–5, sixth visual batch: 26 records or sheets reviewed;
  24 selected. Twenty parish sheets show partial LGA lines, including
  Calderwood (1936), Yarrunga (1968), Beardy Plains (1962), Queanbeyan
  (1958), Hartley (1939), Wonona (1939), Kanimbla (1941), Manly Cove
  (1953, north half), Wallaya (1960 and 1978), Warragamba (1968), Maitland
  (`[1956]`, three sheets), Liberty Plains (1950), Melville (1938), St Luke
  (1937, two sheets) and Field of Mars (1959, two sheets). Bathurst (1939),
  Wyalong (1931) and Wingham (1946) show municipal boundaries. Yarrunga
  also has a reference sheet, excluded from the boundary-scan count.
  The Yarrunga catalogue names Wollongong/Picton and Illawarra councils;
  its printed reference sheet names Moss Vale and Wingecarribee. The
  Warragamba catalogue carries Kiama/Moss Vale/Nowra geographical names;
  the printed map shows Penrith, Blue Mountains and Wollondilly LGA lines.
  Retain catalogue titles for provenance, but inspect the printed geography
  before using either sheet. Manly Cove is only the north half; its southern
  companion was not located. Wyalong is catalogued on two sheets, but only
  one image was exposed; completeness is unresolved. Its municipal line
  differs from its goldfield boundary. Maitland's diagram sheet includes
  municipal lines at Lorn; town and cemetery limits remain separate.
  Calderwood has annotations of unverified date and authority. Hartley is
  faded; Kanimbla has heavy edge grime; Wingham has a missing lower-left
  corner; Liberty Plains has damaged upper corners. The Morts Township
  auction plan (1893) remains deferred because no municipal line was
  confirmed. East Collingwood remains outside the NSW scope. Evidence:
  `nla_municipality_pages45_sixth_review_candidates.csv`.

- Municipality-title search pages 6–7: page 6 returned 71 records; page 7
  returned none. Twenty new digitised identifiers were found; a companion
  St John sheet made 21 records/sheets for review. Six sheets were selected:
  Maitland (1933), Kangaloon (1929), St John (1957, both sheets), Manilla
  (`[1958]`) and Hunters Hill (1886). Maitland's northern sheet shows a
  Kearsley/Bolwarra shire edge; it says "map on 2 sheets", but its catalogue
  exposes only one image. Its coverage is incomplete. Kangaloon shows LGA
  and water-catchment lines separately; the scan is faded and stained.
  St John's northern and southern sheets show several western Sydney LGA
  edges. Reference text on its southern sheet does not make that sheet a
  reference-only image. Manilla's legend says its municipal boundary was
  reproclaimed on 17 December 1926; catalogue publication is `[1958]`.
  Its town, suburban and catchment lines differ from municipal lines.
  Hunters Hill has a municipal outline legend and a faded, torn scan.
  Eleven estate/subdivision plans remain deferred because council edges
  were not confirmed; estate limits must not be inferred as suburb limits.
  Four records are outside NSW. Evidence:
  `nla_municipality_pages67_review_candidates.csv`,
  `nla_municipality_pages67_browse_ids.json` and
  `nla_municipality_pages67_maitland_links.json`.

- Separate municipal-title catalogue search: 138 records returned on pages
  1–2. Of 37 new digitised identifiers, 33 are outside NSW. Four NSW auction
  plans were inspected: Field of Mars `278688358`, `230182707`, `230181447`
  and Concord `230149960`. No explicit municipal perimeter was confirmed;
  coloured sale lots and estate limits are not accepted as suburb limits.
  All four remain deferred. Evidence: `nla_municipal_title_candidates.csv`
  and `nla_municipal_title_review_candidates.csv`.

- General boundary searches: first-page results for `boundary "New South
  Wales"`, `boundaries "New South Wales"` and `"municipal boundaries"`
  returned 300 catalogue records. Thirty-one new identifiers received a
  metadata review. Three promising NSW scans were visually inspected.
  The southeast NSW population-projection map (`485052088`, publication
  `[1971]`) shows shire outlines and small municipality markers. It is a
  simplified thematic map; boundary epoch is unresolved. Projected 1971
  population and 1961–1971 change are not observed census results. Retain
  this as `map_with_shire_boundaries`, with limited value for precise tracing.
  Girrawillie (`2250595147`, `[1967]`, printed 30 May 1967) shows part of a
  shire edge coincident with its western county/land-district boundary.
  Use the legend to separate the shire symbol from county, parish, forest
  and pastures-protection symbols. The Port of Sydney map (`2957385323`,
  1947) shows Maritime Services Board vested-land limits; no council line
  was confirmed. It remains deferred. Other metadata candidates describe
  county, colonial, police, forestry or other administrative boundaries;
  these were not accepted as LGA maps. Evidence:
  `nla_nsw_boundary_general_review_candidates.csv`.
- Municipal-boundaries phrase search pages 2–3 returned 200 records.
  Duplicate saved atlas leaves were excluded before selection. Forty-eight
  further identifiers remained: 47 outside NSW and one Canterbury map
  (`229971700`, publication `[1889?]`). Its municipal-perimeter legend and
  internal ward division are clear; this distinct scan is retained. Preserve
  the uncertain publication date. Evidence:
  `nla_municipal_boundaries_later_review_candidates.csv`.

- Municipal-boundaries phrase search pages 4–5 returned 22 and zero records,
  respectively. Eight new digitised identifiers are outside NSW; none were
  downloaded. Evidence: `nla_municipal_boundaries_pages45_review_candidates.csv`.
- State Library's data.gov.au dataset `fcac036b-5c52-42c8-91c3-4904e50dd9af`
  is described as "Sydney maps 1917", but its CSV contains 714 older Sydney
  detail-survey records. Captions include 1880s–1890s sheets, and six key
  maps. Do not assign 1917 to these sheets from the dataset description or
  repeated `dateofwork` field. The CSV and dataset metadata are retained as
  discovery evidence. The tested legacy `a700001h.jpg` image URL returns
  404. Current State Library series and City of Sydney atlas pages returned
  403 in the tested clients. No map files were saved from those links.
- City of Sydney Historical Atlas boundary layer: one native GeoJSON export
  retained unchanged as `historical_boundary_vector_set`. Source layer has
  10 polygons: nine City of Sydney periods, plus South Sydney City Council
  for 1989–2003. Source `StartDate`/`EndDate` values span 1842–present, with
  periods 1842–1870, 1870–1908, 1908–1948, 1949–1968, 1968–1981,
  1982–1988, 1989–2003, 2003–2004 and 2004–present. The export uses
  longitude/latitude (EPSG:4326). Original `Shape__Area`/`Shape__Length`
  attributes come from the source projected layer (EPSG:28356); do not treat
  them as degree measures or areas recomputed from the GeoJSON. Source
  `Details` text is truncated on some records. Year labels overlap in change
  years; narrative text gives some exact dates. Do not infer census-date
  applicability from inclusive year ranges alone. The source's "present"
  label is preserved as retrieved, not independently validated. Source:
  `https://services1.arcgis.com/cNVyNtjGVZybOQWZ/ArcGIS/rest/services/Historical_Atlas_of_Sydney/FeatureServer/0`.
  Layer metadata, source attributes and independent source-count response
  are retained in the downloader output folder.
  The export matches the independent source count of 10 and all date/council
  attributes. All geometries are nonempty polygons within the Sydney extent.
  Nine are valid. South Sydney City Council (1989–2003, OBJECTID 10) has a
  ring self-intersection at approximately 151.214270 E, 33.903822 S. This
  supplied geometry remains unchanged; repair a separate working copy before
  spatial operations. The preview and `verification.json` retain this issue.
  The repo already holds a nine-polygon 1901-onwards council export in
  `data/raw/city_of_sydney_historical_boundaries/`. This full export adds
  the 1842–1870 polygon; its other nine records overlap that saved subset.
  The earlier folder also holds 82 ward features. Do not count overlapping
  exports as new boundary regimes. Earlier raw exports remain untouched.

### State Library municipal series: first original-image batch

- The public browser catalogue for `74VKPlWXQkwd` exposes 65 digitised images.
  The catalogue describes 73 maps; its checklist lists 66 sheets. These counts
  have different units. Only 12 images are saved in this batch; 53 need review.
- Public original JPEG links work through the browser. Plain HTTP requests
  returned 403. The older public delivery endpoint supplies smaller images
  (about 1,050 px); those were used for discovery, not saved as raw originals.
- All 12 saved originals match the catalogue's pixel dimensions. The batch
  adds 138,189,344 bytes: 11 municipal sheets and one undated key/index map.
  The full collection has 466 readable files and 441 boundary JPEGs.
- Printed map dates: Annandale 3 January 1939; Ashfield 25 August 1940
  (two sheets); Balmain 1 November 1937 (two sheets); Botany 12 December 1932
  (two sheets); Canterbury 25 November 1957 (four sheets). Companion sheets
  without their own printed date use an explicitly labelled edition date.
- Municipal boundary proclamation dates differ: Annandale 12 February 1937,
  Balmain 3 December 1913, Botany 11 October 1929, Canterbury 28 May 1948.
  Canterbury's ward proclamation is 4 November 1955. Ward and municipal lines
  have separate legend entries. These dates do not establish census coverage.
- `FL3739083` is Balmain sheet 1, not Ashfield. The printed marginal caption
  and adjoining geography confirm this. Its provisional inventory title and
  filename were corrected; original bytes and hash remain unchanged.
- The key map's manuscript lines have unverified date and authority.
  Candidate, review and catalogue metadata records are saved with the downloader.

### State Library municipal series: second original-image batch

- Added 18 municipal scans (190,706,215 bytes). All match the catalogue's
  original dimensions and pass hash and readability checks. The collection
  now has 484 files, including 459 boundary JPEGs; the existing raw GeoJSON
  geometry caveat is unchanged. No source bytes were edited.
- Printed map dates: Darlington 3 January 1939; Glebe 1 November 1937;
  Hurstville 12 March 1954 (three sheets); Kogarah 4 October 1956 (three);
  Lane Cove 22 February 1917; Leichhardt 18 January 1939 (two); Marrickville
  30 August 1940 (two); Mascot 22 December 1932 (two); Mosman 22 February
  1917; Newtown 18 January 1939; North Sydney 22 February 1917. Companion
  dates are labelled as edition dates where recorded from another sheet.
- Hurstville and Kogarah legends describe municipal boundaries proclaimed
  19 December 1930. These differ from map dates and internal ward dates.
  The blue line on these sheets denotes the map-sheet edge; consult the
  municipal boundary symbol before tracing. Map edges can overlap boundaries.
- Mascot sheet 2 has a torn/missing upper-left corner. Marrickville sheet 2
  has a torn lower margin. Raw scans preserve this damage. Neither scan
  should be assumed to preserve every part of its printed frame.
- The municipal series has 30 saved images of 65 exposed digitised files.
  The remaining 35 include Randwick editions/reference tables, Rockdale
  sheets and Willoughby. Review them by printed title and legend. Evidence:
  `state_library_municipal_series_second_review_candidates.csv`.

### State Library municipal series: remaining originals

- All 65 exposed images are now saved and match catalogue dimensions. This
  batch adds 35 originals (360,758,539 bytes): 26 municipal map sheets and
  nine reference tables. Total collection: 519 files, 1,454,237,903 bytes,
  including 485 boundary JPEGs and 30 cover/reference/finding-aid images.
  All saved files pass hash and readability checks.
- Randwick has three sets. An undated nine-sheet set exposes only printed
  sheets 3, 4, 6, 7 and 9; sheet 7 is mostly portion tables and classified
  as reference context. Its other sheets and precise map date remain
  unresolved. Do not date this set from adjoining catalogue images.
- The four-sheet Randwick first edition has printed map date 2 May 1933
  on sheet 1. All four map sheets are saved; companion dates are explicitly
  labelled as edition dates.
- Randwick second edition has nine map sheets dated individually: sheets
  1–2, 9 September 1949; 3, 29 August 1949; 4, 21 July 1949;
  5, 30 September 1949; 6, 24 May 1949; 7, 31 May 1949;
  8, 5 November 1948; 9, 25 May 1949. Sheet 9 has torn upper-left
  and lower margins. Blue lines are map-sheet edges; use municipal/ward
  symbols and the legend for boundary tracing. Coastal sheets are partial
  perimeter context; they do not establish legal shoreline limits.
- Eight separate Randwick portion tables are printed reference sheets
  1 and 3–9. Sheet 2 was not exposed. Their association with the later
  nine-map-sheet set needs confirmation; dates remain undated.
- Rockdale has all eight map sheets. Printed dates by sheet: 1, 23 October
  1951; 2, 23 August 1951; 3, 24 October 1951; 4, 6 February 1952;
  5, 12 March 1952; 6, 24 March 1952; 7–8, 1 May 1952. This is a
  municipal series with different sheet dates, not eight maps from one day.
- Willoughby has printed map date 22 February 1917. Its legal North Sydney
  suburban-lands line is distinct from the municipal perimeter and wards.
  Do not label that line as a modern suburb boundary.
- Provisional Randwick titles were corrected from printed captions. Filenames
  and register labels changed; raw bytes and hashes are unchanged. Evidence:
  `state_library_municipal_series_final_review_candidates.csv`.


## 2026-10-10: City archive LGA maps and ANU western Sydney sheet

- Saved City archive municipal PDFs: `1709402` Sydney, third edition, printed
  12 January 1903; `1709080` Glebe, printed 1888; `1709404` Glebe, catalogue
  year 1910. Embedded scans are respectively 5,632 × 7,336, 11,808 × 10,730
  and 11,400 × 9,303 pixels. Municipal perimeter lines were visually checked.
  The 1903 legend states the city boundary proclamation of 20 March 1885;
  later park additions are separately marked. Do not treat proclamation,
  dedication and publication dates as the same event. Glebe scans are faded,
  stained or damaged at margins; missing detail is not a legal boundary.
- Saved four City archive ward PDFs (`1724436`–`1724439`). Their annotated
  periods are 1 January 1949–16 April 1959, 17 April 1959–31 July 1968,
  1 August 1968–31 December 1981 and 1 January 1982–31 December 1988.
  The first, second and fourth use a base dated 1962; the third is dated
  July 1974. Thus some represent earlier boundaries on a later base map.
  They show city, neighbouring municipality and ward lines with separate
  symbols. Preserve these distinctions.
- ANU `F0102.pdf` (item `9edf57f7-0b3c-4a2d-9ff1-49c31cf204bc`) is
  sheet 1 of the six-sheet January 1917 Sydney and environs map, not the
  complete map. It covers western municipalities and shires at
  16,238 × 20,071 pixels. Other NLA copies overlap this coverage. The
  PDF is 20,327,240 bytes; the offered 932 MB TIFF was not downloaded.
  ANU requires prior permission for reproduction; this download is for research.
- Inspected but did not add the central Sydney 1910 street map (`1709403`)
  or Glebe 1939 detail map (`1709405`): useful LGA lines were not confirmed.
  Review candidates and catalogue evidence are kept in the downloader folder.
- Collection total is 527 files, 1,544,073,668 bytes: 485 boundary JPEGs,
  nine single-map boundary PDFs, 30 cover/reference/finding-aid images,
  one cadastral companion JPEG, one six-page compilation PDF and one GeoJSON.
  All registered files passed hashes and readability checks; the known source
  GeoJSON self-intersection remains unchanged and documented separately.


## 2026-10-10: Combined inner Sydney municipal maps

- City archive `1709400` (`A-00880473`) is a Higinbotham and Robinson map
  of Glebe, Camperdown, Newtown, Macdonaldtown and Darlington. It has
  separate municipal, parish and ward symbols. The native PDF contains
  a 6,324 × 10,591 pixel scan and is 10,034,510 bytes. Use the catalogue
  date **circa 1890**. The atlas menu labels the group 1886; this conflict
  is unresolved. No exact publication year was inferred.
- City archive `1709401` (`A-00880474`) is the Sands Directory map of
  Sydney and suburbs, printed 1887. Native PDF: 48,832,197 bytes; embedded
  scan 10,268 × 6,239 pixels. Its legend distinguishes municipality and
  city ward symbols. Red transport annotations and blue water-reserve
  annotations are separate; do not trace them as municipal boundaries.
- Inspected City archive `1709398`, Woolcott and Clarke's 1854 Sydney map.
  Its legend identifies ward and parish boundaries; a distinct external
  municipal symbol was not confirmed. It remains a candidate and was not
  added to the raw collection under the LGA focus.
- New PDFs are unchanged, visually inspected and checked for matching
  bytes, SHA-256 and one-page readability. Existing registered files were
  unchanged. Updated total: 529 files, 1,602,940,375 bytes.

- General NLA NSW boundary searches, page 2: 200 catalogue rows across
  the singular and plural queries, including 93 catalogue URLs not in the
  earlier candidate registers. Titles alone did not confirm further LGA scans.
  Metadata review remains pending; evidence is `nla_general_page2_candidates.csv`
  and the two rendered catalogue HTML snapshots in the downloader folder.


## 2026-10-10: General catalogue review and Alexandria parish LGA segments

- Completed metadata review of the new general-boundary catalogue records:
  93 from page 2 and 83 from page 3, with no fetch failures. Page 2 notes
  did not identify LGA boundaries. Page 3 identified a 1966 NSW statistical
  divisions map with LGAs but no exposed scan, and electoral maps dated
  circa 2000 and circa 2006 with LGA lines. These later maps remain candidates.
  The 2006 record exposes digitised identifiers; it was not added in this pass.
  Catalogue-only records are not counted as downloaded maps.
- NLA Alexandria parish set `589525008` exposes 15 leaves. Inspected all 15
  and saved six map leaves with municipal segments: sheet 5 (`589526935`),
  6 (`589527237`), 8 (`589527519`), 9 (`589528182`), 11 (`589528822`)
  and 12 (`589528840`). They provide partial borders among Sydney, Woollahra,
  Waverley, Randwick, Botany and Marrickville; not complete LGA polygons.
  Separate parish, municipality, planning, reserve and police symbols exist.
  Coloured road or park annotations are not automatically LGA lines.
- Saved reference/legend leaves for sheet 5 (`589526594`) and sheet 9
  (`589527902`). Printed map dates: 5, 3 August 1967; 6, 25 September 1967;
  9, 9 February 1968; 11, 14 June 1967; 12, 11 October 1967. Dates for
  map-only sheets 5 and 9 come from their matching companion references.
  Sheet 8's reference is not exposed; retain catalogue set date 1967–1968
  and leave its exact sheet date unresolved. Later statutory notes and
  annotations can appear on these bases; they do not establish an exact
  historical boundary epoch. The source is faded and sheet 9's reference
  has a damaged top margin.
- Other leaves were not selected in this LGA pass: no separate municipal
  segment was confirmed in their interior or shoreline-only coverage, or
  they were unused companion tables. This does not prove they lack all
  useful cadastral detail. The NLA catalogue says it lacks sheet 2, sheet
  4's tables and sheet 8's tables, and holds two copies of sheet 4's map.
- Review evidence: `nla_general_page2_metadata_review_candidates.csv`,
  `nla_general_page3_metadata_review_candidates.csv`,
  `nla_alexandria_1967_review_candidates.csv` and browse identifiers in
  the existing downloader output folder. Selected NLA metadata snapshots
  are retained under `nla_metadata/`.
- Eight new raw JPEGs are unchanged from the source downloads. They passed
  image readability, dimensions, SHA-256 and unavailable-placeholder checks.
  Total: 537 files, 1,615,799,371 bytes; 491 boundary JPEGs and 32
  cover/reference/finding-aid images. Previous registered files are unchanged.


## 2026-10-10: Borough and planning-map LGA review

- Reviewed 76 new catalogue records from the NSW borough and local-government
  searches. The corrected metadata pass has 51 LGA or planning matches and
  25 records without LGA evidence. All corrected metadata requests succeeded.
  The earlier title-led pass selected six records for immediate scan review. Catalogue notes without LGA evidence are not proof
  that a map lacks LGA lines. The review register is
  `nla_borough_local_government_metadata_review_candidates.csv`.
- Saved Waverley, printed January 1887, by S. Pollitzer. Leaf
  `nla.obj-2004524412` is 3,076 × 5,000 pixels, 1,528,153 bytes. The legend
  separates municipality and ward boundaries. Parent `2004516336` returns
  the same image bytes; only the leaf is registered. Catalogue: `273961`.
- Saved Penrith planning map `1804667397`, printed 1959. Its legend
  distinguishes scheme, parish and local-government lines. The Nepean River
  line carries the local-government cross symbol; Blue Mountains is labelled
  on the other side. This is one exposed map from a catalogue set of 12,
  not a complete set or a full Penrith polygon. The printed sheet index does
  not mark its sheet number. No sheet number was inferred.
- Saved both Goulburn planning sheets, printed 1961: `1532744311` and
  `1532744602`. The outer line carries repeated municipal-style cross marks,
  separate from the zoning and road colours. The legend lists zones but
  does not define that line; confirm its legal extent before final tracing.
  The sheets and their insets give complementary northern/southern coverage.
- Saved Coffs Harbour urban detail (`1589977705`) and wider-area
  (`1589978024`) sheets. Their legends identify shire lines, separate from
  county lines and zoning. They show segments near the southern edge. The
  scheme was submitted by Dorrigo and Bellingen shire councils. Retain the
  uncertain catalogue publication `[1960?]`; the printed date field is blank.
- Saved Inverell detail (`1598086252`) and municipality overview
  (`1598086389`), both printed November 1959. The overview legend explicitly
  identifies municipality boundaries. The detail shows the same cross-mark
  line beside the Macintyre Shire label. The overview includes the municipality
  perimeter; the detail is partial. Open-space outlines and red roads differ.
- Inspected Lismore planning map `241545616`, printed December 1958. Its
  heavy outer dash line is not defined in the legend. It remains a candidate;
  no LGA boundary was asserted from the planning-scheme title alone.
  Wollongong's 6 December 1882 street-lamp plan (`232437479`) has no
  confirmed municipal line and was not added.
- Eight raw JPEG additions passed byte, SHA-256, dimensions and image
  readability checks. Total: 545 files, 1,630,112,217 bytes; 499 boundary
  JPEGs, 11 single-map boundary PDFs and 32 cover/reference/finding-aid
  images, plus the existing companion image, compilation PDF and GeoJSON.
  Search and inspection continue; source copies and partial sheets overlap.
- The first metadata pass for 194 new records from page 2 of the
  local-government query and page 4 of the shire query missed descriptions
  and notes because field labels retained trailing colons. Its initial
  no-evidence classifications were invalid and are being replaced. The same
  error affected 72 of 76 borough/local-government review rows. Saved map
  verification was unaffected. Also completed 70 new general-boundary
  page-4 records with correctly parsed descriptions and notes. Later electoral maps
  remain catalogue candidates; they were not added to this historical pass.
  Registers: `nla_lga_followup_metadata_review_candidates.csv` and
  `nla_general_page4_metadata_review_candidates.csv`.
- Rechecked file size and SHA-256 for all 545 registered downloads: no
  failures or identical-byte duplicates. The 499 boundary-image count
  includes two map indexes that show boundaries. Companion/finding-aid
  counts exclude these two boundary-bearing indexes.


## 2026-10-10: County-map LGA overprints and corrected search evidence

- Completed repair of 266 metadata rows. Strip trailing colons from field
  names; require Bib ID and Description before classifying a catalogue page.
  Read Notes, Summary and Full contents, since LGA information can appear in
  any of these fields. Corrected borough/local-government results: 51 LGA or
  planning matches and 25 without evidence. Corrected follow-up results:
  96 matches and 98 without evidence. No request failures. The 194 follow-up
  records expose no digitised identifiers; matches remain catalogue-only.
- Additional planning/LGA search: 161 candidate rows, 116 new catalogue
  records; 50 LGA/planning matches and 66 without evidence. No request
  failures. Evidence is `nla_planning_lga_metadata_review_candidates.csv`.
- Saved county Clive maps `234419126` (printed 23 July 1907) and
  `234419297` (third edition, printed 14 December 1929). Both show
  Tenterfield's municipal rectangle, distinct from the irregular population
  area. Municipal and population-area lines have different legend symbols.
  These scans are labelled municipal boundary maps, not shire overprints.
- Saved Clive `234419017`: 1929 base, red shire revisions to 11 April
  1956. Tenterfield, Severn and Copmanhurst shire lines and riding letters
  are separate from the cadastral county perimeter. This is another copy
  with a different overprint, not a duplicate of the plain 1929 scan.
- Saved Monteagle `534816128`: printed base 22 November 1937; red
  shire revisions to 22 April 1952. Shows Weddin, Burrangong and Boorowa
  lines, with nearby Waugoola and Demondrille labels. Grenfell and Young
  municipalities are separate. Do not substitute the handwritten 1932
  library annotation for the printed map date.
- Saved Ewenmar `954329567`: 1932 base; shire revisions to 8 February
  1957. Includes Coonamble, Warren, Gilgandra, Timbrebongie and Talbragar
  segments. Urban-area outlines and riding letters are separate.
- Saved Cooper `234419592`: base 14 April 1932; shire revisions to
  1 June 1960. Includes Carrathool, Bland, Wade, Leeton, Narrandera and
  Coolamon segments, with adjoining shire labels. The county sheet limits
  do not form complete polygons for every labelled LGA.
- Inspected Orange planning map `1604338156`, Cumberland administrative
  map `2545018956`, and contact images for 13 exposed Greater Wollongong
  planning leaves under `1735649252`. No separate LGA line was confirmed
  in that review; retain candidates for closer inspection. Scheme, roads,
  parish and county limits must not be inferred as LGA lines. The Illawarra
  joined sheets 17/18 (`740922220`) are also a candidate: the surrounding
  browse list returns siblings in the larger Murray collection, not 22
  confirmed leaves of this particular map. Do not count that list as a set.
- Urabrible parish map `579443516`, dated 22 September 1966, remains
  a candidate; its title locates it in Coonabarabran Shire but does not prove
  that the actual perimeter appears on this interior parish sheet.
- Six new raw JPEGs pass image, dimension, byte and SHA-256 checks. No
  identical-byte duplicates exist in the manifest. Updated total: 551 files,
  1,643,235,708 bytes and 505 boundary JPEGs. Previous 545 files were
  hash-verified in the preceding block; no existing raw file was changed.

- A closer crop of Clive `234419297` confirms 14 December 1929. Corrected
  the earlier misreading of 10 December in the source register and notes.


## 2026-10-10: Sydney 1:10 000 base maps with LGA segments

- NLA base-map series `332691576` exposes 71 map leaves. Reviewed metadata
  for all 71 and fetched public preview JPEGs for inspection. All 71
  are unrestricted and passed minimum-size and JPEG checks. The parent
  image is a library holdings diagram, not one of the actual map sheets.
  The full series has more geography than the exposed leaves; this is
  not a claim that all published sheets are digitised.
- Saved 14 visually reviewed leaves with visible green LGA segments.
  Printed production 1972: Regents Park. Printed production 1973:
  Menangle Park, Dural, Epping, Parramatta, Peakhurst, Mount Colah,
  Pymble, Gladesville, Leichhardt and Kogarah. Printed production 1974:
  Arcadia, Sutherland and Cronulla. The shared catalogue start year
  1972 is not each sheet's publication date. No exact boundary epoch
  was inferred from production dates. The NLA sheetName misspells
  Sutherland as Southerland; the printed sheet title is Sutherland.
- Kind: `base_map_with_lga_boundaries`. These are 1:10 000 cartographic
  base maps showing roads, reserves and water, with municipal/shire lines.
  Green park fill differs from the thin green LGA line. Partial boundaries
  include western Sydney and river/bay segments; no complete polygon
  coverage was asserted for every named LGA. Scans are pale; use the
  unchanged raw JPEGs for later work and check fine lines at full size.
- Initial review did not confirm a distinct LGA perimeter on Berowra
  or Bundeena. They remain inspection candidates; National Park and
  coastline context alone does not establish a municipal or shire line.
  The other 55 exposed sheets are fetched but not yet visually reviewed.
- Metadata review also covered 52 exposed orthophotomap-series records
  under `552137657`. On-site records are excluded from raw downloads.
  A representative request returned a small placeholder; it was not
  registered as a map. The 1:25 000 parent `233670814` image is a 2013
  topographic catalogue/index, not a historical map sheet.
- Evidence: `nla_topographic_metadata_review_candidates.csv`,
  `nla_sydney_base_map_review_candidates.csv` and
  `nla_sydney_base_map_visual_review_candidates.csv` in the downloader
  output folder. Selected leaf metadata is retained under `nla_metadata/`.
- Fourteen new raw JPEGs match source bytes and SHA-256 and pass image
  readability and dimension checks. No identical-byte duplicates in the
  manifest. Updated total: 565 files, 1,665,842,169 bytes; 519 boundary
  JPEGs. Existing raw downloads were not changed.


## 2026-10-10: Further Sydney base-map LGA segments

- Reviewed the next 18 exposed base-map leaves. Saved 14 with green
  LGA lines. Printed production 1972: Maroubra. Printed production
  1973: Coal & Candle Creek, Terrey Hills, Frenchs Forest, Mosman
  (the sheet also includes North Head), Kurnell, Riverstone, Rooty Hill,
  Horsley Park, Cecil Park, Leppington and Minto. Printed production
  1974: Maraylya and Rouse Hill. Dates were read from footer crops.
- These add partial shire/municipal segments in northern and western
  Sydney, plus harbour and Botany Bay context. National Park fill,
  road lines, cadastral lines and the square grid differ from LGA lines.
  Water features do not by themselves establish an LGA perimeter.
- Palm Beach, Mona Vale, Long Reef and Campbelltown remain candidates.
  No separate LGA line was confirmed in the initial review. This is not
  proof that no useful boundary detail exists at the native source scale.
- The visual review register now covers 34 of 71 exposed base leaves:
  28 saved and six retained as candidates. All 71 preview JPEGs are
  fetched and readable; 37 still await visual selection and date review.
  Use `nla_sydney_base_map_visual_review_candidates.csv` to continue
  with the first unreviewed identifier in the browse list. No preview
  fetch job is running; the source fetch completed without failures.
- Fourteen additional raw JPEGs match source bytes and SHA-256 and
  pass full image decoding and dimension checks. No identical-byte
  duplicates in the manifest. Updated total: 579 files, 1,682,692,369
  bytes; 533 boundary JPEGs. Existing raw sources were not changed.


## 2026-10-10: Sydney base-map review completed

- Reviewed the final 37 of 71 exposed leaves. Added 33 raw JPEGs with
  visible external LGA segments. Full series review: 61 saved scans,
  eight leaves without a confirmed external LGA line, and two
  byte-identical aliases retained once. Both Engadine leaves show reserve
  boundaries; no separate external LGA line was confirmed.
- Added Blacktown, Merrylands, Fairfield, East Hills, Harris Forest,
  Woronora, Sydney, Cawdor, Camden, Hughes Creek, Wallacia, Mulgoa,
  Penrith, Castlereagh, Narellan, Bringelly, Badgerys Creek, Erskine Park,
  St Marys and Londonderry, plus further copies of some sheets. Printed
  production years are 1973 or 1974 where shown. Sydney U-1845 has no
  printed production year. Its shared catalogue startDate of 1972 is
  not a verified sheet date. Catalogue misspellings Campden and
  Castelreagh are corrected to printed Camden and Castlereagh in titles.
- Paired western sheets often have the same production year and map
  coverage. Distinct scans are retained, but they are not additional
  boundary regimes. Penrith 727366603 is byte-identical to 727176811;
  Badgerys Creek 727366702 is byte-identical to 727176973. Keep one raw
  file for each pair; both identifiers remain in the visual review CSV.
- All new JPEGs pass full decoding and dimension checks and match the
  fetched source bytes. All 612 registered files were rechecked for
  size and SHA-256 with no failures or identical-byte duplicates. Total:
  612 files, 1,720,654,979 bytes; 566 boundary JPEGs. Previous raw
  downloads were not changed. The selected download batch is finished;
  wider historical LGA source discovery remains in progress.


## 2026-10-10: Main Roads annual-report boundary maps

- Official Data.NSW API lists 55 Department of Main Roads annual reports
  spanning 1932–33 to 1987–88, with some years absent. Retained the full
  catalogue metadata and `dmr_annual_report_review_candidates.csv` in
  the existing downloader output folder. Three reports were downloaded
  and map-reviewed; 52 remain unfetched. No background download job runs.
- Old Data.NSW PDF resource URLs for 1956–57 and 1969–70 return 404.
  The current official resource links point to public Archive-It copies
  of OpenGov downloads. Concurrent archived requests received 429.
  Spaced direct retries to the resolved archive links succeeded.
- Saved unchanged PDFs in `data/raw/historical_boundary_maps/nsw_main_roads/`.
  Kind: `report_with_lga_boundary_maps`. Reports contain other material;
  page locations below refer to one-based PDF pages, not printed pagination.
- 1956–57 report: 134 PDF pages. Map on pages 133–134 is printed
  June 1957 and split into western/central and eastern pieces, with a
  Newcastle inset. Embedded scans: 1727 × 1919 and 702 × 1931 px.
  Fine municipal/shire lines are distinct from coloured roads; the
  report narrative confirms map coverage. Report imprint is 1958.
- 1969–70 report: 153 pages; map on PDF page 2 explicitly shows
  shire and municipal boundaries. Embedded image: 2068 × 1731 px.
  No exact boundary date is printed. Do not assign 30 June 1970 from
  the report period alone. Newcastle and Wollongong insets are visible.
- 1970–71 report: 140 pages; map on PDF page 2 explicitly dates
  shire and municipal boundaries to 30 June 1971. Embedded image:
  2025 × 1701 px. Green roads-division boundaries are separate from
  fine grey LGA lines. Newcastle and Wollongong insets are visible.
- All three original PDFs match fetched source bytes and registered
  hashes. All pages enumerate and reviewed map pages render. The
  collection now has 615 files, 1,763,300,560 bytes; the 566 boundary
  JPEG count is unchanged. No previous raw files were changed.


## 2026-10-10: Earlier Main Roads report map review

- Fetched and reviewed eight more reports with spaced archive requests.
  All eight downloads succeeded; no running fetch job remains. Series
  register now has six saved map reports, five reports with no confirmed
  LGA map, and 44 unfetched records. Outcomes are source-specific; do not
  assume neighbouring years contain the same maps.
- 1932–33 (61 pages), 1933–34 (76), 1939–40 (17), 1948–49 (91)
  and 1953–54 (112): all pages inspected via contact sheets. No LGA
  boundary map confirmed. The 1932–33 road-location sketch on PDF
  page 45 shows roads and terrain, not external council lines. These
  reports remain exploratory candidates, outside the raw map collection.
- Added 1951–52 report (99 pages): Newcastle and environs planned-road
  map on PDF page 12, printed page 13. City boundary and Shire boundary
  labels explicitly identify external lines between Newcastle, Lower
  Hunter and Lake Macquarie. Proposed roads are distinct from LGA lines.
  Exact map/boundary date is not printed; retain report-period label.
  Full-page embedded monochrome image is 1883 × 3090 px.
- Added 1958–59 report (143 pages): statewide map on PDF pages 142–143,
  printed map date June 1959. Embedded parts: 1519 × 1927 and
  1583 × 1917 px. Newcastle inset is visible. Fine shire/municipal
  lines are distinct from coloured roads.
- Added 1960–61 report (163 pages): statewide map on PDF pages 162–163,
  printed map date June 1961. Embedded parts: 1471 × 1944 and
  1473 × 1940 px. Newcastle and Wollongong insets are visible. Other
  traffic-volume maps in this report are not classified as LGA maps.
- New PDFs retain source bytes. Page enumeration, selected map rendering,
  size and hash checks pass. Total: 618 files, 1,837,550,576 bytes;
  566 boundary JPEGs plus six Main Roads reports with boundary maps.
  Previous raw sources were not changed.

### Main Roads LGA maps: April 1956 to June 1962 additions

- Added four unchanged annual-report PDFs. The 1955–56 report has maps on PDF pages 119–120, dated April 1956; this is earlier than the report year-end. Native map images are 1083 × 1950 and 1321 × 1956 pixels.
- The 1957–58 report has maps dated June 1958 on PDF pages 130–131 (1406 × 1910 and 1415 × 1921 pixels).
- The 1959–60 report has maps dated June 1960 on PDF pages 183–184 (1454 × 1902 and 1456 × 1919 pixels).
- The 1961–62 report has maps dated June 1962 on PDF pages 154–155 (1344 × 1902 and 1373 × 1923 pixels). Fine named shire/municipal lines differ from green roads-division lines.
- These are statewide overview maps in two parts, with Newcastle insets; the 1960 and 1962 maps also have Wollongong insets. Native resolution limits fine tracing. Printed map dates do not prove each legal boundary's effective date.
- All 107 pages of the 1952–53 report and all 118 pages of the 1954–55 report were reviewed in contact sheets. No LGA map was confirmed. These reports were not added to raw maps.
- The 55-report discovery register now has ten saved LGA-map reports, seven reviewed without confirmed LGA maps and 38 unfetched. The six-report fetch job finished.
- Collection: 622 files, including ten report PDFs. Four new PDFs match fetched source bytes and SHA-256, open successfully, and have verified page counts and reviewed map pages. Existing 618 files were verified in preceding batches. No registered byte-identical duplicates.

### Main Roads LGA maps: June 1963 to June 1969 additions

- Added seven unchanged annual-report PDFs with statewide named shire/municipal lines. Fine LGA lines differ from coloured roads and green roads-division lines. Maps include Newcastle and Wollongong insets.
- Report 1962-63: printed map date June 1963; PDF map pages 157;158; native embedded map dimensions 157: 1471 x 2031; 158: 1481 x 2029 pixels.
- Report 1963-64: printed map date June 1964; PDF map pages 168;169; native embedded map dimensions 168: 1358 x 1896; 169: 1375 x 1915 pixels.
- Report 1964-65: printed map date June 1965; PDF map pages 52;53; native embedded map dimensions 52: 1344 x 1896; 53: 1371 x 1904 pixels.
- Report 1965-66: printed map date June 1966; PDF map pages 64;65; native embedded map dimensions 64: 1358 x 1950; 65: 1390 x 1935 pixels.
- Report 1966-67: printed map date June 1967; PDF map pages 64;65; native embedded map dimensions 64: 1263 x 1919; 65: 1265 x 1929 pixels.
- Report 1967-68: printed map date June 1968; PDF map pages 2;68; native embedded map dimensions 2: 1981 x 1696; 68: 2010 x 1696 pixels.
- Report 1968-69: printed map date June 1969; PDF map pages 3; native embedded map dimensions 3: 2025 x 1710 pixels.
- The 1967–68 report repeats its complete June 1968 map on PDF pages 2 and 68. These are two scans in one report, not two boundary regimes. Road-surface maps were not classified as LGA maps. Other report maps are not exhaustively inventoried.
- Printed map dates do not prove each legal boundary effective date. These maps provide overview context; native resolution limits fine tracing.
- Collection now has 629 files, including 17 Main Roads report PDFs. All seven new PDFs match fetched source bytes and SHA-256, open successfully, and have verified page counts and reviewed map pages. Existing 622 files were verified in preceding batches. No registered byte-identical duplicates.
- The 55-report register now has 17 saved LGA-map reports, seven reviewed without confirmed LGA maps and 31 unfetched. The seven-report fetch job finished.

### Main Roads LGA maps: boundaries at 30 June 1972–1977

- Added six unchanged annual-report PDFs. Each selected statewide map explicitly dates its LGA boundaries to 30 June of the year below; these dates were read from the map title.
- Report 1971-72: boundary date 30 June 1972; PDF map page 2; native embedded map dimensions 2: 2031 x 1700 pixels.
- Report 1972-73: boundary date 30 June 1973; PDF map page 2; native embedded map dimensions 2: 2054 x 1727 pixels.
- Report 1973-74: boundary date 30 June 1974; PDF map page 2; native embedded map dimensions 2: 2088 x 1737 pixels.
- Report 1974-75: boundary date 30 June 1975; PDF map page 44; native embedded map dimensions 44: 2054 x 1690 pixels.
- Report 1975-76: boundary date 30 June 1976; PDF map page 43; native embedded map dimensions 43: 1958 x 1677 pixels.
- Report 1976-77: boundary date 30 June 1977; PDF map page 43; native embedded map dimensions 43: 1958 x 1692 pixels.
- The 1972–1974 maps include Newcastle and Wollongong insets. The 1975–1977 maps have no such insets. The 1976–1977 maps refer to separate detail maps for Sydney, Newcastle and Wollongong. Those detail maps are not in the selected statewide map image.
- Fine pale LGA lines differ from coloured roads and, where present, bold green Main Roads division lines. Faint lines and native resolution limit fine tracing. Keep the complete PDFs for source context. Other report maps are not exhaustively inventoried.
- Collection now has 635 files, including 23 Main Roads report PDFs. All six new PDFs match fetched source bytes and SHA-256, open successfully, and have verified page counts and reviewed map pages. Existing 629 files were verified in preceding batches. No registered byte-identical duplicates.
- The 55-report register now has 23 saved LGA-map reports, seven reviewed without confirmed LGA maps and 25 unfetched. The six-report fetch job finished.


### Main Roads LGA maps, 1978–1982 (10 October 2026)

- 1977-78: PDF page 44; printed boundaries as at 30 June 1978; embedded map 1975 × 1690 pixels; 206 report pages.
- 1978-79: PDF page 51; printed boundaries as at 30 June 1979; embedded map 1935 × 1681 pixels; 263 report pages.
- 1979-80: PDF page 54; printed boundaries as at 30 June 1980; embedded map 1935 × 1681 pixels; 325 report pages.
- 1980-81: PDF page 54; printed boundaries as at 30 June 1981; embedded map 1988 × 1700 pixels; 320 report pages.
- 1981-82: PDF page 2; printed boundaries as at 1 January 1982; embedded map 2119 × 1679 pixels; 326 report pages.
- All five full source PDFs are preserved unchanged under `data/raw/historical_boundary_maps/nsw_main_roads/`. Source links and SHA-256 hashes are in the downloader manifest. Fine pale-green municipal/shire boundaries differ from coloured roads and bold departmental divisions. No Newcastle/Wollongong insets. The 1978–1981 sheets refer to separate detail maps. These statewide scans limit fine tracing.
- The 1982 boundary date is **1 January**, not 30 June or the report end date. Printed dates are map claims, not independent proof of legal commencement.
- The 1982–83 report was not added to raw maps: all 331 pages inspected via contact sheets; pages 3, 20 and 68 checked at full page resolution. The opening sheet drops confirmed LGA lines and names. Its road and division dates must not become LGA dates. Page 68 shows the Blacktown Main Roads division covering several LGAs, without individual LGA perimeters.
- Series checkpoint: 55 public report candidates; 28 saved with confirmed LGA maps, eight reviewed without a confirmed LGA map, 19 not fetched. Broader discovery remains active.


### Main Roads late-series check (10 October 2026)

- Added the unchanged 1983–84 report PDF (349 pages). Map title: classification of main roads with local government area boundaries, as at 1 January 1984. PDF page 75 shows west/centre NSW; the eastern continuation is on the left of PDF page 76. Native page scans: 2000 × 1727 and 2018 × 1741 pixels. Fine pale-green LGA lines and names are visible. A black gutter interrupts the join. Page 76 also contains a separate rest-area map without LGA lines. Preserve both source pages; do not treat the second page as wholly a boundary map.
- Reviewed all pages of 1984–85 (121), 1985–86 (327), 1986–87 (339), and 1987–88 (356). Map candidates were checked at full page resolution. Their state maps explicitly show departmental divisions dated 30 June 1985/1986/1987/1988, without confirmed individual LGA perimeters. Regional maps show roads/projects or departmental regions. These four reports remain in exploratory review storage, outside raw boundary maps. Candidate records hold the checked page numbers.
- Collection: 641 registered source files, 2,496,754,705 bytes. Added PDF source-byte, SHA-256, size, page-count and map-render checks pass; no registered byte duplicates. Main Roads checkpoint: 29 saved, 12 reviewed without a confirmed LGA map, 14 not fetched.

### Main Roads pre-war review (10 October 2026)

- Reviewed every page in five reports: 1934–35 (77 pages), 1935–36 (88), 1936–37 (118), 1937–38 (113), and 1938–39 (117). No LGA map was confirmed. All remain in exploratory review storage. Raw boundary sources are unchanged.
- Checked map candidates at full page resolution: 1935–36 PDF pages 13, 18 and 38; 1937–38 pages 7, 10, 11 and 14; 1938–39 page 12. They show road pavements, road networks or traffic line-marking. Other diagrams show engineering geometry, not council perimeters.
- Main Roads checkpoint: 29 reports saved with LGA maps, 17 reviewed without a confirmed LGA map, nine not fetched. Collection remains 641 source files. Broader discovery remains active.

### Main Roads wartime review (10 October 2026)

- Reviewed every PDF page of 1940–41 (21 pages), 1941–42 (12), and 1942–43 (11). These reports contain text and tables, with a portrait in 1940–41. No geographic map found. Title-page reporting years match the catalogue periods. All three fetched PDFs open successfully; response status, bytes and page counts are recorded. They remain in exploratory storage.
- Main Roads checkpoint: 29 saved with LGA maps, 20 reviewed without a confirmed LGA map, six not fetched: 1943–44, 1944–45, 1945–46, 1946–47, 1947–48 and 1949–50. No fetch job runs. Raw collection remains 641 source files.

### Main Roads series review completed; NSW Lands comparison (10 October 2026)

- Added the unchanged 1945–46 report (68 pages, 14,849,428 bytes). PDF page 28 shows a dash-dot boundary separating Greater Newcastle and Lake Macquarie on a Newcastle arterial-road planning map, printed 1946. Native page image: 1173 × 1925 pixels. No exact boundary date is given. Page 29 shows Wollongong road planning without confirmed council perimeters. All report pages inspected via contact sheets; both map candidates checked at full resolution.
- Added the unchanged 1946–47 report (87 pages, 15,104,274 bytes). Statewide map spans PDF pages 86–87: native images 1327 × 1888 and 1331 × 1902 pixels. Fine boundaries enclose named shires and the Newcastle inset; roads differ in colour/weight. Printed map date: 30 June 1947, not an explicit legal boundary commencement date. Sydney detail is referenced separately, not supplied on this sheet. Pages 33–34 show Main Roads district boundaries, not LGAs. All report pages reviewed; four map pages checked at full resolution.
- Also reviewed 1943–44 (13 pages), 1944–45 (15), 1947–48 (83) and 1949–50 (106). No LGA map confirmed. Full-resolution checks: 1947–48 page 42 (traffic striping); 1949–50 pages 14 (traffic flow) and 34 (flood damage). Rejected reports remain in exploratory storage.
- All 55 candidates in the discovered Main Roads catalogue series are now reviewed: 31 saved with confirmed LGA boundary information; 24 without a confirmed LGA map. This does not establish completeness of all historical Main Roads publications or boundary maps.
- Added the 2004 NSW Department of Lands comparison map, one-page vector PDF, 818,232 bytes. Catalogue and printed copyright both indicate 2004; PDF creation metadata gives 15 September 2004. Its legend labels red as current LGAs, blue as LGAs before Minister Kelly's amalgamations, green as LGAs before Minister Woods' amalgamations, and yellow shading as Alliance LGAs. Do not combine these layers or infer an exact legal date. Sydney insets include South Sydney, Concord and Drummoyne. Small Campaspe (Victoria) context is part of this NSW map. Exact boundary dates require separate evidence. Source catalogue metadata and fetch record are retained in the downloader output folder.
- Collection now has 644 source files, 2,527,526,639 bytes. Three new PDFs match fetched bytes and hashes, open successfully and have verified page counts and visually reviewed map pages. Earlier 641 files were verified in preceding batches. No registered identical-byte duplicates. No fetch job runs; broader LGA discovery remains active.

### Works/Local Government and election-report source checks (11 October 2026)

- Official Data.NSW title search for local government returned 205 catalogue records. Complete metadata response is retained as `local_government_report_catalogue_search.json` in the downloader output folder. Four historic Works and Local Government reports were identified: year ended 30 June 1936 (92 PDF pages), 1937 (113), 1938 (144), and 1940 (59). Every page was visually reviewed in contact sheets. Text, tables, building images and photographs; no geographic maps found. The four PDFs remain in exploratory review storage and are not raw boundary sources. Fetch status, byte sizes and page counts are recorded per report.
- The 1949 search lead, publication 11089, is a Board of Fire Commissioners report, not a Local Government department report. Its metadata is retained under a corrected filename. It was not fetched or added as a boundary source.
- Registered 147 council reports from the 2008 Local Government elections as unconfirmed candidates. Reviewed every page of Auburn (96 pages), Marrickville (98) and Manly (98). All three contain election text, tables, charts and ballot-paper facsimiles, with no geographic map. Their ward-boundary-change discussion does not supply boundary lines. All three remain in exploratory storage; no new raw sources added.
- The other 144 election reports remain uninspected. They are deferred because the representative reports use a shared template without maps; this does not prove absence in the other reports. Resume from `nsw_2008_election_report_review_candidates.csv` only if stronger map evidence emerges. Other explicitly mapped sources have higher priority.
- Collection unchanged: 644 source files. Both fetch jobs finished; no review remains pending among the seven fetched PDFs. Broader LGA discovery remains active.

### Former Sydney council maps from council documents (11 October 2026)

- Added three full, unchanged source PDFs. Source URLs, hashes, sizes and page counts are in the downloader manifest; page-level review notes are in `council_map_documents_review.csv`. New sources match fetched bytes and SHA-256, open successfully, and have visually inspected/rendered map pages. No registered identical-byte duplicates. Other maps in the two long documents are not exhaustively inventoried.
- Marrickville DCP 2011 precinct sheet: one page, 2,109,537 bytes. Printed production date 2 December 2015. Detailed streets, former council perimeter and numbered planning precincts; those precincts are not wards. DCP title year 2011 is not the sheet date. PDF has later modification metadata (16 December 2020); the saved original preserves it. The 2026 URL directory is not a survey or boundary date. Exact legal boundary date unconfirmed.
- Marrickville Southern Area Heritage Review: April 2015 report, 160 pages, 3,462,491 bytes. PDF page 118 (printed 108), Figure 103, reproduces a cropped 1940 Craigie road and municipal map. Its caption identifies St Peters/Marrickville boundaries before 1948, discusses a 1919 land transfer, and cites State Library MC 811.12/1940/1. The embedded crop is only 422 × 334 pixels. It is coarse boundary context, not a full original map or a precise tracing source. Need the original library scan for better resolution.
- Warringah agenda: meeting 26 April 2016; issued 20 April 2016; 70 pages, 3,068,469 bytes. PDF page 70 shows the former Warringah perimeter and wards A/B/C, with neighbouring councils labelled. Map is undated, explicitly not to scale, and embedded at 623 × 871 pixels. Agenda date does not establish exact boundary commencement. This schematic map is context only for precise digitising.
- A search-indexed 1903 City of Sydney map at the old CDN host could not be fetched because the connection failed. No source bytes saved; alternate-host discovery remains open. This one failed source does not block other discovery.
- Collection: 647 source files, 2,536,167,136 bytes. No fetch job runs; broader discovery remains active.

### Craigie Sydney municipal map, catalogue [1940]

- Saved the full original State Library scan, `state_library_nsw/craigie_1940_sydney_suburbs_municipal_map_36912510.jpg`, unchanged: 7,611 × 10,000 pixels; 23,265,527 bytes. Record `74VvxP3XJBQd`; call number `MC 811.12/1940/1`; original `FL3691253`, display `FL3691261`.
- Catalogue date `[1940]` is inferred from publisher code 0491. It is not an exact legal boundary date. The source includes a municipality/shire table with population and dwellings; those statistics have not been checked or extracted.
- Visually confirmed red municipal outlines and coloured LGA areas across Sydney. The full scan supplies the original behind Figure 103 in the April 2015 Marrickville heritage report, avoiding its small reproduction. Fold lines and coarse street placement remain source limitations; no georeferencing or tracing was done.
- The rediscovered 1903 City of Sydney record `1709402` is already in the manifest; no duplicate was saved.

### Further Craigie LGA maps

- Reviewed all 73 catalogue records returned by the Kenneth Craigie author filter; retained metadata in `craigie_author_search_metadata.json`. This is a bounded publisher search, not a complete NSW catalogue search. Four explicit LGA map records have now been downloaded and visually checked; other records were not fully reviewed for boundaries.
- NSW towns map, shire edition, catalogue 1924 (`74Vvz8eBeWzy`): second edition; full 10,000 × 7,497 scan. Legend distinguishes red shire outlines from hatched municipal outlines. Includes enlarged coastal/central NSW inset and small surrounding-state context. The Western Division is not a shire; do not treat its whole area as one LGA.
- Sydney road and municipal map, catalogue 1928 (`74Vv7oa32GE3`): third edition, 8,777 × 10,000 scan. Legend identifies municipal/shire boundaries with alternating crosses and dashes; tram lines are red. Coloured LGA areas also assist interpretation. Tear loss at the lower edge and fold marks are preserved.
- Sydney motorists edition, catalogue `[1929]` (`74VvRE8Jebmb`): 8,737 × 10,000 scan. Municipal/shire lines use the cross/dash symbol; thick red routes with mileage circles are roads, not LGA boundaries. Strong horizontal fold abrasion obscures some northern lines.
- None of these catalogue/publication dates establishes an exact legal boundary date. Original JPEGs are unchanged; no derived crops are kept in raw data.

### Craigie NSW business map, printed 1940

- Saved the full original map and separate LGA/town index from State Library record `74Vv3555zDaZ` under `state_library_nsw/craigie_1940_nsw_business_shire_map.jpg` and `craigie_1940_nsw_business_shire_index.jpg`. Map: 10,000 × 7,524; index: 10,000 × 7,346. Printed map title explicitly says 1940 and shire edition. It is not an exact legal boundary date.
- Full scan and legend visually reviewed. Legend identifies green shire outlines and hatched municipal areas, distinct from red roads with mileages. Includes an enlarged coastal/central NSW inset; the Western Division is not a single LGA. Some surrounding-state context is part of the unchanged NSW sheet.
- Separate index lists municipalities, shires, Sydney suburbs and towns. P = post office; R = railway station; alphanumeric codes locate map grid cells. Railway mileage is used where available; otherwise mail-route mileage. Population notes say latest census but do not state its year; neither population nor dwellings was extracted or validated.
- Retained both original JPEGs unchanged; dimensions match catalogue. Actual file sizes are 29,194,140 and 27,208,882 bytes; catalogue sizes are rounded and are not used as exact byte checks.

### NSW local government comparative report, 2009/10

- Saved the full 137-page report from the Office of Local Government as `nsw_local_government/olg_comparative_2009_2010_with_lga_maps.pdf`. Copyright page is 2011. The upload path says 2026; that is not the map date.
- Visually confirmed PDF pages 20–22: NSW statewide LGAs, Sydney LGAs, inner metropolitan Sydney LGAs. Maps credit the Department of Lands; no exact boundary date is printed. They show pre-2016 councils including Auburn, Holroyd, Pittwater, Warringah, Manly, Ashfield, Leichhardt, Marrickville, Hurstville and Kogarah.
- Page 20 map is stored as raster strips, page 21 map is 598 × 654 pixels, page 22 map is 1,344 × 1,309 pixels. These are coarse context outlines with scale bars, not detailed street/cadastral tracing sources. Preserve full PDF; no extracted map images are saved in raw data.
- Paddington agency record `62524` mentions an attached 1880s ward map, but its rendered public page offers no map asset. No correspondence or agency-page download was counted as a map.

### OLG older comparative report map review

- Added full 189-page 2006/07 report, `nsw_local_government/olg_comparative_2006_2007_with_lga_maps.pdf`. PDF pages 21–23 are NSW, Sydney and inner metropolitan Sydney LGA maps. Enlarged copyright mark reads Department of Lands 2008, matching report copyright 2008; the reporting period is not the map date. Exact legal boundary date remains unspecified.
- These maps differ from the saved 2009/10 report maps: Baulkham Hills label, explicit unincorporated areas, different layout and line detail. Page 21 source image is 893 × 736; page 22 is 1,018 × 1,312; page 23 is 1,067 × 1,109. Useful context, limited precision for tracing.
- Downloaded and reviewed 2007/08 and 2008/09 map pages. Every embedded map image on PDF pages 21–23 is byte-identical to the corresponding image on 2009/10 PDF pages 20–22; these report PDFs were not added to raw maps. Evidence: `olg_comparative_map_image_comparison.json`. Their later-looking The Hills label also shows why reporting period cannot establish a map boundary date.
- Current OLG archive offers comparative report PDFs back to 2006/07. The former previous-reports URL now gives 404. Data.NSW phrase search returned only a planning-monitoring dataset, not older comparative reports. Two pre-2004 Parliament annual reports could not be retrieved via plain requests or the public browser; fetch records retained.
- April 1998 IPART benchmarking report was fetched for text review; no geographic map was confirmed. It was not fully visually reviewed and was not placed in raw maps.

### Bellingen environmental study, March 1984

- Saved the full original 379-page PDF, EIS 1467 / AA068086, as `bellingen/bellingen_1984_environmental_study_eis1467.pdf` (44,040,876 bytes). Title pages 2–3 say March 1984. Acknowledgements on PDF page 11 say study preparation July 1982–April 1983; map/legal boundary date is not specified.
- Visually reviewed PDF page 42, Protected Lands Map 1, and page 268, Good Agricultural Land Map 15. Both use the full Bellingen shire perimeter with labelled rivers, settlements, roads, north arrow and 0–10 km scale. Map 15 cites an October 1982 Agriculture Department survey for agricultural land; that date does not establish the boundary date. Other thematic maps are present but have not been individually inventoried.
- PDF page 329, Structure Plan—Bellingen Map 23, explicitly labels the existing village boundary. It also shows proposed development, future highway and flood lines; these are not LGA lines. Village/planning boundaries are not automatically modern suburb boundaries.
- Native map scans: PDF 42 = 1,633 × 1,163; PDF 268 = 1,637 × 1,163; PDF 329 = 1,164 × 1,634. Large page size does not imply high scan detail. Preserve full source PDF; no persistent extracted images or georeferencing.
- The 2005/06 development-monitoring report was checked visually across all 64 pages and contains no confirmed geographic maps. The 1941 NRS-5399 map is still a catalogue lead: metadata confirms shire/municipal boundaries but no scan was retrieved from the linked Primo application shell.

### Maroota and Byron EIS boundary maps

- Saved three full source PDFs unchanged from the public EIS scan collection. None of the report dates establishes the legal date of the embedded council boundary. No georeferencing, cropping or enhancement was saved in raw data.
- `hornsby_baulkham_hills/maroota_1988_weavers_eis900.pdf`: 154 pages; 12,739,753 bytes. PDF page 9 certificate visibly dated 6 June 1988. Page 137, Figure 5, shows the Hornsby–Baulkham Hills boundary beside Old Northern Road/Maroota. Legend uses a long-dash/short-dash shire line, distinct from dashed minor roads and solid property/portion outlines. Native whole-page image 1,636 × 1,165; map occupies only its right-hand section. It is a partial LGA boundary segment.
- `hornsby_baulkham_hills/maroota_1994_sand_extraction_eis1048_vol2.pdf`: 297 pages; 35,832,580 bytes. Title page 3 says November 1994, volume 2. Page 8, Figure 3, shows the same local council boundary segment with a different development overlay and page layout; native map scan 845 × 1,165. The source has a blank annotation box. No boundary change is inferred from the different report dates. Only volume 2 was fetched.
- `byron/byron_1983_natural_environment_eis872.pdf`: 154 pages; 19,381,772 bytes. Title pages 2–3 say August 1983. Page 79, Map 13 (Wetlands), shows the full shire perimeter on a topographic base, north arrow and 5 km scale. Native scan 1,162 × 1,635. Wetland areas 1–23 and protection hatches are thematic zones, not council boundary subdivisions. Other map sheets remain in the full PDF but were not individually inventoried.
- All selected boundary maps rendered and visually checked. All three full PDFs open and match fetched bytes, SHA-256, sizes and page counts; no identical source-file hashes already occur in the manifest.

### Elderslie and Bargo EIS boundary maps

- Added two unchanged full PDFs from the public EIS archive. Manifest records source URLs, SHA-256, exact sizes and page counts. All selected map pages were rendered and visually checked. Both raw copies match fetched bytes; no identical-byte duplicate exists in the manifest. These are partial boundary segments, not complete LGA outlines. Exact legal boundary dates remain unspecified.
- `camden_wollondilly/elderslie_1996_soil_extraction_eis1204_vol1.pdf`: March 1996 report, EIS 1204 volume 1 / AB019988; 151 pages, 20,082,802 bytes. PDF pages 43 (Figure 5, Land Zoning and Ownership) and 78 (Figure 19, Noise Measurement Locations) show the Camden–Wollondilly boundary near the Nepean River and Navigation Creek. Legends distinguish shire lines from property, zoning and LEP lines. Native scans 1,645 × 1,163 and 1,647 × 1,163. Earlier noise observations and planning references do not date the council boundary. Only volume 1 was fetched.
- `wollondilly_mittagong/bargo_1975_colliery_eis790.pdf`: January 1975 report, EIS 790 / AB019580; 220 pages, 23,902,959 bytes. PDF page 101, Drawing 15 (Picton–Mittagong Corridor), shows former Mittagong and Wollondilly shire boundary segments and surrounding council context. Legend identifies thin red cross-marked shire lines; heavy red hatching marks water catchment edges. Bowral fill and growth-centre overlays are separate symbols. Native scan 804 × 1,163; coarse source detail limits tracing. Other report maps are retained but not individually inventoried.
- Collection now has 661 source files, 2,867,621,800 bytes. No fetch job is running; broader LGA discovery remains active.

### Hawkesbury-Nepean and Narrabeen regional LGA maps

- Saved two unchanged full EIS archive PDFs. Original bytes, hashes and page counts verified. Selected map pages and report title dates rendered and visually checked. No identical-byte source duplicates in the manifest. Publication dates do not establish the exact legal date of the embedded LGA lines.
- `hawkesbury_nepean/hawkesbury_nepean_1995_cumulative_impact_eis1541.pdf`: 7 March 1995 report, EIS 1541 / AA067887; 144 pages, 15,860,425 bytes. PDF page 13 (printed 2), Figure 1.1, shows regional council outlines including Hawkesbury, Baulkham Hills, Pittwater, Warringah, Gosford and western/southern Sydney councils. Legend explicitly distinguishes local government, Sydney Regional Environmental Plan 20 and Catchment Management Trust boundaries. The heavy planning/Trust outlines are not LGA lines. Native scan 854 × 1,166; coarse context only. Not every council perimeter is complete within the map extent.
- `warringah/narrabeen_1989_dredging_eis1061.pdf`: November 1989 report, EIS 1061 / AB019722; 149 pages, 16,681,435 bytes. PDF pages 117 and 118, Figures 25 (Sand Production in Sydney Area) and 26 (Cartage Costs), show Sydney LGA outlines including former Warringah, Baulkham Hills, Bankstown and Fairfield. Figure 25 legend explicitly identifies local government areas. Some inner councils are numbered without names on these sheets; no names were inferred for them. Native scans 1,688 × 1,167 and 1,688 × 1,166. Production dots, price/quantity annotations and transport-advantage hatches are thematic overlays, not boundary lines. Figure 26 cites July 1, 1988 cartage rates; this is not a boundary date. Separate EIS appendices were not fetched. Other maps in the full report are not individually inventoried.
- October 1975 Hawkesbury sand-mining study, AB019312 / printed EIS 655: full 56-page PDF reviewed via contact sheets, with all six map pages enlarged. Catchment, geology, deposit, road and river maps present; no LGA lines confirmed. Retained in exploratory review storage, not raw boundary maps.
- Evidence: `hawkesbury_and_narrabeen_eis_map_review.csv`. Collection now 663 source files, 2,900,163,660 bytes. No live fetch job; broader LGA discovery remains active.

### ABS 1961 census LGA maps and Colo lead review

- Added full unchanged ABS NSW population volume: 131 pages, 8,705,767 bytes. Preface dated September 1963. PDF pages 129 and 131 show statewide and Sydney LGA boundaries; map footnotes explicitly identify 30 June 1961 census-date councils. Page 130 supplies the LGA number index. Explanatory notes on page 4 confirm census-date geography and note that statistical divisions split some LGAs.
- Map legends separate statistical/metropolitan boundaries from municipal and shire lines. NSW colours represent statistical divisions; Sydney colours distinguish council types. Native scans 1,089 × 963 and 941 × 1,072: coarse context, not detailed cadastral tracing sources. Original full PDF preserved; maps inspected through temporary extracted images only.
- Evidence: `colo_and_abs1961_map_review.csv`. EIS 208 (59 pages) and EIS 262 (251) reviewed by whole-document contact sheets and selected enlarged regional map pages; no council lines confirmed. EIS 262 map legends were not all individually checked. EIS 208 amended April 1983 title retains Colo Shire wording; this does not prove a pre-merger map.
- November–December 2023 Millstone pages 4–5 provide Colo boundary descriptions and gazette references but no map. September 2002 Sydney wine application page 9 maps a mixed wine-region boundary, not a separately labelled LGA network. Neither added to raw maps. Wine PDF fetched through public browser after requests returned 406. Review files remain in the existing exploratory output folder.
- New raw PDF matches fetched bytes and SHA-256, opens successfully, and map legends/date footnotes were visually checked. No registered identical-byte duplicates. Collection: 664 source files, 2,908,869,427 bytes. Broader LGA discovery remains active; no fetch job runs.

### ABS 1954 and 1966 NSW census boundary maps

- Saved two full unchanged NSW census volumes. Original bytes, SHA-256, sizes and PDF page counts verified; no identical source-file hashes in manifest. Embedded map-image hashes differ from the saved 1961 maps. Evidence: `abs1954_1966_1971_map_review.csv` and `abs1954_1966_map_image_checks.csv`. No persistent extracted map images.
- 1954 population volume: 196 pages, 15,677,247 bytes; preface dated 21 September 1955. Statewide map PDF 194 and Sydney PDF 196; council-number index 195. Native maps 1,119 × 939 and 946 × 1,107. Both maps have explicit LGA symbols. **Date conflict:** explanatory notes PDF 4 specify councils constituted at 30 September 1953, while map captions say 30 June 1954. Preserve both statements; exact legal boundary date unresolved. Do not silently assign the census year to every boundary.
- 1966 NSW population/dwellings volume: 520 pages, 29,167,021 bytes; preface August 1969. Map reference PDF 508 explicitly specifies LGAs as used at 30 June 1966 census, consistent with notes PDF 7. Native maps and all legends reviewed: Sydney 509; North Coast/Northern Tableland 510; Hunter/Manning 511; Newcastle 512; South Coast/Southern Tableland 513; Wollongong 514; North Central Plain/North Western Slope 515; Central Western Slope/Central Tableland 516 (includes former Colo); South Western Slope 517; Riverina 518; Western/Central Plain 519; Broken Hill/Albury-Wodonga urban contexts 520. Red urban lines and dashed statistical edges are not LGA outlines.
- 1966 map long edges are 844–1,340 pixels; Sydney 845 × 1,340. Low scan detail and fold/colour abrasion constrain tracing. Page 520 includes neighbouring Wodonga within the unchanged NSW source, not a separate interstate download.
- 1971 NSW Bulletin 6: all 50 pages visually checked; no geographic maps. Retained in exploratory review storage only. Separate Bulletin 13 was later reviewed; see the next batch below.
- Collection now 666 source files, 2,953,713,695 bytes. No live fetch job; broader LGA map discovery active.

### ANU 1966 and ABS 1971 NSW LGA map scans

- Saved two unchanged full PDFs. Raw copies match fetched bytes, SHA-256, sizes and page counts; no identical-byte source duplicates. All 668 registered paths and sizes pass. Evidence: `anu1966_and_abs1971_map_review.csv` and `anu1966_and_abs1971_map_image_checks.csv`. No persistent extracted map images.
- ANU 1966 NSW Bulletin No 1.8: 55 pages, 31,911,013 bytes. PDF 2 release embargo is 13 March 1969; catalogue year 1966 is the census year. PDF 40 map reference and 41 Sydney explicitly specify 30 June 1966 council geography. Selected reference and Sydney/Colo map legends visually checked. PDF 48 Central Western Slope/Central Tableland includes Colo. Same cartographic series as the saved ABS 1966 colour volume; larger monochrome scans do not imply changed boundaries. Sydney first full-page image 2,024 × 3,088; PDF 48 first image 2,560 × 2,024. Foreground masks are not separate map sheets. Full document viewed as contact sheets; extra ending scans not individually inventoried. Paper folds, black borders and monochrome contrast remain. ANU catalogue requires permission before reproduction; research use only.
- ABS 1971 NSW Field Count Statement No 3: 41 pages, 2,469,522 bytes. Release embargo 9 February 1972; census 30 June 1971. All three appended maps rendered and visually checked: Sydney PDF 39, Map 1971/FC/1 (3,508 × 4,961); Newcastle PDF 40, Map 1971/FC/8 (4,981 × 3,537); Wollongong PDF 41, Map 1971/FC/9 (3,508 × 4,961). Map imprint says Division of National Mapping, 1971. Thin LGA lines differ from heavy statistical-division perimeters and urban hatches. Exact legal boundary date not separately confirmed. Some Sydney inner councils lack names on this sheet; do not infer them. Contents list Canberra, but no Canberra map occurs in this scan.
- 1971 Bulletin 13: 22-page national map collection reviewed through a whole-document contact sheet. Retained in exploratory review storage; not added as a national raw source. Individual map legends remain incompletely inventoried. Seek standalone NSW sheets through NLA/Trove.
- Collection: 668 source files, 2,988,094,230 bytes. No live fetch job; broader LGA discovery active. Existing decision and report-asset records need no change: these are research inputs, not final report figures.

### Earlier Sydney ward and absorbed-municipality maps

- Saved eight unchanged original one-page PDFs from the public City archive viewer. Sources `1724428`–`1724435`; each original hash, exact size and PDF readability verified. All full-page maps viewed, with legend/base-date enlargements. No identical source-file duplicates. Evidence: `city_sydney_early_ward_map_review.csv`. Review and discovery files stay in the existing downloader output folder; temporary rendered images stay outside the repo.
- Seven city perimeter/ward maps cover 20 July 1842–1 April 1857; 2 April 1857–19 April 1870; 20 April 1870–19 August 1902; 20 August 1902–21 December 1908; 22 December 1908–2 October 1924; 3 October 1924–21 December 1932; and 22 December 1932–31 December 1948. The coloured overlays are later historical reconstructions. Base-map dates are July 1974 for the first, September 1968 for the next three, and July 1980 for the final three. Modern Northcott/South Sydney street-map labels do not date the historical overlay. Ward changes do not automatically imply a changed city perimeter.
- Absorbed-municipality sheet `1724435`: catalogue and map caption date 31 December 1948; base map 1982. Native scan 5,039 × 6,457. Coloured municipal outlines include The Glebe, Paddington, Darlington, Redfern, Newtown, Erskineville, Alexandria and Waterloo. **Catalogue discrepancy:** description lists Leichhardt among absorbed municipalities, while the coloured map labels The Glebe and leaves Leichhardt as surrounding context. Do not infer Leichhardt absorption from that description. Seven other scans are 5,000 pixels wide, with heights 4,778–4,882. City/municipality symbols and internal ward lines differ; preserve legend distinctions when tracing.
- Trove Sydney 1971 map search first page lists main statistical-division and collectors-district sheets as unavailable online. This is a catalogue search result, not proof that all copies lack scans. Links and rendered search evidence saved. Later result pages not reviewed.
- October 2023 Smillie/Berzins heritage report PDF 11 Figure 2 reproduces the 1932–1948 and absorbed-municipality maps at 540 × 507 and 533 × 688. Not added to raw: original archive PDFs above provide clearer versions. Armidale boundary-history PDF (9 pages) and Groenewegen local-government tax-capacity book (171 pages) viewed as whole-document contact sheets; boundary descriptions/tables, no geographic maps confirmed. They remain exploratory reviews. Evidence: `sydney1971_and_council_history_review.csv`.
- Collection: 676 files, 3,061,691,152 bytes. All registered paths and sizes pass. No live fetch job. No final report assets or new codebase decisions; broader NSW LGA discovery active.

### NSW 1981 census LGA maps and survey/1976 reviews

- Saved full unchanged ANU NSW 1981 persons/dwellings bulletin: 38 PDF pages, 67,184,917 bytes. Original bytes, SHA-256, exact size and readability verified; no identical source-file duplicate. PDF 36 statewide LGA map with council-number index; 37 Sydney with inner-area enlargement; 38 regional statistical districts with LGA lines (Wagga Wagga, Bathurst–Orange, Gold Coast, Broken Hill, Tamworth, Newcastle, Albury–Wodonga, Canberra and Wollongong). All three full sheets visually reviewed. Interstate portions are context within this NSW publication, not standalone interstate raw sources.
- PDF 3 note 4 explicitly uses NSW council boundaries at **1 January 1981**; census 30 June 1981. PDF 1 release 31 March 1983; maps prepared by Division of National Mapping, 1982. Keep these dates separate. Notes say 1976 comparison counts use 1981 LGA geography; they are not proof of 1976 boundaries. Legend separates statistical divisions/subdivisions, LGA lines and urban fill. Urban/Canberra statistical areas are not all legal councils.
- Full-page map image dimensions: PDF 36 first image 4,520 × 2,864; 37 first image 3,952 × 2,856; 38 first image 4,504 × 2,872. Secondary foreground masks are not extra map sheets. Folds, white abrasion, glare and monochrome contrast limit tracing, especially inner Sydney. ANU catalogue permits research use only and requires permission before reproduction. Evidence: `anu1976_1981_nsw_map_review.csv`, `anu1981_nsw_map_image_checks.csv`.
- Three Sydney survey samples viewed in full: Darlington civic survey `1709295`, printed 1950; Erskineville `1709296`, printed 1951 despite catalogue series ending 1950; Paddington East detail sheet `1709114`, catalogue 1949–1972. No separately labelled council perimeter confirmed. Woollahra blank drawing coverage is not a boundary symbol. All remain exploratory review PDFs. Evidence: `city_sydney_survey_sample_review.csv`.
- ANU 1976 NSW summary (38 pages) and NSW LGA characteristics/corrigenda file (30 pages) reviewed through whole-document contact sheets; no geographic maps confirmed. They remain exploratory reviews. Two 1981 search hits were ACT/Tasmania editions with common NSW explanatory wording. The wrong-geography PDFs and extracted texts were removed; fetch metadata and exclusion evidence retained. Verify catalogue/title geography before treating search snippets as NSW evidence.
- Collection: 677 registered sources, 3,128,876,069 bytes. All source paths and sizes pass. No live fetch job; broader discovery active. No final report assets or new codebase decisions.

### Official ABS 1981 and 1986 NSW map scans

- Added two unchanged full official PDFs. Exact bytes, SHA-256, page counts and PDF readability verified; no identical registered source-file hashes. All 679 registered paths and sizes pass. Evidence: `abs1976_1981_1986_nsw_map_review.csv`, `abs1981_1986_nsw_map_image_checks.csv`. Full public archive indexes and links saved for 1976/1981/1986.
- ABS 1981 NSW persons/dwellings bulletin: 67 pages, 3,817,390 bytes. Maps PDF 62 statewide (5,792 × 3,520), 64 Sydney (5,056 × 3,520), 66 regional districts (5,792 × 3,520). All map sheets and note 4 on PDF 4 visually reviewed; NSW council geography 1 January 1981. Same map series as ANU source but clearer black line work, less glare and higher image dimensions. Urban shading is largely absent, including its legend swatch; retain ANU copy to interpret that layer. No changed boundaries inferred from scan differences. Reverse pages 63/65/67 blank; they are not map sheets. Full PDF retained without editing.
- ABS 1986 NSW bulletin: 69 pages, 4,941,851 bytes; release 7 June 1988 on PDF 3. PDF 68 Sydney statistical-local-area map (3,485 × 5,020, stored rotated) includes inner-area enlargement and SLA names/codes. Map imprint 1987. Thin SLA lines differ from statistical subdivision and division edges. Most SLAs are council-based, but Sydney City is divided into Inner (7201) and Remainder (7202); these are not separate legal councils. Definitions PDF 7–8 explicitly distinguish SLAs and legal LGAs. Exact legal boundary date not separately confirmed. Census 30 June 1986; comparison counts for 1981 were recast on 1986 LGA geography. Do not label these as 1981 boundaries.
- Whole 1986 document reviewed through contact sheets: only Sydney outline Sheet 2 on PDF 68; no statewide outline Sheet 1 found in this downloaded scan. PDF 2 and 69 show Sydney intercensal-change SLA choropleths; heavy hatching limits tracing. Main outline and rear choropleth enlarged and visually reviewed. Other thematic map is retained but not separately enlarged. Seek the missing statewide sheet in another NSW source. Original full source preserved.
- Official ABS 1976 NSW LGA characteristics bulletin: 28 pages, all viewed through contact sheet; no geographic maps confirmed. Review-only copy retained. No live fetch job; broader NSW LGA discovery active. Existing decision and final report-asset records need no change.

### Recovered statewide 1986 NSW map

- Saved full unchanged ANU 1986 NSW persons/dwellings bulletin: 72 pages, 30,826,187 bytes. Same publication series as saved official ABS copy; this scan includes statewide Sheet 1 absent from that copy. PDF 67 is the LGA/SLA index plus western portion, 68 central portion, 69 eastern portion and Newcastle enlargement. Sydney Sheet 2 spans PDF 70–71. All five original panels visually checked, with larger statewide index/eastern-panel renders. These are overlapping scans of two sheets, not five separate maps. No persistent stitching, cropping, rotation or enhancement.
- Census 30 June 1986, map imprint 1987, release 7 June 1988. Exact legal boundary date remains unconfirmed. The statewide index has separate LGA and SLA columns. Blayney, Cabonne, Evans, Inverell and Tweed contain lettered SLA parts; Newcastle has Inner/Remainder, and the Sydney index has Sydney Inner/Remainder. Internal SLA boundaries do not define extra legal councils. Statistical division/subdivision lines differ from thin SLA lines; unincorporated/offshore categories are not councils.
- Full-page map images are about 2,072–2,264 pixels wide and 2,904–2,920 high. Embedded masks/foreground images are not extra sheets. Statewide contrast is faint with folds and clipped panel edges; use overlap and index, and seek a clearer original before precise tracing. Sydney panels are less clear than the saved ABS Sheet 2. Both complete source PDFs retained because ANU supplies otherwise missing statewide content. ANU research-only and reproduction-permission conditions apply.
- Official 1986 NSW usual-resident bulletin: 210 pages, 17,624,064 bytes fetched for exploratory review. Ending eight pages and extracted text reviewed; no map appendix found in those ending pages. Whole document not visually reviewed; no confirmed boundary maps, not added to raw. Evidence: `anu1986_statewide_map_review.csv` and `anu1986_statewide_map_image_checks.csv`.
- Raw source matches fetched bytes, SHA-256, exact size and 72-page readability; no identical registered source-file hash. Collection: 680 sources, 3,168,461,497 bytes. All registered source paths and sizes pass. No live fetch job; broader NSW LGA discovery active. No final report assets or new codebase decisions.

### Clearer complete ABS 1986 NSW boundary sheets

- Saved full unchanged ABS age/sex bulletin, catalogue 2454.0: 47 pages, 3,134,141 bytes. Release 29 September 1987 visually confirmed on cover; census 30 June 1986; maps imprint 1987. Exact legal boundary date remains unconfirmed. Geographic definitions PDF 5 and notes PDF 6 distinguish SLAs from legal councils.
- PDF 46 Sydney Sheet 2: native image 3,475 × 5,020. PDF 47 statewide NSW Sheet 1: 3,470 × 5,751. Both stored rotated, with full maps and legends visually reviewed. Statewide Sheet 1 is substantially clearer than the faint three-panel ANU scan and includes the LGA/SLA code index and Newcastle enlargement. No altered or extracted maps stored in raw. Full original source retained.
- Thin SLA boundaries differ from heavy statistical-division and dashed subdivision edges. Lettered council parts and Newcastle/Sydney Inner/Remainder are internal statistical areas, not additional LGAs. Use the LGA column to group SLA parts. Off-Shore Areas and Migratory is not a council. Scan comparisons do not establish identical legal geography; exact legal dates remain unresolved.
- Official 1986 summary-characteristics bulletin: 57 pages, 3,225,910 bytes; ending eight pages and extracted text reviewed. No boundary-map appendix in inspected ending pages. Whole document not visually reviewed; retained as exploratory review only. Evidence: `abs1986_age_sex_map_review.csv`, fetch metadata and original review PDFs in the downloader output folder.
- New raw PDF SHA-256, exact size and all 47-page readability verified. All 681 registered paths and sizes pass; no identical registered hashes. Collection: 681 sources, 3,171,595,638 bytes. No live fetch job; wider NSW LGA discovery active. No new codebase decisions or final report assets.

### 1933 and 1947 NSW census map exclusions

- Downloaded public ABS NSW population-analysis volumes for review: 1933, 150 pages and 11,070,622 bytes; 1947, 126 pages and 9,320,336 bytes. Also NSW summary Bulletin No 9 for each census: 1933, 13 pages and 411,666 bytes; 1947, 12 pages and 334,062 bytes. All four full scans visually reviewed through contact sheets, with ending pages separately. No geographic maps found; none added to raw collection.
- The population PDFs lack extracted OCR text. Empty text-search results do not prove absent maps; visual review supplied the exclusion evidence. Original review PDFs, fetch hashes and public catalogue indexes stay in the existing downloader output folder. Evidence: `abs1933_1947_nsw_map_review.csv`. Catalogue indexes list 69 links for 1933 and 59 for 1947. Other volumes and ANU copies remain unreviewed; do not extend this exclusion to the whole census series.
- Collection unchanged at 681 source files. No live fetch job. Next search lead: 1932 Craigie road and municipal map of Sydney and suburbs; saved Craigie editions include 1928, c1929 and c1940. A commercial listing is a discovery lead, not a verified digitised public source or a confirmed map-date definition.

### Circa 1932 Craigie Sydney municipal map

- Saved unchanged public full JPEG from Antique Print Map Room listing 320926: 2,694 × 3,071 pixels, 3,422,760 bytes. Printed title: Craigie's Road and Municipal Map of Sydney and Suburbs, Motorists Edition; compiled/published Kenneth Craigie, 16 Bridge Street, Sydney. Coverage extends from Newport to Campbelltown and the National Park. Full image and native legend enlargement visually reviewed.
- Legend explicitly separates Municipal & Shire Boundaries from park/reserve boundaries, principal roads, red road distances and railways. Tramways symbol is crossed out. Thin dotted municipal line work can be hard to separate at this resolution. Large upper-case municipal names and lower-case locality names differ. Former Eastwood, Dundas, Rydalmere/Ermington and inner municipalities appear. Do not infer precise boundary geometry from labels alone.
- Seller dates map circa 1932. Printed lower-right code 9201 is visible but its date meaning was not established. Exact production and legal boundary dates remain unconfirmed; do not silently convert seller attribution to legal geography. Seller says edition not found in Trove; this was not independently verified. Photograph has folds, paper wear, uneven light and a surrounding shadow. Full unchanged source retained; no persistent crops or enhancements.
- Public original image fetched from `https://antiqueprintmaproom.com/wp-content/uploads/2020/06/MG_0817-copy.jpg`. Public accessibility does not establish a public-domain reproduction licence. Catalogue, fetch/hash metadata and review record remain in the downloader output folder; no purchase or external message made. Evidence: `craigie_c1932_map_review.json`.
- SHA-256, exact bytes and decoded native dimensions/readability verified. No identical new registered hash. All 682 source paths and sizes pass. Collection: 682 files, 3,175,018,398 bytes. No live fetch job; wider NSW LGA discovery active. No new codebase decisions or final report assets.

### Newcastle 1916–1924 municipal reconstruction and fifth-edition NSW shire map

- Added full unchanged James Cairns Docherty thesis, *The second city: Social and urban change in Newcastle, NSW, 1900–c.1929*, November 1977. ANU source has 363 pages and 7,890,533 bytes. PDF 9 (printed viii) contains Newcastle municipal boundaries 1916–1924, sourced to Craigie Map (1918), plus modern locality names on the same municipal base. Repeated boundary outlines visually checked at PDF 23, 135 and 176; PDF 8 boundary-definition note also visually checked. Page images are 2,480 × 3,506; drawings occupy only part of each page. Full thesis not visually reviewed or all maps inventoried.
- Eleven mapped municipalities: Adamstown, Carrington, Hamilton, Lambton, New Lambton, Merewether, Newcastle City, Stockton, Wallsend, Waratah and Wickham. These are simplified later reconstructions, not original survey plates. The author reports a Newcastle/Hamilton transfer in 1913, Plattsburg incorporation into Wallsend in 1915, minor adjustments in 1925 and Greater Newcastle amalgamation in 1938. These statements have not been independently checked against proclamations. “City” means the former Newcastle City municipality; “city” means the aggregate. Modern locality labels and census urban area/centre definitions do not supply extra municipal boundaries. Seek original 1918 Craigie map for detailed tracing.
- ANU catalogue: https://openresearch-repository.anu.edu.au/items/59d34bcf-50cf-4ba6-b866-c63121a646b9 . First-page use notice limits copy to private study/research and requires author consent for copying or close paraphrase of passages. Full original preserved without extraction or enhancement.
- Added unchanged public Mapworld image of Craigie's Towns Map of NSW, Shire Edition, fifth edition: 4,921 × 3,733 pixels, 5,105,018 bytes. Full map and title, coastal enlargement and central detail visually checked. Printed title confirms fifth edition and Kenneth Craigie, 16 Bridge Street; scale 1:1,500,000. Catalogue attributes 1942; printed production/legal boundary date not independently confirmed. Shire outlines and names appear with roads, railways and municipalities; dense labels/hatches and overlapping lines limit tracing. No complete boundary-symbol legend confirmed; Sydney enlargement primarily shows locality/transport detail, not a full municipal division. Adjacent-state context is part of the unchanged NSW map, not an interstate source.
- Mapworld catalogue: https://www.mapworld.com.au/products/new-south-wales-town-map-by-craigies-shire-edition . Public image is not evidence of a public-domain reproduction licence. No purchase or external message made. Review evidence: `newcastle_and_craigie1942_map_review.json`; original exploratory review files, catalogue HTML and fetch metadata remain in downloader output folder.
- Both raw sources match fetched SHA-256 and bytes. New PDF page count/readability and JPEG native dimensions/readability pass. All 684 registered source paths and sizes pass; no identical registered hashes. Collection: 684 files, 3,188,013,949 bytes. No live fetch job; discovery active. No new codebase decisions or report assets.

### UON Craigie Newcastle–Maitland–Cessnock district map

- Saved original public University of Newcastle Flickr image M4715, catalogue identifier M1998/43: 5,941 × 4,414 pixels, 3,256,057 bytes. Full map, native title/legend and Newcastle detail visually checked. Map title: Craigie's General Map of the Newcastle–Maitland–Cessnock District. Compiled/drawn/published Kenneth Craigie, 16 Bridge Street, Sydney. Catalogue dates it [1920s?]; exact production/legal boundary dates unconfirmed. Do not equate this regional sheet to the 1918 Newcastle map cited by Docherty.
- Legend explicitly identifies Municipalities and Shires using a line with crosses. Colliery holdings, railway, tramway and road symbols differ. Newcastle former municipalities and regional shires appear, including Tarro, Bolwarra, Patrick Plains, Cessnock, Port Stephens and Lake Macquarie. Insets show Singleton and southern Lake Macquarie. Black transport lines can obscure council edges; yellowing, stains, folds and damaged margins limit tracing. Colliery holdings are not council boundaries. Original retained without cropping, enhancement or georeferencing.
- Catalogue: https://www.flickr.com/photos/uon/6071068113/ . Original image link explicitly exposed at public `/sizes/o/` page. UON permits study/personal research; other reproduction requires permission. Catalogue and sizes HTML, fetch/hash metadata and `uon_m4715_map_review.json` retained in downloader output folder. University map-inventory PDF public URL returned HTTP 403; no inventory PDF was saved. This does not block the working Flickr original source.
- Original hash, exact bytes and image readability/native dimensions verified. All 685 registered paths and sizes pass; no identical new source hash. Collection: 685 files, 3,191,270,006 bytes. No live fetch job; wider NSW LGA discovery active. No new codebase decisions or final report assets. Next: other UON Map Treasures entries with dated council lines; original 1918 edition unresolved.

### UON 1911 Newcastle municipal map and album sample review

- Saved unchanged full Flickr original M4633: Map of the City of Newcastle and environs, 10,454 × 7,325 pixels, 3,216,456 bytes. Printed title/legend enlarged and visually checked: copyright 1911, explicit thick municipal-boundary symbol, municipal names, separate ferry routes and tramways. Printed compiler H.C. Trenchard differs from catalogue H.G. Trenchard; record discrepancy, do not silently resolve initials. Catalogue circa 1911; exact legal boundary date unconfirmed. Source https://www.flickr.com/photos/uon/6019951002/ .
- Full map visually reviewed. Catalogue describes a Xerox copy; scan is severely faint/yellow with dark edge bands. High pixel dimensions do not restore lost line contrast. Council perimeter sections remain visible but require corroboration before precise tracing. Original preserved without enhancement; UON personal-study/research use applies, other reproduction needs permission.
- Four other original images inspected but not added to raw: M4631 (6019950140), Oct–Nov 1910 Royal Engineers topographic map, transport/contour legend but no explicit LGA lines confirmed; M4635 (6019953304), 1884 partial-city photocopy, no explicit municipal outline confirmed; M4444 (6003427679), three certificate-of-title parcels with surface/coal ownership edging, not parish/LGA outlines; M4661 (6019959368), DP215203 sheet 2 school-site property plan, 1959 catalogue, later reproduction/conversion markings, Lake Macquarie Shire label not a council perimeter. All stay in exploratory review storage.
- Public Map Treasures album pages 1–4 saved. Embedded-title associations were initially off by one; corrected provisional records use the preceding title, and the five selected titles/dates were verified on individual public catalogues. Other album entries remain provisional and not visually reviewed; do not propagate inferred titles into source records. These four pages do not prove the whole UON map collection is exhausted. Evidence: `uon_map_treasures_provisional_records.json`, individual catalogue/sizes HTML, fetch metadata and `uon_album_sample_map_review.json`.
- New raw hash, exact bytes, decoded native dimensions/readability pass. All 686 registered paths and sizes pass; no identical new source hash. Collection: 686 files, 3,194,486,462 bytes. No live fetch job; wider NSW LGA discovery active. No new codebase decisions or final report assets. Next: other UON parish/council map entries with explicit LGA lines; original 1918 Craigie remains unresolved.

## UON Newcastle parish sheet: LGA search, 11 October 2026

- Saved full original UON M3011, Parish of Newcastle, County Northumberland, Sheet 2. Catalogue circa 1950s; printed improvement-works annotation reads Gaz. 13th August 1954. This is an annotation date, not a verified council boundary date.
- Lake Macquarie Shire is labelled below the southern dash/cross line. This line coincides with the Kahibah parish edge. Retained as a parish map with an LGA edge; it does not show a complete council perimeter. Do not treat all cadastral, parish, reserve or population-area lines as LGA lines.
- Original JPEG: 12,222 × 10,486 pixels; 8,055,566 bytes. Folds and dense cadastral detail limit tracing. No image enhancement or crop saved in raw. UON study/personal-research conditions apply. Catalogue: https://www.flickr.com/photos/uon/5907793120/
- Reviewed but excluded: M4665 Kahibah fourth edition, 5 March 1891 (parish/reserve/town/suburban/population legend; no municipal outline confirmed); M2148 Sydney rail/tram map, 1913 (red tram routes, no municipal outline confirmed). Originals and catalogue evidence remain review-only in the downloader output folder.
- Verification: new source hash, bytes, dimensions and decoded readability passed; all 687 registered paths and sizes passed. Total 3,202,542,028 bytes. No live fetch job. Wider LGA discovery continues.

## Greater Sydney Royal Commission map: 11 October 2026

- Saved State Library original `state_library_nsw/greater_sydney_1913_royal_commission_proposal.jpg`, 5,669 × 9,270 pixels, 10,325,307 bytes. J. Marshall, Department of Public Works; title recommendations 1913, catalogue [1913], published in the commission report in 1914 according to catalogue. https://collection.sl.nsw.gov.au/record/74VvpM8G0XLy
- Whole scan and native legend/central detail reviewed. Red is the first inner-zone step, yellow the second inner-zone step and blue the outer zone. These are recommendations; no legal proclamation established. Dotted council outlines and named shire ridings are useful underlying geography. Ridings are internal divisions, not extra councils. Exact council boundary currency not independently confirmed. Scan colour is faded but line work is readable. Original preserved unchanged.
- Three UON originals pending HTTP 429: Stockrington 1902 (5982538621), West Wallsend/Teralba circa 1920s (6003423765), Kahibah circa 1920s (6003968668). Individual catalogue titles and public original links saved; images not inspected or counted. One later retry of Stockrington also returned 429. No live fetch process.
- New archive leads: NRS-10176, Western Coal Fields, 22 February 1923, X1049 explicitly lists municipal boundaries; NRS-10182 Greater Newcastle locality sheets, 1943–1944, 37 maps, many annotated with ward lines. No scans retrieved. The municipal-boundary description applies to Western Coal Fields, not the adjacent undated Maitland Cessnock Greta record. Source guide: https://concise.mhnsw.au/lo/mines009.htm .
- New original passed hash, byte size, decoded dimensions/readability and catalogue dimension match. All 688 paths and sizes passed. Collection: 688 files, 3,212,867,335 bytes. Evidence and pending source list: `greater_sydney_1913_and_pending_map_review.json` in downloader output.

## Redfern 1889 and Sydney 1854 original maps: 11 October 2026

- Plan of the municipality of Redfern: compiled from the latest official records [cartographic material] / New South Wales Map Publishing Co., Gibbs, Shallard & Co., lithographers. Printed July 1889; catalogue 1889; legal boundary currency unconfirmed. Source image contains two cut sections side by side. Perimeter labelled with Darlington, Alexandria, Waterloo, Woollahra and City of Sydney; survey/parcel edges remain separate. Legend red lines are sewers; building fills represent materials. No stitched derivative created. Original 10000 × 4145 pixels; 15,742,168 bytes. Source: https://collection.sl.nsw.gov.au/record/74Vv3OlEmZAg
- Map of Sydney and suburbs 1854 [cartographic material]. Printed and catalogue 1854; legal ward boundary currency unconfirmed. Catalogue explicitly identifies city ward boundaries. Whole map and native central detail reviewed: faint red/yellow ward lines on street base. Ward names not confirmed from this scan; do not invent names from colour. Tears and loss at folds/edges limit tracing. Key 45 numbers identifies buildings, not wards. Original 4987 × 6000 pixels; 10,083,724 bytes. Source: https://collection.sl.nsw.gov.au/record/74VvkQky638Z
- Both originals saved unchanged. New hashes, bytes, image decoding and catalogue dimensions pass; hashes unique. All 690 registered paths/sizes pass. Collection: 690 files, 3,238,693,227 bytes. No live fetch job. No new codebase decisions or final report assets. Three earlier Flickr originals remain pending; NRS-10176 permalink unavailable through web tool, no archive scan retrieved.

## Sydney population maps with council lines: 11 October 2026

- Metropolitan municipalities showing distribution of population [cartographic material] scale 1 mile to an inch / prepared by H. E. C. Robinson, Wentworth Court, Elizabeth St, Sydney, 1897. Printed and catalogue 1897; legal council boundary currency unconfirmed. Heavy municipal perimeters, council names and acreage/population text; unincorporated police districts are explicitly labelled and are not councils. Blue figures are approximate inhabitants per acre. Railway, water-supply and finer dotted lines are not council outlines. No population statistics extracted or validated. Original 6000 × 4491 pixels; 8,218,125 bytes. Source: https://collection.sl.nsw.gov.au/record/74Vv4V0OqpbM
- Map of Sydney and suburbs [cartographic material] : showing density of population in the year 1921. Catalogue 1921; year space in printed title blank; legal council boundary currency unconfirmed. Catalogue explicitly describes municipal boundaries. Red outlines on river/coast base; council names absent, so identities need another dated source. Each dot represents 100 persons; dot pattern is not a boundary. Catalogue compares a Waverley figure to 1921 and December 1922 statistics; this does not establish boundary currency. No population statistics extracted or validated. Original 6000 × 5195 pixels; 9,444,064 bytes. Source: https://collection.sl.nsw.gov.au/record/74VvOXLev2K3
- Both originals unchanged. New hashes, exact bytes, decoded image readability and catalogue dimensions pass; no identical source hash. All 692 registered paths/sizes pass. Collection: 692 files, 3,256,355,416 bytes. No live fetch job. Review record: `slnsw_sydney_population1897_1921_map_review.json` in downloader output. No new codebase decisions or final report assets.

## Robinson City of Sydney Map No. 4: 11 October 2026

- Saved full original map and street-index verso from https://collection.sl.nsw.gov.au/record/74VKq8WmQGm3 . Catalogue [1948], but Sydney-by-decade guide places this record under 1952. Date conflict unresolved; no exact legal boundary date confirmed. Catalogue uses trolleybus service evidence for dating; not independently verified.
- Explicit municipal-boundary dash/dot legend inspected; it differs from grid dashes, rail/tram and bus/trolleybus route lines. Municipal and locality names have different type styles. Native eastern detail shows council line near Woollahra/Paddington. Partial council geography only. Index is a reference sheet, not a second boundary map.
- Map original 6,003 × 8,700, 19,201,217 bytes; index 5,983 × 8,710, 15,230,696 bytes. Both unchanged. No persistent enhancement, rotation or stitching.
- Reviewed but excluded: two County of Cumberland planning-scheme copies, representation of 27 June 1951 ordinance, reprinted 1956. Whole scans and native legend inspected: land-use zones, county roads and railways; no confirmed LGA lines. Black road lines and zone edges are not LGA boundaries. Catalogue: https://collection.sl.nsw.gov.au/record/74Vv72MJK33l . Originals remain review-only in downloader output.
- Stockrington 1902 original retry returned HTTP 429; three prior UON candidates still pending. No live fetch job. New map/index hashes, exact bytes, decoding and catalogue dimensions pass; no duplicate new hash. All 694 paths/sizes pass. Collection: 694 files, 3,290,787,329 bytes. Evidence: `slnsw_robinson_map4_cumberland_plan_review.json`.

## East Orange wards and Newcastle council panels: 11 October 2026

- Saved unchanged East Orange borough plan, 9,747 × 10,000 pixels, 25,485,324 bytes. Printed borough proclamation 4 April 1888; ward proclamation 15 May 1888. Northwest, Southwest and East wards named. Later red annotation: union with Municipality of Orange, Gaz. 24.12.12. Proclamations not independently verified. Borough dash/cross and internal ward dashes differ from parcel lines. Source: https://collection.sl.nsw.gov.au/record/74VKwlp0Jvm3
- Saved four unchanged Robinson Newcastle and suburbs panels, printed I–IV. One map, not four editions. Catalogue [Between 192-? and 1947?]; exact publication/legal boundary dates unresolved. Native legend explicitly identifies municipal lines; council names include former Newcastle municipalities, Tarro and Lake Macquarie shires. All panels 10,000 pixels wide; heights 7,630, 7,338, 7,510 and 7,511. No stitching, enhancement or georeferencing. Source: https://collection.sl.nsw.gov.au/record/74VKwlXjwEjA
- Reviewed but excluded Maitland plan, catalogue 1842–1850: title supplied by cataloguer; parcel holdings and municipality gazette stamp do not confirm an LGA perimeter or boundary date. Original remains review-only. Source: https://collection.sl.nsw.gov.au/record/74VK24NqOlQX
- Five new original hashes, byte sizes and decoded native dimensions/readability pass; no duplicate new hash. All 699 source paths/sizes pass. Collection: 699 files, 3,376,014,321 bytes. No live fetch job. Regional Bathurst and Maitland queries each returned all 18 results; Newcastle returned 20 of 39, with the second page still pending. Three earlier Flickr originals remain rate-limited. Evidence: `slnsw_regional_orange_newcastle_map_review.json`.

## Macdonaldtown wards, 1954 NSW LGAs and Western Coal Fields: 11 October 2026

- Saved Macdonaldtown plate 27, catalogue [189-?], distinct physical-copy scan at 4,632 × 6,938 pixels. Same map edition already represented by NLA at 3,034 × 4,310; count as another scan, not a new edition. Explicit municipal and ward legend; North, Middle and South wards. Stamp 20 September 1966 is not map date. Exact legal boundary currency unconfirmed. Source: https://collection.sl.nsw.gov.au/record/74VKDapOqKN3
- Saved NSW statistical divisions sheet, 1954, 9,572 × 8,270 pixels. Printed note states LGA geography used in Commonwealth Census of 30 June 1954. Legend separates shire outlines, municipal towns, non-municipal towns, statistical divisions and red statistical retail areas (1953). Statistical divisions are not identical to census divisions. Newcastle and Cumberland insets included. Map refers to overleaf LGA number index; catalogue supplies only map image, so index was not retrieved. Source: https://collection.sl.nsw.gov.au/record/74Vv58KgalGA
- Saved two distinct physical copies of Western Coal Fields map, printed 9 November 1906, 6,605 × 10,000 and 5,881 × 8,953. Native municipal-line legend and Lithgow municipal outline inspected. County/parish/coal holdings differ. Second copy has red manuscript additions; dates/meaning not established. Two scans of one edition, not two dates. This is not the NRS-10176 1923 edition. Dense parcel and mine detail limits tracing. Source: https://collection.sl.nsw.gov.au/record/74VvQz8y7P4b
- All four originals unchanged. New hashes, exact bytes, decoded dimensions/readability and catalogue dimensions pass; no identical new hash. All 703 registered paths/sizes pass. Collection: 703 files, 3,439,401,351 bytes. Full Newcastle search returned all 39 results with limit=50; page=2 repeated first 20. Two remaining digitised leads recorded for next batch. No live fetch job. Three earlier Flickr originals remain rate-limited. Evidence: `slnsw_macdonaldtown_1954_western1906_map_review.json`.

## Southern Sales NSW shires 1907 and Sydney wards 1881: 11 October 2026

- Saved full 1907-catalogue Southern Sales Company NSW map, 7,540 × 10,000 pixels, 33,141,712 bytes. Native legend: shires in colours; municipalities green with dotted outline; separate transport symbols. Statewide shire index and town-population table present; figures not extracted/validated. Sydney and Newcastle insets mainly locality/transport detail; complete municipal outlines not confirmed there. Catalogue publisher W. and A.K. Johnston differs from printed compiled/published Southern Sales Company; attribution not silently resolved. No exact legal boundary date established. Source: https://collection.sl.nsw.gov.au/record/74Vvz8E8BREZ
- Saved full Australian Hand Book Sydney map, printed 1881, 7,643 × 10,000 pixels, 21,705,481 bytes. Native legend explicitly identifies municipal ward dash/dot lines; Gipps, Brisbane, Bourke, Macquarie, Cook and Phillip labels visible. Street/park edges differ. Partial city extent, not complete metropolitan council division. Donation stamp 1965 is not map date; legal boundary currency unconfirmed. Source: https://collection.sl.nsw.gov.au/record/74Vvez3L7xoy
- Originals unchanged. New hashes, exact bytes, decoded native/catalogue dimensions and readability pass; no identical new hash. All 705 paths/sizes pass. Collection 705 files, 3,494,248,544 bytes. Goulburn 8/8 and Wagga Wagga 10/10 catalogue results reviewed; no new digitised LGA maps found. Subdivision/test records excluded. Evidence: `slnsw_1907_shires_1881_wards_map_review.json`.

## NSW proposed shires 1905, shires/ridings 1906 and local council sheets: 11 October 2026

- Saved all 10 digitised proposal sheets A–G, J–L from https://collection.sl.nsw.gov.au/record/74VKZbOEB4kO . 1905 Royal Commission proposals; red shire borders, blue electoral borders, excluded municipalities separately shaded. Do not treat proposed lines as proclaimed geography. H/I absent here. Catalogue general A–K designation conflicts with held/image list through L; use visually confirmed letters. Not a complete original series.
- Saved all 11 digitised shire/riding sheets C–G, J–O from https://collection.sl.nsw.gov.au/record/74VKZbKAmN8b . Catalogue publication 1906, Act title 1905. Solid red shire borders; red dashed internal ridings A/B/C; municipalities excluded and shaded. Ridings are not extra councils. Exact legal proclamation currency not independently checked. A/B/H/I absent here; not a complete original series. Sydney-area sheets G/J, Hunter N, and other regional sheets have distinct coverage. All held originals kept separately, without stitching.
- Blaxland schematic shire/road sheet, catalogue [194-?], 6,071 × 10,000. Dash/dot edges with neighboring councils; blue manuscript notes are not verified boundary changes. Exact production/annotation dates unresolved. Source: https://collection.sl.nsw.gov.au/record/74VMxw5rxZwX
- Colo Shire sheet, catalogue between 1920 and 1947, 6,208 × 7,037. Native legend distinguishes triple-cross shire edges from single-cross riding edges; A/B/C ridings. Catalogue dates from publisher corporate name, not verified legal geography. Catalogue county Monteagle statement conflicts with mapped Hawkesbury geography; do not use it for spatial assignment. Source: https://collection.sl.nsw.gov.au/record/74VKZwD6EDpZ
- Mulgoa municipal district, printed 9 August 1894, 7,287 × 10,000. Native legend separates municipality dash/cross, parish dash/dot and Crown grants. Exact legal boundary currency unconfirmed. Source: https://collection.sl.nsw.gov.au/record/74Vv7MpdlBZg
- All 24 unchanged originals pass new SHA-256, bytes, decoding, native/catalogue dimensions and hash uniqueness. All whole scans reviewed, representative series and individual native legends inspected. All 729 registered paths/sizes pass. Collection: 729 files, 4,009,551,345 bytes. No live fetch job. First 50 of 5,972 shire query matches reviewed; Penrith all 15. Wider query not exhausted. Two single-image series leads pending; three prior Flickr originals remain rate-limited. Evidence: `slnsw_shire_series_colo_blaxland_mulgoa_review.json`.

## 1906 sheet P and additional proposed sheet G copy: 11 October 2026

- Added new 1906 printed sheet P: Warringah 131 and Ku-ring-gai 134 shires and ridings, 6,076 × 10,000, 17,063,198 bytes. Department of Lands imprint Sydney 1906. Solid red shire outlines; dashed internal riding lines A/B/C. Exact proclamation currency unconfirmed; donation 1976 is not map date. Now 12 distinct 1906 sheets held, C–G/J–P; no complete-series claim. Source: https://collection.sl.nsw.gov.au/record/74Vv7lO6OPgg
- Additional damaged physical copy of 1905 proposal sheet G, 6,829 × 10,000, 25,605,764 bytes; same sheet edition already saved. Native legend: shires solid red, electorates blue, municipalities red dashed, areas added to municipalities hatched. Additions remain proposals; not independently established as legal changes. Hunters Hill/Darlington diagrams; torn/stained margins. Source: https://collection.sl.nsw.gov.au/record/74Vv72K75bvA
- Both originals unchanged. New hashes, exact bytes, decoded native/catalogue dimensions and readability pass; no identical source hashes. All 731 paths/sizes pass. Collection 731 files, 4,052,220,307 bytes. First 100/5,972 shire-boundary matches reviewed; next 50 only add digitised Yarrawonga outside agreed NSW scope, not retrieved. Evidence: `slnsw_shire_sheet_p_and_proposed_g_review.json`.

## Cumberland native original, Newcastle 1951 and Sydney traffic maps: 11 October 2026

- Cumberland 1905 proposal Map II full native original: 6,656 × 10,000, 23,466,885 bytes, twice old 3,328 × 5,000 dimensions. Same source previously represented by FL8787726, not a new edition. Old raw unchanged. Native legend: green altered municipal outlines/added areas and red shires; title specifies proposals. Manly addition inset. Proposal is not independently verified proclaimed geography. Source: https://collection.sl.nsw.gov.au/record/74VKZ420MmZM
- Newcastle region communications, printed second edition and information April 1951; catalogue [1951?], 10,000 × 6,030, 15,836,310 bytes. Native legend distinguishes heavy regional border from thin dashed/triple-cross shire borders. Kearsley, Lake Macquarie, Lower Hunter, Port Stephens and other named shires; partial extents. Red main roads, green rail and proposed rail are not council borders. Exact legal boundary currency unconfirmed. Source: https://collection.sl.nsw.gov.au/record/74VKZdgg5OqO
- Sydney traffic map, catalogue [1922], two physical copies: 6,252 × 10,000 (21,398,704 bytes) with attached index; 7,063 × 10,000 (25,039,231 bytes) with separate complete index strip 10,000 × 1,949 (5,317,035 bytes). Native legends identify municipal/shire names and area tints; tint edges are faint under route/street detail. Orange dashed state electorates, green parks/reserves and coloured routes differ. AMP stamp 2 August 1922 supports copy dating, not exact legal boundary currency. No independent proof these are different editions. Sources: https://collection.sl.nsw.gov.au/record/74VKv6v6XWqA and https://collection.sl.nsw.gov.au/record/74VKVoG6ZV4b
- Reviewed but excluded: first traffic holding blank verso; second holding three fabric backs, a blank reverse and partial index where complete index saved. Seven catalogue images are not seven maps. All originals reviewed unchanged; no enhancement/stitching.
- Five new original hashes, bytes, decoded native/catalogue dimensions and readability pass; unique new hashes. All 736 paths/sizes pass. Collection 736 files, 4,143,278,472 bytes. Division/ridings all 8 results and proposed-shires all 54 reviewed. Evidence: `slnsw_cumberland_full_newcastle1951_traffic1922_review.json`.

## Sydney Mail wards, Bankstown, Five Dock and Strathfield: 11 October 2026

- Sydney Mail ward map, 7,950 × 10,000, 27,661,170 bytes. Catalogue 1878 but catalogue/handwritten date note between 1878 and 1881; exact publication/legal currency unresolved. Native municipal ward dash/dot legend; six ward names/base also seen in 1881 handbook, different publication not established changed geography. Faint with surface loss. Source: https://collection.sl.nsw.gov.au/record/74VvezJVxJoX
- Bankstown municipal south sheet, 5,000 × 3,121, 5,184,860 bytes. Catalogue [19--?] versus time-period tags 1898–1904; unresolved. Incomplete copy, two physical sections mounted together; full council extent not available. Native municipal cross/dash, parish and ward legend; purple manuscript lines not confirmed LGA changes. Source: https://collection.sl.nsw.gov.au/record/74VKZMODlA2Z
- Five Dock partial municipal plan, 5,312 × 10,000, 13,246,294 bytes. Printed proclamation 18 January 1890; catalogue 1890; legal proclamation not independently checked. Cross/dash line near T. Casey/Lyons Road differs from parcel edges; full legend not confirmed. Left margin missing, no complete perimeter claim. Source: https://collection.sl.nsw.gov.au/record/74VKw0ZZ5ga3
- Strathfield annexation plan, 6,239 × 10,000, 21,395,703 bytes. Catalogue 1890; mapped Enfield annexation annotation January 1891, unresolved date conflict. Native Strathfield proclamation 2 June 1885 and Rookwood necropolis dedication 2 December 1887 also visible; dedication is not council-boundary date. Dash/cross council lines and adjoining council labels; extreme faintness and surface loss limit tracing. Proclamations not independently verified. Source: https://collection.sl.nsw.gov.au/record/74Vv7BbpdWQy
- All four raw originals unchanged. New hashes, exact bytes, decoded native/catalogue dimensions/readability and uniqueness pass; all 740 source paths/sizes pass. Collection 740 files, 4,210,766,499 bytes. No live fetch job. Generic municipal search first 100 of 1,031 reviewed; 25 direct NSW candidates triaged, four now saved, 21 still unreviewed originals. New catalogue ids may duplicate existing sources. Hornsby 28/28 and Windsor 19/19 searches yielded property/subdivision leads only; no new direct LGA record selected. Wider search incomplete. Evidence: `slnsw_sydney_mail_bankstown_fivedock_strathfield_review.json` and `slnsw_municipal_search100_triage.json`.

### Sydney council original scans: seven sources (11 October 2026)

- Added 12 unchanged SLNSW originals: Manly [1886], Leichhardt [1888] (two sheets plus source combined scan), Paddington 1880, Willoughby 1890 (two sheets), Dundas not before 1920 (two sheets), Redfern 1864 and Botany [1895] (colour copy and monochrome tracing). These are seven council sources, not 12 editions.
- Manly municipal cross/dash symbol verified. Leichhardt dashed ward legend verified; paper cracking and damage affect line reading. Paddington ward labels and tints visible; full symbol legend not found. Redfern red perimeter separates Sydney and Waterloo; foxing and paper loss remain.
- Willoughby and Botany legends distinguish cross-dashed municipality lines, dashed ward lines and grant lines. Willoughby 1890 title also appears in the existing NLA holding; a new edition is not established. Botany tracing is another physical copy of the same map.
- Dundas legend records proclamation 18 June 1891 and boundary alteration in Terrys Estate, 13 August 1916. These notes do not date publication; retain the catalogue's not-before-1920 date. Parish/grant lines are separate symbols.
- Manly/Leichhardt dates are catalogue estimates. Botany [1895] is estimated from a 1894 street alignment notice, not an exact boundary validity date.
- Balmain 1882 Addison street plan remains review-only: no explicit council or ward boundary symbol found.
- Review and source metadata: `explore/output/2026-10-10_download-boundary-maps/slnsw_seven_sydney_councils_original_review.json`. All 752 registered paths/sizes pass; 12 new original hashes and decoded/catalogue dimensions pass. Raw originals remain unchanged. Collection: 752 files, 4427651950 bytes. Thirteen municipal catalogue candidates remain unreviewed.

### Canterbury, Burwood, Sands and NSW municipal plans (11 October 2026)

- Canterbury native municipal plus/dash legend differs from parish x/dash and grant lines. Copy 0 annotated Charted to 30 September 1886; catalogue signature 7.12.87 differs from faint native reading, left unresolved. Copy 1 copyright stamped June 1884. Neither inscription establishes exact legal boundary currency.
- Burwood second edition municipal plus/dash and ward dash legend verified. Proclamation 27 March 1874 and street-name Gazette 17 June 1885 are historical notes; publication catalogue [1893?]. Monochrome copy has later blue manuscript property notes and paper loss.
- Sands 1894 native legend municipalities shown in colour; penny postage area, rail and tram lines are separate features. Damage at upper right affects northeast extent. Statistical table has explicit corrections for Erskineville/Mosman; do not use it as an unqualified 1894 census table.
- Shoalhaven native legend: petitioned x/dash versus proclaimed dash/dot. Two physical copies, hand-colour is additional annotation not a new proclaimed boundary. Catalogue 1859 versus ordered printed 20 January 1860: retain both.
- Quirindi faint x/dash perimeter verified along South Street, surrounding west/east limits; catalogue explicitly municipal boundaries. Paper loss and faintness matter. Nyngan distinctive x/dash outer envelope visible; no full symbol key found; parish/county labels are not council names.
- Gerringong, Walcha and South Shoalhaven originals retained in review only. No municipal symbol key found; prominent cadastral/parish lines must not be assumed council boundaries. Walcha title/catalogue search says 1899, native title and publication metadata read 1889. Date conflict documented without changing raw source.
- Nine unchanged originals saved from six sources. Collection 761 files, 4611581677 bytes. All registered paths/sizes and nine new hashes/dimensions pass. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_canterbury_burwood_sands_shoalhaven_regional_review.json`. Four direct municipal catalogue records remain unreviewed.

### Katoomba, Lithgow and Blacktown history maps (11 October 2026)

- Katoomba proof: native 20 November 1890 proof stamp. Municipal plus/dash versus parish x/dash and grant dash/dot legend verified. Not a certified boundary effective date.
- Katoomba catalogue [1891] holding adds frame, grant details and explanatory terms. Two sheets plus library combined scan per holding are six files from two source maps, not six editions. No change in council geometry established between holdings.
- Lithgow 1933 bold perimeter separates Blaxland Shire from municipality; streets and railway distinct. Catalogue states signature R.H., 28 October 1933. Municipality touches scan edges at north; no full symbol legend.
- Portland source is Victoria, Melbourne Department of Crown Lands and Survey 1863, not NSW. Review-only and excluded from raw. Initial catalogue title did not disambiguate state.
- Blacktown reports: Horne 2023 PDF page 28 (printed 27), Horne 2018 PDF page 5. Both reproduce same later historical reconstruction credited to Gerard Imer 2014. Map title depicts 1914–1918, while 2018 caption says 1913. Retain conflict, not two independent historical geographies. Riverstone exclusion note and adjoining municipalities present. Full PDFs preserved, no extraction/cropping in raw.
- Blacktown SLNSW shire query returned all 12 matches: three parish maps already covered by NLA, municipal traffic map already saved, subdivision plans and undigitised archival map/business records. No new direct shire original selected from this query.
- Added nine source files. Collection 770 files, 4750150820 bytes. Nine new hashes/bytes, seven JPEG native dimensions and two PDF page counts pass; all registered paths/sizes pass. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_katoomba_lithgow_blacktown_review.json`. Municipal first-100 candidate batch reviewed, not entire catalogue.

### Blacktown Memories council-boundary sheet (11 October 2026)

- Node 68 catalogue title Parish of Rooty Hill, Municipality of Blacktown, but printed sheet is Municipality of Blacktown AD301. Partial cadastral sheet, not a full parish/council outline.
- Catalogue explicitly identifies Blacktown/Penrith boundary. Whole scan shows adjacent PENRITH and BLACKTOWN labels and boundary along Ropes Creek; property lines, Commonwealth property and Housing Commission parcels are not interchangeable with council boundaries.
- Downloaded original 012398.jpg, 1933 x 1536 pixels; lower resolution than many SLNSW scans. Original filename and dimensions confirmed by download page. Unchanged bytes preserved.
- Catalogue 1976; text states originally January 1967, amended/replaced 10 August 1976. No exact legal boundary effective date established.
- Node 207 map240 has 1976 catalogue date but no clear municipal boundary in reviewed preview; no original added. Node167 January1965 coloured population/dwelling areas are not verified council/suburb boundaries. Node8298 catalogue August1968, native September1970 print noted; town-development sheet1/2, no explicit council boundary found. Both originals retained review-only.
- Blacktown Memories public original download works through browser /nodes/download/{id}, then first /assets/downloadwiz/ link. Direct requests returned small forbidden pages; do not count these or use max previews as originals.
- Further bounded lead: Blacktown Shire planning-scheme 1957 sheets and council-subject map browse; public browse lists 32 shire-council and 34 municipal-council subject maps, mostly cadastral/planning sheets.
- Collection: 771 files, 4752309952 bytes. New original hash/bytes/dimensions and all registered paths/sizes pass. Review: `explore/output/2026-10-10_download-boundary-maps/blacktown_memories_boundary_review.json`.

### Blacktown 1957 boundary sheets (11 October 2026)

- 1957 sheet301 (node8276, M313) shows Blacktown/Penrith labels on opposite sides of Ropes Creek. Partial council boundary, not full shire outline. Property/Commonwealth and road reservation lines are separate.
- 1957 sheet390 (node8139, M287) shows Blacktown/Holroyd labels and cross/dash council line along Great Western Highway/Church Lane area. Local roads, future motorway corridor and reservoir shoreline are not all council boundaries.
- Both originals match public download advertised pixel dimensions and are unmodified. Catalogue May1957 is map date, not legal boundary effective date.
- Correction: 1976 node68 sheet301 boundary is at Ropes Creek, not South Creek. Previous review/data note amended; original map unchanged.
- 1914 annual report node13480 (12 pages), 1961 information booklet node20274 (8 pages), 1930s pamphlet node19613 (one sheet) and 2020 councillor list node11538 (5 pages) reviewed; no boundary maps found. All four retained review-only, not counted as boundary downloads.
- Map type filter confirmed from catalogue link: ntids [3]. Shire council map-subject first page has 24 entries, 2 now reviewed and saved. Other22 plus later browse page remain unreviewed. ntids14 was oral history and yielded one irrelevant result; corrected search overwrites earlier candidate file.
- Two originals added. Review: `explore/output/2026-10-10_download-boundary-maps/blacktown_1957_boundary_sheets_review.json`.

### Blacktown Shire full outline and further1957 sheets (11October 2026)

- Node64 full shire street map, Robinson, catalogue1930s. Native legend: shire dash/dot line, riding dashed line, railways and roads separately keyed. A/B/C are ridings, not separate councils. Original1774x1536 limits fine-line digitising accuracy. Folds/paper wear retained.
- Native notes list shire boundaries altered7August1912,4November1927,30December1927,11May1928; ridings altered5February1913,4November1927,30December1927,13July1928. These historical dates do not establish exact map publication or legal validity.
- 1957 sheet280 node8274 shows Blacktown/Penrith partial western boundary near South Creek/Ropes Creek, with Penrith label upperleft. Shire limit is only part of map; watercourse outlines and land parcels are not interchangeable with council lines.
- 1957 sheet391 node8140 shows Blacktown/Holroyd labels either side of council boundary near Wentworth Avenue/railway. Partial limit, not full LGA outline.
- 1957 sheets281(node8275),219(node8264),262(node8141),389(node8137) retained review-only: no sufficiently clear municipal line found. Sheet389 conspicuous dashed line at upperleft follows land/road feature, not confirmed council line.
- All32 Blacktown Shire map-subject records now listed across24+8 browse entries. Nine records reviewed cumulatively: node64 plus eight1957 sheets; five sources saved in this catalogue batch cumulatively, four review-only. Twenty-three other records await review. Second-page browse was navigated through actual next-page button; page2 includes new record IDs.
- Three originals added; collection776 files,4758057450 bytes. New hashes/advertised dimensions and all registered paths/sizes pass. Review:`explore/output/2026-10-10_download-boundary-maps/blacktown_shire_streetmap_and_sheets_review.json`.


### Further Blacktown 1957 council boundary sheets — 11 October 2026

Five unchanged original Cumberland County Council planning sheets, catalogue/printed base map May 1957. These show partial council limits; the publication date does not establish the legal boundary effective date.

- Node 8279, sheet 322, Blacktown–Penrith: Council labels straddle Ropes Creek near St Marys; partial western boundary. Original 2038 × 1536 pixels.
- Node 8135, sheet 198, Blacktown–Windsor: Council labels and marked boundary near Bandon Road/Windsor Road, Vineyard; main sheet and inset. Original 2030 × 1536 pixels.
- Node 8272, sheet 370, Blacktown–Holroyd: Council labels and plus/dash line across Toongabbie Road near Cornelia Road; partial boundary. Original 2048 × 1440 pixels.
- Node 8271, sheet 327, Blacktown–Baulkham Hills: Council labels either side of marked boundary along Old Windsor Road near Seven Hills Road. Original 2048 × 1479 pixels.
- Node 8270, sheet 348, Blacktown–Baulkham Hills: Council labels either side of marked Old Windsor Road boundary near Abbott Road/Toongabbie Creek. Original 2048 × 1451 pixels.

Nine other originals inspected but kept review-only: 8280, 8278, 8277, 8273, 8134, 8133, 8132, 8124, 8123. Interior parcel, road and watercourse lines are not sufficient evidence of an LGA boundary. Node 8136 download options returned HTTP 405; retry remains pending. Review: `blacktown_1957_further_boundary_sheets_review.json`. All 781 registered file paths/sizes pass; five additions pass unique SHA-256 and advertised pixel dimensions.

Final catalogue check: node 8136 retry succeeded; sheets 323 (8136), 388 (8143), 304 (8142), 345 (8138) show interior areas without a sufficiently clear council boundary and remain review-only. Five records (8269, 8268, 8267, 8266, 8265) returned HTTP 405 and remain unreviewed. Cumulative Blacktown Shire map catalogue triage: 32 records, 10 saved, 17 review-only, five pending. No fetch jobs remain live. The collection remains 781 registered files (4,763,926,815 bytes); these include companion/index files and are not 781 distinct council boundary editions.


### Randwick, Concord, Hurstville and remaining Blacktown maps — 11 October 2026

Twelve unchanged original images added. Boundary evidence:

- https://blacktownmemories.recollect.net.au/nodes/view/8269: Council labels on opposite sides of Ropes Creek; partial western shire limit.
- https://blacktownmemories.recollect.net.au/nodes/view/8268: Council labels and plus/dash boundary along Junction Road; coloured property annotations retained unchanged.
- https://collection.sl.nsw.gov.au/record/74VvN0J75dp3: Title explicitly identifies Government Street as City of Sydney municipal boundary. Short local section only; sale lots are not council boundaries.
- https://collection.sl.nsw.gov.au/record/74Vv3W7Vk0Mg: Native legend separates municipal plus/dash lines, ward dashed lines and Crown grant dash/dot lines. North, middle, south sheets and library combined image are the same physical map, not four editions. Catalogue date estimated from Bunnerong Road deviation and land dedication at Shark Point.
- https://collection.sl.nsw.gov.au/record/74Vv3rVw4ygM: South-sheet native legend explicitly keys municipal plus/dash boundary, separate from Crown grant lines. Three images are north/south sheets and library combined view of one physical map. Adjacent council names include Strathfield, Burwood and Five Dock.
- https://collection.sl.nsw.gov.au/record/74VMb7kQBbrO: Southern boundary is marked by plus/dash lines beside Paddington, Randwick and Waverley labels. Native notes key Crown grants and fences, but do not separately key the municipal line. Library date estimated from publisher address and street renaming evidence. Folds and faint print remain unchanged.
- https://collection.sl.nsw.gov.au/record/74VKDVj6y3qO: Native title and legend explicitly identify proposed municipal boundary shown with red tint. Neighbours labelled Canterbury, West Botany and Kogarah. Proposal is not evidence of an adopted boundary; exact proposal date unverified.

Review-only sources: Parramatta 1938 tourist map, Field of Mars 1885 land sale plans (two holdings), Manning tourist tours 1940s, Glebe 1888 building map, North Willoughby Leigh map (catalogue 1865–1890). No sufficiently clear LGA line verified. Blacktown nodes 8267 (sheet 392), 8266 (371), 8265 (303) also remain review-only: municipal labels or plus/dash features do not establish an unambiguous boundary on these inspected sheets.

All five Blacktown HTTP 405 retries succeeded. The complete 32-record subject-filtered map catalogue has 12 saved and 20 review-only records; this does not prove the whole council archive is exhausted. Library searches return only the first 100 records: municipality has 1,028 matches, council boundary has 220. Search results are leads, not verified map counts.

Verification: 793 registered files; all paths/sizes pass. Twelve additions pass unique SHA-256 and decoded catalogue/advertised dimensions. Review: `slnsw_randwick_concord_hurstville_blacktown_review.json`. Original sheets and source combined scans are not separate boundary editions.


### Woollahra, Ashfield, Camden, Petersham, Ryde and Hunters Hill — 11 October 2026

- https://collection.sl.nsw.gov.au/record/74VMbRpEeGNb: Catalogue 1924; office copy annotated July 1919–January 1924. Native legend explicitly keys municipal plus/dash line, distinct from Crown grant/fence lines. Catalogue describes cancelled office copy and ink charting from 1 July 1919 to 1 January 1924. Native notes record Vaucluse separation and ward reproclamation in 1895; these historical notes are not the publication date.
- https://collection.sl.nsw.gov.au/record/74Vv3aBB7Gzd: Printed/catalogue April 1883. Native legend keys municipal dash/cross lines, ward dashes, parish dash/dot and estate-section boundaries separately. Prepared for municipal council. Folds, paper wear and faint print retained.
- https://collection.sl.nsw.gov.au/record/74VKwgwaqM8Z: Catalogue 1889; printed proclamation 6 February 1889. Native title and legend explicitly mark municipality boundary with dash/cross line. Printed proclamation date is 6 February 1889; catalogue publication is 1889. Top-left paper loss recorded by library and retained. Parish/county boundaries and allotments are distinct.
- https://collection.sl.nsw.gov.au/record/74VM0z46kQab: Printed May 1887; catalogue 1887. Native legend keys municipal plus/dash line and ward dashes. Adjacent municipalities Ashfield, Leichhardt, Camperdown, Newtown, Marrickville and Canterbury are named. Blue/green ward tints are not separate councils.
- https://collection.sl.nsw.gov.au/record/74VKO46xVXwX: Catalogue [1892–4]; exact publication date uncertain. Southwest-sheet legend explicitly separates municipal plus/dash, ward dashed, parish cross/dash and Crown grant dash/dot lines. Four original sheet scans plus library combined image are one physical map. West, Central and East wards are internal divisions.
- https://collection.sl.nsw.gov.au/record/74VKDBRdV7wd: Printed May 1886; catalogue includes a holding annotated through January 1888. Native legend keys municipal dash/cross line, ward dashes and Crown grants separately. Three physical holdings, each in two sections, plus three library combined images. Image groups 0/3/8, 1/4/7 and 2/5/6 paired visually by colour, printing and paper condition. Library lists an annotated holding with reservation rescissions in red and reclamations in blue through 25 January 1888. Exact holding-year assignment to these image groups remains unverified; all retain printed May 1886 title. Do not count nine scans as nine editions.

18 unchanged original images added from six catalogue records. All six include explicit native municipal boundary legends. No new legal boundary dates inferred. 811 registered files (5,374,076,714 bytes); all paths/sizes pass, and additions pass unique SHA-256, decoded catalogue dimensions and copied-file hashes. Review: `slnsw_woollahra_ashfield_camden_petersham_ryde_hunters_hill_review.json`. Remaining first-100 municipality search leads: 25.


### Rookwood, Balmain, St Leonards, Leichhardt and regional NSW — 11 October 2026

- https://collection.sl.nsw.gov.au/record/74Vv70Qyq0BA: Catalogue 1892. Native reference explicitly keys municipal dash/cross boundary. Neighbouring Concord, Strathfield and Enfield are labelled; allotment lines are distinct.
- https://collection.sl.nsw.gov.au/record/74VvrG0epe4b: Catalogue circa 1883; source image 3 is later facsimile, reproduction date unknown. Native legend explicitly keys ward dashes; external municipal line has no separate key. Library notes municipal boundary and copies/facsimiles. Two map holdings and a later blue facsimile poster with historical photographs, not three boundary editions. Poster footer says reproduced from a library lithograph; 22 April 1970 library stamp is an accession mark, not a proven publication date.
- https://collection.sl.nsw.gov.au/record/74Vv5aQ5dlBO: Catalogue [1859?]; printed meeting 13 December 1859. Appendix A identifies boundaries agreed and ordered to be petitioned for at meeting 13 December 1859; Appendix B shows proposed St Leonards East with boundary symbol. Appendix A also marks land proposed for sale under a reclamation Act: that is not the council perimeter. No adoption or proclamation date established.
- https://collection.sl.nsw.gov.au/record/74Vv3zoA0mDA: Catalogue 1915–1916; manuscript updates through 1 June 1926. Native legend explicitly keys municipal plus/dash boundary; printed borough proclamation 14 December 1871 is a historical note. Catalogue records manuscript additions to 1 June 1926. Office charting and coloured land annotations must not be treated as council boundaries.
- https://collection.sl.nsw.gov.au/record/74Vv3zWW3a3M: Catalogue 1925. Native legend explicitly keys ward dashed boundaries, with original estate section/portion references separate. Leichhardt and Annandale labelled outside southern edge. No separate municipal boundary legend verified; retain as ward map. Very faint original print retained.
- https://collection.sl.nsw.gov.au/record/74Vv7X5ZJaJy: Catalogue [1922]; office copy updated to at least 12 July 1943. Printed plus/dash perimeter is visible against neighbouring Blaxland Shire label; red manuscript lines also trace land/road features and are not all municipal boundaries. Library identifies office copy annotated to at least 12 July 1943. Two original sections and library combined view of one physical map; not a clean 1922 boundary snapshot.
- https://collection.sl.nsw.gov.au/record/74VKwWXa5Op3: Catalogue [1925]; date inferred by library from publisher code. Native legend explicitly keys solid shire/municipal boundaries, distinct from county dash/cross lines, roads and railways. Includes Young inset and surrounding shires. Printed note says area added from Jindalee Shire via Gazette 5 October 1923; this is not the publication date.
- https://collection.sl.nsw.gov.au/record/74VKwE3DBQKZ: Printed drawing April 1895; proclamation 15 March 1895. Sketch title records proclamation 15 March 1895, footer compiled/drawn at District Government Office April 1895. Dash/cross council perimeter follows creeks and straight eastern line; plain allotment lines are separate. Paper damage retained.

12 unchanged source files added from eight catalogue records. Balmain maps classed as ward maps; proposed St Leonards map kept distinct. Publication, proclamation, manuscript update and library accession dates are not interchangeable. 823 registered files (5,589,034,900 bytes); all paths/sizes pass. Additions pass unique SHA-256, decoded catalogue dimensions and copied-file hashes. Review: `slnsw_rookwood_balmain_st_leonards_leichhardt_lithgow_burrangong_picton_review.json`. Remaining first-100 municipality search leads: 17.

### NSW LGA map checks: Randwick, Shoalhaven and Wollongong (11 October 2026)

- https://collection.sl.nsw.gov.au/record/74VMb7yRkGZg: saved. Coloured municipal plus/dash line and ward dashes match the previously saved 1892 map; municipal legend is on that map south sheet. This holding has different colouring, not an established new boundary edition. Partial north sheet.
- https://collection.sl.nsw.gov.au/record/74Vv3We4JbZl: saved. Native south-sheet explanatory notes explicitly key municipality dash/plus boundaries. Western edge separates Randwick from Mascot and Botany. Two sections and library combined view of one physical map, with northern Randwick outside coverage.
- https://collection.sl.nsw.gov.au/record/74VvVoVmO6lg: saved. Bold pink municipal outline surrounds labelled Central Shoalhaven; neighbouring Nowra, Numbaa and South Shoalhaven shown separately. Library confirms boundary by colour. Composite parish maps include sheet dated 15 August 1888; proclamation is not publication date.
- https://collection.sl.nsw.gov.au/record/74VM0rzVmj6y: saved. Native lower-left key explicitly distinguishes municipal dashed boundary from ward dash/dot and original grant solid lines. Municipal line along Para Creek separates North Illawarra. Library dates map before Church Street resumption 28 October 1927; uncertain catalogue date retained.
- https://collection.sl.nsw.gov.au/record/74Vv3z2Mm6XM: review-only. Cadastral plan reviewed at full-sheet scale. No explicit municipal boundary key or sufficiently clear labelled council perimeter verified. Keep as review-only; title does not establish LGA geometry.
- https://collection.sl.nsw.gov.au/record/74VKmGWwQWKZ: review-only. Mounted water-service-operator map. Native note identifies coloured operator districts and addresses corrected 1 June 1942. Council neighbours labelled, but municipality perimeter not sufficiently verified. Operator districts must not be traced as LGA boundaries.
- https://collection.sl.nsw.gov.au/record/74VKO4ZOeRyg: review-only. Part of Tunks Ward cadastral map, combined sections. Native key explains Crown grants, fences, walls, surveyed high-water reservations and land applications; no municipal or ward boundary key verified. Yellow shoreline reservations are not proven LGA edges. Catalogue [1889], but explanatory Gazette citations literally say 1989; catalogue inconsistency retained, not silently corrected.
- https://collection.sl.nsw.gov.au/record/74VKOl2raVGO: review-only. Two original cadastral sections reviewed; one source section is upside down, retained unchanged. Municipal title, building-type key and yellow streets do not establish council perimeter. Library dates situation after June and before December 1861. No explicit LGA boundary verified.

Six unchanged source images added from four catalogue records. Four other records stay in exploratory review storage. 829 registered files (5,708,528,436 bytes); all paths/sizes pass. New originals pass unique SHA-256, decoded catalogue dimensions and copied-file hashes. Review: `slnsw_randwick_shoalhaven_wollongong_leichhardt_st_leonards_balmain_review.json`. Nine first-100 municipality search leads remain. Source combined views and alternate holdings are not distinct boundary editions.

### Remaining municipality leads and council-boundary search checks (11 October 2026)

- https://collection.sl.nsw.gov.au/record/74VKZMNOl2ll: saved. Native lower-right explanatory notes explicitly key municipality dash/plus lines, separate from Crown grant and fence symbols. Incomplete map covers Concord, with Burwood and Strathfield labelled. Blue manuscript coordinate lines and purple estate colouring are not LGA boundaries. Catalogue supplies title and uncertain decade, not an exact 1886 edition.
- https://collection.sl.nsw.gov.au/record/74Vvp33mk5bg: saved. Native dash/cross municipal line follows Parramatta Road against labelled Burwood Municipality; additional partial line continues south. Library explicitly identifies municipality boundaries. Single partial sheet surrounding Hen and Chicken Bay; does not establish complete Concord perimeter.
- https://collection.sl.nsw.gov.au/record/74VveLRzMyvA: saved. Native title dates 1930. Key explicitly distinguishes city boundary (plus/dash with tint), ward boundaries (tinted line) and adjoining municipal boundaries (plus/dash). Colour fills are wards, not separate councils. Adjoining Glebe, Redfern, Paddington, Woollahra and others shown.
- https://collection.sl.nsw.gov.au/record/74VveBZgG4WX: saved. Native dashed internal line explicitly labelled Old Boundary; larger outer town/borough line also visible. Library confirms town boundary and old boundary. Catalogue interval inferred from council start and Hinton ferry replacement by bridge, not a legal date for either line. Don. Close 2.10.35 pencil note is not publication date.
- https://collection.sl.nsw.gov.au/record/74VveLNy0j0X: saved. Native bottom key explicitly separates blue ward lines from dash/plus city boundary. Two holdings of same 1927 map: source image 1 lacks Coulson/date panel and includes pink annotations; source image 2 prints E. W. Coulson, City Engineer & City Surveyor 1927, with coloured wards and missing upper-right corner. Library donation stamps 1972/1977 are not boundary or publication dates.
- https://collection.sl.nsw.gov.au/record/74VvNxjdDGNb: review-only. Catalogue [1861]. Plan labels North, South, East, West and Waterview wards; red lines follow several streets, but no key verified that assigns those red lines to ward boundaries. Numbered lots and title do not prove municipal perimeter. Retain candidate for further ward interpretation, not a verified outer LGA map.
- https://collection.sl.nsw.gov.au/record/74Vvy5WwJbmb: review-only. Printed engineer date 8 February 1887; library says municipal boundaries shown. Native key explicitly identifies prominent green dashed outline as Limit of Drainage Area and distinguishes sewer routes. No separately labelled municipality line verified. Review-only until municipal line can be distinguished; do not treat drainage outline as LGA perimeter.
- https://collection.sl.nsw.gov.au/record/74VvRZmPPdp3: review-only. Catalogue 1894. Native note says prepared from Higinbotham and Robinson municipality map, but coloured areas are tramway/investment company property. Native signature/date panel requires separate transcription; catalogue date is not assumed to date manuscript annotations. No LGA boundary key verified.
- https://collection.sl.nsw.gov.au/record/74VKwy865q6y: review-only. 1938 uncompleted model housing subdivision in Revesby. Shows proposed allotments and streets within existing roads; no LGA boundary. Municipal title is location context only.
- https://collection.sl.nsw.gov.au/record/74VKwa7yWxdg: review-only. Catalogue [Not before 1840], not an exact 1840 map date. One image is description of Boland Lot 25; other shows two portions/land grants in Balgownie. Lot metes and bounds are not North Illawarra municipal boundary.
- https://collection.sl.nsw.gov.au/record/74Vv8Rw2Z0gg: review-only. Printed manuscript survey August 1903. Shows estate allotments, Cardigan Street, Kingston Road and storm-water-channel wall, in municipalities of Camperdown and Petersham. No municipal boundary key or clearly assigned LGA line verified.
- https://collection.sl.nsw.gov.au/record/74Vv8R26R80d: review-only. Manuscript 1902 with deposited plan 3937. Shows estate allotments and storm-water-channel details, in municipalities of Camperdown and Petersham. No municipal boundary key or clearly assigned LGA line verified.

6 unchanged source images added from five catalogue records; 0 byte-identical duplicates. 835 registered files (5,835,162,152 bytes); all paths/sizes pass. Additions pass unique SHA-256, decoded catalogue dimensions and copied-file hashes. Review: `slnsw_concord_balmain_manly_willoughby_bankstown_illawarra_kensington_sydney_morpeth_review.json`. All first-100 municipality leads and first-100 council-boundary leads reviewed; this does not exhaust either full search (1028 and 220 matches respectively). Council-boundary results: 87 records had no listed scans, nine were outside the current NSW LGA focus, three newly accepted and one previously saved.

Further discovery: second 100 catalogue results retrieved for municipality (1028 matches) and council boundary (220 matches), with council page verified disjoint from its first page. Seven municipality candidates remain: Ashfield alternate holding, Gerringong, Walcha, Dubbo, Katoomba, South Shoalhaven and Parramatta. They are leads, not verified boundary files. Search pagination requires source offset/state parameters; literal plus-query probe retained separately. No jobs live.

### Ashfield, Katoomba, Dubbo, West Botany and early Sydney maps (11 October 2026)

- https://collection.sl.nsw.gov.au/record/74Vv3L2Gavey: saved. Native key distinguishes municipality dash/cross, ward dashes, parish dash/dot and Ashfield Park estate sections. Office copy has manuscript additions. Catalogue transcribes Charted to 30th September 1886, H & R 7/12/86. This is an annotated holding of the 1883 map, not a clean 1883 snapshot or independently proven new boundary edition.
- https://collection.sl.nsw.gov.au/record/74Vv7MPJo7E3: saved. Native title explicitly identifies Municipality of Katoomba as proclaimed 24 July 1936. Red hatching identifies newly added areas; violet areas A/B are National Parks and Primitive Areas Council alternatives, not adopted boundary. Text discusses exchanges with Blue Mountains Shire. Advocacy sketch, not survey accuracy; printed about 16.25 square miles is a source claim, not a calculated polygon area.
- https://collection.sl.nsw.gov.au/record/74VvoEz66wdM: saved. Native key explicitly distinguishes municipal dash/cross boundary (proclaimed 19 February 1872, extended 16 May 1906) from town, police-offences, catchment, county, state-forest and reserve boundaries. Talbragar Shire labelled around outer map. Printed map date 15 August 1932 is separate from each historical boundary notification. Library donation 12 January 1933 is not map date.
- https://collection.sl.nsw.gov.au/record/74VKDavlOjpZ: saved. Native key explicitly identifies Present Municipality dash/cross, Ward coloured dash, and Late Municipality dash/plus boundary. West Botany (later Rockdale) map distinguishes neighbouring councils. Catalogue interval inferred from publisher address and council name change, not dates of the two mapped boundaries. Published in municipality map series; alternate scan does not prove another edition.
- https://collection.sl.nsw.gov.au/record/74VKwKkpzrGO: saved. Native attached panel headed Boundary of the City of Sydney gives external limits, followed by six ward descriptions. Map has coloured/tinted wards and perimeter. Catalogue identifies this state as preceding Wells 1843 plate and dates by a comparable signed dedication 25 October 1842; that dedication is not visible on this scan. Folded map and boundary panel kept together unchanged.
- https://collection.sl.nsw.gov.au/record/74VKwEVBerey: review-only. Previously reviewed in slnsw_canterbury_burwood_sands_shoalhaven_regional_review.json. Municipal versus parish/cadastral lines unresolved; no clear municipal key. Catalogue [between 1893 and 1954?], not an exact map date. Original remains in exploratory review storage.
- https://collection.sl.nsw.gov.au/record/74VKwEzZED7A: review-only. Previously reviewed in slnsw_canterbury_burwood_sands_shoalhaven_regional_review.json under walcha_municipal. No municipal symbol key verified; parish/cadastral line ambiguity remains. Catalogue search title says proclaimed 12 March 1899, while native title and publication metadata read 1889. Date conflict retained; source untouched.
- https://collection.sl.nsw.gov.au/record/74VKwEEykQoX: review-only. Previously reviewed in slnsw_canterbury_burwood_sands_shoalhaven_regional_review.json under south_shoalhaven_municipal. No municipal symbol key verified; prominent parish/cadastral lines must not be assumed council perimeter. Catalogue [1895?], title proclamation 17 December 95.
- https://collection.sl.nsw.gov.au/record/74Vv0eVwJ2Ld: review-only. Combined source view of historical-spots street map and descriptive index, dated 1938. Municipal publisher/title, but no verified municipal perimeter or boundary key. Library accession 20 June 1962 is not map date.
- https://collection.sl.nsw.gov.au/record/74VvyRGQXwpb: review-only. Native pink line is James Houison property grant perimeter, within Municipality of Prospect & Sherwood. Survey March 1924, declaration 2 April 1924. No municipal line verified; property polygon is not LGA boundary.
- https://collection.sl.nsw.gov.au/record/74VK24myx2bM: review-only. Very light-pencil allotment/estate plan; catalogue [between 1840 and 1860], part of estate unidentified. No municipal outline or key verified. Original kept unchanged without image enhancement.
- https://collection.sl.nsw.gov.au/record/74VKwa2rWLlg: review-only. Native key explicitly identifies coal area, coal seam outcrop, Yallah wharfage and Lakelands Syndicate property. Allotment lines and company areas are not municipal boundaries. Catalogue [not before 1898] is only lower date bound; no LGA key verified.

Five unchanged scans registered. 840 files (5,922,647,010 bytes); all paths/sizes pass. Additions pass unique SHA-256, decoded catalogue dimensions and raw-copy hashes. Review: `slnsw_ashfield_katoomba_dubbo_west_botany_sydney_and_estate_leads_review.json`. Offset-100 queues now fully reviewed; subsequent pages remain. Earlier regional exclusions linked into these queues to prevent repeat review.

Search coverage update: all 220 results of the exact council boundary map query retrieved and triaged across three disjoint pages. Final 20 are large estate subdivision-plan series, outside current LGA-map focus; individual sheets were not reviewed. First 300 of 1028 municipality results triaged. Offset-200 has one fresh North Annandale estate-map lead; Victorian municipal map is outside NSW scope. Further municipality pages remain. Pagination state must be copied from the preceding source page for each request. Acquisition count remains 840; no jobs live.

Municipality search coverage: all 1028 results retrieved across 11 pages, with every result ID unique and pages disjoint. Later pages were screened using saved manifests, per-batch reviews, metadata and title evidence; this is discovery triage, not native verification of all maps. Many further NSW leads remain. Large subdivision-plan series and explicit interstate/test records are outside the current LGA-map focus. North Annandale catalogue [1893?] sales plan visually reviewed: Sales plan for North Annandale, catalogue [1893?], compiled for Sydney Freehold Land Building and Investment Company. Shows estate sections/allotments, boundaries of company land, streets and creeks. No municipal boundary key or explicitly assigned LGA perimeter verified. Municipality of Leichhardt in title is location context; not accepted as a verified LGA outline. Review: `slnsw_north_annandale_review.json`. No raw files added from that record.


### NSW and Sydney LGA scans: 1865–1924; Cumberland proposals 1905

- https://collection.sl.nsw.gov.au/record/74Vv355RkdEb: Catalogue [1924?]. Native key tints municipalities teal and shires in varied colours; red spots mark headquarters. Catalogue date uncertain.
- https://collection.sl.nsw.gov.au/record/74VKOBapeeOl: Printed 1900; catalogue note June 1900. Southwest and southeast sheets show dash/cross lines between labelled municipal areas, distinct from transport lines. Municipal symbol key not located. Northeast/northwest retained as companion sheets. Fifth image is library source combined view. Paper losses unchanged.
- https://collection.sl.nsw.gov.au/record/74VKvJwJ64VA: Printed 1907. Red outlined named municipalities and shires; catalogue explicitly identifies coloured boundaries. Source scan rotated; raw orientation retained.
- https://collection.sl.nsw.gov.au/record/74VKvJZjxNoy: Printed 1913. Native key distinguishes dot/dash municipality and shire lines from railways and tramways. Second holding includes Fire Brigade Board districts; those districts and manuscript overlays are not LGA boundaries. Two holdings, not proven boundary editions.
- https://collection.sl.nsw.gov.au/record/74VvaEljm6VO: Printed 1918. Native key identifies shire names and boundaries in red and municipalities in green. Four source quarters, no derived stitch. Printed 1918 retained despite 1917 shelf annotation. Southeast includes Lord Howe inset.
- https://collection.sl.nsw.gov.au/record/74VvGRmONMwX: Printed 1865. Native key separates City Boundaries (red dashed/tinted), Municipality (yellow dash/dot) and Parish (cross pattern). Faint municipality lines and major paper losses limit tracing.
- https://collection.sl.nsw.gov.au/record/74VKZbKdmPdM: Printed proposal 1905. Native title states additions proposed by Local Government Areas Commission, 1905. Green altered municipal outlines and pink added areas. Commissioners signature block. Adoption not established.
- https://collection.sl.nsw.gov.au/record/74VvRgl8dXod: Printed proposal 1905. Native title states proposed additions, 1905. Red altered outlines and tinted added areas. Different lithograph identifier from green holding; identical edition not asserted. Adoption not established.

Sixteen unchanged source images registered: 14 boundary scans and two companion sheets. Collection: 856 files (6,219,681,929 bytes). All registered paths/sizes pass; additions pass unique hashes, decoded catalogue dimensions and copied-file hashes. Review: `slnsw_nsw1918_1924_sydney1865_1900_1907_1913_cumberland1905_review.json`. All current fetch sessions finished. Further NSW municipality-search leads remain.


### Sydney municipal atlas Part 1, catalogue [1911?]

https://collection.sl.nsw.gov.au/record/74VKZb6ab43M

Catalogue [1911?] is inferred from publisher addresses and latest map detail. Holding combines sheets with Wentworth Court and 41 Phillip Street imprints, annotated index, and a separate different-edition index. Do not treat all outlines as a uniform 1911 snapshot or use incorporation dates as map publication dates. Randwick is north-only. Rockdale has two sheets. No georeferencing or boundary tracing.

Twenty-two map images have native municipality/ward keys, distinct from tramways and railways. Coverage: Bexley, Burwood, Canterbury, Drummoyne, Glebe, Hurstville, Kogarah, Marsfield, Marrickville, Mosman, Newtown, North Sydney, Paddington, Petersham, Randwick north, Rockdale north/south, Ryde, St Peters, Strathfield, Vaucluse and Waverley. Five companion images: cover, annotated title/index, Public Works list recto/verso, different-edition street-directory index. They are not counted as boundary maps.

- bexley: Bexley proclamation 28 June 1900.
- burwood: Burwood proclamation 27 March 1874.
- canterbury: Canterbury incorporation 17 March 1879.
- drummoyne: Five Dock proclamation 25 July 1871; Drummoyne detached 17 January 1890; amalgamated 12 March 1902.
- glebe: Glebe proclamation 1 August 1859.
- hurstville: Hurstville includes Bexley detachment and boundary reproclamation 28 June 1900. Several earlier dates printed; verify full native text for legal use.
- kogarah: Kogarah proclamation 22 December 1885.
- marsfield: Marsfield proclamation 2 June 1894. Older municipal name retained; catalogue atlas date cannot date this outline.
- marrickville: Marrickville incorporation 1 November 1861.
- mosman: Mosman separated and proclaimed 11 April 1893.
- newtown: Newtown incorporation 12 December 1862.
- north sydney: North Sydney proclamation 29 July 1890, reproclamation 11 April 1893.
- paddington: Paddington proclamation 17 April 1860.
- petersham: Petersham incorporation 14 December 1871.
- randwick north: Randwick north sheet; reproclamation 16 February 1889, wards 30 November 1891. Bottom note states remaining borough south of displayed area; incomplete perimeter on this sheet.
- rockdale north: Rockdale north sheet. Former West Botany; annexation 21 December 1886; 1888 naming act noted.
- rockdale south: Rockdale south sheet. Pair with north sheet for extent; no derived stitch.
- ryde: Ryde note records Marsfield detached and boundaries reproclaimed 2 June 1894.
- st peters: St Peters includes boundaries 16 June 1886 and 9 May 1890; ward reproclamations through 18 December 1902.
- strathfield: Strathfield added area annexed 16 February 1892.
- vaucluse: Vaucluse proclamation 29 March 1895.
- waverley: Waverley proclamation 13 June 1859.

27 unchanged source scans registered, all unique by byte hash. Collection: 883 files (6,458,148,466 bytes), 761 boundary JPEGs. New files pass decoded catalogue dimensions and raw-copy hashes; all registered paths/sizes pass. Review: `slnsw_sydney_atlas_part1_1911_review.json`. No live fetch jobs. Metadata-only leads: Atlas of suburbs of Sydney Part 2 [1889?] (74VKZbdDR46X, 29 images) and Suburban plans [1887?] (74VKDRZp0VXl, 27 images); scans not fetched or boundary-verified yet.


### Sydney atlas Part 2, catalogue [1889?], possible proof holding

https://collection.sl.nsw.gov.au/record/74VKZbdDR46X

Catalogue [1889?] remains uncertain. Library describes possible proof copy. Six main municipal plates plus accompanying coloured Burwood map. Printed and manuscript title order differs. Reserved directory pages are empty. Attached business papers have dates including 1884 and 1889, but these do not establish each map date. No exact legal boundary snapshot established. Monochrome lines can be faint; raw source unchanged.

- Seven municipal maps: Newtown, Camperdown, Macdonaldtown, Glebe, Waverley, Randwick and accompanying Burwood. Each has a native municipality/ward key and visible municipal outline.
- Randwick main map is north-only; whole-borough sketch inset uses a smaller scale. Parish lines have a distinct key. Do not trace the southern boundary from the main-map frame.
- Burwood is coloured by ward and has a blue numbered reference grid; these are not separate LGA boundaries. Its accompanying street directory has empty municipal-statistics fields; no values inferred.
- Two title pages and Burwood directory registered as companions. Six reserved directory pages and 13 business papers reviewed but not added to the raw map collection. Business lists are not evidence that all listed municipal plates are present.

Ten unique unchanged scans registered. Collection: 893 files (6,546,321,193 bytes), 768 boundary JPEGs. Additions pass hashes, decoded catalogue dimensions and copied-file hashes; all registered paths/sizes pass. Review: `slnsw_sydney_atlas_part2_1889_review.json`. No live fetch jobs. Suburban plans [1887?], 27 images, remains a metadata-only lead.


### Suburban plans bound holding, catalogue [1887?]

https://collection.sl.nsw.gov.au/record/74VKDRZp0VXl

Catalogue [1887?] is an uncertain date for a bound collection, not verified publication/legal date for each sheet. Maps have differing publisher imprints and mounting/overlays. Native municipal, ward and parish keys must be read separately; railway/tram tint is not LGA evidence. Proposed Hurstville is not established as adopted. Manuscript index lists sheets not present in catalogue scans; digital holding not claimed complete. Source bytes, orientation, tears, stains and faint lines unchanged.

- 18 municipal map sheets: Auburn, Enfield, Granville, Rookwood, Petersham, Marrickville, St Peters, Leichhardt, Balmain, Ashfield, Kogarah, Strathfield, Dundas, Ryde, East St Leonards, Waterloo, Alexandria and Darlington. Native municipal keys and outlines visually reviewed. These are alternate scans/holdings, not automatically distinct legal boundary editions.
- Hurstville title and key explicitly say proposed municipality. Registered as a proposal.
- Ward colour highlights, property names, proposed railway/water-supply lines and parish boundaries are distinct from the keyed municipal outline. Some native outlines are faint. Do not derive dates from map names alone.
- Front/back covers and manuscript index kept as companions; five blank/label pages review-only. Index contains more names than the available map scans.

22 unique unchanged scans registered. Collection: 915 files (6,680,394,958 bytes), 787 boundary JPEGs. Additions pass hashes, decoded catalogue dimensions and copied-file hashes; all registered paths/sizes pass. Review: `slnsw_sydney_suburban_plans_1887_review.json`. No live fetch jobs. Further NSW discovery leads remain.


### Sydney municipalities and unincorporated areas, 1900

https://collection.sl.nsw.gov.au/record/74VKwMDqdMEb

Six catalogue images are three whole-map views/holdings, two covers and decorative endpaper, not six map sheets. Printed map date 1900; cover ownership annotation 1902 is not publication date. Two flat images show library holding marks 1900/1 and 1900/1A; third is unfolded mounted/folding view. Distinct bytes do not prove distinct boundary editions. Red municipal outline/tint separate from black transport network. Irish Town is unincorporated within Bankstown; do not fill every enclosed area as council land. Raw folds, mounts and orientation unchanged.

Catalogue explicitly describes municipal boundaries overprinted on a base map. Native title, red named council outlines and unincorporated gaps visually reviewed. Extent includes northern Sydney, western municipal areas and Sutherland; map frames truncate some southern/western areas. No exact legal effective date established beyond printed map date.

Five unique unchanged originals registered. Collection: 920 files (6,764,010,750 bytes), 790 boundary JPEGs. Additions pass hashes, decoded catalogue dimensions and copied-file hashes; all registered paths/sizes pass. Review: `slnsw_sydney_municipalities_1900_review.json`. No live fetch jobs; further NSW leads remain.

### Sydney Bartholomew map, printed 1890

- Source: https://collection.sl.nsw.gov.au/record/74VvkQ836lOg. Four scans reviewed: whole map and labelled front/back covers saved; inside-cover bookplate review-only. Original bytes unchanged.
- Native title prints 1890. Legend distinguishes Sydney city, municipal and parish boundaries and rail/tram/bus routes. Red fill means built portions within the city boundary; do not treat it as full council extent. Names and line symbols inspected near Five Dock, Balmain, Leichhardt and Glebe.
- Catalogue scale ca. 1:1,774,080 conflicts with native chains/miles graphic scale. Do not use catalogue ratio for digitising. Exact legal boundary date unverified. Fold gaps and attached Alfred Lee bookplate remain in original scan.
- Three new files pass bytes, unique SHA-256, copied-file hashes and catalogue pixel dimensions. All 923 manifest paths/sizes checked. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_sydney_bartholomew_1890_review.json`.

### NSW commercial, Sydney and planning-region batch

- Commercial map of New South Wales showing shires and municipalities [cartographic material] : map No. 406 / H.E.C. Robinson. Source: https://collection.sl.nsw.gov.au/record/74VKZbwpggLy. Native 6th edition map no. 406. Municipal tint and varied shire tint keyed separately from post/mail routes. Headquarters red spots may sit outside council land with arrow. Native scale 16 miles/inch conflicts with catalogue 1:63,600 and 1 inch=10 miles. Insets A–L have differing scales. Index council statistics at 31 December 1928; summary population estimates labelled 1929; neither proves exact boundary date. One whole map, not six sheets. Decorative endpapers and unlabelled back cover review-only.
- Map of Port Jackson and City of Sydney shewing the adjacent municipalities, N.S.W. [cartographic material] / S. T. Leigh & Co. Source: https://collection.sl.nsw.gov.au/record/74Vv7LpQjMbl. Native legend separates Sydney city, municipal, parish and Police Act boundaries. Printed 1885. Damage/loss near upper left margin retained. Exact legal boundary date unverified.
- Premier's Department regions for survey and planning [cartographic material] : shires and municipalities. Source: https://collection.sl.nsw.gov.au/record/74Vv5gWGrgzX. Native revision note 1 January 1952. Legend separates thick planning regions, thin shire outlines, municipal outlines and dashed pasture protection districts. Regional colour fills are not council fills. Small statewide scale limits Sydney detail.
- Premier's Department regions for survey and planning [cartographic material] : shires and municipalities. Source: https://collection.sl.nsw.gov.au/record/74Vv5gWm00R3. Native revision note 1 July 1953. Legend separates thick planning regions, thin shire outlines, municipal outlines and dashed pasture protection districts. Monochrome image and handwritten annotations preserved. Small statewide scale limits Sydney detail.
- Map of Port Jackson and City of Sydney shewing the adjacent municipalities N.S.W., 1875 [cartographic material] / Sands's Sydney & suburban directory. Source: https://collection.sl.nsw.gov.au/record/74Vv4Vygm70X. Native printed 1875 and legend separates city, municipal, parish, Police Act and cab boundaries. Green denotes government reserves/recreation areas, not council membership. Mounted linen/folds retained. Exact legal boundary date unverified.
- General map of Sydney and suburbs, shewing municipalities, railways, tramways, main roads, etc. [cartographic material] / H.E.C. Robinson. Source: https://collection.sl.nsw.gov.au/record/74VKvK5r0VZg. Native printed 1900 and red named municipal outlines distinct from black transport lines; catalogue confirms boundaries. No separate boundary symbol key located. Irish Town label/road enclosure is not evidence that all Bankstown interior is municipal land. Distinct scan/holding from other Robinson 1900 maps; distinct legal edition not established.
- General map of Sydney & suburbs shewing municipalities and shires, also railways, tramways, main roads [cartographic material] / H.E.C. Robinson Ltd. Source: https://collection.sl.nsw.gov.au/record/74Vv7oV8oJR3. Catalogue date [1921?] inferred from dating code; no printed calendar publication date located. Native legend identifies blue municipal and shire boundaries separately from red tramways, railways and goods railways. Extent Duffy Forest–Cronulla/Riverstone–coast. Exact legal boundary date unverified.
- Twelve source scans visually reviewed; 9 unchanged originals saved. Bytes, unique SHA-256, copied-file hashes and catalogue dimensions pass. All 932 registered paths/sizes pass. Evidence: `explore/output/2026-10-10_download-boundary-maps/slnsw_nsw1929_sydney1875_1885_1900_1921_regions1952_1953_review.json`.

### Five-municipality map, catalogue [1891?], and two screened exclusions

- Source: https://collection.sl.nsw.gov.au/record/74VM0LKLP3bl. Catalogue [1891?] uncertain; no printed calendar publication date located. Native legend: municipal long dashes with plus marks, parish dashes with x marks, ward short dashes, tramways double line. Native scale 5 chains/inch (330 feet/inch). Two-section holding preserved separately and as library-supplied composite, not stitched locally. Two colour whole-map catalogue images have identical decoded pixels despite different file hashes; keep first only. No distinct boundary editions claimed. Park proclamation and allotment dates do not date the council outline.
- Four originals saved: colour whole map, two separate sections and library-supplied composite. All eight source scans in this batch inspected. One colour whole-map duplicate excluded: its decoded RGB pixels equal image 0, SHA-256 `60afe07968c69895bda5d395a9834d57f28f54ce9e6c74262286834b6e162ed0`, despite different JPEG bytes.
- https://collection.sl.nsw.gov.au/record/74Vv72rNMyZl: Electoral divisions shown by red broad outlines and numbered electorate list. No separate municipal boundary legend or lines located. Parish/place names alone do not establish LGA extent. Excluded from current LGA collection.
- https://collection.sl.nsw.gov.au/record/74VK6EkMmeVO: Recto/verso of parcel assignment plan: allotment boundaries, landowner names, street dimensions and locality municipality label. No council or suburb perimeter located. Excluded from current LGA collection.
- Four new originals pass bytes, unique SHA-256, copied-file hashes and catalogue dimensions. All 936 registered paths/sizes pass. Evidence: `explore/output/2026-10-10_download-boundary-maps/slnsw_glebe1891_electorates1880_willoughby_assignment_review.json`.

### Sydney municipal maps, printed 1867, 1868 and 1882

- https://collection.sl.nsw.gov.au/record/74VM4Pv2bK6X: Two whole-map holdings; second has dissected/mounted grid. Native printed 1882 in each. Green marks government reserves/recreation rather than council fill. Native legend distinguishes city dashes, municipal dash-dot lines, parish cross-dash lines and Police Act lines. Native chain/mile graphic scale retained. Exact legal boundary date unverified. Folds, mounts, loss and orientation unchanged; distinct scans/holdings do not establish different boundary editions.
- https://collection.sl.nsw.gov.au/record/74VKw68JalAg: Four source images: front labelled cover, inside title/press with manuscript May 28/68 ownership annotation, unfolded map, unlabelled back cover. Back cover review-only. Ownership date does not replace printed map date 1867. Green denotes reserves/recreation rather than council land. Native legend distinguishes city dashes, municipal dash-dot lines, parish cross-dash lines and Police Act lines. Native chain/mile graphic scale retained. Exact legal boundary date unverified. Folds, mounts, loss and orientation unchanged; distinct scans/holdings do not establish different boundary editions.
- https://collection.sl.nsw.gov.au/record/74VvkQL2NDey: One damaged whole-map holding; many cracks and missing patches retained. Printed title and boundary key readable. Native legend distinguishes city dashes, municipal dash-dot lines, parish cross-dash lines and Police Act lines. Native chain/mile graphic scale retained. Exact legal boundary date unverified. Folds, mounts, loss and orientation unchanged; distinct scans/holdings do not establish different boundary editions.
- https://collection.sl.nsw.gov.au/record/74VvboxLEo6d: One whole map; printed 1868 agrees with bracketed catalogue year. Saint Leonards / East St Leonards labels distinguish it from 1867 holding; this is not a verified complete list of boundary changes. Native legend distinguishes city dashes, municipal dash-dot lines, parish cross-dash lines and Police Act lines. Native chain/mile graphic scale retained. Exact legal boundary date unverified. Folds, mounts, loss and orientation unchanged; distinct scans/holdings do not establish different boundary editions.
- Eight scans visually reviewed. 7 unchanged originals saved; unique SHA-256, bytes, copied-file hashes and catalogue dimensions pass. All 943 registered paths/sizes pass. No same-byte duplicates found; selected images differ in size, so none has identical decoded pixel arrays within this batch. Evidence: `explore/output/2026-10-10_download-boundary-maps/slnsw_sydney1867_1868_1882_review.json`.

### NSW 1943, Cumberland circa 1948, Sydney 1875/1883 and New England 1928

- https://collection.sl.nsw.gov.au/record/74VvV22kzbxb: Native 7th edition, scale 16 miles/inch; catalogue publication 1943. Statistics print 31 December 1936, area in acres. No exact calendar publication imprint located. Municipal blue tint and various shire tints keyed; headquarters spots may be outside council land with arrows. Insets differ in scale. Two sections and library-supplied composite retained; no local stitching. Neither statistics nor catalogue publication proves exact boundary date.
- https://collection.sl.nsw.gov.au/record/74VvjZo77NMl: Printed base title 1882; red overprint states trigonometrical stations to report 26 April 1883. Municipal dash-dot, city dashed, parish cross-dash and Police Act boundaries keyed separately. Red numbered survey points are not boundary updates. Exact legal boundary date unverified.
- https://collection.sl.nsw.gov.au/record/74VKdvejB5zd: Native municipality/shire dotted boundaries keyed separately from long-dashed metropolitan area, railways and roads. Colour council areas and riding labels retained; riding divisions are not separate councils. Native print code 48-1840; catalogue date [1948?] uncertain, exact boundary date unverified.
- https://collection.sl.nsw.gov.au/record/74Vv0KjLdxZM: Two whole-map holdings with different physical condition. Both print 1875. Native legends distinguish city, municipal, parish, Police Act and cab boundaries. Green reserve/recreation shading is not council extent. Missing southeast patch in second retained. Distinct holdings do not establish distinct boundary editions; exact legal boundary date unverified.
- https://collection.sl.nsw.gov.au/record/74VvREDvlEN3: Native footer prints 1928, code 27-491-D. Tourist map has dashed lines labelled shire boundary, including near Guyra/Aberfoyle and Gostwyck; retained for partial shire evidence. Legend mainly covers road quality, rail and tourist features; red thick lines are roads. No separate municipal outline key located: title names Uralla, Armidale and Glen Innes but does not prove their complete perimeters are shown. Do not claim complete council coverage. Exact legal boundary date unverified.
- Eight originals saved unchanged and visually inspected. Unique SHA-256, bytes, copied-file hashes and catalogue dimensions pass. All 951 registered paths/sizes pass. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_nsw1943_cumberland1948_sydney1875_1883_newengland1928_review.json`.

### Individual Sydney municipal maps and Greater Sydney convention (11 October 2026)

- Added 15 unchanged State Library NSW originals: Botany, Concord, Fivedock, Victoria (Willoughby parish), Drummoyne, Newtown, Leichhardt, Glebe, Ryde, Hunters Hill, St Leonards, East St Leonards, Darlington, Waterloo and Greater Sydney convention area.
- All whole maps and fourteen native municipal keys inspected. Keys distinguish municipal, ward, parish and tramway lines where present. Botany and Hunters Hill municipal symbols use cross-dashes; other keys vary. St Leonards separates constructed and authorised tramways. Newtown purple railway corridors are not council outlines.
- Municipal catalogue dates are mostly [189-?], with Botany, Darlington and Waterloo [1890?]. Manuscript dates and red library stamps do not prove publication or boundary dates. Additional physical holdings are not proven distinct boundary editions. Victoria is a historic NSW municipality; upper-right damage remains. Concord labels Homebush not incorporated.
- Greater Sydney native signature reads J. Marshall, Chief Survey Draftsman, 8.11.11. Red internal outlines separate named municipalities and shires from black transport/coast lines. No formal line key located. The convention title does not prove an adopted regional LGA or exact legal boundary date.
- No byte or decoded-pixel duplicates found against registered originals of matching dimensions. All 966 registered files pass existence/size checks; 15 new originals pass hash, copied-byte and catalogue-dimension checks. Full prior-file hashes were checked in earlier batches. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_offset400_individual_municipal_review.json`.

### Further individual municipal holdings (11 October 2026)

- Added nine unchanged originals: two Leichhardt holdings, Camperdown, Mosman, North Sydney, Enfield, Balmain, Glebe and Burwood. Higinbotham, Robinson & Harrison Leichhardt catalogue date is [188-?]; Enfield [1890?]; the others [189-?]. Printed exact calendar dates were not established.
- All nine whole maps and municipal keys inspected. Camperdown has Gas Coys. Sheets handwritten coordinates and coloured streets, with ink obscuring some key lines. Glebe carries gas-company marks. These annotations are not printed council outlines or boundary-date evidence.
- Mosman and North Sydney distinguish constructed red tramways from dashed proposed lines. Leichhardt red hand outlines and ward names differ from black ticked tramways. Enfield retains a ward-proclamation table and lower-margin physical loss. Burwood ward colouring differs from the municipal key; neighbour is labelled not incorporated.
- These additional holdings are not proven distinct boundary editions. No byte/decoded-pixel duplicate found against registered JPEGs of matching dimensions. All 975 paths/sizes pass. Nine new originals pass hash, copied-byte and catalogue-dimension checks; prior hashes were checked in earlier batches. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_offset500_individual_municipal_review.json`.

### Further Sydney municipalities: offsets 600–700 (11 October 2026)

- Added 17 boundary-map originals and the labelled St Peters advertising verso, from 17 catalogue records. All 18 images visually inspected; 16 native municipal keys inspected. Drummoyne has no formal key located; its proclaimed borough title and southern heavy dash/cross boundary were inspected.
- canterbury: Catalogue [1889?] estimated from publisher address and Charlotte Street gazettal in 1888; not an exact boundary date. Native municipal key distinct from ward colours.
- kogarah: Catalogue [1889?] estimated from Oatleys Platform station label (catalogue notes name used in 1889, changed in 1890). Native municipal key retained; station naming is not proof of legal boundary date.
- annandale: Native municipal cross-dash key separate from black ticked tramway; red library stamp is not publication date.
- woollahra: Manuscript EGL 30-4-29 visible in lower-right border; catalogue [1929?]. Native notes give borough proclamation 17 April 1860, Vaucluse detached 29 March 1895 and boundary reproclamation 29 March 1895. These dates differ from drawing date. Council plus-dash key differs from ticked tramways.
- ashfield: Municipal cross-dash, parish dot-dash and ward short-dash keys separate. Coloured ward edges do not replace municipal key.
- burwood600: Coloured streets and manuscript marks are later annotations. Catalogue notes verso stamp Charted on R.E. map June 1924; this is not publication or boundary date. Native municipal/ward keys separate; right-edge physical loss remains.
- erskineville: Catalogue [1888], no printed calendar publication established. Native municipal, ward and tramway symbols separate. Stamp 86 is not edition date.
- drummoyne proclaimed1890: Native title explicitly proclaimed 18 January 1890, scale 4 chains/inch. Borough cadastral plan labels adjacent Municipality of Hunters Hill and ward areas; southern heavy dash/cross edge seen. No formal boundary-line key located. Parcel and proposed street lines must be kept separate; exact interpretation of all water edges remains unverified.
- strathfield: Native parish and municipality keys separate. Catalogue calls mapped area present-day Homebush; retain historic Strathfield title, not a current LGA assignment. Small upper-right physical loss retained.
- randwick: Main map covers northern Randwick; small whole-municipality inset retained at different scale. Purple hand-coloured ward boundaries and handwritten ward names are annotations; native municipal, parish, ward and tramway symbols separate. Stamp 94 is not publication date.
- enfield: Native municipal plus-dash, ward short-dash and red tramway keys separate; library stamp 93 is not date.
- ryde: Manuscript colours/notes and catalogue-mentioned Robinson 1960 stamp are not publication or legal boundary date. Native municipal, ward and parish keys separate; physical losses cross margins and map body.
- rockdale: Native key separates present municipal cross-dash from late municipal plus-dash, and coloured ward edges. Retain both boundary types for comparison; no exact date of either boundary proved by catalogue [189-?].
- st peters: Native municipal cross-dash and coloured ward edges separate. Recto boundary map plus advertising verso retained; verso is a companion document, not a second map.
- marrickville: Catalogue [1886?]. Native municipal and ward keys separate; proposed streets shown in dotted lines, not proposed councils.
- burwood700: Native municipal/ward keys separate; Charles T. Burfitt land-sales imprint retained. Severe left-edge physical loss removes part of map; cannot reconstruct full perimeter from this scan alone.
- petersham: Catalogue [1886?]. Native municipal and ward keys separate; coloured wards not distinct LGAs.
- Additional physical scans are not proven distinct boundary editions. No byte or decoded-pixel duplicates found against registered JPEGs of matching dimensions. All 993 registered paths/sizes pass; 18 new originals pass hash, copied-byte and catalogue-dimension checks. Prior hashes were checked in earlier batches. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_offsets600700_municipal_review.json`.

### Remaining individual municipality/valuation holdings (11 October 2026)

- Six records reviewed, thirteen source images inspected. Added eleven boundary scans and one advertising/postal companion; one visibly unrelated Fairfield-record atlas cover remains review-only.
- st peters harrison: Native municipal/ward key inspected. Native copyright registration stamp 14 September 1885 retained, distinct from catalogue range between 1882 and 1887 and not an exact legal boundary date.
- paddington higinbotham: Two physical holdings; native municipal/ward keys inspected. Catalogue [1888?] estimates date from publisher address and absent Norfolk/Suffolk streets, while series note mentions 1890. These are catalogue dating evidence, not a proven exact boundary date. Upper-left loss in first holding retained; ward colours not separate LGAs.
- north sydney mosman: Native front key distinguishes municipal/ward boundaries and constructed/proposed tramways. Catalogue 1893; advertising verso includes metropolitan postal district map dated November 1893. Postal rate district/city boundary context is not a second full LGA map. Front and labelled verso retained; no exact legal boundary date established.
- fairfield valuer: Five library-supplied physically dissected/reassembled cadastral scans retained unchanged, not locally stitched. Native scale 2 chains/inch; catalogue date span November 1929–December 1935 is a multi-sheet range, not one exact council-boundary date. Labelled municipality segments include Cabramatta and Canley Vale, Prospect and Bankstown. No general municipal boundary-line key located. Partial/faint boundary evidence only, not complete council perimeters or the original twenty-sheet set. Sixth catalogue image is visibly an Atlas of Suburbs of Sydney Part 2 cover labelled Maps/1148, rather than a Fairfield cadastral map (record call number Maps/1147); review-only, not attributed as Fairfield boundary evidence.
- paddington robinson: Native municipality, ward, rail, tramway and main-road keys inspected. Printed borough proclamation 17 April 1860 differs from catalogue publication estimate between 1904 and 1906, based on publisher address and Wesleyan chapel naming. No exact legal boundary date established.
- balmain robinson: Native municipality/ward key separate from tramways and main roads. Printed borough proclamation 21 February 1860 differs from catalogue publication estimate between 1906 and 1910; 41 Phillip Street imprint retained. No exact legal boundary date established.
- No byte or decoded-pixel duplicates found against registered JPEGs of matching dimensions. All 1005 registered paths/sizes pass; 12 new originals pass hash, copied-byte and catalogue-dimension checks. Prior hashes were checked in earlier batches. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_remaining_municipal_review.json`.

### Remaining regional maps (11 October 2026)

- Eight records and eleven images reviewed. Five unchanged LGA-bearing originals saved; six economic map/verso images remain review-only.
- cumberland robinson: Catalogue [1922?]. Native key explicitly uses municipality cross-dash where boundary is not formed by roads, streets or natural features. Red/brown road marking and transport lines must not be read as municipal outlines. Catalogue date uncertain; no printed exact calendar date located.
- survey planning regions: Native revised 1 April 1946; catalogue 1946. Native legend distinguishes municipalities, shires, Pastures Protection Districts and thick regional outlines. Regional colours are not councils. Native note states regional lines follow shire and Pastures Protection District lines except part between Central Darling and Murray Darling regions. Revision date does not establish exact legal date for every council.
- macquarie region: Catalogue [1945]; native code 45.23. Native region outline and labelled shire areas inspected, including Wingadee, Marthaguy, Gilgandra, Timbrebongie and Talbragar. Catalogue explicitly identifies region, shire and municipal boundaries and says title/legend intentionally unfinished. No completed boundary-symbol key present; line interpretation and complete municipal perimeters remain unverified. Native code 45.23; exact legal boundary date unverified.
- cumberland lands: Catalogue [1935]; native code 35-762. Native notes explicitly say municipalities and shires shown, separately from metropolitan area, county remainder, National Park and Ku-ring-gai Chase. Boundary symbol samples are not filled in the notes; road and rail samples are present. Named council outlines retained, but exact boundary-symbol interpretation needs confirmation before tracing. Native code 35-762; no independent legal boundary date verified.
- nsw diagram: Printed 1929; native code 22.682.D. Native title/footer print 1929; code 22.682.D is not substituted for publication date. Red shire boundaries and numbered shire index keyed separately from filled municipal patches, rainfall/wheat-growing limits, territorial divisions and counties. Municipal patches at this scale are not complete detailed perimeters.
- nsw lands a: Catalogue 1948; native code 48-890. Economic map printed in 1948 on 1937 base. Native key shows agricultural/mining areas, meteorological subdivisions, transport and municipal population values (thousands), rather than identified LGA outlines. Both map and information verso visually reviewed; no boundary evidence identified for focused collection, review-only.
- nsw lands b: Catalogue 1950. Native key shows agricultural/mining areas, meteorological subdivisions, transport and municipal population values (thousands), rather than identified LGA outlines. Map and information verso visually reviewed; review-only under LGA focus.
- nsw lands c: Catalogue 1937; native code 37.740. Native key shows agricultural/mining areas, meteorological subdivisions, transport and municipal population values (thousands), rather than identified LGA outlines. Map and information verso visually reviewed; review-only under LGA focus.
- No byte or decoded-pixel duplicate found against registered JPEGs of matching dimensions. All 1010 paths/sizes pass; five new originals pass hash, copied-byte and catalogue-dimension checks. Prior hashes were checked in earlier batches. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_regional_remaining_review.json`.

### Remaining Sydney/Parramatta overview holdings (11 October 2026)

- Seven records, eleven images reviewed. Added nine boundary-bearing source scans and two Craigie companion pages.
- craigie district: Catalogue [1923]. Native city/municipal boundary sample differs from transport and tram-stop symbols. Folded cover/advertisement and street index retained as two companion pages, not extra boundary maps. No printed exact calendar publication established.
- harbour black: Catalogue 1916. Native notes key green recreation reserves, un-gazetted foreshore reservations and other reserves separately; red tramways and dashed red ferries are transport, not LGA outlines. Catalogue explicitly identifies municipal boundaries, but no municipal boundary-symbol sample located in native notes. Retained as base map with LGA evidence; line interpretation needs confirmation before tracing.
- sands overview: Catalogue 1884. Named municipalities and outlines visible; no boundary-symbol key located. Western part physically missing, including mapped area; partial council coverage only. Green/black feature and ward marks must not be inferred as separate LGAs.
- robinson adjacent: Catalogue [1906]. Native explanatory key shows shared city/municipal plus-dash outline, separately from single/double tramway and ferry routes. Edge losses retained. No exact legal boundary date independently verified.
- craigie inner: Catalogue between 1923 and 1927. Native city/municipal key inspected; street index appears below map in this holding. Title excludes parts of Camperdown and Moore Park lands; cannot imply complete suburban coverage. Different physical layout is not proven a distinct boundary edition.
- robinson city: Catalogue [1897], but catalogue describes later Xerox/negative/photographic copies and theatre annotations to 1970. Source scan visibly has coloured theatre annotations. Native city/municipal plus-dash key separate from tramway routes. Retain as scan of a later copy of historical base, not proof of contemporary original paper or updated LGA boundaries. Annotations can obscure lines.
- parramatta: Native title Second Edition. Catalogue 1904 transcribes 13 July 1904 and lithograph code 03.671T. Native key distinguishes town (notified 20 March 1885), parish, reserve, borough and ward lines; borough/ward bracket cites 20 April 1893. Towns Police Act boundaries proclaimed 12 October 1892 are noted identical with borough boundaries. Borough symbols apply where not identical with town boundaries. Private subdivision broken lines differ from LGA outlines. Two sections plus library-supplied composite retained unchanged, not locally stitched. Inset differs in scale; independent gazette/legal-date verification not done.
- No byte or decoded-pixel duplicate found against registered JPEGs of matching dimensions. All 1021 paths/sizes pass; eleven new originals pass hash, copied-byte and catalogue-dimension checks. Prior hashes were checked in earlier batches. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_overview_remaining_review.json`.

### Official Sydney maps (11 October 2026)

- Five records and ten source images reviewed; nine LGA-bearing scans saved unchanged. One trig survey remains review-only.
- temporary issue: Catalogue 1943 local government overprint. Five library source views: four sections and supplied whole-map composite. Catalogue explicitly says Sydney/environs base sheets mounted together and overprinted with 1943 LGAs. Red named council/shire outlines inspected, including Fairfield, Cabramatta and Canley Vale, Bankstown, Hornsby, Ku-ring-gai, Warringah and Sutherland. No formal overprint line key or native exact date located in supplied views. Blue/green spot annotations not interpreted as boundaries. Preserve pre-existing physical assembly; no local stitching and no claim that base survey dates to 1943.
- surveyor general: Printed 1888. Native title prints 1888; scale 8 chains/inch. Explanatory notes distinguish parish, municipality, ward and electoral-district names/boundaries. Parks/reserves have separate dated table; those reserve dates are not boundary revision dates. Lithograph M.8844 per catalogue.
- lands city: Catalogue 1895; lithograph code 0.95.242. Native explanatory notes distinguish parish and municipality boundaries and built features; scale 12 chains/inch. Catalogue dates 1895 and transcribes lithograph code 0.95.242. No native printed calendar publication located in title; dated parks/reserve table does not establish LGA boundary dates.
- twynam: Printed 1888; second holding labelled Second Edition. Two physical holdings. Both native titles print 1888; second explicitly Second Edition and has severe paper loss. Native municipality/parish/ward/electoral notes inspected. Catalogue says one copy coloured for buildings/reserves, another for wards/parishes; these fills do not define separate councils. Different printed edition label does not independently prove a boundary revision.
- adams trig: Catalogue 1877; supplied image prints July 1881. Catalogue describes Sheet 1 First Edition Office 808, August 1877, but supplied scan visibly reads Sheet S.I.W., Preliminary Edition, Office 1063 and July 1881. Native key shows high-water mark, reclamation boundaries, survey stations and purchased reclamations tinted pink; parish labels visible but no LGA outline identified. Mention of compilation from municipal surveys does not prove municipal boundary evidence. Image/catalogue mismatch recorded; review-only under LGA focus.
- No byte or decoded-pixel duplicate found against registered JPEGs of matching dimensions. All 1030 registered paths/sizes pass; nine new originals pass hash, copied-byte and catalogue-dimension checks. Prior hashes were checked in earlier batches. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_official_remaining_review.json`.

### Sydney suburban map collection (11 October 2026)

- Source: https://collection.sl.nsw.gov.au/record/74VK65PAleNZ. Twelve images reviewed: alexandria, botany, darlington, east st leonards, enfield, hunters hill, north botany, redfern, st leonards, strathfield, victoria willoughby, waterloo.
- All twelve whole municipal maps and native municipal keys visually inspected. Collection title supplied by cataloguer; broad catalogue span 1900–1935 is not an individual map publication or legal boundary date. No printed individual calendar date located. Municipality, ward, parish, drain and tramway symbols kept separate where keyed. St Leonards distinguishes constructed/authorised tramways. Alexandria and Redfern broad brown railway corridors are not council boundaries. North Botany drain lines are not boundaries. Victoria is the historic NSW municipality in Willoughby parish. Additional clean physical scans are not proven distinct boundary editions.
- Saved 12 unchanged source scans; 0 duplicate scans not copied. All 1042 registered paths/sizes pass. New originals pass hash, copied-byte and catalogue-dimension checks; prior hashes were checked in earlier batches. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_suburban_collection_remaining_review.json`.

### Sands index map: catalogue [1890]

Source: https://collection.sl.nsw.gov.au/record/74VKwJly5w83

- Whole map and native key inspected: city boundary plus-dash, ward short dashes, tramways double thin lines. Coloured wards are within City of Sydney, not separate LGAs. Scale 8 chains/inch. Catalogue [1890] inferred from Citizens Life 1889 advertisement; no printed calendar imprint located. Cover library label 1889 is not publication evidence. Native advertisement gives 1887=19,857, 1888=34,684 and 1889=57,322 policies; catalogue transcribes 1887 as 19,557. Six companions saved separately from boundary scan; five advertisements review-only.
- Original source bytes preserved. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_sands_index_remaining_review.json`.

### Metropolitan detail key and Wells 1850: boundary evidence

- Source: https://collection.sl.nsw.gov.au/record/74VveyWjXZRZ
- Whole source views and native annotations inspected. Six scans are overlapping views of a three-sheet survey index, not six independent boundary editions. Orange labelled municipality divisions differ from green numbered survey-sheet subdivisions. Handwritten survey-sheet dates vary (including 1908); they are not one legal boundary date. Catalogue series starts 1883, with editions circa 1885/1895 and some 1920 sheets; do not assign those dates to this index. No formal municipal line sample located. A sample library request slip for Camperdown section 9 (1891) does not date the index.
- Source: https://collection.sl.nsw.gov.au/record/74VveVa3wNN3
- Eight source views inspected: four whole-map scans and four detail views of damaged copies. Native imprint on whole-map view 3 reads Sydney, N.S. Wales, Dec. 5th 1850. Inset text separately describes six municipal wards (Brisbane, Gipps, Bourke, Macquarie, Cook, Phillip) and six parishes. Boundary definitions are textual evidence; no general line key for a complete municipal perimeter located. Severe paper loss and wear prevent treating all lines as traceable. Catalogue notes an additional photocopy holding; source images alone do not establish which views belong to that photocopy. Detail views 4–6 provide cadastral context, and view 7 contains the ward/parish text panel. Those four details are companions, not additional complete boundary maps. No local stitching or boundary inference performed.
- All fourteen originals retain source bytes. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_detail_wells_review.json`.

### Sydney utility and Cook/Georges River maps: municipal evidence

- Source: https://collection.sl.nsw.gov.au/record/74VK727LQNbM
- Two whole physical holdings. Native key distinguishes City of Sydney wards (dot-dash), municipality boundaries (cross-dash), Upper Water Reserve (long dashes) and railway appropriations (black band). Coloured holding has an additional red tramway sample for existing/in-construction lines and extensive land annotations. Printed base date 1877 does not independently date that annotation layer. Municipal fill colours, native boundary lines and private subdivisions are distinct. Paper loss in coloured holding.
- Source: https://collection.sl.nsw.gov.au/record/74VvrNrwQEoy
- Two physical sheets plus library composite. Native title includes municipal district West Botany. Native explanation distinguishes municipality cross-dash, ward dashes, parish more frequent crosses, crown grants and fences. Sheet 2 native note says information charted to 1 November 1884; catalogue notes sheet 1 to 1 January 1885. These are information cut-off dates, not independently verified legal boundary dates. Cadastral bearings/distances are not municipal dimensions. Composite is supplied by library, not stitched locally.
- Source: https://collection.sl.nsw.gov.au/record/74Vv7o7JBGvO
- Two source sheets plus library composite of detail-survey index. Native key municipal boundaries long dashes and crosses. Red-tinted sheets are published detail-survey sheets; other sheets are in course of publication, and red numbers/letters identify lithographs. Red grids and publication tints are not council boundaries. Catalogue publication date retained; not an independently checked boundary effective date. Native sample 20 chains/inch scale is shared with related water/sewer index series.
- Source: https://collection.sl.nsw.gov.au/record/74VK7237qPR3
- Two source sheets plus library composite. Native key at 20 chains/inch distinguishes municipal dashed-cross lines from subdivisions, paths, watermarks and swamps. Red-tinted sheets are published detail-survey sheets; red numbers/letters identify lithographs, not councils. Act 43 Victoria No. 32 identifies water/sewer work context, not map publication or legal boundary date. Catalogue 1890 retained.
- Source: https://collection.sl.nsw.gov.au/record/74VK723kqLpb
- Two damaged source sheets plus library composite. Native key distinguishes municipal dashed-cross lines from areas sewered before Board control/by Government/by Board, low-level areas, constructed/proposed main sewers, gravitation limit, stormwater drains, resumptions and areas in course of construction. Coloured service areas are not LGAs. Printed 20 chains/inch. Severe paper loss; completeness cannot be assumed. Catalogue 1892 retained.
- Source: https://collection.sl.nsw.gov.au/record/74VKDkEQVPlg
- One whole plan. Native key municipality dot-dash lines, existing outfall sewers solid lines, and coloured fatal-case symbols by disease. Fatal-case period printed 1 January–30 June 1888 is data coverage, not a boundary effective date. Catalogue [1888], bound with Votes and Proceedings volume 4 (1889); keep publication uncertainty. No health outcome analysis performed.
- Source: https://collection.sl.nsw.gov.au/record/74VvB0rwKogg
- One whole plan, George H. Stayton signed Oct 9th 1886, scale 10 chains/inch. Native black line labelled MUNICIPAL BOUNDARY between St Leonards areas differs from green dashed line labelled LIMIT OF DRAINAGE AREA. Red/blue lines, pipe sizes, tunnels and green outfall works are proposed sewer features, not council limits. Signature dates drawing, not independently verified legal boundary date. Donation stamp 1965 is not publication date.
- 16 unchanged originals saved; 0 exact decoded duplicates. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_utility_remaining_review.json`.

### Remaining Sydney/Blue Mountains maps: statistical, defence and city evidence

- Source: https://collection.sl.nsw.gov.au/record/74VvkjqgJz83
- Two physical map holdings; view 0 has coloured outlines and damaged/missing title/inset area, view 1 has printed title/date and local sketch. Native coloured outlines inspected but no formal municipal line key or legal status located. Catalogue describes a plan of new municipalities of Randwick, Waverley and Coogee and manuscript water-reserve/Sydney-common additions. This does not establish Coogee as an adopted independent LGA, or identify every coloured outline. Save as reference/cadastral companions; exclude both from confirmed boundary scan count pending corroboration. Boundaries not inferred from parcels.
- Source: https://collection.sl.nsw.gov.au/record/74VKdrqKvk7A
- Native reference explicitly states LGAs (cities, municipalities, shires) as used in Commonwealth Census 30 June 1954. Thin LGA lines differ from bold metropolitan statistical-area boundary. City/municipality/shire fills distinguish types; red numbers and lines denote Statistical Retail Area Boundaries (1953), not LGAs. Catalogue publication 1954; census geography date directly supported by native note.
- Source: https://collection.sl.nsw.gov.au/record/74VKdagGDGx3
- Named municipal areas and outlines on dyeline base, with red protection-zone outlines/hatching. Native pencil note reads Bankstown included in Zone 1/4/42. This is a compulsory-protection zone amendment, not a Bankstown boundary change. No formal general municipality line sample located. Source municipal outline evidence retained separately from protection-zone overlay.
- Source: https://collection.sl.nsw.gov.au/record/74VKOQgKrq3g
- Native title says Defence Act of 1903–18, whereas catalogue title says Defense Act of 1908–18; preserve catalogue title and record native discrepancy. Native issue date 1 July 1918. Native black municipality/shire dot-dash key differs from red solid battalion-area lines, red dashed training-area lines and red headquarters dots. Issue date is not independent proof of each boundary legal effective date.
- Source: https://collection.sl.nsw.gov.au/record/74VvlkXvb0rA
- Front map and text/advertisement verso. Native municipal boundary plus-dash key differs from railway ladder lines, thick road symbols and half/one/one-and-half/two-mile circles around Katoomba station. Copyright Act 1905 printed on verso does not date publication. Catalogue [1926?] retained; verso saved as map companion, not boundary scan.
- Source: https://collection.sl.nsw.gov.au/record/74VvezkzNGKb
- Native city/municipal plus-dash key differs from tramway and ferry samples. Printed scale 6 chains/inch. Catalogue [1907?] estimated from tramway history; no printed publication calendar date located. Donation stamps 1961/1971 not publication evidence. Additional physical scan not proven distinct legal boundary edition.
- Source: https://collection.sl.nsw.gov.au/record/74VvkjMDAXgM
- Native title Sands six-mile circuit map 1876–77, John Sands 392 George Street. Named municipal areas and dashed-cross outlines, including West Botany, visible; no formal boundary sample located. Road, railway and natural-feature lines not treated as municipal limits. Additional State Library holding not assumed a different boundary edition from NLA holdings.
- 9 unchanged originals saved: 6 boundary scans and 3 references/companions; 0 exact decoded duplicates. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_misc_remaining_review.json`.

### Sewerage collection and commercial-power map: scope screening

- Source: https://collection.sl.nsw.gov.au/record/74VKwBVW7JQy
- All 33 catalogue previews inspected; first three originals inspected. Collection contains sewer sections, arches, foundations, pipe details and small engineering watercourse plans. No identified LGA outline in previews. No claim of full-resolution review of the other 30 drawings; geographic alignment plans remain engineering context. No originals added to LGA collection.
- Source: https://collection.sl.nsw.gov.au/record/74VKwl5gq7wd
- All four original map sheets and four later handwritten research-note leaves inspected. Native red key says boundaries of areas supplied with names of supplier, transmission lines, towns with electric supplies. Diagram K coloured areas name electricity suppliers, including Sydney City Council Electricity Dept, St George County Council and councils receiving bulk supply. These service territories are not adopted as LGA boundaries. No independent municipal line key identified on base map. Sixth edition, map 406, catalogue between 1930 and 1936 uncertain based on railways/1935 legislation. Handwritten notes discuss 1935 news and a 1954 supply-area map; later notes are not a native publication date. All eight scans review-only.
- Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_sewer_power_selection_review.json`. No files added to the registered LGA collection.

### Field of Mars sales plans and cable-tramway sketch

- Source: https://collection.sl.nsw.gov.au/record/74VKO46JQWdM
- Whole source scans and local-sketch inset inspected. Title Municipal District of Ryde locates the sales plan; it does not identify a drawn council perimeter. Native red note says land for sale is tinted red. Local sketch depicts site, named localities, roads, railway and shoreline, without an identified municipal-boundary sample. Parcel, reserve, common and cemetery edges not adopted as LGA boundaries. M85.51 is two sheets plus supplied library composite; M85.52 is one sheet. No original added to LGA collection.
- Source: https://collection.sl.nsw.gov.au/record/74Vvj6Db5egg
- Whole source scans and local-sketch inset inspected. Title Municipal District of Ryde locates the sales plan; it does not identify a drawn council perimeter. Native red note says land for sale is tinted red. Local sketch depicts site, named localities, roads, railway and shoreline, without an identified municipal-boundary sample. Parcel, reserve, common and cemetery edges not adopted as LGA boundaries. M85.51 is two sheets plus supplied library composite; M85.52 is one sheet. No original added to LGA collection.
- Source: https://collection.sl.nsw.gov.au/record/74VKDwjor26X
- Whole map and native key inspected. Native Sydney Municipal Boundary is dashed with crosses; red cable-tramway route sample and black existing tramway sample are separate. A proposed tramway does not imply proposed municipal limits. Native Plan 1, chain scale; no printed calendar imprint located. Catalogue date malformed as 1891?] and bound with Votes and Proceedings vol 5 (1891/92); retain uncertainty. Map includes named suburbs/municipalities but key specifically names Sydney municipal boundary, not a complete perimeter for every council shown.
- One unchanged municipal-boundary original saved; four sales-plan originals review-only. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_mars_cable_review.json`.

### Electoral and cadastral boundary review

- Map shewing electorates of Balmain, Refern, Glebe, Newtown, Paddington, East Sydney, South Sydney and West Sydney as per schedule 'A' of electorial bill 43 of Victoriae [cartographic material] / New South Wales Dept. of Lands. — Whole scan, native key and imprint inspected. August 1880 imprint, Office No. 978. City of Sydney wards use dot-dash, municipality cross-dash, Upper Water Reserve long-dash. Red lines and numbers identify electorates, not LGAs. Publication date does not establish legal boundary effective date. Source: https://collection.sl.nsw.gov.au/record/74Vv3q4G446X
- [Cadastral map of area near Five Dock and Drummoyne, New South Wales] [cartographic material]. — Whole scan, native header and boundary labels inspected. Parish of Concord, County of Cumberland, Sheet No. 2; map with reference in five sheets. Cross/dash municipal-boundary evidence and M.B. label near Five Dock Bay/Drummoyne; Boundary Police Act shoreline label has separate meaning. No formal general municipal key located. Partial sheet does not establish complete council perimeter. Catalogue [19--?] retained; lithograph P.95.173 not adopted as publication year. Public recreation Drummoyne Park annotation 15.6.33 is an annotation date, not boundary/publication date. Source: https://collection.sl.nsw.gov.au/record/74VKZMXQLyRZ
- New South Wales showing State electoral districts and Commonwealth electoral divisions [cartographic material] — All three original scans inspected: north and south sheets plus library composite. Catalogue [1930], Commercial Map Sixth Edition, Map 406.C. Red State electoral districts and blue Commonwealth electoral divisions/fills; no identified separate LGA outline or municipal-boundary key. Shire/municipality statistical indexes include 1928 data, not boundary outlines. No original added to LGA collection. Source: https://collection.sl.nsw.gov.au/record/74VvVMLR7ezy

### Shire index and tourist-source review

- Index to sheets of 4 chains to an inch map of Blue Mountains Shire N.S.W. — Whole original and native key inspected. Native thick red line explicitly keyed Shire Boundary, separate from thin red numbered sheet grid and prices. Katoomba Municipality is excluded inside an outlined hole. Neighbouring shire/municipality labels are location context, not proof of complete neighbouring perimeters. Catalogue [1915] is inferred publication date; no native calendar imprint located. Native publisher H.E.C. Robinson differs from catalogue publisher NSW Department of Lands. Native index scale one mile/inch; indexed sheets four chains/inch. Index is usable boundary evidence, not the indexed detailed sheets. Source: https://collection.sl.nsw.gov.au/record/74VvDjbXEvLX
- Official road & tourist guide of Erina Shire [cartographic material] : embracing Brisbane Water and Tuggerah Lakes. — Both originals inspected: road/tourist map and advertising verso. Catalogue [1935?]; green fills identify forests/reserves, native key highways/main roads/tracks/railways. No identified LGA perimeter or municipal/shire line key. Title Erina Shire alone does not identify a drawn boundary. Source: https://collection.sl.nsw.gov.au/record/74VMbVOaPpXg
- Scenic short tours within Gloucester Shire, Manning Shire, Stroud Shire, Taree Municipality, Wingham Municipality [cartographic material] / Tourist Committee. — Both originals inspected: title/text/waterway insets and tour-route map. Catalogue [194-?]. Red numbered tour routes and black roads/coastline do not identify LGA perimeters. Named shires/municipalities in title are service-area context. No identified LGA outline. Source: https://collection.sl.nsw.gov.au/record/74VKzlwZE8ZM

### NSW parish/village LGA-evidence review

- Parish of Jooriland, County of Westmoreland : Land District of Picton, Wollondilly Shire, Eastern Division N.S.W. / compiled, drawn & printed at the Department of Lands, Sydney, N.S.W. — Both originals visually inspected: fourth edition, native Date of Map 18 November 1918 and printed December 1918. Key distinguishes shire triple-cross/dash from county cross/dash, parish dot/dash, land-district and gold-field lines. Wollondilly and Wingecarribee shire labels flank mapped boundary; coverage is part of their perimeters. Two physical holdings have different annotations/damage; not two legal boundary editions. Catalogue lease-lot annotations and donation/holding marks do not date council limits. Source: https://collection.sl.nsw.gov.au/record/74Vv3qD4VM8Z
- Parish of Jamberoo, County of Camden [cartographic material] : Land Districts of Kiama & Moss Vale, Wingecarribee Shire, Eastern Division N.S.W. / compiled, drawn and printed at the Department of Lands. — Whole original and native key/date/boundary label inspected. Sixth edition, Date of Map 24 March 1910. Key distinguishes Borough cross/dash and Shire triple-plus/dash from parish/land-district/reserve/private-subdivision lines. Native Borough of Shellharbour Proclaimed 5 January 1880 and Borough of Jamberoo Proclaimed 30 October 1890 are printed historical statements, not publication dates or independently verified legal perimeter dates. Wingecarribee shire title does not imply whole-shire coverage. Source: https://collection.sl.nsw.gov.au/record/74VvvZ7WwJpb
- Parish of Harwood, County of Clarence : land district of Grafton, Eastern Division N.S.W. Harwood Shire / compiled, drawn and printed at the Department of Lands, Sydney, N.S.W. — Whole original inspected. Third edition, catalogue 1908, Date of Map 21 December 1908 in catalogue. Native key parish, reserves, observation station and population; Harwood Shire appears in title without an identified council outline. Population/proclaimed-area and parish lines not adopted as LGAs. Source: https://collection.sl.nsw.gov.au/record/74VvvDNmlJKZ
- Parish of Amungula, County of Murray [cartographic material] : Land District of Queanbeyan, Yarrowlumla Shire / compiled, drawn and printed at the Department of Lands, Sydney, N.S.W. March 1909. — Both originals inspected. Third edition, catalogue 1909. Native key parish, gold field, reserves, trig station and coal/mining reservation, without a shire line sample or identified LGA perimeter. Yarrowlumla Shire title locates map. Population area of Queanbeyan, reserve/classification area and gold field are not adopted as municipal boundaries. Source: https://collection.sl.nsw.gov.au/record/74VvOlLNB8jA
- Parish of Nattung, County of Cowley [cartographic material] : Land District of Cooma, Monaro Shire, Eastern Division / compiled, drawn and printed by the Department of Lands. — Whole original and native date/key inspected. Second edition, Date of Map 9 November 1915, printed December 1915. Key explicitly distinguishes shire triple-plus/dash from county cross/dash, parish and gold-field/reserve lines. Named Monaro, Gadara, Tumut, Dalgety shire context and mapped lines cover boundary portions only. Coodradigbee Gold Field proclamation 4 December 1897 is a separate historical layer, not map/LGA date. Source: https://collection.sl.nsw.gov.au/record/74Vvv0KgwLqA
- Parish of Balerang, County of Benarba, Land District of Moree, Boomi Shire, Central Division N.S.W. [cartographic material] / compiled, drawn & printed at the Department of Lands. — Whole original and native key inspected. Third edition, catalogue 1918. Native key parish, county, reserve, occupation licence and public roads, without identified shire outline. Boomi Shire title locates parish. Gwydir railway and GIL GIL river not adopted as council boundaries without separate evidence. Source: https://collection.sl.nsw.gov.au/record/74Vv6lqWo3Py
- Map of Village of Southgate : Parish of Southgate, County of Clarence, Copmanhurst Shire [cartographic material] — Whole original and native key inspected. Village and Suburban boundary samples are separate from Shire Roads & streets; these are not an identified Copmanhurst council perimeter. Native note village proclaimed Gazette 20 March 1885 and boundaries re-notified 24 January 1919; do not assume LGA status. Native bottom draughting annotation F.W.B. 15 April 1929 conflicts with catalogue [1920?]; retain uncertainty. Review-only under current LGA focus. Source: https://collection.sl.nsw.gov.au/record/74VvKlbm2NeX

### Coastal NSW parish LGA-evidence review

- Parish of Jillaga, County of Dampier [cartographic material] : Land District of Moruya, Eurobodalla Shire, Eastern Division, N.S.W. / compiled, drawn and printed at the Department of Lands, Sydney. — Whole original, native date and key inspected. Second edition, map 13 December 1913, printed December 1913. Native shire triple-plus/dash is distinct from land-district double-plus/dash, parish dot/dash and resumed-area cross/dash. Tallaganda Shire and Shoalhaven land-district labels are distinct; western boundary labelled approximate position of watershed. Retain that approximation; not a surveyed legal perimeter. Coverage is a portion of Eurobodalla/Tallaganda boundary; resumed areas 1113/696 are not LGAs. Paper loss at upper margin. Source: https://collection.sl.nsw.gov.au/record/74Vvv0lgA57A
- Parish of Coondella, County of Dampier [cartographic material] : Land District of Moruya, Eurobodalla Shire, Eastern Division N.S.W. / compiled, drawn and printed at the Department of Lands, Sydney. — Whole original inspected. Fourth edition, catalogue 1914; native key parish boundary, reserve, classified area, trig station and permanent marks, without identified LGA outline. Eurobodalla Shire title locates parish. Crown lease classification and resumed-area lines not adopted as council limits. Source: https://collection.sl.nsw.gov.au/record/74Vvv0gP2poy
- Parish of Bumbo West, County of Dampier [cartographic material] : Land District of Moruya, Eurobodalla Shire, Eastern Division N.S.W. / compiled, drawn and printed at the Department of Lands, Sydney. — Whole original inspected. Third edition, catalogue 1913; native key parish, reserve and gold-field lines, without identified LGA outline. Eurobodalla Shire title locates parish. Gold leases, mining tenements, GULPH gold-field extension and mining-purpose reserve 37848 are not council boundaries. Source: https://collection.sl.nsw.gov.au/record/74VvvbQ5EQWd
- Parish of Uranbene, County of Dampier [cartographic material] : Land District of Moruya, Eurobodalla Shire, Eastern Division N.S.W. / compiled, drawn and printed at the Department of Lands, Sydney, N.S.W. — Whole original and native date/key inspected. Second edition, map 19 November 1913, printed December 1913. Shire triple-plus/dash is distinct from parish, land-district, resumed-area and classified-area lines. Tallaganda shire versus Shoalhaven land district labels distinguish concepts. Western boundary labelled approximate position of watershed; retain source approximation. Bendethera public recreation/resumed area 1022 and resumed area 1036 are separate land layers, not council limits. Partial boundary coverage; lower-margin paper loss. Source: https://collection.sl.nsw.gov.au/record/74VvvBL0rQdM

### Regional shire-map evidence review

- Richmond-Tweed region [cartographic material] : showing statistical units & unimproved land values / drawn and printed at the Department of Lands, Sydney. — Whole original, native key and imprint inspected. Native black triple-plus/dash identifies shire names/boundaries; thick black dot/dash region perimeter is separate. Red solid/dashed police patrol/subdivision boundaries are as at 31 March 1941; that date does not establish shire boundary effective dates. Red numbers and factory symbols are separate. Colour fills identify unimproved land-value bands in pounds per acre, not councils. Catalogue malformed 1944?] normalised [1944?]; native imprint 44.673 is a printing identifier, not independently dated publication. Catalogue holding note tendered 7 November 1944 is not map/boundary date. Native Map No. 10 versus catalogue No. [7] reflects pasted number described by catalogue. Named region includes shires/localities; do not assume complete municipal perimeters from locality labels. Source: https://collection.sl.nsw.gov.au/record/74VKZdGpOaLd
- Map of the principal roads between Sydney and Newcastle [cartographic material] / James Emery. — Whole original and native key inspected. Catalogue [1938?], copyright Lake Macquarie Shire Council. Native key identifies Pacific Highway, main/other roads, roads under construction and tracks; railways also drawn. No identified LGA outline or municipal/shire-boundary key. Council copyright and tourist-district title do not establish a council perimeter. Source: https://collection.sl.nsw.gov.au/record/74VKqzk7LWdM
- Liverpool plains, No. 47 [cartographic material] : counties of Buckland, Darling, Nandewar, Parry and Pottinger. — Whole original and native key/title inspected. Shire boundaries use triple-plus/dash; riding boundaries use single-plus/dash and A/B/C labels. Native title Local Government Act 1906 names legislation, not a publication date. Catalogue [1906?] retained; native No. of Lith. 07.158 D. differs from catalogue D7.158 D. and is not independently dated as 1907. Counties/parishes/numbered parcels and surrounding advertisements are separate. Original sheet is one scan with advertising margins, not a locally cropped or stitched map. Native title Liverpool Plains No. 47 does not establish every named neighbouring shire perimeter. Source: https://collection.sl.nsw.gov.au/record/74VKwllydGE3

### South coast and Dunphy municipal-proposal review

- Map of south coast embracing Waterfall, Appin and Bulli [cartographic material] / N.M. Melville. — Whole original and native key inspected. Native copyright N.M. Melville 3 April 1933; catalogue 1933. Key National Park Boundary is distinct from roads, tracks and negotiable routes, but no identified shire/municipal outline. National Park boundary is not adopted as an LGA. Library deposit/copyright annotations not used to date council limits. Source: https://collection.sl.nsw.gov.au/record/74Vv8pJaEp7O
- Map of Waterfall-Otford and district [cartographic material] / R. Ward. — Whole cyanotype original inspected. Catalogue [1932?]; native magnetic variation 1932, R. Ward 2360 is an identifier. Native reference roads, railways, tracks, trig stations and marshes; National Park boundary labelled separately. No identified LGA outline. Park/rail/track lines not adopted as councils; magnetic-variation year not boundary effective date. Source: https://collection.sl.nsw.gov.au/record/74Vv8RJx7E6X
- One-day walking tours in the area between Sutherland and Stanwell Park [cartographic material] / compiled by George H. Matheson ; map drawn by G.J. de Courcy Lewis. — Both originals inspected: native NSW Railways 1933 walking-tour map and verso with 33 numbered tour descriptions. Native key railways, roads, tracks and sign posts; route numbers and vegetation/hachures not LGA divisions. No identified council outline; neither map nor verso added to LGA collection. Source: https://collection.sl.nsw.gov.au/record/74Vv8pKEr623
- Proposed scheme for the reservation of the popular Garawarra coastal strip as a much-desired "primitive area" park [cartographic material] : for that increasing section of the public which have used it for walking tours ... / Myles J. Dunphy. — Both supplied originals are map sheets of Heathcote parish sixth-edition base, Date of Map 23 August 1911, printed September 1911. Sheet 2 key explicitly distinguishes Shire triple-plus/dash and Municipal triple-dash/cross from parish, national park hatching, reserve/classified area, village/suburban/urban, police-offences boundary and railway lines. Sutherland, Bulli and adjoining municipality boundary portions depicted; no full-council coverage claim. Later coloured Garawarra park proposal is signed November 1932; park proposal does not update all underlying LGA lines to 1932 or imply proposed council limits. Library 1933 call-number and donation date not map dates. Originals kept as supplied, not stitched. Source: https://collection.sl.nsw.gov.au/record/74VKM55DZkm3
- [Kowmung River - Coxs River region] [cartographic material] / [by Myles J. Dunphy] — Whole tracing original and native-size north/south detail inspected. Catalogue [1935?], supplied title. Faint red Blue Mts Shire and Oberon Shire are locality/context labels; no identified separate LGA boundary key/line. Red Crown Lands area 2984 and dashed annotations not adopted as council perimeter. Double river banks, creeks and cliffs are geographic features; no inferred council line from watercourses. Review-only; no council outline identified. Source: https://collection.sl.nsw.gov.au/record/74VvlJlqyWVO
- [Proposed Blue Mountains National Park] [cartographic material] / alternative scheme by National Parks and Primitive Areas Council, Jan., 1936. — Whole coloured dyeline original and native outcome note inspected. Native National Parks and Primitive Areas Council January 1936 alternative scheme; areas A/B explicitly proposed additions to Katoomba Municipality, with existing Municipality of Katoomba F and Blackheath E depicted separately from park/primitive areas, water reserve, cliffs and proposed scenic roads. Sublime Point area D retained by Katoomba is marked approximate. Later undated red Result: Areas G and H were added to Municipality of Katoomba is a source annotation, not independently verified legal outcome/date. Colours/hatching and area table serve scheme divisions, not all present councils. Save as proposed local-government boundary evidence. Source: https://collection.sl.nsw.gov.au/record/74VvljAlW8gl
- [Proposed Blue Mountains National Park] [cartographic material] / [proposed by the] National Parks and Primitive Areas Council, Jan., 1936. — Whole ink-on-linen original inspected. Native National Parks and Primitive Areas Council January 1936. A/B labelled proposed additions to Katoomba; existing Katoomba F and Blackheath E depicted. Primitive/park areas, water reserve C, proposed scenic roads (dotted), railway and serrated cliffs are distinct concepts. Sublime Point D retained by Katoomba marked approximate. No adoption assumed from proposal. Shares underlying scheme geography with alternative holding, but separate original material/annotations; not claimed as independent legal edition. Source: https://collection.sl.nsw.gov.au/record/74VvljALMgJd
- Sketch map of Narrow Neck Peninsula [cartographic material] / National Parks and Primitive Areas Council, Oct 1935. — Whole original and native proposal note inspected. Native present municipal boundary explicitly labelled; note says Katoomba Municipal Council applied for portions/parts outlined in red to be added. Native National Parks and Primitive Areas Council October 1935. Red proposal outlines and existing boundary distinguished from thick cliffs, streams and parcel numbers (114/115 etc.). An application is not an adopted legal boundary. Sketch scale one mile; partial Katoomba/Narrow Neck coverage, not surveyed complete perimeter. Source: https://collection.sl.nsw.gov.au/record/74VvljXk8JKZ

### Sydney-area parish LGA review — 11 October 2026

- Seven originals reviewed; six registered unchanged. Keys and native imprints checked.
- Banksia: third edition, map 22 September 1908, printed October 1908. Native title says Wollondilly & Nattai Shires; catalogue says Wollondilly and Mittagong. Preserve the conflict. Shire triple-plus/dash differs from land-district double-plus/dash and parish dot/dash.
- Eckersley: fifth edition, map 11 August 1914, printed October 1914. Municipal cross/dash and shire triple-plus/dash are distinct from reserves, land districts, population areas and roads. Partial Sutherland, Wollondilly, Bulli and Campbelltown lines.
- Bala: third edition, map 25 October 1909, printed December 1909. Cessnock/Colo shire line shown. Native warning says the map is only approximately correct.
- Oldbuck: fifth edition, map 4 January 1915, printed February 1915. Two holdings show Wollondilly/Mulwaree and Nattai portions; annotations and damage differ. They are not two verified legal editions.
- Mangrove: third edition, map 18 August 1909, printed November 1909 (native imprint checked). Colo/Erina shire line is distinct from land districts, classified lease area and reserve notices.
- Hawkesbury: second edition, map 27 February 1908, printed March 1908. Within Colo Shire locates the parish only. Native key identifies county/parish/reserve lines; no LGA outline identified. Review-only.
- All accepted sheets provide partial council limits. Reserve/population-area notices do not date LGA boundaries. No legal adoption or complete-perimeter claim.
- Six new files pass hashes, decoded catalogue dimensions and RGB duplicate checks. All 1,111 registered paths and sizes pass; 956 boundary JPEG scans include 12 indexes. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_sydney_parish_remaining_review.json`.

### Windsor, Blue Mountains and lower Hunter parish review — 11 October 2026

- Six originals reviewed; four registered unchanged. Native keys and imprints inspected.
- Strathdon: seventh edition, map 25 February 1914, printed March 1914. Two holdings show portions of Blue Mountains, Colo and Nepean shires and Castlereagh/Penrith municipalities. Municipal/shire symbols differ from town, suburban, population, county, parish and reserve lines. One holding has coloured historical-road traverses dated 1813–1830s; these are not LGA limits or dates. Population area proclaimed 10 April 1886 is separate. Two holdings are not two verified legal editions.
- Cook, County of Hunter: second edition, map 3 September 1909, printed October 1909. Native key and full-resolution Colo River detail distinguish shire triple-plus/dash from layered county cross/dash and land-district double-plus/dash. Colo/Blaxland shire portions shown. Native warning: This Map is only approximately correct. Trial line and classification reserve are not council limits.
- Finchley: third edition, map 19 October 1911, printed October 1911. Native Cessnock Shire differs from catalogue Kearsley Shire; preserve conflict. Keyed shire line along northern watercourse adjoining Patrick Plains, distinct from land districts, classified area and roads. Native approximation warning retained. Notice 19 August 1908 is not an LGA date.
- Parr and Palomorang: second editions, map 20 September 1909, printed October 1909. Titles locate parishes in Colo/Patrick Plains shires, but mapped lines and keys identify county, parish, land districts and reserves only; no LGA outline identified. Both review-only. Classification notices from 1906/1907 do not date council limits.
- Accepted maps give partial council limits; no complete-perimeter or legal-adoption claim. Four new files pass hashes, copied-file hashes, decoded catalogue dimensions and RGB duplicate checks. All 1,115 registered paths/sizes pass; 960 boundary JPEG scans include 12 indexes. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_windsor_hunter_remaining_review.json`.

### Southern and mixed NSW parish review — 11 October 2026

- Six originals reviewed; three registered unchanged. Native keys and map dates inspected.
- Parish of Cookbundoon, County of Argyle: Native map 5 June 1911; catalogue printed July 1911. Fourth edition trigonometrical compilation. Whole original and native key inspected. Mulwaree Shire title locates parish; no identified LGA outline. Key parish, reserve, goldfield extension, meridian observations, trig stations, reserve from lease, classified areas and public roads. Argyle/Camden/King goldfield and proclamation 29 November 1881 are not council boundaries/dates. Review-only.
- Parish of Wollumboola, County of St Vincent: Native map 27 January 1904; printed March 1904. Third edition. Native municipal cross/dash key and mapped line around Numbaa along Crookhaven watercourse verified at native resolution. Municipal line differs from parish, private subdivisions, reserves, goldfield and soundings. Catalogue title adds Clyde Shire, which is not in the native title; do not relabel native 1904 municipal evidence as a Clyde shire edition. Coolangatta goldfield, Crookhaven Park reserve dates and private towns of Greenwell/Jervis are separate concepts. Partial municipal evidence only.
- Parish of Farnham, County of St Vincent: Native map 27 April 1938. Seventh edition. Whole original and native key inspected. Clyde Shire title locates parish; no identified council outline. Heavy mapped border near Commonwealth Territory is keyed State and Commonwealth, distinct from land-district, parish, reserve, state forest and bird/animal sanctuary lines. State/Commonwealth border is not adopted as LGA evidence. Sanctuary proclamation 26 February 1937 and reserve notices do not date council limits. Review-only.
- Parish of Collector, County of Argyle: Native map 5 November 1907; printed December 1907. Third edition. Whole original and native bottom key inspected. Within Gunning Shire locates parish; no identified LGA outline. Native key parish, county, land district, goldfield, reserve from sale, town, suburban, trig station, classified areas and annual-lease reserve. Town/suburban limits are cadastral settlement concepts, not accepted as municipal limits. Goldfield proclamation and reserve notices not LGA dates. Catalogue title names Gunning and Mulwaree; native within-Gunning statement retained. Review-only.
- Parish of Parkes, County of Hawes : Land Districts of Walcha & Scone, Aspley & & Nundle Shires, Eastern Division, N.S.W. / compiled, drawn and printed at the Department of Lands, Sydney, N.S.W., July 1912.: Native map 15 July 1912; printed July 1912. Fourth edition. Native title Apsley & Nundle Shires (catalogue Aspley typo retained separately). Native shire triple-plus/dash key differs from county cross/dash, land-district double-plus/dash, resumed area, reserve and classified area. Full-resolution central divide shows layered shire/land-district symbols; Apsley/Nundle and adjoining Woolooma portions depicted. Scone/Walcha/Tamworth are land districts. Tomalla resumed area and Sarton goldfield are not council limits; no complete perimeter/legal adoption claim.
- Parish of Ooma, County of Forbes: Native map 30 January 1959. Fifth edition. Native Weddin & Jemalong Shires and key shire triple-plus/dash inspected; faint mapped line portions along road/land-district divisions distinguished from public-road pattern and land-district double-plus/dash. Key separately identifies county, parish, cadastral town/suburban/urban, municipality, catchment, police-offences, pastures-protection, goldfield and reserve concepts. Native Within Pastures Protection District of Forbes and Lachlan Gold Field Procd 31 August 1865 are not LGA boundaries or effective dates. Partial, faint council boundary evidence only; not a complete legal perimeter.
- Three additions pass hashes, copied-file hashes, decoded catalogue dimensions and RGB duplicate checks. All 1,118 registered paths/sizes pass; 963 boundary JPEG scans include 12 indexes. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_southern_mixed_remaining_review.json`.

### Regional NSW parish and Bathurst review — 11 October 2026

- Six originals reviewed; three registered unchanged. Native keys, line detail and dates inspected.
- Map of Stockdale, County of Buccleuch, within Land District of Gundagai, Adjungbilly Shire: Catalogue [18--?]; native date unresolved. Whole original and native key inspected. Adjungbilly Shire title locates private land holding. Key parish, reserved roads, freehold lands and title volumes/folios; five coloured numbered holdings are not council divisions. No identified LGA outline. Catalogue uncertain nineteenth-century date retained without assigning shire-effective year. Review-only.
- Parish of Erasa, County of Forbes: Native map 9 July 1958. Seventh edition. Native key shire triple-plus/dash distinguished from land-district double-plus/dash, parish, goldfield, reserves, public roads, catchment double-cross/dash and state forest. Native south-road detail shows layered shire/land-district line portions adjoining Weddin from Jemalong. Within Forbes Pastures Protection District, Forbes Catchment Area proclaimed 12 December 1919, bird/animal sanctuary 2 December 1932, Lachlan Goldfield 31 August 1865 and eastern goldfield extension 1 December 1888 are separate layers, not LGA dates. Partial council evidence only.
- Parish of Pringle, County of Pottinger: Native map 27 November 1918; catalogue 1918. Third edition. Whole original and native key inspected. Tamarang Shire title locates parish only. Key parish, reserve, O.L., dividing line, classified areas, territorial/land district, public roads, trig stations and sale/lease reserves. Large black dashed Gunnedah/Murrurundi/Central/Eastern division line is not a shire outline. More Devil resumed area 532/532A and lease notices are not LGA boundaries/dates. Review-only.
- Parish of Wadbilliga West, County of Dampier: Native map 6 March 1913; printed April 1913. Second edition. Native key distinguishes shire triple-plus/dash from land-district double-plus/dash, parish, holding cross/dash and reserve from sale. Full-resolution Tuross River detail shows separate layered shire and land-district symbols along Eurobodalla/Monaro line. Resumed area 699 internal cross/dash and straight holdings are not LGA lines. Partial western/southern council evidence only; no complete perimeter/legal adoption claim.
- Parish of Eden, County of Auckland: Native map 23 October 1916; printed November 1916. Fourth edition. Whole original and native key inspected. Imlay Shire title locates parish; no identified LGA outline. Key parish, town, suburban, population, police acts, goldfield, reserve, meridian observation, classified area and public roads. Town/suburban cadastral limits, police-act line and Twofold Bay shore are not accepted as council limits. Reserve 34353 and Eden population proclamation 9 January 1885 are not LGA dates. Review-only.
- Map of the City of Bathurst and part of suburban lands: Native printed 29 September 1911. Fifth edition. Whole original, north boundary, explanatory key and native imprint inspected. Native key explicitly distinguishes Municipality of Bathurst cross/dash from City cadastral and Suburban lines notified 20 February 1897, goldfield and reserves. Abercrombie/Turon shire portions also labelled/mapped. Native statements city proclaimed 20 March 1885, municipality 13 November 1862, and Towns Police Act 14 December 1858 boundary identical with municipal boundary are source claims, not independently verified legal dates/equivalence. Partial municipal/shire coverage; no complete-perimeter claim.
- Three additions pass hashes, copied-file hashes, decoded catalogue dimensions and RGB duplicate checks. All 1,121 registered paths/sizes pass; 966 boundary JPEG scans include 12 indexes. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_regional_parish_remaining_review.json`.

### Riverina parish LGA review — 11 October 2026

- Six originals reviewed; three registered unchanged. Native keys, line detail and dates inspected.
- Parish of Womboota, County of Cadell: Native map 17 November 1915; printed November 1915. Second edition. Whole original and native key inspected. Murray Shire title locates parish only; no identified council outline. Key parish, sale reserve, public roads, town, suburban and classified areas. Native town/suburban cadastral limits near village of Womboota are not accepted as municipal limits. Freehold parcels and roads not councils. Review-only.
- Parish of Nowranie, County of Urana: Native map 19 July 1917; printed August 1917. Third edition. Native Wunnamurra Shire differs from catalogue Wannamurra spelling. Key shire triple-plus/dash differs from parish, sale reserve and public roads. Eastern line explicitly labelled Shire & Parish boundary and has triple-plus symbols adjoining Urana Shire; northern Billabong Creek also forms depicted shire portion. Within Jerilderie Water Supply Catchment Area and Water District proclaimed 17 January 1896 is a separate jurisdiction/location notice, not council boundary date. Partial council coverage only.
- Parish of Gwynne, County of Wakool: Native map 1 December 1916; printed December 1916. Third edition. Whole original and native key inspected. Windouran title and neighbouring Wakool Shire label locate councils, but key identifies land-district double-plus/dash, parish, public roads, dividing line and P.O.L.; no separate identified LGA line. Western Hay/Balranald South district line and Tchelery lease blocks are not inferred to be council boundaries. Source paper loss at top retained. Review-only.
- Parish of Howell, County of Urana: Native map 2 June 1917; printed June 1917. Second edition. Native key distinguishes shire triple-plus/dash from county cross/dash, land-district double-plus/dash, parish, reserves, O.L., classified area and roads. Full-resolution western boundary shows triple-plus symbols between Urana and Yanko Shire, with Narrandera land district and Boyd/Gonne county portions separately named. Yarrabee and Goree lease blocks/reserve 36005 notified 10 June 1903 are not LGA boundaries or dates. Partial council evidence only.
- Parish of Bingellibunbi, County of Townsend: Native map 12 August 1909; printed November 1909. Second edition. Whole original and native key inspected. Windouran title locates parish only; no identified LGA outline. Key parish, land-district double-plus/dash, resumed area, dividing line, sale reserve and roads. Hay/Deniliquin district division and Zara/Caroonboon resumed areas 393/257 are not adopted as council boundaries. Review-only.
- Parish of Wononga, County of Townsend: Native map 10 November 1917; printed November 1917. Second edition. Native key includes separate parish, county, land district, shire, sale reserve, occupation licence and dividing-line symbols. Native-size eastern straight-line detail explicitly labels Land District, Shire and County Boundary; accept this directly labelled coincident boundary, not an inference from adjacent Conargo/Urana shire names. Wunnamurra neighbour named on map. Watercourses with county crosses alone and Goree/Hartwood/Yanko occupation licence blocks are not separately inferred as shire outlines. Partial council coverage only; no complete legal perimeter claim.
- Three additions pass hashes, copied-file hashes, decoded catalogue dimensions and RGB duplicate checks. All 1,124 registered paths/sizes pass; 969 boundary JPEG scans include 12 indexes. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_riverina_remaining_review.json`.

### Neighbouring Riverina parish review — 11 October 2026

- Six originals reviewed; two registered unchanged. Native keys, line detail and dates inspected.
- Parish of Bookit, County of Wakool: Native map 6 July 1936. Third edition. Whole original and native key inspected. Wakool Shire title and Murray Shire neighbour label locate councils; no identified separate LGA outline. Key parish, county, sale reserve, public/closed roads, observation station and Water Trust District circle/dash. Within Wakool Domestic and Stock Water Supply and Irrigation District Gazette 17 June 1932 is not an LGA boundary/date. Moulamein Pastures Protection Board hatching not councils. County/water-trust line along rivers not inferred as LGA. Review-only.
- Parish of Yanko, County of Urana: Native map 17 June 1916; printed July 1916. Second edition. Whole original, native key and northern road detail inspected. Wunnamurra title and adjoining Murrumbidgee Shire label locate councils, but key identifies county cross/dash, parish, reserves, occupation licence, dividing line, classified area, public roads and land-district double-plus/dash. Native northern road has county/land-district symbols; no directly identified LGA outline. Kulki occupation licence 431 and county of Boyd are separate concepts. Review-only.
- Parish of Colkmannan, County of Urana: Native map 16 September 1914; printed October 1914. Third edition. Native shire triple-plus/dash key distinguished from county cross/dash, parish, reserve, occupation licence, land-district double-plus/dash and roads. Native western detail shows three-plus shire line adjoining Wunnamurra; northern Murrumbidgee and Yanko shire portions also depicted around Urana. Narrandera is land district, Boyd a county. Goree occupation licence 454 and lease parcels are not council divisions. Partial boundary evidence only; no complete legal perimeter claim.
- Parish of Kirrabirri, County of Wakool: Native map 10 April 1916; printed May 1916. Third edition. Whole original and native key inspected. Windouran title locates parish only; no identified LGA outline. Native key county cross/dash, parish, sale reserve, classified area and public roads. County of Townsend label and Billabong Creek county line are not inferred as shire boundary. Land set apart 1904 and reserve notices not council-effective dates. Review-only.
- Parish of Broome, County of Urana: Native map 9 December 1919; printed February 1920. Fourth edition. Whole original and native key inspected. Jerilderie Shire title locates parish only; no identified council outline. Native key county, parish, reserve, occupation licence, classified area, public roads and sale/lease reserve. Bundure O.L. 604 and Yanko P.O.L. 421 are lease areas, not councils. Catalogue publication 1919 differs from native February 1920 imprint; preserve map and print dates. Review-only.
- Parish of Bundure, County of Urana: Native map 13 August 1915; printed September 1915. Second edition. Native key explicitly distinguishes shire triple-plus/dash from parish dot/dash, occupation licence, dividing line and public roads. Native eastern straight-line detail shows triple-plus shire symbols adjoining Urana across Douglas/Paloumbo parishes, with Wunnamurra on title. Broome side and Billabong Creek/lease blocks are not separately assumed to be LGA limits. Bundure occupation licence 604 and parcel boundaries are distinct. Partial council evidence only; source folds/edge damage retained.
- Two additions pass hashes, copied-file hashes, decoded catalogue dimensions and RGB duplicate checks. All 1,126 registered paths/sizes pass; 971 boundary JPEG scans include 12 indexes. Review: `explore/output/2026-10-10_download-boundary-maps/slnsw_riverina_neighbours_review.json`.

### Riverina west parish maps — 11 October 2026

- **Yathong South** — Native map 25 January 1916; printed March 1916. Third edition. Whole original and native key inspected. Wunnamurra title locates parish only; no identified LGA outline. Key parish, reserve, occupation licence, reserve from lease, classified area, sale/lease reserve and public roads. Jerilderie Water Supply Catchment Area and Water District proclaimed 17 January 1896 is not an LGA boundary/date. Billabong Creek and adjoining parish limits not inferred as council lines.
- **Cadell** — Native map 26 November 1914; printed December 1914. Third edition. Whole original and native key inspected. Wunnamurra title locates parish only; no identified LGA outline. Key parish, public roads, occupation licence and dividing line. Bundure occupation licence 604 and cadastral blocks are not council divisions. This parish of Cadell in Urana County is distinct from the adjoining Cadell Shire on the Mia Mia map.
- **Mein** — Native map 19 August 1915; printed September 1915. Third edition. Whole original and native key inspected. Wakool Shire title locates parish only; no identified LGA outline. Key parish, reserve from sale, occupation licence, dividing line, classified area and public roads. Moolpa O.L. 123 and Mooloomoon O.L. 89 are lease areas, not councils.
- **Mia Mia** — Native map 30 August 1919; printed September 1919. Third edition. Whole original, native key, eastern Murray River and western detail inspected. Native shire triple-plus/dash distinguished from county cross/dash, parish, public roads and preferential occupation licence. Murray River detail shows shire triple-plus and county crosses together, with adjoining Cadell Shire in Murray County and Wakool on title. Partial coincident shire/county boundary evidence only; not a complete council perimeter. Barham P.O.L. 651A and reserve/forest notices are not LGA divisions or effective dates.
- **Liewa** — Native map 15 November 1919; printed December 1919. Third edition. Whole original and native key inspected. Wakool Shire title locates parish only; no identified LGA outline. Key county cross/dash, parish, eighteenth-section lease, preferential occupation licence, public roads, sale/lease reserve and State Forests boundary. Liewah P.O.L. 144, forest dedication and river/reserve notices are not council evidence. County-only river lines not inferred as LGA.
- **Yarrein** — Native map 12 January 1916; printed March 1916. Third edition. Whole original and native key inspected. Wakool Shire title locates parish only; no identified LGA outline. Key parish, sale/lease reserve, occupation licence, dividing line, observation station, public roads and eighteenth-section lease. Liewah P.O.L. 144, reserve 40608 and lease notices are not council divisions or effective dates. Edward and Wakool river/parish limits not inferred as LGA.

One untouched original added; total 1,127 files, 10,007,112,391 bytes and 972 boundary JPEGs (including 12 boundary indexes). Counts are physical scans, not unique legal boundary editions. SHA-256, copied bytes, catalogue dimensions and RGB duplicate checks pass for the addition; all registered paths and sizes pass. Six-image review checkpoint: `explore/output/2026-10-10_download-boundary-maps/slnsw_riverina_west_remaining_review.json`.

### Kurnell branch railway lead — 11 October 2026

Both whole originals and native title, colour note and companion text inspected. Appendix A2 map copied from Office Map June 1884; reserves examined 14 August 1884; source warns map only approximately correct. Parish of Sutherland and Liverpool/Campbelltown land districts are not municipal limits. Pink edges show land to be resumed; green edges notified reserves; red route is proposed railway, as companion confirms. National Park dedication 3 August 1880 is separate from LGA boundaries. Appendix A1 page 26 accompanies evidence of J. J. Whitton dated 15 June 1887 and includes Alfred Vine report 8 November 1884 plus November 1884 correspondence. No directly identified LGA outline on either sheet; both review-only. Review checkpoint: `explore/output/2026-10-10_download-boundary-maps/slnsw_kurnell_branch_remaining_review.json`. No raw collection additions.

### Boyd County parish maps — 11 October 2026

- **Mycotha** — Native map 30 March 1916; printed April 1916. Second edition. Whole original and native key inspected. Murrumbidgee title locates parish only; no identified LGA outline. Key parish, reserve, occupation licence, public roads and classified area. Tubbo O.L. 620, land parcels and lease blocks are separate from councils.
- **Peter** — Native map 19 February 1919; printed March 1919. Second edition. Whole original, native key and southern line detail inspected. Native shire triple-plus/dash distinguished from parish and public roads. Southern road line explicitly labelled Parish, County, Land District, Shire and Occupation Licence Boundary; adjoining Jerilderie Shire in County/Land District Urana, with Murrumbidgee on title. Accept partial coincident boundary evidence; not a complete legal perimeter. Tubbo O.L. 620 and reserve notices are separate concepts.
- **Waddaduri** — Native map 24 January 1919; printed February 1919. Second edition. Whole original and native key inspected. Murrumbidgee title locates parish only; no identified LGA outline. Key parish, reserve from sale and reserve from licence/lease. Public-road enclosure permission and reserve notices not council boundaries or effective dates.
- **Oolambeyan** — Native map 10 December 1918; printed December 1918. Second edition. Whole original, native key and western detail inspected. Native shire triple-plus/dash distinguished from parish and public roads. Western line explicitly labelled Shire, County and Parish Boundary; triple-plus symbols and adjoining Waradgery Shire in County Waradgery, with Murrumbidgee on title. Partial coincident boundary evidence only; land holdings and roads are not separately assumed to be council limits. Map and imprint both December 1918.
- **Gundadaline** — Native map 29 June 1918; printed August 1918. Second edition. Whole original and native key inspected. Murrumbidgee title locates parish only; no identified LGA outline. Key parish, reserve from sale, public roads and classified area. Reserve 42753 notified 27 May 1908 and road enclosure permission are separate from LGA boundaries/dates.
- **Kabarabarabejal** — Native map 5 March 1913; printed March 1913. Third edition. Whole original, native key and southern detail inspected. Native shire triple-plus/dash distinguished from county crosses, parish, sale/lease reserves, permanent mark and public roads. Southern road depicts triple-plus shire line adjoining Windouran and Conargo in County Townsend; western line adjoins Waradgery Shire, with Murrumbidgee on title. Partial coincident shire/county evidence only; no complete council perimeter claim. Timber/stock/camping reserve 38302 notified 7 September 1904 and land-holding limits are separate concepts.

Three untouched originals added; total 1,130 files, 10,071,726,404 bytes and 975 boundary JPEGs (including 12 boundary indexes). Counts are physical scans, not unique legal boundary editions. SHA-256, copied bytes, catalogue dimensions and RGB duplicate checks pass for additions; all registered paths and sizes pass. Six-image review checkpoint: `explore/output/2026-10-10_download-boundary-maps/slnsw_boyd_remaining_review.json`.

### Boyd County neighbouring parish maps — 11 October 2026

- **Duderbang** — Native map 28 January 1919; printed February 1919. Second edition. Whole original and native key inspected. Murrumbidgee title locates parish only; no identified LGA outline. Key parish, occupation licence, dividing line and observing station. Kerarbury P.O.L. 582A and land holdings are not council divisions. Reserve notices are not LGA effective dates.
- **Dow** — Native map 22 October 1918; printed November 1918. Second edition. Whole original, native title/imprint and lower-left key inspected. Murrumbidgee title locates parish only; no identified LGA outline. Key parish and reserve from sale. Reserve 42753, Gum/Coinbil creeks, road/parcel and neighbouring parish limits are not inferred as council boundaries.
- **Glengalla** — Native map 22 October 1918; printed November 1918. Second edition. Whole original and native key inspected. Murrumbidgee title locates parish only; no identified LGA outline. Key parish, dividing line and reserve from lease/licence. Singorambah blocks and P.O.L. 231/231A are lease/holding areas, not council divisions. No council line inferred from adjoining parishes.
- **Singorambah** — Native map 28 January 1919; printed February 1919. Second edition. Whole original, native key and northern river detail inspected. Native shire triple-plus/dash distinguished from parish, sale reserve, public roads and State Forest. Northern Murrumbidgee River carries shire triple-plus and explicit Parish, Shire and County Boundary labels; adjoining native Carrathool Shire in County Sturt, with Murrumbidgee on title. Partial coincident boundary evidence only. Wyvern State Forest 387 dedicated 5 April 1917 and timber/stock/camping reserve 29515 notified 27 October 1899 are separate from LGA effective dates.
- **Wangabawgul** — Native map 23 August 1918; printed October 1918. Second edition. Whole original, native lower-left key, date and southern line detail inspected. Native shire triple-plus/dash distinguished from county crosses, parish, reserves, classified areas and public roads. Southern line explicitly labelled Parish, County and Shire Boundary; triple-plus mapped along road and western extension adjoining Conargo Shire in County Townsend, with Murrumbidgee on title. Partial coincident council/county boundary evidence only; western reserve and land parcels not separately inferred as councils. Reserve 42753 notified 27 May 1908, preferential Crown leases and road notices are not LGA effective dates.

Two untouched originals added; total 1,132 files, 10,114,811,232 bytes and 977 boundary JPEGs (including 12 boundary indexes). Counts are physical scans, not unique legal boundary editions. SHA-256, copied bytes, catalogue dimensions and RGB duplicate checks pass for additions; all registered paths and sizes pass. Five-image review checkpoint: `explore/output/2026-10-10_download-boundary-maps/slnsw_boyd_neighbours_review.json`.

### Benarba County parish maps — 11 October 2026

- **Collyu** — Native map 6 February 1919; printed February 1919. Third edition. Whole original and native key inspected. Boomi title locates parish only; no identified LGA outline. Key parish and classified areas. Settlement/Crown lease areas, road enclosure permissions, Gil Gil Creek and adjoining parish limits not inferred as council boundaries or effective dates.
- **Cook** — Native map 21 June 1898; printed July 1898. Second edition. Whole original and native key inspected. Native map is 1898 and omits Boomi Shire wording present in catalogue title; preserve this mismatch. Key parish, county cross/dash, land-district double-plus/dash and reserve from sale. Southern Denham County and Walgett/Narrabri land-district line not inferred as shire boundary. Oreel Resumed Area 251 and reserve notices separate from LGA evidence. No directly identified council outline.
- **Boonerey** — Native map 19 February 1919; printed March 1919. Third edition. Whole original and native lower title/key inspected. Boomi title locates parish only; no identified LGA outline. Key parish, reserve, classified area and public roads. Gil Gil/Boomi creek parish limits, settlement lease areas and 1904/1906 land notifications are not councils or LGA effective dates.
- **Narrawall** — Native map 22 October 1909; printed December 1909. Third edition. Whole original and native key inspected. Boomi title locates parish only; no identified LGA outline. Key parish, sale reserve, holding, dividing line, sale/lease reserve, lease reserve and public road. Wirrah Resumed Area 301A, reserves 37746/26225 and Boomi/Gil Gil river/creek limits not inferred as council evidence or dates.
- **Biroo** — Native map 1 May 1914; printed June 1914. Third edition. Whole original, native title/date and key inspected. Boomi title locates parish only; no identified LGA outline. Key parish, classified area and public roads. Settlement leases, named holdings, road enclosure permissions and adjoining parish limits are not councils or LGA effective dates. Source edge damage retained in review original.
- **Greenaway** — Native map 2 December 1918; printed January 1919. Third edition. Whole original, native key/date and southern Gwydir River detail inspected. Native shire triple-plus/dash distinguished from parish, sale reserve, public roads and observation station. River detail carries triple-plus shire symbols adjoining Walgett Shire, with Boomi on title. Partial council boundary evidence only; reserve 4263/4260 and timber/stock/camping notices distinct. Map dated 2 December 1918 but native imprint January 1919; preserve both dates. River/land parcel limits elsewhere not automatically treated as council boundaries.

One untouched original added; total 1,133 files, 10,137,325,041 bytes and 978 boundary JPEGs (including 12 boundary indexes). Counts are physical scans, not unique legal boundary editions. SHA-256, copied bytes, catalogue dimensions and RGB duplicate checks pass for addition; all registered paths and sizes pass. Six-image review checkpoint: `explore/output/2026-10-10_download-boundary-maps/slnsw_benarba_remaining_review.json`.

### Northern parish-map review — 11 October 2026

- **Gin** — Native printed May 1919. Third edition. Whole original and native key inspected. Boomi title locates parish only; no identified LGA outline. Native key parish, preferential occupation licence, reserve, classified areas, public roads and Water Trust District circles. Meroe Bore Water Trust District and Midkin P.O.L. 458A are not councils. Water-trust/lease notifications and road/river limits not inferred as LGA evidence or effective dates.
- **Wirrir North** — Native map 22 June 1914; printed July 1914. Third edition. Whole original and native title/key inspected. Boomi title locates parish only; no identified LGA outline. Key parish, sale reserve, public roads, lease reserve and classified area. Gwydir River, reserve 4263, settlement leases and neighbouring parish limits not inferred as shire boundaries.
- **Merimborough** — Native map 23 June 1902; printed July 1902. Second edition. Whole original and native title/key inspected. Native 1902 title omits Namoi Shire wording in catalogue; preserve mismatch. Key county cross/dash, parish, reserve, holding and dividing line. White County line, forest reserve 24587, resumed area 650 and Cubbo/Dunwerian 588A not council boundaries. No directly identified LGA outline.
- **Mcfarlane** — Native map 21 March 1902; printed April 1902. Second edition. Whole original and native lower title/key inspected. Native 1902 title omits Walgett Shire wording in catalogue; preserve mismatch. Key county cross/dash, parish, holding, dividing line, classified areas and observation station. Southern Leichhardt County line and Goangra resumed areas 219/219A and Wingade resumed area 174 not LGA evidence. No directly identified council outline.
- **Manilla** — Native map 6 June 1911; printed September 1911. Third edition. Whole original and native title/key inspected. Walgett title locates parish only; no identified LGA outline. Key parish, sale reserve, resumed area, classified areas and eighteenth-section lease. This is Manilla parish in Denham County, not the town of Manilla. Merkandool resumed area 155A, Pian Creek and timber/stock/camping reserve 26351 are separate from councils or LGA effective dates.
- **Finley** — Native map 4 July 1913; printed July 1913. Third edition. Whole original and native title/key inspected. Walgett Shire title locates parish only; no identified LGA outline. Native key land-district double-plus/dash, parish, sale/lease reserve, observing station, public roads and classified areas. Narrabri/Walgett land-district line is not inferred as council boundary. This is Finley parish in Denham County, not the southern NSW town of Finley. Settlement leases and reserve notices are not council divisions/dates.

All six originals review-only; no additions to the raw boundary collection. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/slnsw_northern_parish_remaining_review.json`.

### Namoi/Wingadee remaining parish sheets — 11 October 2026

Six full originals and native keys reviewed; no directly identified LGA outlines. Shire names in titles locate parishes only.

- Parish of Bulgah, County of Leichhardt: Native map 20 February 1911; printed March 1911. Third edition. Wingadee Shire title locates parish only. Key parish, reserve, dividing line, observing station, public roads and eighteenth-section leases. Wingadee resumed area 174 is not a council. Whole original and native title/key inspected; no directly identified LGA outline. Reserve, lease and classification notices are not LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvO36rkdEb
- Parish of Nelgowrie, County of Leichhardt: Native map 10 July 1911; printed July 1911. Third edition. Wingadee Shire title locates parish only. Key classified area, dividing line, resumed area, parish, sale/lease reserve and public roads. Nelgowrie resumed areas 177/177A and Nedgera Creek are not identified council limits. Whole original and native title/key inspected; no directly identified LGA outline. Reserve, lease and classification notices are not LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvOBQM6R7O
- Parish of Nuable, County of White: Native map 19 April 1916; printed May 1916. Second edition. Namoi Shire title locates parish only. Key parish, sale/lease reserves, permanent marks and observation stations. Goona Creek and classification blocks 152/153 are not identified council limits. Whole original and native title/key inspected; no directly identified LGA outline. Reserve, lease and classification notices are not LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74Vv33Z8EgRZ
- Parish of Dangar, County of White: Native map 18 April 1916; printed May 1916. Second edition. Namoi Shire title locates parish only. Key parish, land district and sale/lease reserve. Northern Narrabri/Coonabarabran land-district line is not inferred as council boundary. Classification blocks 162/163 are not councils. Whole original and native title/key inspected; no directly identified LGA outline. Reserve, lease and classification notices are not LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74Vv3qMVvDvO
- Parish of Coghill, County of White: Native map 1 August 1916; printed August 1916. Second edition. Namoi Shire title locates parish only. Key parish, county, sale/lease reserve and observation station. Western Baradine County line, classification blocks and water reserve 473 are not identified LGA evidence. Whole original and native title/key inspected; no directly identified LGA outline. Reserve, lease and classification notices are not LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74Vv3PQ8ajGO
- Parish of Arrarownie, County of White: Native map 8 August 1916; printed December 1916. Second edition. Namoi Shire title locates parish only. Key parish, county, land district, sale/lease reserve, observation station and state forest. Western Baradine County and internal Narrabri/Coonabarabran land-district lines are not inferred as shire boundaries. Pilliga East State Forest 266 dedication and classification dates are separate from councils. Whole original and native title/key inspected; no directly identified LGA outline. Reserve, lease and classification notices are not LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74Vv3PO4Z6R3

Review checkpoint: `explore/output/2026-10-10_download-boundary-maps/slnsw_namoi_wingadee_remaining_review.json`. Raw collection unchanged.

### Northern six remaining parish sheets — 11 October 2026

Four originals accepted; two review-only. Native dates and shire symbols confirmed at full resolution.

- Saved: Parish of Pringle, County of Inglis Land District of Armidale, Cockburn Shire, Eastern Division N.S.W. / compiled, drawn and printed at the Department of Lands, Sydney N.S.W., Feb. 1912.. Native map 17 January 1912; printed February 1912. Third edition. Native key separates shire triple-plus/dash from county cross/dash and land-district double-plus/dash. Western Namoi River carries shire symbols beside adjoining Tamworth Shire; Cockburn Shire in title. Partial council edge, not complete shire coverage. Retreat resumed area 395 and Longford resumed area 208A are not council divisions. Whole original, native key, imprint and relevant mapped edge inspected. Publication/map dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74VKaLO5WNxb
- Saved: Parish of Kickerbell, County of Pottinger. Native map 7 August 1918; printed September 1918. Fourth edition. Native key shire triple-plus/dash distinct from county cross/dash, occupation licence, parish, reserve and roads. Southern road edge carries shire symbols beside adjoining Warrah Shire; Tamarang Shire in title. Partial edge only. Buckland County and occupation licence 445 are separate from council boundaries. Whole original, native key, imprint and relevant mapped edge inspected. Publication/map dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvRq0W7Ap3
- Saved: Parish of Rodgers, County of Drake. Native map 17 June 1916; printed July 1916. Third edition. Native key shire triple-plus/dash distinct from county cross/dash, land district, parish and occupation licence. Eastern Clarence/Mann River carries shire symbols beside adjoining Dorrigo Shire and Clarence County; Severn Shire in title. Partial council edge only. Forest reserve 35365 notified 22 November 1902 and occupation licences 760/309 are not council divisions or LGA dates. Whole original, native key, imprint and relevant mapped edge inspected. Publication/map dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvKRajLNxZ
- Saved: Parish of Abington, County of Hardinge. Native map 28 June 1916; printed August 1916. Third edition. Native key shire triple-plus/dash distinct from land-district double-plus/dash, parish, gold field, reserve and occupation licence. Southern Abington Creek carries shire symbols beside adjoining Gostwyck Shire; Guyra Shire in title. Partial edge only. Western Inverell and northern Bundarra land-district limits are not independently treated as councils. Laura occupation licences 347/347A/522A and gold-field proclamation are separate from councils. Original upper-right edge damaged. Whole original, native key, imprint and relevant mapped edge inspected. Publication/map dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvJVMza6Mg
- Review-only: Parish of Chandler, County of Gresham. Native map 13 June 1916; printed July 1916. Second edition. Nymboida Shire title locates parish only. Native key parish, gold-field boundary and occupation licence; no directly identified LGA outline. Marengo Gold Field, Boyd/Little River occupation licence 425A and Chandlers Creek further extension to occupation licence 316A are not council divisions. Gold-field proclamation 28 June 1890 is not an LGA date. Whole original, native key, imprint and relevant mapped edge inspected. Publication/map dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvJrRly7m3
- Review-only: Parish of Eilginbah, County of Oxley. Native map 26 June 1914; printed July 1914. Second edition. Marthaguy Shire title locates parish only. Native key reserve from lease, parish and public roads; no directly identified LGA outline. Burril Creek, Great Western Railway, parcel limits and neighbouring parishes are not inferred as shire boundaries. Whole original, native key, imprint and relevant mapped edge inspected. Publication/map dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74Vv7NwKgWVO

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/slnsw_northern_six_remaining_review.json`. Four new originals pass hashes, catalogue dimensions and decoded RGB duplicate checks. All 1,137 registered paths/sizes pass: 10,217,576,533 bytes. The collection includes 982 JPEG scans with boundary evidence, including 12 boundary indexes. Counts describe scans, not unique council editions.

### Southern seven remaining parish sheets — 11 October 2026

Two originals accepted; five review-only. Native keys, imprints and relevant map edges inspected at full resolution.

- Review-only: Parish of Gecar, County of Wellesley. Native map 25 October 1912; printed November 1912. Third edition. Bibbenluke Shire title locates parish only. Key parish, reserve, gold field, resumed area, dividing line, classified area, public roads and reserve from occupation under Mining Act. No directly identified LGA outline. Cambalong resumed area 31A, Maharatta settlement purchase area 26 and Bombala Gold Field are not councils or LGA dates. Whole original, native title/key/imprint and relevant mapped detail inspected. Map/printing dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74Vvz8GgK0dM
- Review-only: Parish of Burnima, County of Wellesley. Native map 3 April 1914; printed April 1914. Third edition. Bibbenluke Shire title locates parish only. Key parish, reserves, classified area, gold field, population area, roads, village and suburban limits; no identified council boundary. Village of Bibbenluke, temporary common 3829 and Bombala Gold Field are not inferred as LGA limits. Village/suburban cadastral limits are separate from shire boundaries. Whole original, native title/key/imprint and relevant mapped detail inspected. Map/printing dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvzWWGRda3
- Review-only: Parish of Arable, County of Wallace. Native map 18 December 1918; printed January 1919. Third edition. Native printing date January 1919 differs from catalogue year 1918. Dalgety Shire title locates parish only. Key parish, county cross/dash, sale reserve and public roads; no directly identified LGA outline. Eastern Beresford County line, Burrinjuck catchment label and reserve notices are not council limits or LGA dates. Whole original, native title/key/imprint and relevant mapped detail inspected. Map/printing dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvzNNZRK8b
- Saved: Parish of Clive, County of Buccleuch. Native map 30 May 1911; printed June 1911. Third edition. Yarrowlumla Shire title. Native key distinguishes shire triple-plus/dash from county cross/dash and land-district double-plus/dash. North-western Nottingham Creek and adjoining stepped straight edge carry repeated triple-plus/dash symbols matching the shire key. Partial edge, not complete council coverage; adjoining council not explicitly named in inspected detail. Eastern Goodradigbee River is a river name beside Cowley County line, not an adjoining council label. Southern Queanbeyan land-district line is not independently treated as council evidence. Burrinjuck catchment, Coodradigbee Gold Field proclamation 4 December 1897, resumed areas and reserve 42989 are separate from councils. Whole original, native title/key/imprint and relevant mapped detail inspected. Map/printing dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvMA7yNvKb
- Review-only: Parish of Headford, County of Denison. Native map 18 July 1917; printed August 1917. Third edition. Berrigan Shire title locates parish only. Native key parish, occupation licence, dividing line and public roads; no directly identified LGA outline. Barooga occupation licences 242/242A and neighbouring parish limits are not councils. This is Headford parish in Denison County. Whole original, native title/key/imprint and relevant mapped detail inspected. Map/printing dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvK2Zj7e83
- Review-only: Parish of Gorton, County of Cooper. Native printed May 1917. Third edition. Carrathool Shire and irrigation area in native title. Key parish, land district, sale/lease reserve, public roads, land acquired for irrigation and irrigation-area boundary; no directly identified LGA outline. Narrandera/Yanco land-district line, Bourke Cooper irrigation area 9, Murrumbidgee Northern Irrigation Scheme, resumption/appropriation notices and Dowling/Gipps Gold Field are not inferred as councils or LGA dates. No separate native map date confirmed. Whole original, native title/key/imprint and relevant mapped detail inspected. Map/printing dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvvoKa4Aa3
- Saved: Parish of Kalingan, County of Gipps. Native map 25 May 1918; printed 1928. Fourth edition. Native printing year 1928 differs from catalogue year 1918; later parcel annotations include 1925 and 1928. Do not treat as an unchanged 1918 snapshot. Bland Shire in title; native northern adjoining Lachlan Shire named. Northern road edge carries repeated shire triple-plus/dash distinct from keyed land-district double-plus/dash. Partial council edge only. Condobolin land-district wording, Bourke Cooper Dowling/Gipps Gold Field proclamation 15 October 1880 and classified areas are separate from council boundaries or LGA effective dates. Original lower-right paper edge damaged. Whole original, native title/key/imprint and relevant mapped detail inspected. Map/printing dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvKQAqDVkA

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/slnsw_southern_seven_remaining_review.json`. Two new originals pass hashes, catalogue dimensions and decoded RGB duplicate checks. All 1,139 registered paths/sizes pass: 10,258,557,016 bytes. Collection includes 984 JPEG scans with boundary evidence, including 12 boundary indexes. Counts describe scans, not unique legal council editions.

### Yarrowlumla/Queanbeyan remaining parish sheets — 11 October 2026

Three originals accepted; four review-only. Boundary keys, map detail and imprints checked at full resolution.

- Saved: Parish of Brayshaw, County of Cowley. Native map 8 July 1912; printed July 1912. Third edition. Commonwealth Territory and Yarrowlumla Shire coexist in native title. Key distinguishes state single-plus/dash, land-district double-plus/dash, shire triple-plus/dash and county cross/dash. Southern composite edge includes grouped shire marks beside county/state lines; adjoining Monaro and Cooma shire names printed. Partial edge only; not a complete legal council snapshot. Native note says map is only approximately correct. Greenfield resumed area 234A, Boboyan 276, Demandering 458A and Bullanam ang 381A are not councils. Burrinjuck catchment notification 16 August 1911 is separate from LGA dates. Original lower-left edge damaged. Whole original, native key/imprint and relevant mapped detail inspected. Map/printing dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74Vvvjxv7XRZ
- Review-only: Parish of Naas, County of Cowley. Native map 21 March 1912; printed March 1912. Third edition. Commonwealth Territory and Yarrowlumla Shire in title only; no directly identified LGA outline. Key parish, sale/lease reserves, holding, trig/observation stations and classified area. Booroombi resumed area 117A, Naas/Gudgenby Rivers and parcel boundaries are not councils. Blue later lease annotations and paper damage at key retained in review original. Burrinjuck catchment notification 16 August 1911 is not an LGA date. Whole original, native key/imprint and relevant mapped detail inspected. Map/printing dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74Vvv4D3qyLy
- Saved: Parish of Cotter, County of Cowley. Native map 5 March 1912; printed March 1912. Second edition. Commonwealth Territory and Yarrowlumla Shire coexist in native title. Native key separates state single-plus/dash, land-district double-plus/dash and shire triple-plus/dash. Southern composite edge carries repeated shire groups beside state/land-district marks; adjoining Monaro Shire and Cooma land district explicitly named. Boundary detail itself is labelled approximate position. Partial edge only; no inference that the title establishes post-transfer council jurisdiction. Burrinjuck catchment notification 16 August 1911, improvement lease 1497, permissive occupancy and reserve notices are not council dates or divisions. Whole original, native key/imprint and relevant mapped detail inspected. Map/printing dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74Vvvjlm8DGO
- Review-only: Parish of Milligan, County of Cowley. Native map 17 July 1912; printed August 1912. Third edition. Commonwealth Territory and quoted Yarrowlumla Shire in title only. Key parish, state single-plus/dash and sale/lease reserve; western NSW/Commonwealth Territory line is not inferred as council boundary. No directly identified LGA outline. Native warning map is only approximately correct. Blue annual lease cancellation references February 1924; preserve later annotations rather than treat sheet as unchanged 1912 snapshot. Burrinjuck catchment notification and improvement lease 150 are not LGA dates/divisions. Lower edge damaged. Whole original, native key/imprint and relevant mapped detail inspected. Map/printing dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvvbM7wXQX
- Review-only: Parish of Tidbinbilla, County of Cowley. Native map 9 February 1912; printed March 1912. Third edition. Commonwealth Territory and Yarrowlumla Shire in title only. Native key parish, sale reserve, resumed area, trig station, dividing line, land-district double-plus/dash, sale/lease reserve and state single-plus/dash; no shire symbol. Western state/land-district line is not inferred as council boundary. No directly identified LGA outline. Resumed area 1044, timber reserves and Burrinjuck catchment notification are separate from councils. Whole original, native key/imprint and relevant mapped detail inspected. Map/printing dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74Vvv03kXqzd
- Saved: Parish of Queanbeyan, County of Murray. Native map 30 January 1904; printed March 1904. Third edition. Native title omits Gunning Shire wording in catalogue. Native key explicitly identifies Borough cross/dash distinct from parish, town, population area and Towns Police Act limits. Mapped Borough of Queanbeyan has cross/dash perimeter, including southern straight edge. Printed proclamation wording inside borough retained as source annotation, not independently verified legal effective date. Towns Police Act area, town grid, population area and temporary common 4916 are separate from municipal boundary. Save original as historical borough evidence, not Gunning Shire evidence. Whole original, native key/imprint and relevant mapped detail inspected. Map/printing dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74Vv7VEogllM
- Review-only: Parish of Canberra, County of Murray. Native map 16 January 1908; printed February 1908. Third edition. Native wording Within Yarrowlumla Shire locates parish only. Key parish, reserve from sale and trig station; no directly identified LGA outline. Parish of Canberra in Murray County; not a modern municipal/city boundary. Molonglo River, parcel limits and neighbouring parish lines are not inferred as councils. Whole original, native key/imprint and relevant mapped detail inspected. Map/printing dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74Vv7Z0Xr22b

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/slnsw_yarrowlumla_remaining_review.json`. Three new originals pass hashes, catalogue dimensions and decoded RGB duplicate checks. All 1,142 registered paths/sizes pass: 10,309,732,696 bytes. Collection includes 987 JPEG scans with boundary evidence, including 12 boundary indexes. Counts describe scans, not unique legal council editions.

### Town/Dewhurst remaining sheets — 11 October 2026

Five originals reviewed; no raw additions.

- Review-only: Parish of Dewhurst, County of Denham [cartographic material] : Land District of Walgett, Walgett Shire, Central Division N.S.W. / compiled, drawn and printed at the Department of Lands, Sydney N.S.W. Native map 8 October 1917; printed October 1917. Third edition. Walgett Shire in title only. Key parish, sale reserve, observation station and classified area. No directly identified LGA outline. Creek, neighbouring parish, lease and road lines are not council boundaries. Whole original, native key/title/imprint and mapped detail inspected. Map/printing dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvvjLdx8Ml
- Review-only: Map of the village of Tottenham and suburban lands [cartographic material] : parish of Beaconsfield, county of Kennedy, land district of Nyngan, Lachlan Shire N.S.W. 1916 / compiled, drawn and printed at the Department of Lands. Catalogue 1916; native printing 6 March, damaged year; later annotation 24 November 1933. Second edition. Lachlan Shire in title only. Native key identifies village and suburban limits, reserves, classified area and streets/roads under Local Government Act; these are not identified council limits. Village proclamation 6 November 1907 and Logan Gold Field wording are separate from LGA dates. Large losses affect title and map. Mining information charted to 24 November 1933; not an unchanged 1916 snapshot. Whole original, native key/title/imprint and mapped detail inspected. Map/printing dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74Vvje2eZLrA
- Review-only: Map of the town of Binalong and suburban lands [cartographic material] : Parish of Binalong, County of Harden, Land District of Boorowa, Goodradigbee Shire, N.S.W. 1922 / compiled, drawn and printed at the Department of Lands. Native printing 7 June 1922; margin charted to 1941. Third edition. Goodradigbee Shire in title only. Key town, suburban, reserve, Towns Police Act, railway and classified-area lines; no directly identified LGA outline. Native town proclamation 20 March 1885 and town/suburban notification 17 July 1912 are separate from council dates. Later annotations and charted-to-1941 margin prevent treating this as an unchanged 1922 snapshot. Whole original, native key/title/imprint and mapped detail inspected. Map/printing dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvrOxjZ4yg
- Review-only: Map of the village of Bellbrook and suburban lands [cartographic material] : parish of Nulla Nulla, county of Dudley, land district of Kempsey, Macleay Shire, N.S.W. 1922 / compiled, drawn and printed at the Department of Lands. Native printing 27 February 1922. Second edition. Macleay Shire in title only. Key village, suburban, reserve and classified-area limits. Native village proclamation 29 October 1892 and village/suburban notification 6 June 1919 are separate from LGA dates. Police Offences Act area, Orara Gold Field and Macleay River do not establish council limits. No directly identified LGA outline. Whole original, native key/title/imprint and mapped detail inspected. Map/printing dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvL5e0pDdl
- Review-only: Map of the village of Barellan and suburban lands [cartographic material] : county of Cooper, parish of Barellan North, land district of Narrandera, Yanko Shire, N.S.W. 1909 / compiled, drawn and printed at the Department of Lands. Native printing 14 June 1909. Yanko Shire in title only. Key village, suburban, parish and sale/lease reserve limits; no directly identified LGA outline. Village proclamation and village/suburban notification 19 May 1909 are not inferred as LGA dates. Bourke Cooper Dowling/Gipps Gold Field, Temora-Barellan railway betterment area, railway and timber reserve are separate layers. Whole original, native key/title/imprint and mapped detail inspected. Map/printing dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvL33x2v3g

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/slnsw_town_dewhurst_remaining_review.json`. Five review originals pass fetch SHA-256 and catalogue dimensions. All 1,142 registered paths/sizes pass, unchanged at 10,309,732,696 bytes; 987 boundary JPEG scans including 12 indexes. These are scan counts, not unique legal boundary editions.

### Miscellaneous remaining shire leads — 11 October 2026

Three originals reviewed; no raw additions.

- Review-only: Ph. of Osborne Co. of Bathurst. Undated native plan; catalogue time-period code d1892. Native heading Shire of Lyndhurst locates an Osborne parish subdivision. Plan shows portions 42, 71, 80 to 82, 180, 220, 230 to 233 and parts 34, 35, 70 and 83, measured roads, fences and Combing Creek. No directly identified council outline. No native date confirmed; preserve catalogue date as metadata, not established map or legal LGA date. Whole original, native title/key or reference table and mapped detail inspected. Source: https://collection.sl.nsw.gov.au/record/74VKvlLrXNyg
- Review-only: Map of Eastern & Central divisions of New South Wales [cartographic material] : showing estates subdivided under the Closer Settlement (Promotion) Act / by T. Rowston ; [map copyright] H.E.C. Robinson, Ltd. Catalogue between 1917 and 1947?; no native publication date confirmed. T. Rowston/H.E.C. Robinson estate promotion map. Table groups 69 numbered estates under shires and Municipality of St Marys (Penrith), with area, price per acre and farm count. Mapped numbers and town/transport/river lines locate estates; no directly identified council outlines. Council names in table do not make this an LGA boundary map. Donation stamp 29 December 1977 is not map publication date. Do not treat table as a complete estate census; native text limits coverage to properties submitted by promoter. Whole original, native title/key or reference table and mapped detail inspected. Source: https://collection.sl.nsw.gov.au/record/74VKwxddw7E3
- Review-only: Plan of the township of Nundle on the River Peel, N.S.W. [cartographic material] : the property of Peel River Land and Mineral Company / G.E. Darby Surveyor, A.A. Co. ; drawn by G. Ogden. Catalogue 1854; native map date not independently confirmed. Native title identifies township on River Peel as property of Peel River Land and Mineral Company. Streets, sections, cultivation allotments, sale/lease paddocks and reserved market, court, church, cemetery and company sites are cadastral features; no directly identified LGA outline. Pink/pencil names are annotations. Catalogue historical explanation of 1854 township approval and sale is not a verified legal council date; no verso image supplied in this one-image record. Whole original, native title/key or reference table and mapped detail inspected. Source: https://collection.sl.nsw.gov.au/record/74VvRNlbPZod

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/slnsw_misc_shire_remaining_review.json`. Three review originals pass fetch SHA-256 and catalogue dimensions. All 1,142 registered paths/sizes pass, unchanged at 10,309,732,696 bytes; 987 boundary JPEG scans including 12 indexes. Counts describe scans, not unique legal boundary editions.

### Estate/river remaining leads — 11 October 2026

Six source images reviewed; three originals saved.

- [Map of Barwon River, Macquarie River, Castlereagh River] [cartographic material]. Catalogue between 1836 and 1856; native date not confirmed. River/station sketch. Rivers and creeks are coloured pink, properties/stations marked by squares, relief hachured. No directly identified LGA outline. Catalogue Gilgandra Shire history reference explains dating, not a mapped council boundary. Whole originals, native title/stamp, mapped boundary detail and relevant annotations inspected. Map/catalogue dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74VK2OlrRMGA
- Plan of Camden Park [cartographic material] / [Rygate & West] Undated native plan; catalogue not before 1920?. Native Camden Municipality and Wollondilly Shire labels sit on opposite sides of the heavy cross/dash division along Wire Lane, adjoining straight section and Navigation Creek. Partial council division indicated by labels and mapped line; no standalone boundary key. Preserve cadastral coincidence with lane/creek without treating all property or fence lines as council boundaries. Rygate & West ownership stamp supplies catalogue lower date estimate; not an independently confirmed map or legal boundary date. Estate parcels, transmission easement, road widening and Nepean River are separate features. Whole originals, native title/stamp, mapped boundary detail and relevant annotations inspected. Map/catalogue dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvvNzrl3QX
- Plan of Rothbury Estate, County of Northumberland [cartographic material] / surveyed by A. F. Hall L[icensed] S[urveyor], Newcastle. Undated native plan; catalogue 189?; shire layer and later annotations not dated. Two native source sections show Patrick's Plains and Cessnock shires separated by triple-plus/dash line. Source image 0 explicitly labels this line Shire Boundary; source image 1 carries northern continuation towards Hunter River and council names. Partial council edge only. Preserve both originals separately, without stitching. Catalogue describes heliograph of an earlier edition and ownership-change annotations; catalogue 189? does not establish date of shire layer. No legal effective date confirmed. Parish and estate lot limits, railway, coloured sale/ownership marks and townships of Rothbury, Branxton and Belford are separate features. Native paper is damaged. Whole originals, native title/stamp, mapped boundary detail and relevant annotations inspected. Map/catalogue dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74VMyM8X2RbM
- The Holt-Sutherland estates, minature sketch shewing approximate distances [cartographic material] / Gibbs, Shallard & Co., litho. Catalogue 1881?; native date not confirmed. Native miniature sketch shows approximate distances and yellow Holt-Sutherland estate. Estate outline, township, reserve, national park, transport routes and suburb names are not directly identified LGA boundaries. No council outline found. Catalogue dating explanation distinguishes estate company formation and proposed transport; donation/lease annotations are not map publication or council dates. Whole originals, native title/stamp, mapped boundary detail and relevant annotations inspected. Map/catalogue dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74Vvlda2XwVO
- [Survey maps of Fassifern] [cartographic material] Catalogue 1881?; native composite includes later references, date not established. One source image contains four survey plans for portions 235–236, 250–254, 240–246 and 256–258. Lake Macquarie Shire headings locate cadastral surveys only. Native 31 January 1881 wording belongs to reserve notice, not independently confirmed map date; lower-right suburban holding notification reads 15 March 1921. No directly identified LGA outline. Portion, railway, road, creek, holding and reserve lines are separate layers; do not treat composite as unchanged 1881 snapshot. Whole originals, native title/stamp, mapped boundary detail and relevant annotations inspected. Map/catalogue dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvmoeJZgwX

Two Victorian CSIRO records (`74VvajpMa8Jy`, `74VvajpkjyGA`) explicitly identify Moira County, Victoria in catalogue titles. Routed outside agreed NSW scope from metadata only; originals not visually reviewed. Routing checkpoint: `slnsw_remaining_victoria_metadata_routing.json`.

Review checkpoint: `explore/output/2026-10-10_download-boundary-maps/slnsw_estate_river_remaining_review.json`. Three additions pass hashes, catalogue dimensions and decoded RGB duplicate checks. All 1,145 registered paths/sizes pass: 10,329,111,205 bytes. 990 boundary JPEG scans include 12 indexes; scan counts are not unique legal council editions.

### Gloucester estate/road remaining leads — 11 October 2026

Seven image entries, five unique originals reviewed. No raw additions.

- Review-only: Plan showing deviation from Government Road from Waukivory to the Myall River, Parish of Avon, County of Gloucester, Land District of Maitland, Land Board District Shire of Gloucester [cartographic material] / M. O. Hungerford, licensed surveyor. Native charted annotation 27 November 1914. Road deviation survey. Pink new route and yellow original Government Road distinguished explicitly. Eastern Boundary of Gloucester Estate is an estate line, not an LGA outline. Gloucester Shire wording locates survey; road width one chain and traverse measurements are not council limits. Whole originals, native title/annotations and relevant mapped detail inspected; no directly identified council outline. Survey/charting/catalogue dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74VK24qZyMp3
- Review-only: Plan of resubdivision of part of block 32 of Avon Valley subdivision at Gloucester in the Parish of Gloucester, County of Gloucester [cartographic material] / A.J Trier, licensed surveyor. Native survey 28 February 1911, replacing struck-out 29 October 1911. Resubdivision of part of Avon Valley block 32. Native survey date amended: retain both the replacement and struck-out date. Red road proposed for handover to Shire Council and dedication wording refer to road administration, not council boundary. Lot, river, North Coast Railway and cemetery limits are cadastral features. Whole originals, native title/annotations and relevant mapped detail inspected; no directly identified council outline. Survey/charting/catalogue dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74VK20NmOMQX
- Review-only: [Manuscript cadastral map of land near Gangat, New South Wales] [cartographic material]. Catalogue 1903?; catalogue/native charted annotation 28 November 1914. Manuscript measured lots, roads, waterways and Gangat trig station; no directly identified LGA outline. Council-history reference in catalogue explains estimated estate subdivision date only. Two source image entries supply byte-identical originals, not two map editions. Whole originals, native title/annotations and relevant mapped detail inspected; no directly identified council outline. Survey/charting/catalogue dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74VKwpwvy6qA
- Review-only: Plan of roads one chain wide in Gangat, Belbora, and Barrington No. 3 subdivision of Gloucester Estate Ltd. N.S.W. [cartographic material]. Catalogue 190-?; native complete date not confirmed. One-chain roads in Gangat, Belbora and Barrington No. 3 subdivision. Native Gloucester Shire Council wording concerns dedication and handover of roads, not council perimeter. Road traverse table, lots and creeks are separate features. Paper edge damage removes part of date/cartography; do not supply missing date. Whole originals, native title/annotations and relevant mapped detail inspected; no directly identified council outline. Survey/charting/catalogue dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74VKwpqD5xeX
- Review-only: Gloucester Estate, New South Wales [cartographic material] : Barrington-Paddock, Upper Gangat, Belbourie Creek and Bakers Creek No. 2 subdn. Catalogue 1903?; catalogue/native charted annotation 28 November 1914. Coloured estate lots in Barrington-Paddock, Upper Gangat, Belbourie Creek and Bakers Creek No. 2 subdivision. Colour fills identify cadastral lots, not councils. Parish, river, road and estate outlines are not directly identified LGA lines. Council-history reference in catalogue explains estimated estate date only. Two source image entries supply byte-identical originals, not two map editions. Whole originals, native title/annotations and relevant mapped detail inspected; no directly identified council outline. Survey/charting/catalogue dates do not establish legal LGA effective dates. Source: https://collection.sl.nsw.gov.au/record/74VKwpvXQGZg

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/slnsw_gloucester_estate_remaining_review.json`. All seven fetch hashes and catalogue dimensions pass. Gangat and Gloucester Estate duplicate source entries confirmed by byte hashes. All 1,145 registered paths/sizes unchanged: 10,329,111,205 bytes; 990 boundary JPEG scans including 12 indexes. Counts describe scans, not unique legal council editions.

### Final online shire-search leads — 11 October 2026

Eight originals reviewed; no raw additions.

- Review-only: Plan of subdivision of- J.H. Carven's 640A. Gt.- Shire of Cessnock, Parish of Heddon; County of Northumberland [cartographic material] / Henry Ferdinand Halloran. Native survey February 1905; later shire heading/annotations undated. J.H. Carven grant subdivision near Heddon Greta racecourse. Shire of Cessnock in heading only. Streets, racecourse, railway, sections and lots are cadastral features; no directly identified council outline. Native February 1905 survey date does not date shire heading or later annotations. Whole original, title, relevant native dates/annotations and mapped detail inspected. No directly identified LGA outline; map/survey/catalogue dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvVKeMQl5A
- Review-only: Plan showing land (colored red) situated in Midson St. Epping transferred to [C.?] Dawson by G. Ray [cartographic material] : being portion of land comprised in certificate of title vol. 284, fol. 129. Shire of Hornsby, parish of Field of Mars, County of Cumberland. Undated native plan; catalogue not before 1906. Hornsby Shire title locates land transferred by G. Ray to Dawson on Midson Street, Epping. Red-tinted parcel and measured holdings, Ray's Road and adjoining road are not council limits. Catalogue derives lower date from Hornsby incorporation; not independently verified map date. Donation stamp 15 February 1972 is separate. Whole original, title, relevant native dates/annotations and mapped detail inspected. No directly identified LGA outline; map/survey/catalogue dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74VKD8ZrvmjA
- Review-only: Auction sale of Crown lands at Bermaguee South [cartographic material] : on Saturday 20th  December 1924. Native printing November 1924; auction 20 December 1924. Auction poster maps village town/suburban lots in Bermaguee and Bermaguee South, Mumbulla Shire. Village boundaries and shaded sale lots are not shire limits. Two plan panels plus local sketch are one source image. Auction date is not legal LGA effective date. Whole original, title, relevant native dates/annotations and mapped detail inspected. No directly identified LGA outline; map/survey/catalogue dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74Vvvvdx7Ryg
- Review-only: Auction sale Crown lands at the Lands Office Scone [cartographic material] Native printing December 1910; auction 18 January 1911. Auction location Scone differs from mapped land: part of village of Bunnan, Tyrone Parish, Brisbane County, Woolooma Shire. Sale-lot shading, village boundary, roads, Wyong Creek and reserves are not directly identified council limits. Preserve printing/auction date difference. Whole original, title, relevant native dates/annotations and mapped detail inspected. No directly identified LGA outline; map/survey/catalogue dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74Vvv4BZlxWX
- Review-only: Plan of the township of Rye Park [cartographic material] being subdivision of portion 84 [...] for auction sale on [...] Tuesday 26 January 1886 / by James Chester. Native auction 26 January 1886; catalogue c1886. James Chester portion 84 subdivision in Olney Parish, King County, Burrowa land district. Township lots, named streets, neighbouring holdings, school and church are not directly identified LGA boundaries. Catalogue GNB locality-boundary reference mentions Gunning Shire but does not identify council perimeter in this sale plan. Whole original, title, relevant native dates/annotations and mapped detail inspected. No directly identified LGA outline; map/survey/catalogue dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74VvzKxPWLwy
- Review-only: [Allotments of land formerly to Wm. Balmain and Giles Moore between South Creek and Pitt Town Road, McGraths Hill] [cartographic material]. Catalogue between 1813 and 1833; native date not confirmed. Measured holdings and applications between South Creek and Pitt Town Road. Green parcel lines, lagoon, buildings, roads and owners are cadastral features, not directly identified LGA outlines. Catalogue dates from historical road/owner context; no native map date confirmed. Source faded and torn; uncertain labels not reconstructed. Whole original, title, relevant native dates/annotations and mapped detail inspected. No directly identified LGA outline; map/survey/catalogue dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74VKwmOAQ8jA
- Review-only: Plan of part of land in C.T. vol. 3377 fol.31, being part of portion 40, Parish of Nattery, County of Argyle [cartographic material] / Francis Fraser Kell, surveyor. Native survey completed 8 December 1952. Mulwaree Shire heading locates portion 40, Nattery Parish, Argyle County. Green edge explicitly Reserve 79119 for preservation of graves, area 6.5 perches. Reserve perimeter is not council boundary. Connection diagram, Towrang Creek, parish, parcel and road limits are separate. Whole original, title, relevant native dates/annotations and mapped detail inspected. No directly identified LGA outline; map/survey/catalogue dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74VKwx8QK0rA
- Review-only: Plan of part of land in conveyance reg. no. 693 bk. 1808, being part of portion 254, Parish of Towrang, County of Argyle [cartographic material] / Francis Fraser Kell, surveyor. Native survey completed 8 December 1952. Mulwaree Shire heading locates portion 254, Towrang Parish, Argyle County. Green edge explicitly Reserve 79121 for memorial (historical relic), including powder magazine, area 4.75 perches. Reserve perimeter is not council boundary. Wollondilly River, connection diagram, parcel and road limits are separate. Whole original, title, relevant native dates/annotations and mapped detail inspected. No directly identified LGA outline; map/survey/catalogue dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74VKwx46Rvwd

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/slnsw_final_shire_leads_review.json`. Eight originals pass fetch SHA-256 and catalogue dimensions. All 1,145 registered paths/sizes pass, unchanged at 10,329,111,205 bytes; 990 boundary JPEG scans include 12 indexes. All 290 unique online shire-search catalogue records have a resolved triage state; states distinguish saved/reviewed evidence from metadata/scope routing. Other-source discovery remains open; no claim of comprehensive NSW boundary coverage.

### Municipality search evidence audit — 11 October 2026

13 stale triage states reconciled: four prior review-only sources, one registered Camden Park source, one 65-image municipal series and seven explicit non-NSW catalogue titles. Series source URLs match all 65 registered files; includes reference sheets. Metadata scope routing is not visual review. Reconciliation checkpoint: `explore/output/2026-10-10_download-boundary-maps/slnsw_municipality_existing_evidence_audit.json`.

Four more originals reviewed; no raw additions.

- Review-only: [Municipality of Maitland, showing the Maitland race course, A. McDougal's farm, the Hunter's River and surrounding area] [cartographic material]. Catalogue between 1842 and 1850; native municipal stamp Gaz. 30.6.44 fo.1069. Native note explicitly defines cross/dash lines as original boundaries of the grant. Municipal stamp is not a boundary key. Grant lines, farm, racecourse, fences, river and property tints are not directly identified municipal limits. Stamp year not expanded to a legal effective date. Source faded, torn and partly lost. Whole original, native title/notes and relevant mapped detail inspected. No directly identified LGA outline. Catalogue/map dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74VK24NqOlQX
- Review-only: Riversdale Estate, Chatswood, Lane Cove River [cartographic material]: Torrens Title / Griffin & Harrison Licensed Surveyors under R.P. Act ; E. A. Cantle. Catalogue 1920s incomplete year; native date not confirmed. Native estate note places land in Municipality of Ryde, Hunters Hill Parish, Cumberland County. Chatswood title names locality; does not establish council membership or perimeter beyond printed estate note. Map shows sale lots, roads, park and Lane Cove River, without directly identified LGA outline. Whole original, native title/notes and relevant mapped detail inspected. No directly identified LGA outline. Catalogue/map dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74VKZdzyb8Xg
- Review-only: Harbour View estate (adjoining the famous wireless estate), North Willoughby [cartographic material] : auction sale on the ground, Saturday May 16 at 3 p.m. / Cramer Bros., auctioneers, Crows Nest (next to Crows Nest Post Office), A.J.C. Mills, Cr. Rosewall & Penshurst Streets, auctioneer in conjunction. Catalogue 1925; native auction Saturday 16 May, year not printed in inspected title. Native subdivision heading Municipality of Willoughby locates estate only. Lots, estate drainage/access road and streets are not council outlines. Auction day/month and catalogue year preserved separately; source right edge damaged. Whole original, native title/notes and relevant mapped detail inspected. No directly identified LGA outline. Catalogue/map dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74VKMOeyrvWy
- Review-only: Plan of North Scarborough Estate : situate at Botany Bay, in the Parish of St. George, in the County of Cumberland N.S.W. [cartographic material] / Ferdinand H. Reuss, junr., licensed surveyor. Catalogue 1877?; native publication date not confirmed. Estate subdivision at Botany Bay, St George Parish, Cumberland County. Streets, coloured lot edges, recreation reserve, Government Swamp and adjoining South Scarborough are not directly identified council limits. West Botany owner address does not define municipality boundary. Source tears obscure parts of map. Whole original, native title/notes and relevant mapped detail inspected. No directly identified LGA outline. Catalogue/map dates do not establish legal council effective dates. Source: https://collection.sl.nsw.gov.au/record/74Vvz8GrGV0X

Review checkpoint: `explore/output/2026-10-10_download-boundary-maps/slnsw_municipality_audit_remaining_review.json`. Four fetch hashes and catalogue dimensions pass. All 1,145 registered paths/sizes remain valid: 10,329,111,205 bytes; 990 boundary JPEG scans including 12 indexes. Remaining municipality-search leads open.

### Council-plan and geography review

- Six State Library originals reviewed. Retained `74VKDkzlGPWd`: explicit municipal-boundary labels along Boundary Street and South Street with Ashfield and Canterbury named on opposite sides. Partial line only; red/blue proposed-street tints are property interests. Torn title/notes. Catalogue says not before 1879; no legal effective date established.
- `74Vvz5aDgEPd` — Catalogue 1934; native auction 12 April 1934. Auction of council-owned freehold residues and Elizabeth Street allotments. Sale parcels, frontage hatching and local sketch do not identify an LGA outline.
- `74VvpDeD4zWd` — Catalogue 1927; native publication date not confirmed. Martin Place extension land to be resumed. Red parcel/resumption outlines and street/building ownership do not identify an LGA outline.
- `74VKmpk2G76y` — Catalogue 1937. Municipal Council of Sydney market layout: buildings, market uses, proposed vegetable market, roads and railway siding. Council producer does not establish an LGA outline.
- `74VvzD6Zk2jA` — Catalogue 1881; native council approval 5 April 1881. Proposed subdivision of Roslyn Hall property, Darlinghurst. Native note records Municipal Council of Sydney approval on 5 April 1881. Parcel dimensions, lanes, buildings and approval do not identify an LGA outline.
- `74VveJxwxpeX` — Catalogue 1854; native grant annotation 14 November 1825. Allotments belonging to William Lithgow with local sketch of Willoughby Parish. Native note defines black-edged allotments as property for sale. Township, government land, grant annotations and parcel limits do not identify an LGA outline.
- Catalogue subjects place Portland, Sandridge, Oakleigh and Portland tramway in Victoria, and Calliungal in Queensland. Outside agreed NSW scope; metadata routing only, no original visual review. Evidence: `slnsw_municipality_geography_routing.json`.
- Review evidence: `explore/output/2026-10-10_download-boundary-maps/slnsw_sydney_council_plan_remaining_review.json`. New original copied unchanged; fetch/copy hashes, native dimensions and decoded-image duplicate checks pass. All registered paths and sizes pass.

### Final five municipality-search leads

- `74Vv8gdxAXbl` — Catalogue 1920; native auction 19 February 1920. Upper Glenburn Farm sale plan. Municipality of Jamberoo names the locality across the map. Farm/neighbour parcels, roads and Minnamurra River have no directly identified municipal boundary line or key. Catalogue general note claims municipal boundaries, but native image does not confirm which line is municipal; no LGA outline accepted.
- `74VveB8EGeab` — Catalogue 1921; native A. & T. H.E.C. Robinson imprint 1960. Church of England glebe subdivision: lot boundaries, streets, adjoining owners, paddock, church and schools. No identified municipal outline. Catalogue dates the glebe division to 1921, but printed margin reads 1960. Catalogue event date and scan imprint are separate; do not call this an unchanged 1921 scan.
- `74Vv5aoo8D7A` — Catalogue not before 1817; native publication date not confirmed. Thomas 40-acre grant plan: coloured property subdivisions, owners, dimensions, roads and grant line. Native boundary labels explicitly name Thomas Grant. No directly identified LGA outline; grant date does not establish a municipal boundary date.
- `74VvlZRW4OrO` — Catalogue between 1840 and 1859?; native publication date not confirmed. 39 market-garden allotments near Sir Joseph Banks Hotel. Municipality of Botany annotation locates land only; sale lots, drains, reserved roads, reserve and Botany Bay shore have no municipal boundary key or identified LGA outline. Undated council annotation may differ from catalogue base-map date.
- `74VKPDNkqzzy` — Catalogue 1924; native survey/approval annotations 1924. Hamilton Hume memorial-site resumption, 3 roods 38 perches, with red parcel/access-road outline and inset of grant lands and Georges River. Campbelltown Municipality heading locates the site only. No identified municipal outline. Survey/resumption dates do not establish an LGA effective date.
- Evidence: `explore/output/2026-10-10_download-boundary-maps/slnsw_municipality_final_five_review.json`. Five fetch hashes and native dimensions pass. No new raw originals; all 1,146 registered paths/sizes unchanged.

- Municipality-search coverage audit: all 1,028 unique catalogue records retrieved across 11 pages. No `unreviewed` states remain. Two review cases remain open: Western Suburbs sewerage (33 sheets, preview review only) and Randwick/Waverley/Coogee reference scans (boundary status unresolved). This is catalogue coverage, not a claim that all source originals were reviewed. Checkpoint: `slnsw_municipality_coverage_audit.json` in the downloader output folder.

- Western Suburbs sewerage follow-up: remaining 30 originals downloaded and whole-sheet reviewed; all 33 source originals now screened. No directly identified LGA outline. Geographic sheets 23 (Alexandria Park–Shea’s Creek watercourse) and 32 (Munni Street–Shea’s Creek, Macdonaldtown) show engineering channel/culvert/chainage detail, without municipal-line identification. Enlarged mapped detail checked; no full transcription of engineering annotations claimed. Evidence: `slnsw_western_sewer_original_review.json`. All 33 fetch hashes and dimensions pass.
- Randwick–Waverley–Coogee 1859 reference scans rechecked unchanged. Native Randwick Municipality annotation names an area; no colour key located. Bounded trover newspaper search (first page of 1850s results) did not corroborate coloured-line identity. Reference/companion kinds retained; no new legal boundary/date claim. Search DOM and two article renditions registered as research evidence in `trover_randwick_reference_evidence.json`. Map collection remains 1,146 files, 991 boundary JPEG scans including 12 indexes; all registered paths/sizes pass.

### Sydney–Glebe Wentworth Park boundary proposal

- Source: City of Sydney Archives A-00437897, node `948822`, catalogue 1892–1893. Saved original five-page PDF in `data/raw/historical_boundary_maps/city_of_sydney/wentworth_park_sydney_glebe_boundary_proposal_1892_1893.pdf`.
- PDF page 5 (folio 115): partial existing City Boundary explicitly labelled; City of Sydney and Glebe named on opposite sides. Blue tint explicitly denotes area proposed to be added to Glebe. Existing boundary and proposed transfer are separate; neither correspondence nor proposal proves enactment. Map scale 8 chains/inch, undated base.
- Four correspondence pages discuss the boundary revision and objections about Wattle Street. Native correspondence spans November 1892–March 1893; catalogue span and map date kept separate. A separate tracing is described in catalogue metadata but not present in the exposed PDF. No second map claimed.
- Public viewer images are 1,000 pixels wide. Download wizard provides original PDF with 3,103 × 4,360 map image; only PDF registered. Generic display-PDF route failed; actual file route `assets/downloadwiz/3794610` succeeded. All five pages reviewed. Fetch/copy hashes, readability, page count and embedded dimensions pass. All 1,147 registered paths/sizes pass. Evidence: `city_sydney_wentworth_boundary_1892_1893_review.json`.

### Sydney–Marrickville boundary proposals: archive A-00115515

- Original 27-page PDF saved unchanged. Catalogue file span: 4 March 1953–30 June 1970. PDF page 26 stamped 5 May 1953; page 27 City Engineer date 8 April 1953. File closure is not a legal effective date.
- Two partial boundary maps around Campbell Street, May Street, Barwon Park Road and Alexandria Canal. Page 27 red dash-plus symbol is explicitly keyed “Proposed New Boundary”; scale 4 chains to 1 inch. Land-use fills are not LGA extents. Page 26 coloured comparison overlays have no confirmed standalone key. No adopted boundary inferred.
- Embedded map sizes: 3,732 × 5,174 and 9,315 × 14,609 pixels. All 27 pages screened; both maps inspected enlarged. Correspondence was not fully transcribed. Whole PDF retained; map extracts were temporary review aids only.
- Four further PDFs (1881 Newtown Road, 1885 City–Randwick Park Road, 1890 Paddington street extension, 1891 Great Barcom Street) expose letters only. Mentioned tracings/plans are not present in these downloaded assets. The 1885 letter reports disagreement between boundary tracings; the 1881 note describes unclear statutory wording. These letters do not establish a mapped perimeter.
- Five more metadata records expose no PDF. Only the 1936 Sydney–Glebe deed explicitly says “Digitised record No”; the other four lack an exposed download, which does not prove no physical plan exists.
- Two City archive searches retain first pages only (reported 1,053 and 1,609 results). Quoted query was not verified as an exact phrase filter. This is bounded discovery, not full archive coverage. Evidence: `explore/output/2026-10-10_download-boundary-maps/city_sydney_boundary_correspondence_review.json` and `city_sydney_boundary_search_triage.json`.

### City of Sydney boundary-marker plans, 1928–1929

- Archive A-00114324, catalogue 24 August 1928–29 October 1929. Original 33-page PDF retained unchanged. Page 33 is Map of the City of Sydney 1928, native scan 12,286 × 10,479 pixels. Its key separates City Boundary, Ward Boundaries and Adjoining Municipal Boundaries. Red numbered circles/fills concern proposed marker positions, not proposed land transfers.
- PDF pages 8–30 contain 24 numbered local sketches; page 25 combines sketches 18 and 19. City Boundary is keyed on sketches; selected detail names Waterloo and Randwick across from Sydney. These are partial local boundary details, not 24 complete council perimeters.
- Native 26 September 1928 memorandum says City/ward boundaries changed without adjustment of historic posts. Do not infer old legal boundaries from surviving post locations. Map and file dates do not prove statutory effective dates.
- All 33 pages screened; overview, selected sketch and memorandum inspected enlarged. Four additional PDFs (Glebe definition request, Thomas Smith adjustment letter, City Solicitor Boundary Street memorandum, City–Paddington sewer letter) expose correspondence only. No full handwriting transcription claimed. Five fetch hashes and page counts pass; accepted raw copy hash matches. Evidence: `explore/output/2026-10-10_download-boundary-maps/city_sydney_boundary_marks_discovery.json`.

### City archive focused boundary searches

- Four small queries fully retrieved: boundary map (32 unique cards), boundary tracing (21), boundary alteration (34), boundary alteration plans (2). Counts overlap across queries. Coverage does not extend to the whole catalogue. Next-page DOM keeps a stale page input of 1, but distinct card-ID unions match all reported results.
- Six new metadata leads inspected. Glebe/Annandale 1933–1938 files and a 1953 Marrickville/Newtown exclusion proposal expose no PDF. The 2004 Sydney–South Sydney amalgamation library record describes 49 pages and a map chapter; no exposed download or exact public digital copy found in a bounded web search. Physical/public map availability remains unresolved.
- A one-page 1888 City Surveyor memorandum requests the Government Road–Macquarie Street north boundary tracing, without exposing it. A three-page 1883 PDF exposes a Pottinger Street extension tracing (1 chain to an inch); its red line marks the proposed street extension, not an identified LGA boundary. Both PDFs remain review-only. Four pages visually reviewed; fetch hashes and page counts pass.
- Evidence: `explore/output/2026-10-10_download-boundary-maps/city_sydney_boundary_focused_search_coverage.json` and `city_sydney_boundary_alterations_discovery.json`. No additions to the 1,149 registered originals in this batch.

### Newtown–Camperdown plans and Sydney ward map

- A-00533849: native undated plan, red dashed Boundary Line along Bishopsgate Street and across Stanley Street parcels, Newtown/Camperdown on opposite sides; scale 66 feet to 1 inch. Catalogue span 1868–1908 is not a printed native date. One-page original PDF, embedded scan 6,615 × 4,634 pixels.
- A-00533853: title explicitly identifies part boundary of Newtown/Camperdown; black dashed division, signed Daniel Murphy, Licensed Surveyor, Newtown, 4 September 1888. Scale 20 feet to 1 inch. One-page original PDF, scan 7,908 × 5,538. Both plans show local edges, not complete council perimeters. Series label 1957–1975 is not the plan date.
- Both plan records say Digitised record No but expose working PDFs. Availability flags can be stale. Two PDF routes for each are byte-identical; one original per record saved.
- A-01153253: Map of Sydney, creator Withers and circa 1882 from catalogue; no native printed date. Original TIFF 2,572 × 3,151. Native note explicitly keys municipal ward boundaries. Do not infer complete outer LGA perimeter. Catalogue has an unrelated harbour-wharf alternative title and a donor authenticity/integrity caveat; neither resolves dating.
- A-00528044 Macdonaldtown information file describes early borough-boundary maps but has no exposed download and explicitly says not digitised. Four council organisation descriptions refer to already registered municipality atlas maps. These are metadata findings, not original review.
- Robinson publisher memorandum of 2 May 1898 has two letter/acknowledgement pages, no enclosed map; review-only. Cooper/Terry/Winder grant-claim PDF lead remains unreviewed.
- All accepted originals pass fetch/copy SHA-256, page/dimension checks. All 1,152 registered paths/sizes pass. Evidence: `explore/output/2026-10-10_download-boundary-maps/city_sydney_camperdown_new_leads_discovery.json` and `city_sydney_council_collections_discovery.json`.

### City archive search pages 2–4 and Cooper watershed review

- Six more search pages retrieved (144 cards). Boundary plans and municipal map queries each now have 96 unique cards over four pages; reported totals are 299 and 440. Remaining pages are open. This is card coverage, not visual review of all maps.
- Six selected records expose no original download or asset route. Two 1925–1926 valuation books describe Fitzroy/Camperdown ward maps but say not digitised; the 1972 lighting plan is undigitised microfilm. A 1939 residential-zoning file describes a November 1937 map, and a 1968 Leichhardt planning correspondence file describes copies of a map/ordinance, but neither exposes them. A municipal library-map title overlaps an existing subject; edition identity is not confirmed.
- A-00453519 Cooper grant-claim original PDF downloaded as review evidence: 28 pages, map on page 18, native 7,297 × 10,965. All pages screened; map inspected enlarged. Native colours identify Corporation property, government water-purpose land, required purchases and drainage land. Blue line marks present/proposed watershed extent. No LGA outline identified. Corporation ownership and council jurisdiction are different. No financial figures extracted.
- Source SHA-256/readability/page count pass; no map added to raw collection. All 1,152 registered paths/sizes unchanged. Earlier unresolved Cooper lead marked reviewed. Evidence: `explore/output/2026-10-10_download-boundary-maps/city_sydney_cooper_watershed_990141_review.json` and `city_sydney_search_pages_2_4_coverage.json`.

### Newtown 1885 and Liberty Street boundary maps

- A-01146556: native Plan of Newtown, Daniel Murphy Licensed Surveyor, Newtown 1885. Explicit borough-boundary dash key; scale 264 feet to 1 inch. Neighbouring council names surround Newtown. Original TIFF 4,186 × 5,944, retained without rotation. Donation annotation 25 January 1918 is not the map date. Heavy foxing and cracks reduce legibility. Native title/key inspected enlarged.
- A-00533852: undated plan of proposed Liberty Street extension to Railway Avenue. Explicit Municipal and Electoral Boundary with Petersham/Camperdown opposite; scale 40 feet to 1 inch. Street closure and water/sewerage resumption colours are distinct from council jurisdiction. Old copy with added detail; catalogue 1868–1908 is not a native/legal date. Original one-page PDF, scan 6,482 × 7,001. Partial boundary only.
- Four municipal/ward aperture-card records (1956, 1962, 1974) explicitly say not digitised and expose no originals. A 1958–1959 proposed ward-division file exposes no download. These are metadata findings; not original review.
- Six further search pages add 144 cards. Seven pages per query now retrieved; adjacent pages contain duplicate IDs. Unique-query coverage is incomplete, even if all nominal pages are later retrieved. Audit IDs rather than sum pages.
- Two originals pass fetch/copy SHA-256, native dimensions/readability and registered-hash checks; Newtown TIFF RGB checked against same-size registered images. All 1,154 registered paths/sizes pass. Evidence: `explore/output/2026-10-10_download-boundary-maps/city_sydney_search_pages_5_7_discovery.json` and `city_sydney_search_pages_5_7_coverage.json`.

### City archive nominal-page coverage and Camperdown map offer

- Remaining pages of the same boundary plans and municipal map searches retrieved: all 13/19 nominal pages saved. Unique ID totals fall short of reported 299/440 due repeated cards across relevance pages. Full-query unique coverage is not established. A supported stable-sort audit is needed; all cards have not had record-level metadata inspection.
- Three additional 1925–1926 ward-map rate books (Denison, Phillip, Pyrmont) marked not digitised and expose no originals. City-map copyright/pricing file (1956) also exposes no download. Official handbook 1913 is the water/sewerage board publication; its catalogue mentions sewerage/catchment maps, with no download.
- Camperdown map-offer file A-00220814, March 1909: original PDF downloaded and all seven pages visually screened. Offers for a map/tracing are correspondence only; no enclosed map exposed. Fetch SHA-256 and seven-page readability pass. Review-only; no financial figure transcriptions.
- No new accepted maps this batch. All 1,154 registered paths/sizes unchanged. Evidence: `explore/output/2026-10-10_download-boundary-maps/city_sydney_search_all_pages_coverage.json` and `city_sydney_search_pages_8_10_discovery.json`.

### City archive stable-sort audit and 1958 planning scheme

- Supported archive sort node_id ascending independently retrieves all 299 boundary-plans and 440 municipal-map cards, strict increasing IDs and no duplicates. Five missing IDs recovered; title screening routes them to building/property works, baths or Central Railway improvement, without original inspection. Complete coverage applies only to these two queries at observation time. Many cards have not had original review.
- A-01203126 native title says Council adopted City planning scheme on 15 December 1958; imprint 1959. Native caveat says scheme is not prescribed and remains subject to amendment. Do not infer statutory prescription or an LGA boundary effective date.
- Mapped black dash-cross City edge with opposing Leichhardt/Randwick/Marrickville/Botany names; no standalone municipal-boundary key found in inspected legend. Identification uses geographic labels and continuous line symbols. Legend fills are zoning, parks, roads and parking, not council areas. Native title/key and west boundary viewed enlarged.
- Original uncompressed TIFF retained unchanged, 6,504 × 8,131. One-page PDF reviewed at same embedded dimensions, but RGB hashes differ; no pixel-equality claim. PDF remains companion review evidence, not another registered map. Both fetch hashes pass; TIFF raw copy/readability/dimensions and same-dimension RGB duplicate checks pass.
- Four metadata files (1928 departmental ward map, 1957–1964 housing schemes, 1947 planning procedure, 1977 historical-map presentation) expose no originals; no content review claimed. All 1,155 registered paths/sizes pass. Evidence: `explore/output/2026-10-10_download-boundary-maps/city_sydney_stable_sort_coverage_audit.json` and `city_sydney_planning_ward_leads_discovery.json`.

### Remaining City ward-map references

- Ten remaining ward-map valuation books explicitly not digitised and expose no downloads (Bourke, Bligh, Flinders, Lang, Cook twice, Denison, Gipps, Macquarie, Belmore). An 1868 Sydney map microfilm record also says not digitised with no exposed original. Metadata availability is distinct from physical map existence.
- A-00107745 Chief Warden map request, 1939: original PDF six pages visually screened, covers/correspondence/verso only. No map exposed. SHA-256 and page-count checks pass; no financial claims extracted.
- Erskineville agency 62519 describes a Macdonaldtown municipal/ward map attachment; no download or asset route exposed. Attachment availability unresolved, no visual review.
- Bounded web discovery found an ANU 1971 census scan lead; browser returned 403. The 1971 NSW Field Count Statement No 3 with LGA maps is already registered, but exact ANU edition/content identity has not been verified. No byte-duplicate claim.
- Stable-sort catalogue audit reconciled with registered originals and saved discovery checkpoints. Remaining card-only records are explicit; complete card coverage does not mean all original maps reviewed. All 1,155 registered paths/sizes pass unchanged. Evidence: `explore/output/2026-10-10_download-boundary-maps/city_sydney_remaining_ward_books_discovery.json`, `city_sydney_remaining_ward_reference_leads.json` and `city_sydney_stable_sort_coverage_audit.json`.

### Ryde and other NSW council archive discovery

- Ryde History Hub: first search pages only for boundary (55 reported results), municipality map (106), council map (550). Six relevant records inspected: proposed seven-council/shire boundary rearrangement (undated), City boundary map (1995), Meadowbank planning sheet (undated), neighbourhood map (1949), population distribution (1949), Hunters Hill parish/Ryde 1922–1949 catalogue map. No exposed original downloads. Physical holdings are described at Ryde Library.
- Five visible thumbnail routes yield two unique generic 500×500 map icons; both visually inspected. They are placeholders, not native maps, and were excluded from raw collection. No native geography/date/key review claimed. Neighbourhood map catalogue says population information only, not interim plan; these areas are not current suburb boundaries. Publisher 1949 and shelf label 1951 are distinct metadata fields.
- North Sydney council links to public Stanton digital collection. It includes Mapping North Sydney and block-plan collections. Search-form URL attempt showed home/collection content; filtering and original download route remain unverified. Bankstown web-indexed catalogue record 960316 describes a municipal map; record-level download availability remains uninspected.
- No new original accepted. All 1,155 registered paths/sizes pass unchanged. Evidence: `explore/output/2026-10-10_download-boundary-maps/ryde_lga_maps_discovery.json`, `ryde_lga_maps_preview_checks.json` and `other_nsw_council_archive_discovery.json`.

### North Sydney and Bankstown council-map review

- North Sydney Heritage Centre: the native “Mapping North Sydney” collection control (`data_id=717`) returned 550 results. Only the first 15 cards and three selected item details were inspected; collection coverage is incomplete. Direct search URLs had previously returned the home content, so these are native-control results.
- Stanton item 120875, LH REF MF526: catalogue year 1995; preview title “North Sydney Local Government Area — proposed suburb boundaries”. The preview key distinguishes the LGA boundary from proposed suburb boundaries. Do not treat proposed suburb lines as adopted boundaries.
- Item 120876, LH REF MF519: catalogue date February 1981, municipal planning scheme, S.W. Seymour. Item 120869, LH REF MF616: catalogue date 1967, one-bedroom-unit limits. Hatched planning areas are not LGA boundaries. Municipal line identity on these two previews remains unresolved.
- All three exposed large previews are 600 × 600 pixels. Native Available formats controls returned no download options. No full-size originals were added; availability remains unresolved, not proven absent. Required Stanton credit for the first two records: “Image courtesy Stanton Library Historical Services”. The third record says to contact Stanton Library. No account, order or contact was initiated.
- Bankstown catalogue record 960316, PN-000053, miscellaneous plan no. 184: catalogue date 19 January 1928; native drawing is signed R.A.T. and dated 19.1.28. Exposed JPEG is 1000 × 785 pixels. Visual review found streets, railway, Water Board pipeline and unkeyed red shading, with no labelled LGA boundary. Excluded from the boundary collection.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/north_sydney_bankstown_lga_map_review.json`. Review images remain temporary; raw holdings unchanged.

### Willoughby council history: municipal-map reproductions

- Added the council-hosted *The Heritage of East Chatswood*, Vince Egan, 1988. Title and copyright pages confirm the book year and publisher. Original 146-page PDF is unchanged in `data/raw/historical_boundary_maps/willoughby_council/heritage_of_east_chatswood_1988_with_municipal_maps.pdf`.
- PDF page 12 (printed page 3): Willoughby parish-map reproduction has a Municipal Boundary key, separate from parish, reserve and proposed tramway line styles. Parish geography is not itself an LGA. PDF page 18 (printed page 9): council map reproduction explicitly captions municipal boundaries and shows the Willoughby outline. Both reproduced maps are undated; do not assign 1988 as their survey or legal boundary date. These are book reproductions, not established new editions of earlier registered maps.
- New PDF passes fetch/copy SHA-256, nonduplicate whole-file hash, 146-page readability and page-location checks. All registered paths and file sizes pass. No claim of a fresh full rehash of older holdings.
- The 1966 centenary history PDF was screened at page-thumbnail scale and map pages 14, 17 and 113 enlarged. These show settlement, parish and land grants; no explicit municipal-boundary map was confirmed. Retained as review evidence only.
- Stanton’s native keyword form submission for “boundaries” again returned home content, so no zero-result or complete-search claim is valid. Liverpool’s council collection page points to its Spydus archives; that catalogue remains to be inspected.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/willoughby_council_history_map_review.json`.

### Willoughby bicentennial book batch

- Four council-hosted PDFs retrieved: West Ward (106 pages), Naremburn (162), Artarmon (178), Castle Cove/Middle Harbour (138). Title/copyright pages inspected; accepted books confirm 1988. Original PDFs remain unchanged. Whole-file hashes differ from registered holdings; this does not establish a new edition of each reproduced map.
- West Ward: PDF page 10 (printed 1), caption explicitly identifies municipal boundaries, with ward/locality labels. Reproduced map undated; do not assume all heavy road lines are ward or council lines.
- Naremburn: PDF page 161 (printed 152), amended/deleted portion of Department of Lands parish sheet 2. Printed municipality names identify the partial Willoughby/North Sydney division at Wheatleigh Street. PDF page 57 (printed 48) independently describes Wheatleigh Street as a municipal boundary. Portion/estate boundaries elsewhere are not automatically LGA boundaries. Map date not established.
- Artarmon: PDF page 173 (printed 164), suburb/locality outline on parish base with neighbours named outside. Stored under `report_with_suburb_boundary_maps`; no claim every outer edge is an LGA edge. Map undated. Copyright page names Grace Warner; credits differ from council-owned volumes.
- Castle Cove PDF page 15: locality-boundaries map shares the council base-map design seen in East Chatswood page 18. Caption/crop differ; no distinct municipal-map edition established. Not added. Later map plates remain to be visually reviewed.
- Review scope: first 28 pages of each book screened, text keyword hits examined; last 28 pages of Naremburn and Artarmon screened. These checks locate accepted evidence, not complete visual review of every page. New originals pass SHA-256 copy equality and PDF page-count/readability checks; all 1159 registered paths/sizes pass.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/willoughby_bicentennial_batch_review.json`.

### Willoughby publication coverage and remaining histories

- Native Next-page forms retrieved 10 + 10 + 4 unique titled publication articles, matching 24 reported entries. This proves list-card coverage only; it does not prove all linked PDFs or all council holdings reviewed. Some entries contain multiple PDF links. Coverage checkpoint: `willoughby_publications_coverage.json` in the boundary-map output folder.
- Castle Cove PDF pages 31, 34, 42, 49, 55 and 56 inspected: topographic base, iron-rod photograph, land grants and Cammaray estate sale plan. No additional labelled LGA boundary found. Ownership and sale-lot edges are not LGA boundaries.
- Castlecrag page 25, Northbridge page 13 and *Willoughby: the Suburb and its People* page 13 show crops of the shared council base map. No distinct LGA edition established; not registered as additional municipal maps. Map lists checked; complete visual reviews of these books not claimed.
- *Willoughby’s Fifty Years*: all 118 page thumbnails visually screened, no map located. Extracted text exists, but keyword search returned no hits; keyword absence alone did not support exclusion. Kept review-only.
- Four selected additional histories reviewed, no new raw holdings. All 1159 registered paths/sizes checked and unchanged. Next: Liverpool Spydus archive. Review checkpoint: `explore/output/2026-10-10_download-boundary-maps/willoughby_remaining_histories_review.json`.

### Liverpool public catalogue and Council Gazette map

- Native public archive searches: Title “map” with cartographic-material filter returned four records; Anywhere “boundary” returned six; Anywhere “map” returned 24. Full catalogue Anywhere “map” AND “Liverpool” returned 56. Each exact query fits one 100-record page and unique title links match reported counts. Complete-query card coverage does not establish complete archive coverage or full original review.
- Council Gazette electronic record BRN 256354: public holdings panel exposes 13 download assets for 1970, 1971, 1972, 1973, 1974, 1975, 1976, 1978, 1979, 1980–81, 1982–83, 1984 and 1987–88. Stable `/api/open/1.0/digitalassets/<id>/download` routes recorded; expiring redirect URLs are not provenance.
- Added original 1975 issue (asset 9823304), 156 pages. PDF page 11 (printed page 9) explicitly identifies three wards and 32 districts. North/South/East wards are labelled; main map includes the city outline and numbered areas, with an enlarged local inset. Stippled ward key and separate main/inset scale bars are visible. District names are the source’s own categories; do not equate them with official suburb boundaries. Issue year 1975 is not a separate map survey or legal boundary date.
- New PDF passes whole-file duplicate exclusion, fetch/copy SHA-256 and 156-page readability checks. All 1160 registered paths/sizes pass; older hashes were not freshly recalculated.
- The 1970 issue (61 pages) was visually screened at page-thumbnail scale; no LGA map located. The fetched 1978 (92 pages) and 1980–81 (113 pages) issues remain under visual review. Ward-member portraits alone are not boundary maps.
- Population-estimate and 1979 urbanisation essay catalogue records expose physical holdings, with no original download found. The 1968 Rotary Park map-photo record is a photograph, not a native map scan; image content not yet reviewed.
- Checkpoints: `liverpool_council_search_coverage.json` and `liverpool_council_gazette_map_review.json` in `explore/output/2026-10-10_download-boundary-maps/`.

### Liverpool Gazette 1978 and 1980–81 visual review

- Added unchanged 1980–81 issue, asset 9823308, 113 pages. All thumbnails screened across two work blocks; maps on PDF pages 62 and 111 enlarged. Page 62 is a walking-route map and does not identify an LGA boundary.
- PDF page 111 (printed 103): main numbered map lists 31 named areas, with a local inset and circular Liverpool city-ward inset. Numbering and layout differ from the 1975 32-district map. This establishes distinct reproduced source evidence, not a legal boundary change or official suburb definitions. The map is separately undated; retain issue year 1980–81.
- The 1978 issue, asset 9823306, 92 pages, is now review-only. All thumbnails screened; Bent’s Basin topographic map on PDF page 24 (printed 22) enlarged. No labelled LGA boundary found. Map is faint; contours, property and park edges are not established council lines.
- New 1980–81 original passes whole-file duplicate exclusion, hash/copy equality and PDF readability/page count. All 1161 registered paths/sizes pass. Original 1971–73 issues have been fetched from the confirmed public holdings routes and await visual review (79, 86 and 92 pages respectively). Fetch process is terminal; no live job remains.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/liverpool_gazette_1978_1981_review.json`.

### Liverpool Gazette 1971–73 review

- Added unchanged 1971 issue, asset 9823300, 79 pages. PDF page 11 enlarged: municipal outline, 31 numbered named areas and a local inset. Main-map design matches the later 1980–81 reproduction, without its separate circular ward inset. Retained for earlier issue-date evidence, not a new legal boundary edition. Printed folio unconfirmed; map separately undated. Numbered area labels are not verified official suburb definitions.
- All 79, 86 and 92 page thumbnails screened for 1971, 1972 and 1973 respectively. No LGA maps located in 1972 or 1973. Those originals remain review-only.
- New raw original passes SHA-256 copy equality, whole-file duplicate exclusion and PDF page count/readability. All 1,162 registered paths/sizes pass; older hashes not freshly recalculated. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/liverpool_gazette_1971_1973_review.json`.

### Liverpool Gazette 1974, 1976 and 1979 review

- All 64, 145 and 88 page thumbnails screened respectively. Original fetch hashes rechecked. No additional raw source accepted.
- 1974 PDF page 55 (printed 54–55) maps the open-space corridor/scenic protection area, not an established LGA line. Page 58 (printed 58–59) Holsworthy development plan labels adjacent Campbelltown, Bankstown and Sutherland councils but has no keyed municipal-boundary line. Line identity remains unresolved; not registered.
- 1976 PDF page 51 (printed 48) repeats the three-ward/32-district map saved from 1975. No distinct map edition established. Page 20 (printed 17) is a land-use study; page 132 (printed 129) maps graves. These three pages inspected enlarged.
- No LGA map located in the 1979 issue. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/liverpool_gazette_1974_1976_1979_review.json`.

### Liverpool Gazette 1982–88 and public-series audit

- Added unchanged 1987–88 issue, asset 9823311, 84 pages. PDF page 5 (printed 3): municipal outline, three labelled wards, stippled ward key, 34 numbered areas and local inset. Hinchinbrook (33) and Voyager Point (34) are additions to the 1975 reproduced design. Numbered source areas are not verified official suburbs; no legal LGA change inferred. Map separately undated. Native council roster on PDF page 4 confirms 1987–88 issue period.
- All 84, 72 and 84 thumbnails screened for 1982–83, 1984 and 1987–88. No LGA map located in 1982–83. Enlarged 1984 pages 5, 30 and 65 are release/investigation areas, factory layout and business locator respectively.
- 1987–88 PDF page 60 (printed 58), Chipping Norton Lake recreation map, names adjoining councils but lacks a council-boundary key. Its line identity remains unresolved. Page 22 is a Water Board advertisement, not a map. Original retained for the clear page 5 map.
- All 156 thumbnails of the saved 1975 issue reviewed again; no additional LGA map located. All 13 public holdings issues now thumbnail-screened (1,216 PDF pages in total), with selected map pages enlarged. Four source documents registered; document count is not unique legal boundary-edition count. This does not establish complete Liverpool archive coverage.
- New original passes whole-file duplicate exclusion, fetch/copy SHA-256 and PDF readability/page count. All 1,163 registered paths/sizes pass; older hashes not freshly recalculated. No live tool session remains. Checkpoints: `liverpool_gazette_1982_1988_review.json` and `liverpool_gazette_public_series_review.json` in the boundary-map output folder.

### Hills and Hornsby former council boundaries

- Hills Shire original one-page PDF, native 28 June 2018, linked by the council as its pre-boundary-adjustment suburb map. Whole sheet inspected. Southern hatched areas explicitly labelled now part of Parramatta show former council extent before May 2016. Coloured suburb layer includes Norwest and North Kellyville, associated with 2018 naming/boundary changes on the source page. Do not use the sheet as a single-date pre-2016 suburb map. Native scale 1:125,000. Map retained unchanged.
- Hornsby Active Living Strategy, unchanged 212-page council PDF, native 5 February 2016 (Issue I, Final). PDF/printed page 16 Figure 01.01 identifies Hornsby LGA and adjoining councils. Page 52 Figure A2.07 keys dashed black administrative boundaries and orange planning district boundaries, labels wards A/B/C. Page 26 repeats the base for open space. Selected pages 16, 26 and 52 inspected enlarged; complete visual report review not claimed.
- Hornsby native report predates May 2016 transfer; present council source describes that transfer separately. PDF metadata modification 12 June 2024 does not establish a new geography date. Source map effective legal dates not independently verified. Green park fills are not council lines.
- Both PDFs pass fetch/copy SHA-256, whole-file duplicate exclusion and page count/readability. All 1,165 registered paths/sizes pass; older hashes not freshly recalculated. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/hills_hornsby_historical_boundary_map_review.json`.
- Parramatta street-name page cites c.1913 Robinson municipal map but links no scan. Public catalogue searches failed with access errors (HTTP 403/405); search results are unverified, not empty. Browser and shell processes terminal. No original reviewed or registered from that catalogue. Current/previous Hornsby comparison-map link also remains unexposed in this batch.

### Hills 2008 ward map in older reports

- Added unchanged 70-page 2012–13 Operational Plan. PDF page 6 (printed 2), History of Our Shire, maps the pre-2016 full council extent and four wards (North, Central, East, West), with suburb outlines/names. Key explicitly says 2008 LG Ward Boundaries. Report date is 2012–13; do not overwrite the map-layer year or infer a legal commencement day. Map uses native PDF vector artwork; no embedded raster on this page. Only selected page inspected visually.
- 2007–08 Annual Community Report: all 43 PDF spread thumbnails screened; pages 3 and 10 enlarged. Page 10 (printed 18–19) reproduces the same 2008 design as a 345×651-pixel raster. Not registered as another edition; the saved 2012–13 vector plate is better for later tracing. Whole original SHA-256 recorded in fetch/review checkpoints.
- Indexed Hornsby 2007–08 original report route returned 404; council attachment page returned 403. These errors do not prove absence of maps. No Hornsby original accepted from these two routes.
- New PDF passes SHA-256 copy equality, whole-file duplicate exclusion and 70-page readability/page count. All 1,166 registered paths/sizes pass; older hashes not freshly recalculated. No live tool sessions. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/hills_hornsby_older_reports_review.json`.

### Hills 2015 ward alterations

- Added unchanged 512-page council agenda, 27 October 2015. Item 14 pages 396–407 describes review and recommends exhibition before final determination. Selected text and maps reviewed; full agenda visual review not claimed.
- PDF and printed pages 408 (Central), 409 (East), 410 (West) are detailed plates dated 23 October 2015, scale 1:24,000. Legend explicitly distinguishes existing 2008 ward fills from proposed boundary-alteration lines; arrows mark changes. Keep proposed status for the October document.
- Source error: page 407 attachment list promises North Ward attachment 3, but pages 410 and 411 both carry West Ward attachment 4. Both plates inspected enlarged. Map-area RGB renders excluding page footers have identical SHA-256; count one West plate, not two distinct maps. Missing North plate remains a discovery lead.
- Primary 15 December 2015 council minutes, printed page 12, item 13, resolution 676 records adoption of publicly exhibited ward boundaries in attachments 1–4 to that later report. This does not establish legal commencement or repair the October source anomaly. Later agenda attachment maps not yet retrieved.
- New raw PDF passes fetch/copy SHA-256, whole-file duplicate exclusion and 512-page readability. All 1,167 registered paths/sizes pass; older hashes not freshly recalculated. No live tool sessions. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/hills_ward_agenda_2015_review.json`.

- Hills 15 December 2015 agenda section 3 (402 pages): complete Central/East/North/West maps on PDF pages 272–275 (printed 1539–1542). North is on PDF 274 and recovers the missing October attachment; scale 1:90,000, other maps 1:24,000. All map plates dated 23 October 2015 and distinguish existing 2008 ward fills from proposed alterations. Selected report/map pages reviewed. Council minutes item 13, resolution 676 record adoption on 15 December; legal commencement not independently verified. Unchanged original retained; collection 1,168 registered files.

- Hornsby explicit historical ward comparison: one-page A0 PDF, scale 1:40,000. Native title specifies 9 September 2017 election wards based on SA1 2011; legend distinguishes green 2017 wards, yellow pre-May 2016 proclamation wards and grey Parramatta area since May 2016. Whole sheet, legend and southern transfer detail inspected. PDF metadata created/modified 15 October 2018; this is not the boundary-layer date. Original saved unchanged. Collection 1,169 registered files. Evidence: `hornsby_ward_comparison_review.json` in downloader output.

- Ryde Central, West and East ward original PDFs saved, native date 10 December 2014. Scales 1:30,000 (Central/West) and 1:33,000 (East); linked on Council’s 2021 election page. The 2008 copyright is base attribution, not map or legal commencement date. Each sheet has a named ward and clipped perimeter; internal magenta park/path linework is not a ward boundary. All three whole sheets inspected. Five older History Hub ward/suburb records metadata-reviewed via browser: Download controls have asset ID 0, no original exposed in inspected HTML; thumbnails not reviewed in this batch. Collection 1,172 registered files. Checkpoints: `ryde_2014_ward_maps_review.json`, `ryde_remaining_ward_leads.json`.

- Ryde Integrated Open Space Plan adopted 24 July 2012: unchanged 233-page original. PDF/printed page 46 has regional council and Ryde LGA/ward outlines on aerial bases (regional source Google Earth Professional 2010). Page 48 Figure BR.03 keys blue ward lines separately from grey “13 Suburb Collector Boundaries”. Page 45 explains suburb aggregation for IOSP/id.profile Census analysis; these groups are not verified official suburb boundaries. Selected maps/text reviewed, not the full report. 2010–11 annual-report schematic remains review-only (no streets/scale); 2008 governance section thumbnail-screened without LGA map. Collection 1,173 files. Checkpoint: `ryde_older_reports_review.json`.

- Ryde boundary keyword query now has complete card coverage: 55 unique IDs across three native search pages, matching the reported total with no duplicates. This is not full archive coverage or all-original review. Seven new selected map records expose Download asset ID 0. Metadata identifies 1995 city/ward map, 1997 planning map and August 1973 planning-scheme sheets; three “Planning scheme” records are actually local contour sheets. No source scans added; physical holdings remain possible. Checkpoints: `ryde_boundary_search_remaining_pages.json`, `ryde_boundary_pages_2_3_selected_records.json`. Collection unchanged at 1,173 files.

- Parramatta 12 December 2011 agenda item 11.2 attachments 3/4: two unchanged 3,507 × 2,480 PNG originals compare CURRENT and PROPOSED Arthur Phillip–Caroline Chisholm and Elizabeth Macarthur–Woodville ward lines. Scale 1:12,000; CCD legend elector statistics dated 17 June 2011, not map production date. Partial ward-change sheets, not full LGA maps. Monochrome halftone/street readability limits preserved; smaller GIF derivatives excluded. Agenda seeks exhibition/later determination, final adoption unverified. Source recommendation says 6 January 2011 while paragraph 18 says 6 January 2012; do not treat as boundary commencement. Collection 1,175 files. Checkpoint: `parramatta_2011_ward_attachments_review.json`.

- Parramatta 27 February 2012 final ward-review item 11.4: four unchanged colour PNGs (2,481 × 3,508), AP→CC, EM→AP, EM→Woodville, EM→Lachlan Macquarie parkland correction. First three printed 14 December 2011, scale 1:12,000; correction printed 19 January 2012, scale 1:1,339. Whole sheets inspected; current/proposed panels, CCD lines/hatches and elector-statistics date 17 June 2011 kept separate. Minutes resolution 12970 adopts revised transfers/correction; legal commencement not independently verified. IMPORTANT: final five/one/three CCD transfers differ from earlier December agenda four/five proposals; do not label the earlier two saved sheets as adopted. JPG derivatives excluded. Collection 1,179 files. Checkpoint: `parramatta_2012_ward_attachments_review.json`.

- Auburn City Residential Development Strategy 2015: unchanged 161-page PDF. PDF page15 (printed9) Figure2 shows whole former Auburn LGA, red dashed keyed boundary, adjacent council labels, roads/railway and kilometre scale. Land-use fills/station-distance rings are separate. Map footer18 March2015; final revision table also lists27 March2015, neither independently verifies legal boundary commencement. Selected map inspected, not full report. Parramatta Smart City2015 PDF49/printed47 simplified wards diagram remains review-only; fetched2014–15 annual report visual review pending. Collection1,180 files. Checkpoint: `parramatta_auburn_pre2016_reports_review.json`.

- Historical Planning Portal originals saved: Parramatta LAP_001 IDs ending20110616 and20150122, Holroyd LAP_001 ending20130218. All one-page A3 PDFs inspected: 1:80,000 Parramatta, 1:40,000 Holroyd, GDA94/MGA56. Native LGA key differs from LEP application Included key; internal grey planning exclusions are not LGA holes. Parramatta2015 includes central area excluded from LEP2011 sheet, with no LGA change inferred. Portal application periods2011–15/2015–22/2013–23 describe instrument maps, not council-boundary commencement. Cadastre dates27May2011/24Nov2012 preserved separately. Holroyd metadata title20121126 differs from printed ID20130218. Parramatta annual-report all133 thumbnails screened without map; contents refers to PartC beyond this file. Collection1,183 files. Checkpoint: `parramatta_holroyd_historical_lap_review.json`.

- Historical Auburn/Bankstown Land Application originals: Auburn IDs ending 20100728, 20121115 and 20130604; Bankstown ending 20150211. All four one-page sheets inspected and saved unchanged. Auburn scales 1:40,000/1:30,000; Bankstown 1:60,000, all A3. LGA boundary keys are separate from LEP coverage, deferred-matter zones and grey exclusions; no LGA change inferred from altered planning coverage. Portal application periods and cadastre dates are preserved separately from legal boundary dates. SOURCE QUIRK: Auburn 20121115 and 20130604 print MGA Zone 55; 20100728 prints Zone 56. Verify before georeferencing; source labels not corrected. Four source editions, not four verified legal boundary editions. Collection 1,187 files. Checkpoint: `auburn_bankstown_historical_lap_review.json`.

- Southern Sydney historical LAP originals: Canterbury 20121105; Hurstville 20120822/20130410/20150505/20150715; Rockdale 20110630/20140409; Kogarah 20121113. Eight unchanged one-page originals, all whole sheets inspected. A3 scales 1:40,000 except Rockdale 1:35,000; GDA94 Zone56. Hurstville 2015 sheets omit the separate LGA legend used in 2012/2013: former extent supported by LGA inset, neighbour labels and earlier-map comparison; black Included/red DM keys describe planning coverage. Rockdale northern grey exclusion is not an LGA hole. Portal periods are planning application; 20150505 is listed made and replaced on 24July2015. Native IDs/cadastre dates and PDF metadata titles retained separately. No distinct legal boundary change inferred. Collection 1,195 files. Checkpoint: `southern_sydney_historical_lap_review.json`.

- Inner West/Botany Bay historical LAP originals: Ashfield 20130820, Leichhardt 20131213, Marrickville 20111118 and 20200928, Botany Bay 20130612. Five unchanged one-page sheets inspected, all explicit LGA keys. A3 scales 1:20,000 except Botany Bay 1:40,000; GDA94 Zone56. Leichhardt/Botany grey planning exclusions and red deferred-matter areas are not LGA holes. Marrickville 2020 explicitly labels Former Marrickville LGA, not the whole Inner West extent; updated cadastre and neighbouring council names do not establish a new legal boundary edition. Portal periods, native IDs and cadastre dates recorded separately. Portal to-date wording preserved as retrieved, not independently verified current legal status. Collection 1,200 files. Checkpoint: `inner_west_botany_historical_lap_review.json`.

- Northern Beaches historical LAP originals: five Manly sheets 20130315/20150127/20150311/20150804/20151023, Warringah 20110919/20131016, Pittwater 20140217. Eight unchanged one-page sheets inspected, explicit LGA keys distinct from LEP Included and red Deferred Matter. A3 scales Manly 1:25,000; Warringah/Pittwater 1:80,000, GDA94 Zone56. Changing Manly DM areas and large Warringah internal red area are planning coverage, not LGA holes or proven legal boundary changes. Three 2015 Manly files are image-only; native IDs/keys read visually. Source quirk: Manly 20151023 cadastre addendum reverts to 30August2011, while 20150311/20150804 print 16June2014. Source preserved without correction. Portal periods/native IDs/cadastre dates kept separate. Collection 1,208 files. Checkpoint: `northern_beaches_historical_lap_review.json`.

- Gosford/Wyong historical LAP originals: twelve Gosford portal editions from 20140110 to 20200102 and two Wyong editions 20131220/20150303. Fourteen unchanged one-page sheets inspected, all explicit LGA keys. A3 scales Gosford 1:195,000; Wyong 1:145,000; GDA94 Zone56. Later Gosford editions retain former Gosford extent, not whole Central Coast. DM and Gosford City Centre SEPP areas are planning coverage, not LGA holes. Source quirks: Gosford file/portal 20180613 prints ID 20180504; 20200102 printed ID omits _195; 20140514 heading says Plan2013 instead of portal Plan2014; Wyong 20150303 printed ID uses _145000_ instead of _145_. Preserve originals and both IDs. Portal Gosford 20140514 period ends11Sep2014, next20140819 begins12Sep2014; made-and-replaced entries have no assumed duration. No distinct legal boundary change inferred. Collection 1,222 files. Checkpoint: `central_coast_historical_lap_review.json`.

- Western Sydney historical LAP originals: Blacktown 20150122; four Penrith sheets 20100623/20130121/20140417/20141104; Fairfield 20130117/20130926; Liverpool 20080815/20130228/20140716. Ten unchanged one-page sheets inspected, explicit LGA keys distinct from LEP Included and Deferred Matter. Grey internal planning exclusions are not LGA holes. A3 scales Penrith/Liverpool 1:120,000, Fairfield 1:80,000. SOURCE QUIRK: Blacktown prints 1:250,000 despite _080_ in native/portal ID; preserve and verify before georeferencing, do not silently correct. All GDA94 Zone56. Portal application, map-ID and cadastre dates separately recorded; no legal boundary change inferred from source editions. Collection 1,232 files. Checkpoint: `western_sydney_historical_lap_review.json`.

- Northwest Sydney LAP originals: Hawkesbury20120209; Hills20120404/20140918 and later20181112; Hornsby20130903 and later20221019; Ku-ring-gai20150114 and Local Centres20121023. Eight unchanged one-page sheets inspected. Seven explicit LGA keys; Hornsby2022 keys Included only, saved as later planning-extent comparison without independently keyed LGA line. Hills/Hornsby older maps include southern pre-transfer extents; later maps show reduced southern extents, without independent legal commencement/transfer-geometry proof. Ku-ring-gai local-centre islands and grey exclusions/redDM are planning coverage, not LGA holes. Hornsby2013 named internal outlines are not verified official suburbs. A3 scales Hawkesbury1:300,000, Hills/Hornsby2013 1:160,000, Hornsby2022 1:170,000, Ku-ring-gai1:60,000; GDA94 Zone56. Ku-ring-gai2015 ID/scale/cadastre numerals read visually because text extraction omits them. Dates/IDs separate. Collection1,240 files. Checkpoint: `northwest_sydney_historical_lap_review.json`.


- Ryde/North Shore historical LAP originals: four Ryde sheets 20100527/20130625/20140528/20141205; Willoughby20121112, Lane Cove20091201, North Sydney20130607, Mosman20111124, Hunters Hill20111219. Nine unchanged one-page sheets inspected. Eight explicit LGA keys. North Sydney keys only LEP Included; retained as planning-extent comparison, not independently keyed LGA evidence. Ryde red deferred matters are planning coverage, not LGA holes. A3 scales Ryde 1:40,000 except 20130625 1:35,000; Willoughby 1:30,000; Lane Cove/North Sydney/Hunters Hill 1:20,000; Mosman 1:25,000. All GDA94 MGA56. Lane Cove native neighbour label spells CITY OF RIDE COUNCIL; preserve source typo. Map-ID, cadastre and portal application dates recorded separately; to-date wording is as retrieved. No distinct legal boundary edition inferred. Collection 1,249 files. Checkpoint: `north_shore_ryde_historical_lap_review.json`.


- Eastern Sydney/Canada Bay historical LAP originals: Randwick20120615; Waverley20120508 and Bondi Junction Centre20100317; Woollahra20141205; Canada Bay20130419/20140304. Six unchanged one-page originals inspected, all explicit LGA keys. Bondi Junction centre coverage, Randwick internal grey areas and Canada Bay red DM are planning coverage, not LGA holes. A3 scales Randwick1:50,000, Waverley/Canada Bay1:40,000, Woollahra1:30,000; all GDA94 Zone56. SOURCE QUIRK: Woollahra bar prints 0/200/400/600 Kilometres, inconsistent with local extent/native scale; preserve unchanged and verify units before georeferencing. Canada Bay20140304 metadata title uses20140128, native ID matches portal. Bondi Junction portal to-date text coexists with Repealed status; no current legal status inferred. Map-ID, cadastre and application dates separate. No legal boundary change inferred. Sutherland2015, Burwood2012 and Strathfield2012 registers opened but no LAP entry found; other layers/sources remain open. Collection1,255 files. Checkpoint: `eastern_canada_bay_historical_lap_review.json`.


- Southwest Sydney LAP originals: Camden20100705/20140121/20140808 and later20171123; Campbelltown20150428 and later20171212; Wollondilly20110131. Seven unchanged one-page sheets inspected, all explicit LGA keys. A3 scales Camden1:60,000, Campbelltown1:120,000, Wollondilly1:320,000; all GDA94 MGA56. Grey LEP exclusions and red DM are planning coverage, not LGA holes. Later Camden/Campbelltown sheets retained for comparison; no independent legal commencement/transfer geometry verified. SOURCE QUIRK: Camden portal/file20140808 ID uses_060_, native printed ID uses_020_, native scale1:60,000; preserve both IDs. Portal application, map-ID and cadastre dates separate. Sutherland Heathcote Ridge20150511 downloaded and visually screened, excluded: main map keys only Subject Land; small LGA locator inset is context. Collection1,262 files. Checkpoint: `southwest_sydney_historical_lap_review.json`.


- Southwest comparison LAP originals: Camden20180705; Campbelltown20170411/20170412/20170424/20180111/20180124; Wollondilly20180322/20180427/20190813. Nine unchanged one-page sheets inspected, all explicit LGA keys. A3 scales Camden1:60,000, Campbelltown1:120,000, Wollondilly1:320,000, GDA94 MGA56. Internal Excluded/DM/SRGC are planning coverage, not LGA holes; changing DM areas are not legal boundary-change evidence. SOURCE QUIRK: Wollondilly20180322 native ID uses_3320_ versus portal/file_320_; printed scale1:320,000. Camden20180705 metadata title uses20130415, native ID matches portal. Map-ID, cadastre and portal dates separate. These plus previous batch cover exposed LAP editions up to2019 in the three registers; later maps unreviewed. No legal commencement/transfer geometry independently verified. Collection1,271 files. Checkpoint: `southwest_comparison_lap_review.json`.


- Blue Mountains/Sutherland/Burwood/Strathfield LAP originals: Blue Mountains20150601/20180515/20180516; Sutherland20150424/20180221; Burwood20120531; Strathfield20120924. Seven unchanged one-page sheets inspected, all explicit LGA keys. A3 scales Blue Mountains1:240,000, Sutherland1:90,000, Burwood1:20,000, Strathfield1:25,000. GDA94 Zone56, MGA printed except Burwood. Red DM areas are planning coverage, not LGA holes. Sutherland2018 neighbouring amalgamated council names are not proof of Sutherland boundary change. Map-ID, cadastre and application dates separate; to-date text as retrieved. CORRECTION/RESOLUTION: previous no-LAP findings covered retrieved page content only. Sutherland LAP entries are on page=1; indexed Burwood/Strathfield entries expose originals. Full-register coverage must account for pagination. No legal boundary change inferred. Collection1,278 files. Checkpoint: `blue_mountains_sutherland_innerwest_lap_review.json`.


- Sutherland Amendment7 proposal Part2 maps original: source filename19September2016;200-page PDF saved unchanged. Whole-LGA sheets on PDF pages138/139 have native IDs20150424/20151120, explicit LGA keys, scale1:90,000 A3, GDA94 MGA56. Explanation PDF page137 proposes including874–876 Old Princes Highway in LEP coverage. Second sheet is proposal; adoption/application period unverified. Red DM changes are not LGA boundary changes. Both sheets inspected; full-document page-by-page review not claimed. Original PDF retained rather than extracted raw pages. Collection1,279 files. Checkpoint:`sutherland_proposal_lap_review.json`.

- Trover Sutherland discovery: first newspaper result page saved (20 unique articles), four OCR renditions screened. Article159721925 (Sydney Mail21January1925 page18) describes a district map in Frank Cridland history of Port Hacking/Cronulla/Sutherland; book original/map not yet reviewed. Article235366622 (Propeller22August1935 page1) discusses preparing a riding-transfer map, not exposed original. Trove .txt route returned HTML with OCR text; unchanged bytes retained. No complete search, earliest-date or image verification claim. Library node251 plain request403; asset unexposed. Checkpoint:`trover_sutherland_map_boundaries_review.json`.

- Sutherland 2015 ward review: two unchanged originals saved. Detailed one-page Option 2 sheet has proposed ward fills, red CURRENT ADOPTED WARDS Bdy and magenta SA1 (2011 Census) overlay. Seven-page report dated 14 September 2015; PDF6 existing wards, PDF7 proposal over existing red lines. All three sheets visually inspected. Whole Shire outline present, no separate LGA key; no scale/CRS assertion. Council resolution endorses exhibition, not verified final adoption. Report says last adjustment in 2002; continuous legal validity not assumed. Linked exhibition 25 September–6 November2015 supplies detailed sheet context; sheet itself undated. Cridland1924 catalogue confirms maps but original scan/LGA evidence remains unresolved. Collection1,281 files. Checkpoint: `sutherland_2015_ward_review.json`.

- Blacktown historical comparison: two unchanged one-page LAP originals saved (IDs ending 20160503 and 20181029). Both whole sheets inspected; explicit LGA Boundary key is separate from LEP Included key. Native scale 1:80,000 at A3; GDA94 MGA56. Cadastre dates: 19 January 2016 and 29 October 2018. Indexed government register periods: 3 June 2016–27 February 2019 and 28 February 2019–22 May 2025. These periods refer to planning-map application, not proven LGA change dates. Later sheet retains neighbouring Holroyd label; do not use this to assert legal validity. Printed IDs match filenames. Collection: 1,283 files. Checkpoint: `blacktown_historical_lap_comparison_review.json`.
- Pagination audit limit: direct requests to all 46 previously used Planning Portal registers returned HTTP403. Zero pages audited through that transport. Web/index fallback found the two Blacktown originals; full register coverage remains open. Checkpoint: `sydney_lap_pagination_audit.json`.

- Fairfield 2019 ward maps: published images saved unchanged, 845×575 existing three wards (March2019 news) and 900×636 proposed two wards (August2019 exhibition). Both whole council outlines visually inspected, with labelled ward fills but no separate LGA line key. Proposed w900 file is a published derivative; unsuffixed file404, larger original unresolved. Low resolution limits precision digitising. Sheet dates inferred only from linked news context; final proposal adoption unverified.
- Blacktown ward/suburb PDF: native preparation date4May2020, one page, 1:75,000 at A3. Whole sheet visually inspected. Separate Blacktown LGA, Suburb and ward keys. CRS and legal-validity period unverified. Original unchanged. Collection1,286 files; 993 boundary JPEGs including12 indexes. Checkpoint: `fairfield_blacktown_historical_wards_review.json`.
- North Sydney November2019 ward-options report indexed at council document8999241; direct PDF403, not saved. Old consultation URL now returns landing page. Blacktown2016 archive map page returns polling-place table without original map asset. Bankstown2012 archive index accessible, map asset unresolved.

- NSWEC 2017 local government election supplementary report saved unchanged (196 pages).45 council map plates indexed in `nswec_2017_supplement_map_page_index.csv`. All45 thumbnail screened; detailed whole-sheet review for North Sydney PDF118, Parramatta136 and Canterbury–Bankstown32 confirms red Local Government Boundary and purple Ward Boundary keys. Individual base-map dates differ from report/election year. Other plates need detailed review before precision digitising; full-report visual review not claimed.
- North Sydney18November2019 report saved (9 pages). Detailed whole council proposal map PDF8, native scale1:5500, north/south ward fills and red small polygons; no separate LGA key. AEC figures22October2019 date is enrolment context. Proposal preserved; later adoption is not automatically assigned to this sheet. Prior403 resolved with project research User-Agent.
- Canterbury–Bankstown23July2019 agenda saved (149 pages). PDF90 has two local ward-change panels, not whole LGA. Report89–90 states proposed route restores former Canterbury council boundary along Punchbowl Road. Proposal only; no standalone LGA line key or verified final adoption. Original retained unchanged. Collection1,289 files. Checkpoint:`nswec_north_sydney_cbcity_historical_ward_reports_review.json`.

- NSWEC2016 supplementary report saved unchanged (259pages), with76 council map plates indexed in `nswec_2016_supplement_map_page_index.csv`. All76 thumbnail screened; enlarged whole-page reviews for Blacktown PDF27, Forbes93, Liverpool148 and Sutherland197 confirm red LGA and purple ward keys. Sutherland whole-council inset and Liverpool detail inset distinguished. Embedded maps often low resolution; native dimensions indexed. Election/report year does not prove every base-map or neighbouring council layer date.
- NSWEC2008/2012 reports retained as review-only sources outside raw map collection. Four/27 large-image pages respectively thumbnail screened; map-reference text searched. No boundary-map plate located by these checks; full198/915page visual review not claimed. 127 printed2012 map references recorded in `nswec_2012_printed_map_references.csv`; links not yet verified. Collection1,290files. Checkpoint:`nswec_2008_2012_2016_map_review.json`.

- Older Sydney council reports: three unchanged originals saved. Blacktown Appendix18 (15 PDF pages) has whole-LGA map on PDF1 with explicit magenta Blacktown LGA key and native date4December2013; rate subcategories are proposals, separate from LGA outline. Bankstown2012–13 annual report (201 pages) has city profile map PDF8 and four-ward council map PDF10. Canterbury2008–09 annual report (133 PDF pages) has whole council three-ward map on PDF5 (printed8–9). These three pages/spread reviewed at full size; annual-report maps are small, without separate LGA line key. Report years do not establish map preparation dates or legal validity. Canterbury2003–04 original retained review-only outside raw collection: native text and first18 pages screened; no map located by those checks, not a full148page visual audit. Bankstown2012 archive map page exposed polling-place table, no original map asset in bounded page check. Collection1,293 files. Checkpoint:`blacktown_bankstown_canterbury_older_report_review.json`.

- Earlier Canterbury whole council ward maps saved in three unchanged annual reports:2004–05 PDF5 (149pages),2006–07 PDF6 (170pages),2007–08 PDF4/printed10–11 (121pages). Each map page reviewed enlarged; first18pages thumbnail screened. Three ward fills form whole council outlines, without separate LGA key, scale or CRS.2004–05 is a stylised raised-perspective raster graphic; poor precision.2006–07/2007–08 contain drawing paths and native map labels; spatial coordinates not verified. Report dates are context, not proven map dates/legal validity; differences do not prove boundary change. Holroyd financial report12April2013 (39pages) and Living Holroyd community plan (64pages) retained review-only outside raw collection: all pages thumbnail screened, native text checked; no usable map located. Decorative outlines not accepted. Collection1,296 files. Checkpoint:`canterbury_2004_2008_holroyd_report_review.json`.

- Two IPART2015 originals saved unchanged. Sydney Olympic Park merger submission30June2015 (98pages): PDF9 whole map reviewed, explicit purple LGA Boundary key shows whole former Auburn, Burwood and Canada Bay outlines; embedded753×753 map. PDF10 says existing council areas; merger proposal is not verified adoption. Appendix C October2015 council assessments (290PDFpages): Holroyd locator PDF121/printed235 reviewed, Holroyd blue with neighbouring councils labelled;223×156 image is too small for precision tracing, no separate LGA key/scale/CRS. Individual base-map dates/legal validity unverified; full reports not visually audited. Ryde2012 integrated open-space plan exact URL already registered, skipped. Collection1,298 files. Checkpoint:`ipart_2015_merger_assessment_map_review.json`.

- Holroyd2013 complying-development sheet saved unchanged. Native ID20131016/cadastre23September2013;1:10000 A3,GDA1994 MGA56. Whole sheet inspected: partial Blacktown edge identified by grey external area/Blacktown City label, plus whole-LGA locator; no separate LGA line key. Pink planning exclusions/yellow frame are not council boundaries. Register application22February2014-to-date is planning context, not legal LGA validity. Old Guildford flood study saved unchanged (130pages, reportAugust2010): PDF15/Figure1-2 inspected, yellow explicit LGA Boundary key, partial former Holroyd/Parramatta/Fairfield/Bankstown edges. Native7April2010Version2,1:20000 A4,GDA1994 MGA56. Red study/blue catchment separate. Renderer emitted zlib warning in selected-page run; target map rendered, fullPDF integrity not claimed. Holroyd2017 flood-volume API metadata accessible but resource pages/download routes403; no original or boundary-map evidence verified. Collection1,300 files. Checkpoint:`holroyd_2013_guildford_2010_boundary_review.json`.

- Four unchanged2010 SEPP complying-development sheet001 PDFs saved for Botany Bay, Marrickville, Mosman and Pittwater. Allwholepages visually inspected. Each has whole council outline in small locator inset; detailed panels partial. No separate LGA line key; Marrickville grey external mask gives partial edge. Coast/exclusion outlines in other panels are not independently keyed LGA lines. Cadastre:Botany1February2010,Marrickville8December2008,Mosman1June2010,Pittwater14September2010. ScaleA3:Botany1:20000,others1:10000. GDA1994Zone56;MGAexplicitMosman/Pittwater. Native mapIDs20101022, register application31December2010-to-date; dates separate from legal LGA validity. Pink exclusions and sheet frames are not council boundaries. Onlysheet001 per council retrieved; remaining sets unreviewed. Bounded Holroyd2017 mirror search found no original link; public portal403 unresolved. Collection1,304files. Checkpoint:`sydney_2010_sepp_locator_review.json`.

- Remaining2010 Marrickville/Botany Bay LCD002–004 originals saved unchanged; both LCD001–004 sets now retained. Allsixwholepages visually inspected. Marrickville grey outside mask follows former council edge; whole-LGA locators on all. Botany mapped council context contains large blank outside areas;002/004 sparse airport/port context. No standalone LGA line key. Pink exclusions and coloured frames are not council boundaries; detailed panels partial. Native IDs20101022;Marrickville cadastre8December2008/1:10000A3,Botany1February2010/1:20000A3;GDA1994Zone56. Application dates not legal LGA validity; complete four-sheet sets do not establish full historical register coverage. Collection1,310files. Checkpoint:`marrickville_botany_2010_sepp_remaining_review.json`.

- Four archived Leichhardt LEP2000 originals saved unchanged and whole sheets visually inspected. Residential density printed12June2002 includes Glebe in whole council-shaped mapped extent, scale1:6000. Heritage titleIssuedJune2003 versus printed9July2009/copyright2004, scale1:6000; Glebe not included in highlighted context. Zoning digital reconstruction nativeIssued31January2013 versus cadastre31January2014/footer5February2014, throughAmendment19. No standalone LGA key; planning extent not independently verified legal council boundary. Exact transfer geometry/commencement unverified. Foreshore PDF kept as companion, with whole context and Balmain/Glebe insets,1:2500/10000; red control lines are not LGA boundaries, native do-not-scale warning. Copyright1999 not proven creation date. CRS unverified;2026server paths are hosting dates, LEP2000 is instrument label, not all map edition dates. Collection1,314files. Checkpoint:`leichhardt_lep2000_archived_map_review.json`.

- Six unchanged Leichhardt DCP2000 suburb-profile originals saved. First map page of each visually inspected enlarged. Balmain PDF1/A217 and RozellePDF1/A184 explicitly describe thick black suburb outline; two boundary-map reports. AnnandaleA92,GlebeA130,LeichhardtA58,LilyfieldA21 map distinctive planning neighbourhoods/conservation overlays; four registered as companion documents, not verified gazetted suburb/LGA maps. First-page amendment dates respectively7November2001,23January2002,8August2001,4April2001;Balmain12March2003,Rozelle17July2002. Amendments are not map creation dates; later page editions vary. Scale/CRS/legal commencement unverified; small raster detail limits precision. General section65pages review-only outside rawcollection;first12/PDF41–65 thumbnails,text/image inventory screened, control maps41–43 not independently confirmed LGA evidence. Full-document detailed reviews not claimed. Collection1,320files. Checkpoint:`leichhardt_dcp2000_profile_map_review.json`.


### Rockdale archived council papers: 2013 and 2015 map review

- Saved two unchanged public Bayside-hosted former Rockdale council-paper PDFs: November2013 (753 pages) and May2015 (481 pages). Each full PDF is one registered original. The November volume repeats annual-report material.
- November2013 PDF69 / 2012–13 annual-report printed11: whole Rockdale outline split into five labelled ward fills, including the airport area. Native vector paths/text. No explicit LGA line key, scale or CRS confirmed. Report year and meeting date do not establish map creation or legal boundary dates.
- May2015 PDF109 / Draft Biodiversity Strategy2014 printed19 Figure1: whole-city aerial vegetation map with black line explicitly keyed “Rockdale City Council”. Native map date2June2014; GDA1994 MGAZone56; scale bar0–800metres. Whole page and enlarged date/CRS inspected. The ecological overlays are separate from the council outline.
- May2015 PDF215 / MorrisonLow business case printed17 Figure8: labelled council outlines/fills for Canterbury, Rockdale, Hurstville and Kogarah. Embedded682×561 raster limits digitising precision; no scale/CRS or LGA line key confirmed. Whole page inspected.
- May2015 PDF437 and442–445 were thumbnail-screened only: council outlines and merger options. Proposed mergers are not evidence of adoption. These archival maps do not independently verify legal boundary commencement.
- Both volumes were text-screened; selected pages were visually reviewed, not all1234 pages. Source URLs, map pages and review limits are in `explore/output/2026-10-10_download-boundary-maps/rockdale_2013_2015_council_map_review.json`.
- Verification: new fetch/copy SHA256 hashes, PDF page counts and duplicate exclusion pass. All1,322 registered paths and byte sizes pass. Older collection hashes were not recalculated in this batch.


### NSW Department of Local Government: 2003–05 report map review

- Registered one unchanged164-page2004–05 annual report from the official Data.NSW linked Archive-It/OpenGov archive. Parliament’s direct PDF returned403; archive original returned200.
- PDF4 / printed2: inner-Sydney and outer-Sydney council-area outlines with labels and scale bars0–5km/0–10km. Embedded383×323/365×489 raster insets limit digitising precision. The Sydney credit date is too small to verify; do not infer it from the annual-report year.
- PDF5 / printed3: statewide council-area map, native copyright NSWDepartmentofLands2005, embedded792×568 raster. Includes regionalNSW, as authorised. No CRS confirmed. Headings identify council areas; publication/copyright dates do not independently prove legal boundary commencement. Both map pages visually inspected whole.
-2003–04 report169pages: text-screened and24 selected pages thumbnail-screened (first12,last8,and other large-image pages). No boundary map found in that bounded review; not a full visual absence audit. Kept only under `explore/output/2026-10-10_download-boundary-maps/nsw_dlg_review_only/`.
- Source checkpoint: `explore/output/2026-10-10_download-boundary-maps/nsw_dlg_2003_2005_map_review.json`. New hashes/page counts/duplicate exclusion pass; all1,323 registered paths and sizes pass. Older hashes not recalculated.


### NSW Department of Local Government: 2002–03 and2005–06 follow-up

- Registered unchanged172-page2005–06 annual report from official Data.NSW linked Archive-It/OpenGov original. PDF168/169 (printed166/167) show inner/outerSydney and statewide council-area maps; both whole pages visually checked.
- Same apparent map layout as2004–05 report, at lower raster resolution: inner333×281, outer317×425, statewide652×467. Do not infer a boundary change from the different report year. Statewide map copyright2005; no CRS confirmed. Sydney scale bars0–5km/0–10km. Precision remains limited.
-2002–03 report158pages text-screened, first12/last8 pages thumbnail-screened, no boundary map found in that review. Retained review-only under the existing exploratory output folder; not counted as a map original. This is not a full visual absence audit.
- Catalogue query “Department of Local Government” returned7 records, all retrieved. Earliest annual report returned was2002–03; this does not establish complete archive coverage. A2000–01 Parliament report is an open lead.
- Checkpoint `explore/output/2026-10-10_download-boundary-maps/nsw_dlg_2002_2006_map_review.json` contains source URLs and review limits. New hashes/pagecounts/duplicate exclusion pass; all1,324 registered paths/sizes pass. Older hashes not recalculated.


### Manly2011 LGA map within archived draftDCP2013 Amendment8

- Saved unchanged214-page draftDCP PDF from former Manly Council archive. Whole PDF159 / printed158 visually inspected: Schedule1MapB ResidentialOpenSpaceAreas. Legend explicitly keys dash-dot LGA boundary, with Manly/Warringah boundary context and offshore line sections. Open-space colour classes are separate planning areas. Do not assume every southern/offshore boundary is visible within the map frame.
- Native map credit November2011; scale1:16000@A3; ProjectionMapGridofAustralia, datumGDA94. Zone not confirmed. Embedded1367×957 raster limits precision.
- Cover says draftAmendment8 with last-amended @2016 placeholder. OriginalDCP adoption16July2012/commencement19April2013 do not establish this draft’s adoption or legal boundary commencement. Map date, plan dates and draft dates remain separate. Other candidate mapsPDF158/160 were text-located but not visually verified.
- Annual report2003–04 (56pages) text-screened, first12/last4 thumbnail-screened. No boundary map found in that bounded review; kept review-only, not full visual absence audit. Earlier NSWDLG2000–01 Parliament PDF returned403; no original obtained.
- Checkpoint `explore/output/2026-10-10_download-boundary-maps/manly_2011_draft_dcp_map_review.json` records sources and limits. New hashes/pagecount/duplicate exclusion pass; all1,325 registered paths/sizes pass; older hashes not recalculated.


### Georges River April1999 keyed LGA map set; council report review

- Saved unchanged8-page GeorgesRiverCatchment map set from NSWPlanning PDF archive. Native publisher pagePDF2 says April1999, DepartmentofUrbanAffairsandPlanning. URL filename2009 is not the map edition date. One PDF contains an overview plus5 detailed sheets, counted as one original.
- WholePDF3 overview andPDF5 Map2of5 visually inspected. Explicit legend distinguishes black patterned LGA line from thickgrey catchment edge. Overview1:200000/0–6km; detailedPDF5 1:100000/0–3km, Bankstown,Canterbury,Hurstville,Kogarah,Rockdale boundary sections. Maps cover catchment-related areas and surrounding sections, not every whole council. Coloured catchment fills do not define LGAs. No CRS confirmed; publication date is not independent legal-validity evidence.
- All6 map pages have native vector drawings/text and no embedded raster images. All8 pages thumbnail-screened; PDF4/6/7/8 sheets not reviewed at full size.
- Four Hurstville/Kogarah2010–11/2011–12 report originals retained review-only in exploratory output: all text screened; first18 pages each visually thumbnail-screened, plus Hurstville2010–11 PDF78–84 and Kogarah2011–12 PDF48–60. No boundary map found in these bounded screens; not full visual absence audits. Official annual-report page has10 historic links;4 inspected,6 remain.
- Existing review checkpoint `explore/output/2026-10-10_download-boundary-maps/georges_river_1999_map_report_review.json` records pages/source limits. New map hash/pagecount/duplicate exclusion and4 review-only copy hashes pass; all1,326 registered paths/sizes pass. Older hashes not recalculated.


### KogarahJuly2015: HurstvilleGrove/Penshurst local boundary amendment

- Saved unchanged20July2015 governance working-party16-page report with maps, plus27July2015 council16-page minutes as a map companion. Council agenda70pages retained review-only; it links the working-party source but its boundary map was not confirmed. PublicAGN_AT.PDF route works; AGN.PDF/AGN.HTM variants404.
- Working-partyPDF11 Annexure1current andPDF13 Annexure3proposed maps visually inspected whole. Both explicitly key red suburb boundaries and show localOatley context. Current includes32ParkviewAvenue inPenshurst; proposed includes it inHurstvilleGrove. Neither is a whole-suburb or LGA map. Native scale1:2000atA4; no CRS or map creation date confirmed. Embedded1377×1948/1377×1947 raster maps. Aerial companionsPDF12/14 not visually reviewed.
- Council minutesPDF11 adoptedMinute90/2015 resolves the alteration. ReportPDF10 says Council must inform GNB and await approval/processing notification. No finalGNBapproval record or legal commencement was obtained; keep current/proposed/councilresolution states distinct.
- Checkpoint `explore/output/2026-10-10_download-boundary-maps/kogarah_2015_suburb_boundary_review.json` records sources and page limits. Two originals consist of one map-bearing report and one resolution companion; not two independent map editions. Newhashes/pagecounts/duplicate exclusion and review-only copy hash pass; all1,328 registered paths/sizes pass. Older hashes not recalculated.


### Kogarah2011 ward-map gap and Hurstville2014 keyed map

- Saved unchanged23-page NSWEC HurstvilleWard by-election report15March2014. All23 pages thumbnail-screened, PDF5 / printed3 whole visually inspected. Explicit redLGA/purpleWard line keys. Panel covers HurstvilleWard and partialformerHurstvilleLGA edges adjacentCanterbury,Rockdale,Kogarah; not a wholeLGA map. Embedded470×665 raster limits precision; no scale/CRS confirmed. Pollingplaces current28January2014 is not legalboundary date.
- Kogarah10October2011 councilreportPDF23–25 lists4 current/proposedCCD/UBDward-map annexures. They are absent from the reviewed32-page downloadedvolume: PDF26startsnextreport; PDF23–32thumbnail-screened. December12reportPDF57/58 refers back toOctober report. October17governanceagenda7pages has no ward report in contents. All3 originals retained review-only, not counted as maps. No claim of wholearchive absence.
- Kogarah2011–12 annual reportPDF193 states revisedwards exhibitedOctober/November2011 and NSWEC records updated after12December2011 resolution. Those statements locate the search; they do not substitute for missingmap annexures. Three other guessedpublicagenda routes404; recorded.
- Checkpoint `explore/output/2026-10-10_download-boundary-maps/kogarah_2011_hurstville_2014_ward_review.json` recordsmapreview and missingannexure evidence. Newhash/pagecount/duplicate exclusion,3review-onlycopyhashes pass; all1,329 registeredpaths/sizes pass; olderhashes not recalculated.


### NSWEC 2014 Sydney by-election map batch

- Saved five unchanged report PDFs: Woollahra Double Bay (22 pages), Willoughby mayoral (25), Willoughby Sailors Bay (23), Marrickville West/Burraga (24), and Leichhardt Birrabirragal/Balmain (27). Each contains a map on PDF page 5; all five map pages inspected whole, first eight pages of each report thumbnail-screened. Remaining pages not visually reviewed.
- Willoughby mayoral map shows the whole council outline and four wards. Other maps show ward panels and partial LGA edges. Legends explicitly distinguish red LGA and purple ward boundaries; Marrickville uses the wording “Local Government Ward Boundary”. No scale or CRS confirmed.
- Embedded raster sizes, in the order above: 901×651, 1250×904, 1587×1122, 866×1221, 1349×950. These limit digitising precision.
- Election dates: 15 March, 12 April, 14 June, 15 November and 2 August 2014. Polling-place currency dates respectively: 13 February, 13 March, 20 May, 14 October and 30 June 2014. Polling-place dates do not establish legal boundary commencement.
- Kogarah public archive index filtered to October 2011 returned eight agenda/minute links, without separate ward-map annexures. This bounded response leaves the four missing annexures unresolved; it does not prove archive-wide absence.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2014_sydney_by_election_map_review.json`. Five new hashes, PDF page counts and duplicate exclusion pass. All 1,334 registered paths and sizes pass; older hashes not recalculated.

### NSWEC Sydney by-election maps: Ryde 2015, Blacktown and Campbelltown 2017

- `data/raw/historical_boundary_maps/nsw_electoral_commission/2017_blacktown_ward_2_by_election_report.pdf`: PDF 7 (printed 7). Partial Blacktown LGA boundary with The Hills and Parramatta context; whole Ward 2. By-election 8 April 2017; polling places current 21 February 2017; polling date is not legal boundary date. Embedded raster 1253 × 886 pixels.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2017_campbelltown_by_election_report.pdf`: PDF 7 (printed 7). Whole Campbelltown LGA outline; neighbouring LGA sections. By-election 18 March 2017; polling places current 16 February 2017; polling date is not legal boundary date. Embedded raster 834 × 1180 pixels.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2015_ryde_east_ward_by_election_report.pdf`: PDF 5 (printed 3). Partial Ryde LGA boundaries around East Ward; Ku-ring-gai, Willoughby, Lane Cove and Hunters Hill context. By-election 21 February 2015; polling places current 23 January 2015; polling date is not legal boundary date; LGA key states boundaries as at 1 June 2014; report copyright 2016. Embedded raster 849 × 1201 pixels.
- All three keys identify red LGA and purple ward boundaries. No scale or CRS confirmed. First eight pages screened; map pages wholly reviewed. Other report pages not visually reviewed. Three unchanged original PDFs registered after hash, page-count and duplicate checks. These maps do not independently prove legal boundary commencement.

### Hurstville 2012 contributions plan and 2012–15 council annual reports

- `data/raw/historical_boundary_maps/hurstville_council/2012_contributions_plan.pdf`: PDF 79 (printed 72), whole Hurstville outline in black dash-dot line. Surrounding LGAs are named; boundary symbol is not separately keyed. Native map title says Draft. Enclosing plan adopted 12 December 2012, effective 14 March 2013. These are plan dates, not verified LGA commencement dates. No map-native date, scale or CRS confirmed. Embedded raster is 832 × 1184 pixels. Grey internal lines are not independently confirmed suburb boundaries.
- Six Hurstville/Kogarah annual reports (2012–13, 2013–14, 2014–15) are review-only: all native text screened and first 20 pages viewed as thumbnails. Kogarah 2014–15 PDF 20 wholly viewed: walking/cycling guide and newsletter collage, no clear LGA key. No useful boundary original accepted from this bounded review; remaining pages not visually reviewed. MuPDF emitted stitching-function syntax warnings during text screening. Originals are unchanged; selected renders succeeded.
- Hurstville plan PDF 57–64 and 75–87 screened as thumbnails, with PDF 79 wholly reviewed. New original hash, page count and duplicate checks pass. Collection total is 1,338; review-only reports excluded.

### NSWEC 2008 Kogarah and Hurstville election map originals

- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_kogarah_lga_ward_map.pdf`: one-page original, whole sheet viewed. Whole Kogarah LGA outline and four wards. Key explicitly identifies red LGA and purple ward boundaries. Native title dates map to the 2008 election; no precise map date, scale or CRS confirmed. No legal boundary commencement inferred.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_hurstville_lga_ward_map.pdf`: one-page original, whole sheet viewed. Near-whole Hurstville outline and three wards; northern LGA edge clipped by map frame. Key explicitly identifies red LGA and purple ward boundaries. Native title dates map to the 2008 election; no precise map date, scale or CRS confirmed. No legal boundary commencement inferred.
- The PDFs contain native text/vector content and numerous small raster fragments. Text extraction repeats many labels; preserved without modification. New fetch/copy hashes, page counts and registered-hash duplicate checks pass. All 1,340 collection paths and sizes checked.
- Three archived 2012 public Hurstville/Kogarah routes returned HTTP 200 through direct requests. Returned HTML has polling-place tables but no map PDF/image/KML asset link identified. This resolves the prior web fetch errors for the pages; it does not recover the original interactive map.

### NSWEC 2008 Sydney council maps: eight further originals

- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_rockdale_lga_ward_map.pdf`: Whole depicted Rockdale LGA outline, including airport and southern water extension; five wards. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_canterbury_lga_ward_map.pdf`: Whole Canterbury LGA outline; three wards. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_bankstown_lga_ward_map.pdf`: Whole Bankstown LGA outline; four wards. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_marrickville_lga_ward_map.pdf`: Near-whole Marrickville LGA outline; western edge clipped by map frame; four wards. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_ashfield_lga_ward_map.pdf`: Whole Ashfield LGA outline; four wards. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_leichhardt_lga_ward_map.pdf`: Whole depicted Leichhardt mainland/coastal outline; four wards; offshore extent not independently established. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_auburn_lga_ward_map.pdf`: Whole Auburn LGA outline; two wards; map has no polling-place symbols. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_holroyd_lga_ward_map.pdf`: Whole Holroyd LGA outline; four wards. One-page PDF, whole sheet viewed.
- All eight keys identify red LGA and purple ward boundaries. Native titles identify the 2008 election. No precise map-native date, scale or CRS confirmed; no legal boundary commencement inferred. Offshore and neighbouring boundaries are only accepted to the extent drawn in each map.
- Original PDFs preserved unchanged. New fetch/copy hashes, page counts and registered-hash duplicate checks pass. All 1,348 registered paths/sizes checked; older collection hashes not recalculated.

### NSWEC 2008 northern beaches and western Sydney maps

- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_manly_lga_ward_map.pdf`: Whole depicted Manly mainland/coastal outline; undivided council; offshore extent not independently established. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_pittwater_lga_ward_map.pdf`: Whole depicted Pittwater outline with three wards, western bays and Scotland Island; offshore extent not independently established. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_warringah_lga_ward_map.pdf`: Near-whole Warringah outline and three wards; northern edge clipped near Cottage Point. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_parramatta_lga_ward_map.pdf`: Near-whole pre-merger Parramatta outline and five wards; eastern river edge clipped by map frame. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_ryde_lga_ward_map.pdf`: Whole depicted Ryde outline and three wards; neighbouring LGA sections. One-page PDF, whole sheet viewed.
- All five maps explicitly key red LGA boundaries. Four also key purple ward boundaries; Manly is undivided. Titles identify the 2008 election. No precise map date, scale or CRS confirmed; no legal boundary commencement inferred. New originals pass fetch/copy hash, page-count and registered-hash duplicate checks. All 1,353 collection paths/sizes pass; older hashes not recalculated.
- Botany Bay: guessed `result.BotanyBay.html` route returned 404. Official index instead links `result.Botany_Bay.html`, which returned 200 but has no PDF/map/polling-place hyperlink in the returned page. No original accepted. Official 2008 council index links are saved in the existing download output folder; remaining map availability is unreviewed.

### NSWEC 2008 Sydney, eastern suburbs and inner-west maps

- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_sydney_lga_ward_map.pdf`: Whole depicted Sydney mainland/coastal outline, including Glebe; undivided council; harbour/island extent not independently established. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_waverley_lga_ward_map.pdf`: Whole depicted Waverley mainland/coastal outline and four wards; offshore extent not independently established. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_woollahra_lga_ward_map.pdf`: Whole depicted Woollahra mainland/coastal outline and five wards; offshore extent not independently established. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_randwick_lga_ward_map.pdf`: Whole depicted Randwick mainland/coastal outline and five wards; offshore extent not independently established. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_burwood_lga_ward_map.pdf`: Whole Burwood LGA outline; undivided council. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_strathfield_lga_ward_map.pdf`: Whole Strathfield LGA outline; undivided council. One-page PDF, whole sheet viewed.
- All six maps explicitly key red LGA boundaries. Waverley, Woollahra and Randwick also key purple ward boundaries; Sydney, Burwood and Strathfield are undivided. Titles identify the 2008 election. No precise map date, scale or CRS confirmed; no legal boundary commencement inferred. No whole offshore/harbour-island extent inferred from the coastal outlines.
- New originals pass fetch/copy hashes, page counts and registered-hash duplicate checks. All 1,359 registered paths/sizes pass; older collection hashes not recalculated.

### NSWEC 2008 harbour and lower north shore maps

- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_canada_bay_lga_ward_map.pdf`: Whole depicted Canada Bay mainland/coastal outline; undivided council; harbour/island extent not independently established. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_lane_cove_lga_ward_map.pdf`: Whole depicted Lane Cove mainland/coastal outline; 3 wards; harbour/island extent not independently established. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_hunters_hill_lga_ward_map.pdf`: Whole depicted Hunters Hill mainland/coastal outline; 2 wards; harbour/island extent not independently established. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_mosman_lga_ward_map.pdf`: Whole depicted Mosman mainland/coastal outline; 3 wards; harbour/island extent not independently established. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_north_sydney_lga_ward_map.pdf`: Whole depicted North Sydney mainland/coastal outline; 4 wards; harbour/island extent not independently established. One-page PDF, whole sheet viewed.
- `data/raw/historical_boundary_maps/nsw_electoral_commission/2008_willoughby_lga_ward_map.pdf`: Whole depicted Willoughby mainland/coastal outline; 4 wards; harbour/island extent not independently established. One-page PDF, whole sheet viewed.
- All six maps explicitly key red LGA boundaries. Five also key purple ward boundaries; Canada Bay is undivided. Titles identify the 2008 election. No precise map date, scale or CRS confirmed; no legal boundary commencement inferred. Whole harbour/island coverage is not inferred from mainland/coastal outlines.
- New originals pass fetch/copy hashes, page counts and registered-hash duplicate checks. All 1,365 registered paths/sizes pass; older collection hashes not recalculated.


### NSWEC 2008 outer Sydney LGA maps

Six unchanged one-page originals saved from published NSWEC result-page links. Each sheet has explicit red LGA and purple ward boundary keys. All six whole sheets were visually inspected.

- Blacktown: Five wards (1–5). Near-whole outline; eastern Seven Hills edge meets or clips the right frame.
- Baulkham Hills: Four wards (North, West, Central, East). Overview and southern urban inset. Northern Wisemans Ferry tip meets or clips the frame; inset covers part of overview context.
- Hornsby: Three wards (A–C). Overview and two urban insets, including Epping. Northern/eastern overview edges are partly clipped or covered by the inset panels.
- Ku-ring-gai: Five wards (Wahroonga, St Ives, Comenarra, Gordon, Roseville). Whole depicted LGA outline; no independent legal extent verification.
- Sutherland: Five wards (A–E). Overview and central urban inset. Northern Georges River/Sandy Point tip and southern coast boundary meet or clip the frame; offshore extent unconfirmed.
- Liverpool: Two wards (North, South). Overview and urban inset. Southeastern Holsworthy edge meets or clips the right frame.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_outer_sydney_map_review.json`.


### NSWEC 2008 western Sydney LGA maps

Seven unchanged one-page originals saved from published NSWEC result-page links. Each sheet has an explicit red LGA boundary key. Five warded councils also show purple ward keys; Campbelltown and Hawkesbury are undivided. All seven whole sheets were visually inspected.

- Blue Mountains: Four wards (First–Fourth). Overview with Katoomba/Leura/Wentworth Falls and Springwood urban insets. Northern boundary tip reaches the top frame; do not treat overview as complete.
- Camden: Three wards (North, South, Central). Near-whole outline; western boundary reaches or clips the left frame.
- Campbelltown: Undivided council. Whole depicted LGA outline; explicit red local-government key, no ward layer.
- Fairfield: Three wards (Parks, Fairfield, Cabravale). Whole depicted LGA outline.
- Hawkesbury: Undivided council. Whole depicted LGA outline with Windsor/South Windsor urban inset; explicit red local-government key, no ward layer.
- Penrith: Three wards (North, South, East). Whole depicted LGA outline with central urban inset.
- Wollondilly: Three wards (North, Central, East). Near-whole outline; southeastern Darkes Forest edge meets or clips the right frame.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_western_sydney_map_review.json`.


### NSWEC 2008 Sydney fringe and coastal LGA maps

Four unchanged one-page originals saved from published NSWEC result-page links. Each sheet has an explicit red LGA boundary key. Wyong also has a purple ward boundary key; the other three councils are undivided. All four whole sheets were visually inspected.

- Gosford: Undivided council. Whole depicted mainland/coastal outline with two urban insets (Woy Woy/Umina and Erina/Terrigal). Harbour/island and offshore extent not independently established.
- Kiama: Undivided council. Whole depicted mainland/coastal outline; offshore extent not independently established.
- Wingecarribee: Undivided council. Whole depicted LGA outline.
- Wyong: Two wards (A, B). Overview with two urban insets. Northern Lake Macquarie-facing boundary is partly covered by Inset A; no complete overview inferred. Offshore extent not independently established.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_sydney_fringe_coastal_map_review.json`.


### NSWEC 2011 Illawarra election report maps

Two unchanged report PDFs saved from the official NSWEC report index. All 64 pages were thumbnail-screened and all three map-bearing pages viewed whole. The reports have copyright 2012. Each map identifies polling on 3 September 2011, not a precise map creation date.

- shellharbour: PDF3, printed1: whole depicted mainland/coastal LGA outline, explicit red local-government key. Undivided council. Embedded raster 291 × 258 pixels; limited digitising precision and offshore extent unconfirmed.
- wollongong: PDF3, printed1: Ward1 map (264 × 343 pixels). PDF4, unnumbered continuation: Ward2 (264 × 350) and Ward3 (264 × 286). Red LGA and purple ward keys; each panel gives partial LGA context. Insets are inside the panels. No standalone whole-LGA overview confirmed.

No precise map creation date, scale or CRS confirmed; election and polling dates do not prove legal boundary commencement. Low-resolution raster locators provide limited precision for digitising. Wollongong panels remain one original report. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2011_illawarra_election_report_map_review.json`.


### NSWEC 2008 Hunter and Shoalhaven LGA maps

Six unchanged one-page originals saved from published NSWEC result-page links. Each sheet has explicit red LGA and purple ward boundary keys. All six whole sheets were visually inspected.

- Cessnock: Four wards (A–D). Whole depicted LGA outline with Cessnock and Kurri Kurri urban insets.
- Lake Macquarie: Three wards (North, West, East). Overview with northern urban inset. Eastern boundary near the Newcastle/coastal junction meets or clips the right frame; offshore extent unconfirmed.
- Maitland: Four wards (West, Central, North, East). Overview with Rutherford/Telarah and East Maitland urban insets. Southeastern river edge meets or clips the bottom frame.
- Newcastle: Four wards (1–4). Overview with central urban inset. Eastern Stockton/coastal context meets the right frame; no complete offshore extent inferred.
- Port Stephens: Three wards (West, Central, East). Whole depicted mainland/coastal and harbour outline; island/offshore extent not independently established.
- Shoalhaven: Three wards (1–3). Whole depicted mainland/coastal outline with Nowra/Bomaderry and St Georges Basin urban insets. Jervis Bay boundary context is shown, but island/offshore extent not independently established.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_hunter_shoalhaven_map_review.json`.


### NSWEC 2008 Hunter and Mid North Coast LGA maps

Six unchanged one-page originals saved from published NSWEC result-page links. Each sheet has an explicit red LGA key. Dungog and Singleton also key purple wards; the other four councils are undivided. All six whole sheets were visually inspected.

- Dungog: Three wards (A–C). Whole depicted LGA outline.
- Great Lakes: Undivided council. Whole depicted mainland/coastal LGA outline with Forster/Tuncurry urban inset; island/offshore extent not independently established.
- Greater Taree: Undivided council. Whole depicted mainland/coastal LGA outline with Taree/Cundletown urban inset; island/offshore extent not independently established.
- Muswellbrook: Undivided council. Whole depicted LGA outline with Muswellbrook urban inset.
- Singleton: Three wards (A–C). Whole depicted LGA outline with Singleton urban inset.
- Upper Hunter: Undivided council. Whole depicted LGA outline with Scone urban inset.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_hunter_midnorth_map_review.json`.


### NSWEC 2008 western regional NSW LGA maps

Six unchanged one-page originals saved from published NSWEC result-page links. Each sheet has an explicit red LGA boundary key. All six councils are undivided and no ward layer is shown. All six whole sheets were visually inspected.

- Bathurst: Undivided council. Whole depicted LGA outline with Bathurst urban inset.
- Gloucester: Undivided council. Whole depicted LGA outline; no inset.
- Goulburn Mulwaree: Undivided council. Whole depicted LGA outline with Goulburn urban inset.
- Lithgow: Undivided council. Whole depicted LGA outline with Lithgow urban inset.
- Mid-Western: Native map title names Mid-Western Regional. Undivided council. Overview with Mudgee urban inset. Eastern Kelgoola boundary meets or clips the right frame; no complete outline inferred.
- Oberon: Undivided council. Whole depicted LGA outline; no inset.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_western_regional_map_review.json`.


### NSWEC 2008 NSW tablelands LGA maps

Six unchanged one-page originals saved from published NSWEC result-page links. Each sheet has an explicit red LGA key. Cabonne also shows a purple ward key; the other five councils are undivided. All six whole sheets were visually inspected.

- Cabonne: Six wards (Goobang, Yuranigh, Ophir, Canobolas, Nangar, Bellubula). Near-whole outline; eastern/southeastern boundary meets or clips the right frame.
- Orange: Undivided council. Whole depicted LGA outline; no inset.
- Palerang: Undivided council. Whole depicted pre-merger NSW LGA outline; ACT shown only as neighbouring context, not a separate collected jurisdiction.
- Queanbeyan: Undivided council. Near-whole pre-merger NSW LGA outline; western Environa/Googong-side tip meets or clips the left frame. ACT shown only as neighbouring context.
- Upper Lachlan: Undivided council. Near-whole outline; eastern White Hanworth edge meets or clips the right frame.
- Yass: Native map title names Yass Valley. Undivided council. Whole depicted NSW LGA outline; ACT shown only as neighbouring context.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_tablelands_map_review.json`.


### NSWEC 2008 central and southwestern NSW LGA maps

Seven unchanged one-page originals saved from published NSWEC result-page links. Each sheet has an explicit red LGA boundary key. All seven councils are undivided and no ward layer is shown. All seven whole sheets were visually inspected.

- Blayney Shire: Native map title: Blayney. Undivided council. Whole depicted LGA outline. Apparent source-label error: western neighbouring area is labelled Armidale Dumaresq, geographically inconsistent with this Blayney sheet. Preserve original and do not use that neighbour label as evidence.
- Boorowa: Undivided council. Whole depicted pre-merger LGA outline.
- Cootamundra: Undivided council. Near-whole pre-merger LGA outline; western Stockinbingal-side edge meets the left frame. Frame coverage requires checking before tracing.
- Cowra: Undivided council. Whole depicted LGA outline; southern tip has a narrow margin to the bottom frame.
- Gundagai: Undivided council. Whole depicted pre-merger LGA outline.
- Harden: Undivided council. Whole depicted pre-merger LGA outline; eastern edge has a narrow frame margin.
- Young: Undivided council. Whole depicted pre-merger LGA outline.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_central_southwest_map_review.json`.


### NSWEC 2008 Riverina and southwestern NSW LGA maps

Six unchanged one-page originals saved from published NSWEC result-page links. Each sheet has an explicit red LGA key. Weddin also shows a purple ward key; the other five councils are undivided. All six whole sheets were visually inspected.

- Junee: Undivided council. Whole depicted LGA outline; western edge has a narrow frame margin.
- Temora: Undivided council. Whole depicted LGA outline; southern tip has a narrow frame margin.
- Tumbarumba: Undivided council. Whole depicted pre-merger NSW LGA outline. Blank area southwest of the Murray/state-border side is neighbouring context, not missing NSW LGA interior.
- Tumut: Undivided council. Whole depicted pre-merger LGA outline.
- Wagga Wagga: Undivided council. Whole depicted LGA outline with Wagga Wagga urban inset; southern edge has a narrow frame margin.
- Weddin: Five wards (A–E). Whole depicted LGA outline with Grenfell urban inset.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_riverina_map_review.json`.


### NSWEC 2008 central NSW and Riverina LGA maps

Four unchanged one-page originals saved from published NSWEC result-page links. Each sheet has an explicit red LGA key. All four councils are undivided. All four whole sheets were visually inspected.

- Coolamon: Undivided council. Whole depicted LGA outline; eastern edge has a narrow frame margin.
- Forbes: Undivided council. Whole depicted LGA outline; northern and southern tips have narrow frame margins.
- Narrandera: Undivided council. Whole depicted LGA outline.
- Parkes: Undivided council. Whole depicted LGA outline with Parkes urban inset.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_central_riverina_map_review.json`.

Bland and Lockhart published result pages returned HTTP 200 but no map link was identified. Lockhart B and C ward pages also had no map link. This bounded review does not prove that maps are absent from the archive.


### NSWEC 2008 central and western NSW LGA maps

Four unchanged one-page originals saved from published NSWEC result-page links. Each sheet has an explicit red LGA key. Lachlan and Leeton also show wards; Griffith and Narromine are undivided. All four whole sheets were visually inspected.

- Griffith: Undivided council. Whole depicted LGA outline with Griffith urban inset; eastern side has a narrow frame margin.
- Lachlan: Five wards (A–E). Near-whole LGA overview with Condobolin ward inset. The inset covers part of the northwestern main outline; do not assume complete overview coverage.
- Leeton: Three wards (A–C). Near-whole LGA overview with Leeton/Yanco ward inset. Western Murrumbidgee boundary meets the frame; edge coverage is limited.
- Narromine: Undivided council. Whole depicted LGA outline; western and eastern edges have narrow frame margins.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_central_west_map_review.json`.

Carrathool and Wellington published result pages returned HTTP 200 but no map link was identified. Carrathool B–E ward pages also had no map link. This bounded review does not prove that maps are absent from the archive.


### NSWEC 2008 Murray-region NSW LGA maps

Five unchanged one-page originals saved from published NSWEC result-page links. Each sheet has an explicit red LGA key. Urana also shows wards; the other four councils are undivided. All five whole sheets were visually inspected.

- Albury: Undivided council. Whole depicted NSW LGA outline; northern and southern river edges have narrow frame margins. Victoria is neighbouring context only.
- Berrigan: Undivided council. Whole depicted NSW LGA outline; northern and southern river edges have narrow frame margins. Victoria is neighbouring context only.
- Corowa: Undivided council. Whole depicted pre-merger NSW LGA outline. Victoria is neighbouring context only.
- Deniliquin: Undivided council. Whole depicted pre-merger LGA outline; western and northeastern corners have narrow frame margins.
- Urana: Three wards (A–C). Whole depicted pre-merger LGA outline; eastern tip and southeastern corner have narrow frame margins.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_murray_map_review.json`.

Conargo published result page returned HTTP 200 but no map link was identified. This bounded review does not prove that maps are absent from the archive.


### NSWEC 2008 lower Murray and western NSW LGA maps

Six unchanged one-page originals saved from published NSWEC result-page links. Each sheet has an explicit red LGA key. Greater Hume and Murrumbidgee also show wards; the other four councils are undivided. All six whole sheets were visually inspected.

- Balranald: Undivided council. Whole depicted NSW LGA outline; western river edge and eastern tip have narrow frame margins.
- Greater Hume: Three wards (North, South, East). Whole depicted NSW LGA outline; western edge and northeastern tip have narrow frame margins. Victoria is neighbouring context only.
- Jerilderie: Undivided council. Whole depicted pre-merger LGA outline.
- Murray: Undivided council. Near-whole depicted pre-merger NSW LGA outline. Eastern edge at Ulupna Island meets the frame; do not assume complete edge coverage. Deniliquin is neighbouring LGA context.
- Murrumbidgee: Two wards (West, East). Whole depicted pre-merger LGA outline; southwestern and northeastern corners have narrow frame margins.
- Wentworth: Undivided council. Whole depicted NSW LGA outline with Wentworth/Dareton urban inset; northern and southern tips have narrow frame margins.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_lower_murray_map_review.json`.


### NSWEC 2008 far-western NSW LGA maps

Six unchanged one-page originals saved from published NSWEC result-page links. Each sheet has an explicit red LGA key. Central Darling also shows wards; the other five councils are undivided. All six whole sheets were visually inspected.

- Bogan: Undivided council. Whole depicted LGA outline; southern tip has a narrow frame margin.
- Bourke: Undivided council. Whole depicted NSW LGA outline; northern state-border edge has a very narrow frame margin.
- Brewarrina: Undivided council. Whole depicted NSW LGA outline; southern tip has a narrow frame margin.
- Central Darling: Three wards (A–C). Whole depicted LGA outline with White Cliffs, Wilcannia and Menindee ward insets.
- Cobar: Undivided council. Whole depicted LGA outline; western Bulbodney-side tip has a narrow frame margin.
- Walgett: Undivided council. Whole depicted NSW LGA outline; southwestern corner has a narrow frame margin. Queensland is neighbouring context only.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_farwest_map_review.json`.


### NSWEC 2008 western slopes NSW LGA maps

Four unchanged one-page originals saved from published NSWEC result-page links. All four councils are undivided. Coonamble, Dubbo and Gilgandra have explicit red LGA keys. Warrumbungle has a heavy red outline but its legend says No Window. All four whole sheets were visually inspected.

- Coonamble: Undivided council. Whole depicted LGA outline; northern tip has a narrow frame margin. Explicit red LGA legend.
- Dubbo: Undivided council. Whole depicted pre-merger LGA outline with Dubbo urban inset. Explicit red LGA legend.
- Gilgandra: Undivided council. Whole depicted LGA outline; western Armatree-side edge has a very narrow frame margin. Explicit red LGA legend.
- Warrumbungle: Undivided council. Whole depicted LGA outline, identified by the native council/election title and heavy red outline with neighbouring council labels. Legend contains only No Window; no explicit boundary key is printed.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_westslopes_map_review.json`.

Broken Hill and Warren published result pages returned HTTP 200 but no map link was identified. Warren B–D ward pages also had no map link. This bounded review does not prove that maps are absent from the archive.


### NSWEC 2008 northwestern NSW LGA maps

Six unchanged one-page originals saved from published NSWEC result-page links. Each sheet has an explicit red LGA key. All six councils are undivided. All six whole sheets were visually inspected.

- Gunnedah: Undivided council. Whole depicted LGA outline with Gunnedah urban inset.
- Gwydir: Undivided council. Whole depicted NSW LGA outline. Queensland is neighbouring context only.
- Liverpool Plains: Undivided council. Whole depicted LGA outline; northern Piallaway-side tip has a narrow frame margin.
- Moree Plains: Undivided council. Whole depicted NSW LGA outline with Moree urban inset; northeastern state-border junction has a narrow frame margin. Queensland is neighbouring context only.
- Narrabri: Undivided council. Whole depicted LGA outline with Narrabri urban inset; southern tip has a narrow frame margin.
- Tamworth: Undivided council. Whole depicted LGA outline with Tamworth urban inset. Native map and official index title use Tamworth; neighbouring sheets label the council Tamworth Regional.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_northwest_map_review.json`.


### NSWEC 2008 New England NSW LGA maps

Five unchanged one-page originals saved from published NSWEC result-page links. Each sheet has an explicit red LGA key. Guyra and Walcha also show wards; the other three councils are undivided. All five whole sheets were visually inspected.

- Armidale Dumaresq: Undivided council. Whole depicted pre-merger LGA outline with Armidale urban inset; northern and southeastern tips have narrow frame margins.
- Glen Innes: Undivided council. Native map title is Glen Innes Severn. Near-whole LGA overview with Glen Innes urban inset; northwestern The Gulf/Ashford-side edge meets the frame, so complete edge coverage is not confirmed.
- Guyra: Three wards (A–C). Whole depicted pre-merger LGA outline; western side has a narrow frame margin.
- Inverell: Undivided council. Near-whole LGA overview with Inverell urban inset; northwestern Boonal/Tullashmura-side boundary exits the frame, so complete edge coverage is not confirmed.
- Walcha: Four wards (A–D). Whole depicted LGA outline with Walcha ward inset.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_newengland_map_review.json`.

Uralla published result page returned HTTP 200 but no map link was identified. This bounded review does not prove that maps are absent from the archive.


### NSWEC 2008 Northern Rivers NSW LGA maps

Six unchanged one-page originals saved from published NSWEC result-page links. Each sheet has an explicit red LGA key. Ballina and Kyogle also show wards; the other four councils are undivided. All six whole sheets were visually inspected.

- Ballina: Three wards (A–C). Whole depicted mainland/coastal LGA outline. Offshore/island extent is not confirmed.
- Byron: Undivided council. Whole depicted mainland/coastal LGA outline; western side and Cape Byron tip have narrow frame margins. Offshore/island extent is not confirmed.
- Kyogle: Three wards (A–C). Whole depicted NSW LGA outline with Kyogle ward inset; western side has a narrow frame margin. Queensland is neighbouring context only.
- Lismore: Undivided council. Whole depicted LGA outline with Lismore/Goonellabah urban inset; southern Woodburn tip has a narrow frame margin.
- Richmond Valley: Undivided council. Whole depicted mainland/coastal LGA outline with Casino urban inset. Offshore/island extent is not confirmed.
- Tweed: Undivided council. Near-whole depicted NSW mainland/coastal LGA outline; southern Mount Burrell/Commissioners Creek side meets the frame. Complete edge and offshore/island coverage are not confirmed. Queensland is neighbouring context only.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_northern_rivers_map_review.json`.


### NSWEC 2008 north-coast NSW LGA maps

Five unchanged one-page originals saved from published NSWEC result-page links. Each sheet has an explicit red LGA key. All five councils are undivided. All five whole sheets were visually inspected.

- Bellingen: Undivided council. Near-whole mainland/coastal LGA overview; northeastern coastal junction meets the frame. Northern and southeastern tips have narrow frame margins. Complete edge and offshore/island coverage are not confirmed.
- Clarence Valley: Undivided council. Near-whole mainland/coastal LGA overview with Iluka/Maclean/Yamba and Grafton insets. The upper inset covers part of the northeastern overview/coast; complete overview and offshore/island coverage are not confirmed.
- Coffs Harbour: Undivided council. Whole depicted mainland/coastal LGA outline with Coffs Harbour urban inset. Some offshore red features are shown, but complete offshore/island coverage is not confirmed.
- Kempsey: Undivided council. Near-whole mainland/coastal LGA overview with Kempsey urban inset. The upper inset covers part of the northeastern overview and northern coastal junction; complete overview and offshore/island coverage are not confirmed.
- Nambucca: Undivided council. Whole depicted mainland/coastal LGA outline; northwestern and southern tips have narrow frame margins. Offshore/island extent is not confirmed.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_northcoast_map_review.json`.

Port Macquarie-Hastings published result page returned HTTP 200 but no map link was identified. This bounded review does not prove that maps are absent from the archive.


### NSWEC 2008 southern tablelands/coast and Tenterfield NSW LGA maps

Six unchanged one-page originals saved from published NSWEC result-page links. Each sheet has an explicit red LGA key. Tenterfield also shows wards; the other five councils are undivided. All six whole sheets were visually inspected.

- Bega Valley: Undivided council. Native map title is Bega. Whole depicted NSW mainland/coastal LGA outline with Bega and Merimbula insets. Offshore/island extent is not confirmed.
- Bombala: Undivided council. Whole depicted pre-merger NSW LGA outline; southern state-border junction has a narrow frame margin. Victoria is neighbouring context only.
- Cooma-Monaro: Undivided council. Whole depicted pre-merger NSW LGA outline with Cooma urban inset; western tip has a narrow frame margin. ACT is neighbouring context only.
- Eurobodalla: Undivided council. Whole depicted mainland/coastal LGA outline; northern tip has a narrow frame margin. A red offshore feature is shown, but complete offshore/island coverage is not confirmed.
- Snowy River: Undivided council. Whole depicted pre-merger NSW LGA outline; northern and southern state-border tips have narrow frame margins. ACT is neighbouring context only.
- Tenterfield: Five wards (A–E). Near-whole NSW LGA overview with Tenterfield ward inset. Western Dumaresq River edge meets the frame and the upper inset abuts the northwestern outline; complete overview edge coverage is not confirmed. Queensland is neighbouring context only.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_southern_tablelands_map_review.json`.


### NSWEC 2008 final index-entry NSW LGA maps

Two unchanged one-page originals saved from published NSWEC result-page links. Both sheets have explicit red LGA keys; Wakool also shows three wards. Both whole sheets were visually inspected.

- Hay: Undivided council. Whole depicted LGA outline; southwestern corner has a narrow frame margin.
- Wakool: Three wards (A–C). Whole depicted pre-merger NSW LGA outline with Moulamein and Barham ward insets.

The native title identifies the 2008 election. No precise map date, scale or CRS confirmed; election year does not prove legal boundary commencement. Insets count as parts of one PDF. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nswec_2008_final_entries_map_review.json`.

Shellharbour and Wollongong published result pages returned HTTP 200 but no map link was identified. This bounded review does not prove that maps are absent from the archive.


### Canterbury and Bankstown additional historical annual report maps

Nine unchanged council annual report PDFs saved. First 20 PDF pages screened per report; selected whole map pages then visually inspected. These are publication originals, not nine proven distinct boundary editions.

- bankstown_2014_15: PDF page 11 (printed 11). Whole depicted former Bankstown outline with four labelled ward fills: North, South, East and West. Simplified councillor graphic; no street-level boundary detail or scale.
- bankstown_2013_14: PDF page 6 (printed 6). Whole depicted former Bankstown profile silhouette with roads and locator inset. Low-resolution raster and no explicit LGA line-style key. Retained as contextual council-profile boundary evidence, not a survey-quality map.
- canterbury_2014_15: PDF page 10 (printed 7). Whole depicted former Canterbury outline; labelled Central, East and West ward fills. Internal thin lines and suburb labels have no separate suburb-boundary key; do not infer legal suburb polygons.
- canterbury_2013_14: PDF page 11 (printed 8). Whole depicted former Canterbury outline; labelled Central, East and West ward fills. Internal thin lines and suburb labels have no separate suburb-boundary key; do not infer legal suburb polygons.
- canterbury_2012_13: PDF page 11 (printed 08). Whole depicted former Canterbury outline; labelled Central, East and West ward fills. Internal thin lines and suburb labels have no separate suburb-boundary key; do not infer legal suburb polygons.
- canterbury_2011_12: PDF page 9 (printed 08). Whole depicted former Canterbury outline; labelled Central, East and West ward fills. Internal thin lines and suburb labels have no separate suburb-boundary key; do not infer legal suburb polygons.
- canterbury_2010_11: PDF page 5 (printed 9). Whole depicted former Canterbury outline; labelled Central, East and West ward fills. Internal thin lines and suburb labels have no separate suburb-boundary key; do not infer legal suburb polygons.
- canterbury_2009_10: PDF page 6 (printed 11). Whole depicted former Canterbury outline; labelled Central, East and West ward fills. Internal thin lines and suburb labels have no separate suburb-boundary key; do not infer legal suburb polygons.
- canterbury_2005_06: PDF page 5 (printed 5). Whole depicted former Canterbury outline; labelled Central, East and West ward fills. Internal thin lines and suburb labels have no separate suburb-boundary key; do not infer legal suburb polygons.

Canterbury 2009–15 graphics appear substantially reused. No precise map-native date, scale or CRS confirmed. Report years do not prove legal boundary commencement. Detailed legal digitising should use higher-detail originals already collected where available. Review checkpoint: `explore/output/2026-10-10_download-boundary-maps/canterbury_bankstown_additional_annual_report_map_review.json`.

The NSW Parliament Occasional Paper 1/2003 publishes seven SED–LGA GIF links and describes 2001 Census inputs. All seven direct requests returned HTTP 403; no image originals saved, sheet extents or boundary key reviewed. Follow-up checkpoint: `explore/output/2026-10-10_download-boundary-maps/parliament_2003_sed_lga_map_link_review.json`.


### Sydney 1961 and 1991 LGA maps; Cumberland former-council portions

Three unchanged source originals saved. Selected whole maps visually inspected.

- Metropolitan statistical area of Sydney — ANU holding with 1961 census LGA boundaries: Whole map inspected. Explicit reference keys statistical area boundaries separately from thinner LGA boundaries; cities, municipalities and shires have separate fills. Northern/western edge LGAs extend beyond the map frame; not whole-LGA coverage for all labelled councils. Native mile scale; catalogue ratio 1:603429 not independently calibrated. CRS unconfirmed. ANU stamped holding is an additional scan of an edition also represented by State Library holding, not a newly established boundary edition. Date: Native note: LGAs as used in Commonwealth Census 30 June 1961; catalogue issued 1961.
- Sydney profiles — AIFS 1991 report with Sydney LGA map: PDF page 3 title explicitly identifies Sydney LGAs grouped according to ABS labour force regions. Whole plate depicts LGA outlines with regional pattern fills. Individual LGA names, region key, scale and CRS are not shown on the plate; thin lines are difficult to distinguish within dark hatching. Use as historical overview, not high-detail digitising evidence. All 40 page thumbnails screened; whole map page visually inspected at larger render. Date: Source publication date 31 December 1991; individual map date and legal boundary commencement unconfirmed.
- Draft Cumberland LEP planning proposal August 2020 — map of former council portions: PDF/printed page 3 shows whole depicted Cumberland outline with labelled Former Holroyd, Former Parramatta and Former Auburn portions. Only portions transferred to Cumberland are shown: do not treat them as complete former LGAs. Surrounding text explains this scope. Raster overview with disclaimer; no map-native scale or CRS confirmed. Image-bearing pages screened and selected whole map page visually inspected. Date: Native report August 2020 (for finalisation); depicts 2016-created Cumberland and former council portions, not complete pre-2016 LGAs.

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/sydney_1961_1991_cumberland2020_map_review.json`. Data NSW resource `document_11846.pdf` returned HTTP 404; no original saved or map content reviewed from that mirror. Source-site absence not inferred.


### ANU thesis and ABS 1984–1986 report LGA maps

Three unchanged source originals saved. Selected whole maps visually inspected.

- Fa'a-Samoa: continuities and change — 1995 thesis with Sydney, Canterbury and Bankstown LGA maps: PDF page 21 (printed xx): whole Sydney overview, explicit LGA title, 10 km bar; northern Baulkham Hills/Hornsby extents simplified or truncated at straight line. PDF pages 97/98 (both printed 74–75): whole depicted Canterbury and Bankstown outlines, explicit LGA titles and 2 km bars; council map credits. Bankstown internal suburb labels and lines lack a separate legal suburb-boundary key. Circled numbers are household interviews, not boundary codes. Native CRS not confirmed. Only selected NSW map pages visually reviewed; unrelated Samoa map not collected separately. Date: Native thesis August 1995; precise individual map dates and legal boundary commencement unconfirmed.
- Perinatal Deaths NSW 1984 and 1985 — bundled native reports with NSW and Sydney LGA maps: PDF pages 25/52: whole statewide NSW plates, explicit distinct LGA versus statistical division/subdivision reference lines, km bars. PDF pages 26/53: whole Sydney Statistical Division LGA index views and council numeric/alphabetic indexes; faint contrast. Pages 27/54 repeat lower portions/index continuation; not separate maps. Native covers show 1984 then 1985 reports (second starts PDF28); filename agrees. Catalogue instead says Perinatal Deaths NSW 1989, issued1991; preserve conflict and use native map dates. No substantive perinatal data extracted. CRS unconfirmed. Selected map sheets and native covers visually inspected. Date: Native map notes: LGA boundaries 30 June 1984 and 30 June 1985; map footers January 1985 and January 1986 respectively. Catalogue title/date conflict..
- The Labour Force NSW November 1986 — statewide and Sydney maps of 1985 LGA geography: PDF41 whole statewide NSW map with explicit distinct LGA versus statistical division/subdivision keys and km scale. PDF42 Sydney Statistical Division LGA index view, faint lines and numeric council index; lower alphabetic/numeric indexes partly cut by scan frame. Same January1986 map edition also appears in bundled perinatal report, different scan and source context; not a new boundary date. No CRS confirmed. Selected whole map sheets visually inspected; broader report not exhaustively screened. Date: Report November 1986; native map LGA boundaries 30 June 1985; statewide map footer January 1986.

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/anu_1995_thesis_1984_1985_1986_abs_map_review.json`. Native map dates take precedence over mismatched catalogue metadata. Duplicate scans inside bundled reports are not separate map editions.


### ABS Regional Statistics NSW 1986 and 1993 boundary maps

Two unchanged source originals saved. Selected whole maps visually inspected.

- Regional Statistics NSW 1986 — 1984 LGA and statistical maps: All 96 page thumbnails screened. PDF91–92: split statewide statistical division/subdivision map with explicit LGA key; PDF93–94: split Sydney LGA index view (faint contrast); PDF95–96: split statewide map titled Local Government Areas of NSW, with explicit LGA-only reference and native date. Whole selected panels inspected; panel seams/overlap not registered or stitched. Pure LGA map adds evidence without statistical lines overlaid. Same 1984 vintage appears in other reports; do not count as new boundary date. Native km scale, CRS unconfirmed. PDF90 labour-force regional diagram is not an individual-LGA map. Date: Native LGA map boundaries 30 June 1984; map footer January 1985; report 1986.
- Regional Statistics NSW 1993 — LGA-derived SLA maps including Sydney: All 96 page thumbnails screened. PDF12/13 (printed6/7): whole Sydney Statistical Division overview and inner Sydney inset; explicit statistical local area (SLA) dotted-line key, km scales, ASGC code labels. Whole selected map pages inspected; overview/inset frame clips individual SLA edges and does not prove complete outlines for every inner council. PDF79 (printed73) states SLAs are usually whole or divided legal LGAs; PDF86 (printed80) code index identifies individual councils and split Sydney/Newcastle/Tweed units. Do not equate all SLA lines to whole legal LGA boundaries or infer map date from population-table geography. Other regional plates only thumbnail-screened. No CRS confirmed. Date: Native report 1993; precise individual map boundary date unconfirmed. Notes date population geography to 30 June 1991, not independently the map plates..

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/anu_regional_statistics_1986_1993_map_review.json`. The selected 1983 perinatal report catalogue/bundle request closed its connection twice; no original or map content retrieved. This remains a source lead; absence not inferred.


### 1971 Census colour NSW LGA map volume and 1984 births report

Two unchanged source originals saved. Selected whole maps and native keys visually inspected.

- 1971 Census Bulletin 13 — NSW colour LGA maps including Sydney and East Central NSW: All 22 page thumbnails screened. NSW selected whole plates and title/reference blocks inspected: PDF3 NSW sheet1 statewide, explicit LGA line key and numerical/alphabetical index, native scale1:2,000,000; PDF17 East Central NSW, LGA key and index, scale1:500,000; PDF21 Sydney Statistical Division including inner Sydney inset, explicit LGA key and native 30 June 1971 note, main scale1:300,000 and inset1:127,000. Outer northern/western/southern LGAs extend beyond frame, so Sydney plate does not give every full council outline. PDF1 NSW sheet4 urban centres Condobolin/Tamworth/Kempsey/Taree/Albury-Wodonga/Wagga Wagga/Orange, explicit LGA key, scale1:100,000, boundaries may be frame-clipped; red fill is urban centre, not LGA. Whole Commonwealth volume preserved unchanged; interstate plates not separately collected. Scan folds and local fading; stated scales not digitally calibrated; CRS unconfirmed. Date: Native NSW and Sydney maps: LGAs used at Census 30 June 1971; NSW sheet 1 prepared 1972; Sydney and East Central NSW prepared/printed 1973.
- Births NSW 1984 — 30 June 1984 LGA maps: All 27 page thumbnails screened. Whole PDF23 statewide statistical divisions/subdivisions plate inspected: explicit thin LGA boundary key, date30June1984 and January1985 imprint, km bar and numbered councils. PDF24–25 overlapping Sydney LGA index panels inspected with numerical/alphabetical index; faint contrast, bottom of first panel continued on next page. Same 1984 boundary vintage already represented; this is an additional source scan, not a new boundary edition. The statewide plate is on one page rather than split across two pages as in the 1986 regional statistics report. Unchanged report preserved; no health data extracted. No CRS confirmed; overlap not registered or stitched. Date: Native report Births NSW 1984; LGA map boundaries 30 June 1984; map imprint January 1985; holding stamp 19 November 1985.

Three other retrieved scans were screened on all page thumbnails but not registered: final 1971 Census Bulletin6 NSW (48 pages), The taxable capacity of local government in NSW (1976,171 pages), and Building Approvals NSW March1985 (23 pages). No map plates seen in those scans. This does not prove absence in other copies or editions. Bulletin6 explicitly directs map users to separate Bulletin13 (PDF5/11/48). Checkpoint: `explore/output/2026-10-10_download-boundary-maps/abs_1971_colour_and_1984_births_lga_map_review.json`.


### NSW Year Book1976: LGA maps dated30June1975

- Official Year Book of NSW No.64 1976 — 30 June 1975 LGA maps: PDF1194: statewide statistical agricultural areas and component subdivisions, with explicit separate thin LGA line key. PDF1196: statewide statistical divisions/subdivisions with LGA key. PDF1195 and1197: two Sydney Statistical Division LGA index views with numerical/alphabetical council keys and explicit30June1975 date. Whole four plates and native keys visually inspected; the Sydney views depict same indexed geography with different scan contrast, not distinct boundary dates. Key identifies split Blue Mountains and Greater Cessnock council parts: statistical-frame outlines are not proof of complete legal council boundaries. Statewide thin lines and coloured number labels faint;1197 right alphabetical column partially clipped by scan. Native km bars; no CRS or digital scale calibration confirmed. Only first100 and last97 page thumbnails screened; body maps not comprehensively reviewed. Unchanged1197-page source PDF preserved. Date: Native LGA boundary date 30 June 1975 on all four end plates; book No.64 labelled1976; native preface May1978, catalogue release31May1978.

Selected1976 census leads: ABS final LGA characteristics28-page scan and summary tables38-page scan both thumbnail-screened on all pages; no map plates seen. ANU preliminary NSW LGA report metadata timed out then reset; two regional statistics catalogue leads also reset. Agricultural report abare010 returned HTTP202 with zero bytes on both standard public download routes. Two NSW planning report links (Tweed1978/Murray1980) returned an identical blank297-byte PDF, not source reports; neither registered. These are retrieval failures, not evidence that reports lack maps. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nsw_1976_census_and_yearbook_lga_map_review.json`.


### NSW Year Books1971 and1979 LGA end plates

- Official Year Book NSW 1971 — LGA boundary maps: First50 and last30 page thumbnails screened, body maps not comprehensively reviewed. Whole PDF1194 statewide Statistical Divisions/Subdivisions map and PDF1195 council numerical/alphabetical index inspected. Explicit LGA thin black line key, native30June1971 note and October1971 imprint, mile scale. Red lines denote statistical regions; blue handwriting appears on source map, not formal council codes. Fine individual council lines in Sydney metropolitan area are not legible at this statewide scale; do not use statistical Sydney outline as individual-LGA geometry. Fold marks and show-through in council index; no CRS or digital scale calibration confirmed. This adds a source scan for a1971 vintage already represented, not a new legal boundary date. Date: Native map LGAs30June1971; map imprintOctober1971; book No.61 labelled1971; native prefaceFebruary1972/catalogue28February1972.
- Official Year Book NSW 1979 — LGA boundary maps: First50 and last30 page thumbnails screened, body maps not comprehensively reviewed. Whole four end plates and native keys inspected: PDF799 statewide Statistical Agricultural Areas and component subdivisions; PDF801 statewide Statistical Divisions/Subdivisions; both explicit thin LGA line key and30June1977 note, January1979 imprint. PDF800 and802 Sydney LGA index views depict same geography; PDF800 extremely faint, PDF802 clear black lines. Both have30June1977 note, council numerical/alphabetical keys, km bars and separate heavier statistical subdivision lines; alphabetical/subdivision group labels are not extra LGAs. Key marks Blue Mountains and Greater Cessnock parts: frame/statistical parts are not proof of whole legal council outlines. Two Sydney scan views count as plates of one edition, not distinct vintages. No CRS or digital scale calibration confirmed. Date: Native four end plates LGAs30June1977; statewide imprintJanuary1979; book No.65 labelled1979; native prefaceOctober1979/catalogue31October1979.

The1966 retrieved1082-page scan refers to a frontispiece map (PDF18/61/869), but no LGA map was seen in first50/last30 thumbnail pages; body not comprehensively reviewed. No original saved for boundary collection. Catalogue queries1968/1980 returned no PDF links; official release list identifies published1969/1979 editions. These are selected-query failures, not evidence of missing archive coverage. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nsw_yearbooks_1966_1971_1979_lga_map_review.json`.


### NSW Year Books1961,1964 and1969: Sydney and statewide LGA plates

Three unchanged source originals saved. Boundary dates follow native map notes, not book cover labels.

- Official Year Book NSW 1969 — LGA maps including Sydney: PDF1129: statewide1966 Census Statistical Divisions map with explicit LGA thin-line key and numerical codes. PDF1130: alphabetical/numerical council index, fold seams through some entries. PDF1131: Sydney Statistical Division map with inner Sydney inset, explicit LGA key/date and1966 imprint. Thin black LGA lines differ from red Sydney Metropolitan Area/urban-centre outlines and heavier statistical boundary. Outer Blue Mountains council extends beyond frame; frame/statistical edge is not proof of whole outer-council outline. Same1966 vintage already represented elsewhere; source scan not a new legal boundary date. First50 and last30 page thumbnails screened; body maps not comprehensively reviewed. Selected whole plates and native keys/date notes inspected. Native mile bars; folds, fading and show-through; no CRS or digital scale calibration confirmed. Date: Native NSW/Sydney LGA maps used at Census30June1966; Sydney imprint1966; book No.60 labelled1969; native prefaceMay1970/catalogue31May1970.
- Official Year Book NSW 1964 — LGA maps including Sydney: PDF3: colour statewide NSW frontispiece with numbered council boundaries and Cumberland/Newcastle-area insets. Native date30June1964; fine shire lines differ from thicker statistical division borders, coloured statistical regions and red rainfall-limit line. PDF4: Metropolis of Sydney council map, explicit separate Metropolitan Statistical Area versus LGA boundary key, native30June1964 note; includes alphabetical and numerical council indexes. Metropolitan boundary cuts outer councils: index explicitly lists council parts, so white metropolitan area and its heavy boundary do not define every complete legal LGA. Outer council outlines may be frame-clipped. PDF4 council index faint; scan contrast uneven. First50 and last30 page thumbnails screened; body maps not comprehensively reviewed. Selected whole plates and native keys/date notes inspected. Native mile bars; folds, fading and show-through; no CRS or digital scale calibration confirmed. Date: Native NSW and Sydney map boundaries30June1964; book No.58 labelled1964; native prefaceJuly1965/catalogue31July1965.
- Official Year Book NSW 1961 — LGA maps including Sydney: PDF3: colour statewide NSW frontispiece with numbered council boundaries and Cumberland/Newcastle-area insets. Native date30June1963; fine shire lines differ from thicker statistical division borders, coloured statistical regions and red rainfall-limit line. PDF4: Metropolis of Sydney council map, explicit separate Metropolitan Statistical Area versus LGA boundary key, native30June1963 note; includes alphabetical and numerical council indexes. Metropolitan boundary cuts outer councils: index explicitly lists council parts, so white metropolitan area and its heavy boundary do not define every complete legal LGA. Outer council outlines may be frame-clipped. PDF4 council index faint with strong reverse-side show-through. First50 and last30 page thumbnails screened; body maps not comprehensively reviewed. Selected whole plates and native keys/date notes inspected. Native mile bars; folds, fading and show-through; no CRS or digital scale calibration confirmed. Date: Native NSW and Sydney map boundaries30June1963; book No.57 labelled1961; native prefaceJanuary1964/catalogue31January1964.

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nsw_yearbooks_1961_1964_1969_lga_map_review.json`. Selected batch complete; whole year-book series and body-map review remain incomplete.


### NSW Year Books 1955, 1957 and 1959: shire and Sydney LGA plates

Three unchanged source originals saved. Boundary dates follow native map notes, not book cover labels.

- Official Year Book of New South Wales 1959: statewide and Sydney LGA maps: PDF 3 statewide map and PDF 4 Metropolis of Sydney both explicitly dated 30 June 1960. Statewide shire lines and municipal town symbols; coloured statistical divisions and red rainfall limit are separate layers. Sydney thin local government lines differ from heavy metropolitan statistical boundary; outer councils are clipped by the frame and metropolitan boundary. Numbered council indexes included. Folds, speckling and faint index text. Selected whole plates visually inspected. First 50 and last 30 pages screened as thumbnails; book body not comprehensively reviewed. Native mile scales; CRS unknown and no georeferencing performed. Date: Native map boundaries 30 June 1960; book No. 56 labelled 1959; preface May 1961; catalogue 1 May 1961.
- Official Year Book of New South Wales 1957: statewide shire boundary map: PDF 3 statewide Diagram Map has explicit red shire boundaries and numbers with numerical/alphabetical Index to Shires. Black county/territorial divisions, red rainfall limit, municipal symbols and irrigation hatching are separate layers. County lines are not LGAs; municipal symbols do not establish complete municipal outlines. Sydney detail is congested. Department of Lands footer has no confirmed year. General base resembles 1955; no alignment or distinct boundary vintage established. Selected whole plates visually inspected. First 50 and last 30 pages screened as thumbnails; book body not comprehensively reviewed. Native mile scales; CRS unknown and no georeferencing performed. Date: Book No. 55 labelled 1957; preface November 1957; catalogue 1 November 1957; precise map boundary date unconfirmed.
- Official Year Book of New South Wales 1955: statewide shire boundary map: PDF 3 statewide Diagram Map has explicit red shire boundaries and numbers with numerical/alphabetical Index to Shires. Footer confirms Department of Lands compilation/drawing/printing in 1956, not a precise legal boundary date. Black county/territorial divisions, red rainfall limit, blue commercial wheat growing limit, municipal symbols and irrigation hatching are separate layers. Counties are not LGAs; municipal symbols do not establish complete municipal outlines. Sydney detail is congested. Selected whole plates visually inspected. First 50 and last 30 pages screened as thumbnails; book body not comprehensively reviewed. Native mile scales; CRS unknown and no georeferencing performed. Date: Map compiled/drawn/printed 1956; book No. 54 labelled 1955; preface October 1956; catalogue 1 October 1956; precise legal boundary date unconfirmed.

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nsw_yearbooks_1955_1957_1959_lga_shire_map_review.json`. Selected batch complete; whole year-book series and body-map review remain incomplete.


### NSW Year Books 1947-48, 1948-49 and 1950-51: statewide shire plates

Three unchanged source originals saved. Boundary dates follow native map notes, not book cover labels.

- Official Year Book of New South Wales 1950-51: statewide shire boundary map: PDF 3 statewide Diagram Map: red shire boundaries and numbers, numerical/alphabetical Index to Shires. Black county/territorial lines and coloured statistical divisions are separate layers, not LGAs. Red rainfall limit, blue commercial wheat growing limits and municipal symbols are separate map features; municipal symbols do not establish complete legal municipal outlines. Sydney detail is congested at statewide scale. Selected whole map, legend and footer inspected; first 50 and last 30 pages thumbnail screened, book body not comprehensively reviewed. Scan folds and small blurred legend/index text. Native mile bar; CRS unknown, no georeferencing or boundary alignment performed. No distinct boundary vintage claimed from cover dates. Date: No. 53; preface March 1955; catalogue 1 March 1955; map footer compilation/drawing/printing 1954; precise legal boundary date unconfirmed.
- Official Year Book of New South Wales 1948-49: statewide shire boundary map: PDF 3 statewide Diagram Map: red shire boundaries and numbers, numerical/alphabetical Index to Shires. Black county/territorial lines and coloured statistical divisions are separate layers, not LGAs. Red rainfall limit, blue commercial wheat growing limits and municipal symbols are separate map features; municipal symbols do not establish complete legal municipal outlines. Sydney detail is congested at statewide scale. Selected whole map, legend and footer inspected; first 50 and last 30 pages thumbnail screened, book body not comprehensively reviewed. Scan folds and small blurred legend/index text. Native mile bar; CRS unknown, no georeferencing or boundary alignment performed. No distinct boundary vintage claimed from cover dates. Date: No. 52; preface July 1952; catalogue 1 July 1952; map footer compilation/drawing/printing May 1951; precise legal boundary date unconfirmed.
- Official Year Book of New South Wales 1947-48: statewide shire boundary map: PDF 3 statewide Diagram Map: red shire boundaries and numbers, numerical/alphabetical Index to Shires. Black county/territorial lines and coloured statistical divisions are separate layers, not LGAs. Red rainfall limit, blue commercial wheat growing limits and municipal symbols are separate map features; municipal symbols do not establish complete legal municipal outlines. Sydney detail is congested at statewide scale. Selected whole map, legend and footer inspected; first 50 and last 30 pages thumbnail screened, book body not comprehensively reviewed. Scan folds and small blurred legend/index text. Native mile bar; CRS unknown, no georeferencing or boundary alignment performed. No distinct boundary vintage claimed from cover dates. Date: No. 51; preface September 1950; catalogue 1 September 1950; no map footer date confirmed; precise legal boundary date unconfirmed.

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nsw_yearbooks_1947_48_1948_49_1950_51_shire_map_review.json`. Selected batch complete; whole year-book series and body-map review remain incomplete.


### NSW Year Books 1940-41, 1941-42/1942-43 and 1945-46: statewide shire plates

Three unchanged source originals saved. Boundary dates follow native map notes, not book cover labels.

- Official Year Book of New South Wales 1945-46: statewide shire boundary map: PDF 4 statewide Diagram Map: red shire boundaries and numbers, numerical/alphabetical Index to Shires. Black county/territorial lines and coloured statistical divisions are separate layers, not LGAs. Red rainfall limit, blue wheat growing limits explicitly labelled 1922 (not the shire boundary date) and municipal symbols are separate map features; municipal symbols do not establish complete legal municipal outlines. Sydney detail is congested at statewide scale. Selected whole map, legend and footer inspected; first 50 and last 30 pages thumbnail screened, book body not comprehensively reviewed. Scan folds and small blurred legend/index text. Native mile bar; CRS unknown, no georeferencing or boundary alignment performed. No distinct boundary vintage claimed from cover dates. Map footer names Department of Lands, Sydney; small imprint numbers do not establish a confirmed date. No detailed Sydney municipal map identified in selected thumbnail pages. Date: Book No. 50 labelled 1945-46; native preface and catalogue 1 December 1948; map printing and precise legal boundary dates unconfirmed.
- Official Year Book of New South Wales 1941-42 and 1942-43: statewide shire boundary map: PDF 3 statewide Diagram Map: red shire boundaries and numbers, numerical/alphabetical Index to Shires. Black county/territorial lines and coloured statistical divisions are separate layers, not LGAs. Red rainfall limit, blue wheat growing limits explicitly labelled 1922 (not the shire boundary date) and municipal symbols are separate map features; municipal symbols do not establish complete legal municipal outlines. Sydney detail is congested at statewide scale. Selected whole map, legend and footer inspected; first 50 and last 30 pages thumbnail screened, book body not comprehensively reviewed. Scan folds and small blurred legend/index text. Native mile bar; CRS unknown, no georeferencing or boundary alignment performed. No distinct boundary vintage claimed from cover dates. Map footer names Department of Lands, Sydney; small imprint numbers do not establish a confirmed date. No detailed Sydney municipal map identified in selected thumbnail pages. Date: Book No. 49 labelled 1941-42 and 1942-43; native preface and catalogue 27 December 1946; map printing and precise legal boundary dates unconfirmed.
- Official Year Book of New South Wales 1940-41: statewide shire boundary map: PDF 3 statewide Diagram Map: red shire boundaries and numbers, numerical/alphabetical Index to Shires. Black county/territorial lines and coloured statistical divisions are separate layers, not LGAs. Red rainfall limit, blue wheat growing limits explicitly labelled 1922 (not the shire boundary date) and municipal symbols are separate map features; municipal symbols do not establish complete legal municipal outlines. Sydney detail is congested at statewide scale. Selected whole map, legend and footer inspected; first 50 and last 30 pages thumbnail screened, book body not comprehensively reviewed. Scan folds and small blurred legend/index text. Native mile bar; CRS unknown, no georeferencing or boundary alignment performed. No distinct boundary vintage claimed from cover dates. Map footer names Department of Lands, Sydney; small imprint numbers do not establish a confirmed date. No detailed Sydney municipal map identified in selected thumbnail pages. Map scan is lighter with blurred key/index text. Date: Book labelled 1940-41; native preface and catalogue 15 September 1943; map printing and precise legal boundary dates unconfirmed.

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nsw_yearbooks_1940_41_1941_43_1945_46_shire_map_review.json`. Selected batch complete; whole year-book series and body-map review remain incomplete.


### NSW Year Books 1937-38, 1938-39 and 1939-40: statewide shire plates

Three unchanged source originals saved. Boundary dates follow native map notes, not book cover labels.

- Official Year Book of New South Wales 1939-40: statewide shire boundary map: PDF 3 statewide Diagram Map: red shire boundaries and numbers, numerical/alphabetical Index to Shires. Black county/territorial lines and coloured statistical divisions are separate layers, not LGAs. Red rainfall limit, blue wheat growing limits explicitly labelled 1922 (not the shire boundary date) and municipal symbols are separate map features; municipal symbols do not establish complete legal municipal outlines. Sydney detail is congested at statewide scale. Selected whole map, legend and footer inspected; first 50 and last 30 pages thumbnail screened, book body not comprehensively reviewed. Scan folds and small blurred legend/index text. Native mile bar; CRS unknown, no georeferencing or boundary alignment performed. No distinct boundary vintage claimed from cover dates. Map footer names Department of Lands, Sydney; small imprint numbers do not establish a confirmed date. No detailed Sydney municipal map identified in selected thumbnail pages. Date: Book labelled 1939-40; native preface and catalogue 19 June 1941; precise legal boundary date unconfirmed.
- Official Year Book of New South Wales 1938-39: statewide shire boundary map: PDF 3 statewide Diagram Map: red shire boundaries and numbers, numerical/alphabetical Index to Shires. Black county/territorial lines and coloured statistical divisions are separate layers, not LGAs. Red rainfall limit, blue wheat growing limits explicitly labelled 1922 (not the shire boundary date) and municipal symbols are separate map features; municipal symbols do not establish complete legal municipal outlines. Sydney detail is congested at statewide scale. Selected whole map, legend and footer inspected; first 50 and last 30 pages thumbnail screened, book body not comprehensively reviewed. Scan folds and small blurred legend/index text. Native mile bar; CRS unknown, no georeferencing or boundary alignment performed. No distinct boundary vintage claimed from cover dates. Map footer names Department of Lands, Sydney; small imprint numbers do not establish a confirmed date. No detailed Sydney municipal map identified in selected thumbnail pages. The scan has pale red shire lines and faint index text. Date: Book labelled 1938-39; native preface and catalogue 31 May 1940; precise legal boundary date unconfirmed.
- Official Year Book of New South Wales 1937-38: statewide shire boundary map: PDF 2 statewide Diagram Map: red shire boundaries and numbers, numerical/alphabetical Index to Shires. Black county/territorial lines and coloured statistical divisions are separate layers, not LGAs. Red rainfall limit, blue wheat growing limits explicitly labelled 1922 (not the shire boundary date) and municipal symbols are separate map features; municipal symbols do not establish complete legal municipal outlines. Sydney detail is congested at statewide scale. Selected whole map, legend and footer inspected; first 50 and last 30 pages thumbnail screened, book body not comprehensively reviewed. Scan folds and small blurred legend/index text. Native mile bar; CRS unknown, no georeferencing or boundary alignment performed. No distinct boundary vintage claimed from cover dates. Map footer names Department of Lands, Sydney; small imprint numbers do not establish a confirmed date. No detailed Sydney municipal map identified in selected thumbnail pages. This scan has no inserted ABS disclaimer page before the map, so the map is PDF 2; do not reuse later editions' page offsets. Date: Book labelled 1937-38; native preface and catalogue 19 September 1939; precise legal boundary date unconfirmed.

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nsw_yearbooks_1937_38_1938_39_1939_40_shire_map_review.json`. Selected batch complete; whole year-book series and body-map review remain incomplete.


### NSW Year Books 1934-35 and 1936-37: statewide shire plates

Two unchanged source originals saved. Boundary dates follow native map notes, not book cover labels.

- Official Year Book of New South Wales 1936-37: statewide shire boundary map: PDF 3 statewide Diagram Map: red shire boundaries and numbers, numerical/alphabetical Index to Shires. Black county/territorial lines and coloured statistical divisions are separate layers, not LGAs. Red rainfall limit, blue wheat growing limits explicitly labelled 1922 (not the shire boundary date) and municipal symbols are separate map features; municipal symbols do not establish complete legal municipal outlines. Sydney detail is congested at statewide scale. Selected whole map, legend and footer inspected; first 50 and last 30 pages thumbnail screened, book body not comprehensively reviewed. Scan folds and small blurred legend/index text. Native mile bar; CRS unknown, no georeferencing or boundary alignment performed. No distinct boundary vintage claimed from cover dates. Map footer names Department of Lands, Sydney; small imprint numbers do not establish a confirmed date. No detailed Sydney municipal map identified in selected thumbnail pages. Date: Book labelled 1936-37; native preface and catalogue 14 July 1938; precise legal boundary date unconfirmed.
- Official Year Book of New South Wales 1934-35: statewide shire boundary map: PDF 3 statewide Diagram Map: red shire boundaries and numbers, numerical/alphabetical Index to Shires. Black county/territorial lines and coloured statistical divisions are separate layers, not LGAs. Red rainfall limit, blue wheat growing limits explicitly labelled 1922 (not the shire boundary date) and municipal symbols are separate map features; municipal symbols do not establish complete legal municipal outlines. Sydney detail is congested at statewide scale. Selected whole map, legend and footer inspected; first 50 and last 30 pages thumbnail screened, book body not comprehensively reviewed. Scan folds and small blurred legend/index text. Native mile bar; CRS unknown, no georeferencing or boundary alignment performed. No distinct boundary vintage claimed from cover dates. Map footer names Department of Lands, Sydney; small imprint numbers do not establish a confirmed date. No detailed Sydney municipal map identified in selected thumbnail pages. Plate scan is small and blurred, particularly the legend and index; digitising may require a higher resolution source. Date: Book labelled 1934-35; native preface and catalogue 31 December 1936; precise legal boundary date unconfirmed.

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nsw_yearbooks_1934_35_1935_36_1936_37_shire_map_review.json`. Selected batch complete; whole year-book series and body-map review remain incomplete.

- 1935–36 year book: native contents (PDF 5) refers to a NSW frontispiece map, but none appears in the first 50/last 30 reviewed thumbnail pages. Full book body unreviewed. Not registered as a boundary original; a better-copy lead remains. Native preface PDF 4/catalogue: 4 February 1938.


### NSW Year Books 1931-32, 1932-33 and 1933-34: statewide shire plates

Three unchanged source originals saved. Boundary dates follow native map notes, not book cover labels.

- Official Year Book of New South Wales 1933-34: statewide shire boundary map: PDF 3 statewide Diagram Map: red shire boundaries and numbers, numerical/alphabetical Index to Shires. Black county/territorial lines and coloured statistical divisions are separate layers, not LGAs. Red rainfall limit, blue wheat growing limits explicitly labelled 1922 (not the shire boundary date) and municipal symbols are separate map features; municipal symbols do not establish complete legal municipal outlines. Sydney detail is congested at statewide scale. Selected whole map, legend and footer inspected; first 50 and last 30 pages thumbnail screened, book body not comprehensively reviewed. Scan folds and small blurred legend/index text. Native mile bar; CRS unknown, no georeferencing or boundary alignment performed. No distinct boundary vintage claimed from cover dates. Map footer names Department of Lands, Sydney; small imprint numbers do not establish a confirmed date. No detailed Sydney municipal map identified in selected thumbnail pages. Date: Book labelled 1933-34; native preface and catalogue 20 March 1936; precise legal boundary date unconfirmed.
- Official Year Book of New South Wales 1932-33: statewide shire boundary map: PDF 3 statewide Diagram Map: red shire boundaries and numbers, numerical/alphabetical Index to Shires. Black county/territorial lines and coloured statistical divisions are separate layers, not LGAs. Red rainfall limit, blue wheat growing limits explicitly labelled 1922 (not the shire boundary date) and municipal symbols are separate map features; municipal symbols do not establish complete legal municipal outlines. Sydney detail is congested at statewide scale. Selected whole map, legend and footer inspected; first 50 and last 30 pages thumbnail screened, book body not comprehensively reviewed. Scan folds and small blurred legend/index text. Native mile bar; CRS unknown, no georeferencing or boundary alignment performed. No distinct boundary vintage claimed from cover dates. Map footer names Department of Lands, Sydney; small imprint numbers do not establish a confirmed date. No detailed Sydney municipal map identified in selected thumbnail pages. Small plate scan; legend and index are blurred. Date: Book labelled 1932-33; native preface and catalogue 23 May 1935; precise legal boundary date unconfirmed.
- Official Year Book of New South Wales 1931-32: statewide shire boundary map: PDF 3 statewide Diagram Map: red shire boundaries and numbers, alphabetical Index to Shires with red numbers. Black county/territorial lines and coloured statistical divisions are separate layers, not LGAs. Red rainfall limit, blue wheat growing limits explicitly labelled 1922 (not the shire boundary date) and municipal symbols are separate map features; municipal symbols do not establish complete legal municipal outlines. Sydney detail is congested at statewide scale. Selected whole map, legend and footer inspected; first 50 and last 30 pages thumbnail screened, book body not comprehensively reviewed. Scan folds and small blurred legend/index text. Native mile bar; CRS unknown, no georeferencing or boundary alignment performed. No distinct boundary vintage claimed from cover dates. Map footer names Department of Lands, Sydney; small imprint numbers do not establish a confirmed date. No detailed Sydney municipal map identified in selected thumbnail pages. Different layout: legend bottom left, alphabetical index bottom right and Australia locator inset. Locator state/territory lines are not NSW LGAs; inset retained within unchanged original, not counted as a separate boundary map. Native preface is PDF 7. Date: Book labelled 1931-32; native preface and catalogue 8 December 1933; precise legal boundary date unconfirmed.

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nsw_yearbooks_1931_32_1932_33_1933_34_shire_map_review.json`. Selected batch complete; whole year-book series and body-map review remain incomplete.


### NSW Year Books 1928-31 review: confirmed 1930-31 statewide shire plates

One unchanged source original saved. Boundary dates follow native map notes, not book cover labels.

- Official Year Book of New South Wales 1930-31: statewide shire boundary map: PDF 9 statewide Diagram Map: red shire boundaries and numbers, alphabetical Index to Shires with red numbers. Black county/territorial lines and coloured statistical divisions are separate layers, not LGAs. Red rainfall limit, blue wheat growing limits explicitly labelled 1922 (not the shire boundary date) and municipal symbols are separate map features; municipal symbols do not establish complete legal municipal outlines. Sydney detail is congested at statewide scale. Selected whole map, legend and footer inspected; first 50 and last 30 pages thumbnail screened, book body not comprehensively reviewed. Scan folds and small blurred legend/index text. Native mile bar; CRS unknown, no georeferencing or boundary alignment performed. No distinct boundary vintage claimed from cover dates. Map footer names Department of Lands, Sydney; small imprint numbers do not establish a confirmed date. No detailed Sydney municipal map identified in selected thumbnail pages. Different layout: legend bottom left, alphabetical index bottom right and Australia locator inset. Locator state/territory lines are not NSW LGAs; inset retained within unchanged original, not counted as a separate boundary map. Native preface is PDF 5. Map appears after the preliminary pages, not beside the cover. Date: Book labelled 1930-31; native preface PDF 5 and catalogue 12 August 1932; precise legal boundary date unconfirmed.

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nsw_yearbooks_1928_29_1929_30_1930_31_shire_map_review.json`. Selected batch complete; whole year-book series and body-map review remain incomplete.

- 1928–29 and 1929–30 ABS year-book scans: no boundary map confirmed in first 50/last 30 thumbnail pages; bodies not comprehensively reviewed. Not registered as boundary originals; better-copy leads remain. Native prefatory dates (PDF 4) match catalogue dates: 6 January 1930 and 16 April 1931 respectively.


### NSW Year Books 1925-28 review: confirmed 1927-28 statewide shire plates

One unchanged source original saved. Boundary dates follow native map notes, not book cover labels.

- Official Year Book of New South Wales 1927-28: statewide shire boundary map: PDF 3 statewide Diagram Map: red shire boundaries and numbers, alphabetical Index to Shires with red numbers. Black county/territorial lines and coloured statistical divisions are separate layers, not LGAs. Red rainfall limit, blue wheat growing limits explicitly labelled 1922 (not the shire boundary date) and municipal symbols are separate map features; municipal symbols do not establish complete legal municipal outlines. Sydney detail is congested at statewide scale. Selected whole map, legend and footer inspected; first 50 and last 30 pages thumbnail screened, book body not comprehensively reviewed. Scan folds and small blurred legend/index text. Native mile bar; CRS unknown, no georeferencing or boundary alignment performed. No distinct boundary vintage claimed from cover dates. Map footer names Department of Lands, Sydney; small imprint numbers do not establish a confirmed date. No detailed Sydney municipal map identified in selected thumbnail pages. Different layout: legend bottom left, alphabetical index bottom right and Australia locator inset. Locator state/territory lines are not NSW LGAs; inset retained within unchanged original, not counted as a separate boundary map. Native preface is PDF 5. Map footer explicitly dated 1929; printing year does not establish an exact legal boundary date. Small/blurred plate key and index. Date: Native map compiled/drawn/printed 1929; book labelled 1927-28; native preface PDF 5: 18 February 1929; catalogue: 18 January 1929 (conflict); precise legal boundary date unconfirmed.

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nsw_yearbooks_1925_26_1926_27_1927_28_shire_map_review.json`. Selected batch complete; whole year-book series and body-map review remain incomplete.

- NSW Year Books 1925–26 and 1926–27: selected PDF 4 maps show county/territorial lines and coloured statistical divisions. Keys contain no explicit shire boundary layer or index. Whole plates/key/footer inspected; first 50/last 30 thumbnail pages screened, bodies unreviewed. Not registered as LGA sources. Map printing years: 1926 (plate title 1925 in 1925–26 book) and 1928 (1926–27 book). Native prefaces/catalogue: 19 November 1926 and 7 March 1928.


### NSW Year Books 1922–24 and Rent and Sales Report 118: Sydney LGA evidence

One unchanged source original saved. Boundary dates follow native map notes, not book cover labels.

- NSW Rent and Sales Report 118: Greater Metropolitan Region and inner Sydney LGA maps: PDF 10 (printed 9): explicitly labelled Greater Metropolitan Region LGA map plus larger inner/middle Sydney LGA inset. Numbered polygons refer to table LGA indexes (PDF 4–6/11–13). Separate statewide SSD map is not a statewide LGA map. Cyan shading denotes Sydney/inner ring groupings, not individual councils. Native notes PDF 16 (printed 15) say SLA ASGC 2011 aggregates to LGA and SA2 ASGS 2011 aggregates to SA3/SA4; map has former Auburn, Canterbury, Bankstown, Holroyd, Manly and Pittwater councils. Do not assign 2016 merger geography from report cover date; map itself has no precise legal boundary date. All 16 pages thumbnail screened; whole map inspected and native notes read. No scale bar/CRS stated; schematic outlines need georeferencing and comparison to stronger original legal boundary sources. Date: Report rent December quarter 2016 / sales September quarter 2016; native notes use ASGC/ASGS 2011 geography; precise map legal boundary date unconfirmed.

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nsw_yearbooks_1922_24_and_rent_sales118_lga_map_review.json`. Selected batch complete; whole year-book series and body-map review remain incomplete.

- NSW Year Books 1922, 1923 and 1924: PDF 4 plates show county/territorial lines and coloured statistical divisions; no explicit shire/LGA key or index. Whole maps/keys inspected, first 50/last 30 page thumbnails reviewed, bodies unreviewed. Not registered as LGA originals. Plate printing years: 1923, 1924, 1925 respectively. Native prefatory dates PDF 6 match catalogue: 15 December 1923, 29 July 1924 and 30 November 1925.


### NSW Rent and Sales issues 83, 97 and 104: Sydney LGA plates

Three unchanged source originals saved from the DCJ archive. Issues 83/97/104 cover rent March 2008/September 2011/June 2013 and sales December 2007/June 2011/March 2013. Their native notes retain the 2005 LGA framework. These are source editions, not three distinct LGA vintages. Issue 104 changes statistical regions to ASGS 2011 while retaining ASGC 2006 SLA-to-LGA aggregation. Archive discovery yielded 38 PDF links, not a claim of whole-series coverage.

- NSW Rent and Sales Report 83: Sydney and Greater Metropolitan Region LGA map: PDF page 10 (printed 9) has Greater Metropolitan Region LGA outlines and enlarged inner/middle Sydney LGA inset; numbered councils refer to report tables. PDF page 16 (printed 15) states LGA boundaries unchanged from 2005 framework. Statewide panel is SSDs for issues 83/97, SA3s for 104, not statewide LGAs. Exact legal map date, scale and CRS not established; schematic outlines require georeferencing. These three reports do not establish three distinct LGA vintages. Date: 2008 report; ASGC effective 1 July 2006, LGA boundaries unchanged from 2005 framework.
- NSW Rent and Sales Report 97: Sydney and Greater Metropolitan Region LGA map: PDF page 10 (printed 9) has Greater Metropolitan Region LGA outlines and enlarged inner/middle Sydney LGA inset; numbered councils refer to report tables. PDF page 16 (printed 15) states LGA boundaries unchanged from 2005 framework. Statewide panel is SSDs for issues 83/97, SA3s for 104, not statewide LGAs. Exact legal map date, scale and CRS not established; schematic outlines require georeferencing. These three reports do not establish three distinct LGA vintages. Date: 2011 report; ASGC effective 1 July 2006, LGA boundaries unchanged from 2005 framework.
- NSW Rent and Sales Report 104: Sydney and Greater Metropolitan Region LGA map: PDF page 10 (printed 9) has Greater Metropolitan Region LGA outlines and enlarged inner/middle Sydney LGA inset; numbered councils refer to report tables. PDF page 16 (printed 15) states LGA boundaries unchanged from 2005 framework. Statewide panel is SSDs for issues 83/97, SA3s for 104, not statewide LGAs. Exact legal map date, scale and CRS not established; schematic outlines require georeferencing. These three reports do not establish three distinct LGA vintages. Date: 2013 report; ASGC 2006 LGA aggregation, boundaries unchanged from 2005 framework; ASGS 2011 statistical regions.

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nsw_rent_sales_83_97_104_sydney_lga_map_review.json`. Selected batch complete; whole Rent and Sales archive coverage remains incomplete.

Follow-up discovery: earlier Rent and Sales searches did not yield a downloadable pre-2005 report. City of Sydney archive record 1754658 (1948 County of Cumberland planning report) remains a lead: web read returned 403; direct public read returned HTTP 202 with zero bytes. No report original saved. This differs from the already saved 1948 standalone Cumberland municipal/shire map.


### NSW Year Books 1914, 1915 and 1916: LGA map screening

No original registered from this three-book batch. Whole PDF page 3 plates show counties and territorial/statistical regions, not confirmed LGA boundaries. First 50/last 30 thumbnails screened per book; bodies not fully reviewed. For 1914, additional candidate plates and PDF pages 801-833 were screened. Its Sydney map at PDF page 813 (facing printed 805) is a street/tramway map, printed 1915, with no confirmed LGA layer. Do not infer LGA polygons from suburb names. Native prefaces are 24 June 1915, 19 September 1916 and 1 December 1917 respectively. OCR printing years can conflict with prefaces; no boundary date assigned. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nsw_yearbooks_1914_1915_1916_lga_map_review.json`. The 1948 Cumberland report alternate-copy search remains unresolved; Dictionary of Sydney supplies an image link, not yet accepted as an original boundary map.


### Further NSW LGA source screening: regional reports and Auburn 1951-1953

ABS archive pages 1304.1 for 1988/1989/1992 supplied no original PDF links. The three corresponding ANU item/bundle fetches reset their connections; no original retrieved and map content remains unreviewed. These remain leads, not no-map results. The Cumberland-hosted Auburn Triennial Report 1951-1953 downloaded and all 36 page thumbnails were screened. Its PDF page 13 (printed 11) is a parcel plan of Mountain View Estate, 44 home sites auctioned 21 November 1953; whole plan/caption inspected. It is not a whole suburb or LGA boundary map, so the report was not added to raw boundary originals. Checkpoints: `explore/output/2026-10-10_download-boundary-maps/nsw_regional_1988_1989_1992_abs_download_discovery.json` and `explore/output/2026-10-10_download-boundary-maps/nsw_regional_1988_1989_1992_and_auburn1951_map_review.json`.


### Census 1933 and 1947 Statistician reports: NSW and Sydney LGA maps

Two unchanged source originals saved. Census dates and later report prefaces are recorded separately. NSW provincial municipality point symbols do not supply full outlines; Sydney maps clip some council areas to the census metropolitan extent.

- 1933 Census Statistician’s Report — NSW shire and Sydney municipal boundary maps: PDF 468: NSW map with shire outlines, council numbers, Sydney inset, population-density hatching and separate railways. Provincial municipalities are represented by circles/squares, not complete polygons. PDF 476: Sydney and Suburbs map with explicit municipal boundary and metropolitan boundary keys, named former councils (including Alexandria, Annandale, Darlington, Glebe, Redfern and Waterloo) and numeric labels for small councils. Census metropolitan extent clips some LGAs (Holroyd labelled part); this is not complete outer-Sydney council coverage. Hatching is population density, not boundary type. Miles scale; CRS unconfirmed. Notes describe LGA geography at census and units or parts adopted for metropolitan area. Preserve the whole unchanged national report as the source of NSW maps; no interstate search expansion. Date: Census 30 June 1933; native report preface 13 November 1940; precise legal revision date of map plate not separately established.
- 1947 Census Statistician’s Report — NSW shire and Sydney municipal boundary maps: PDF 392: NSW map with shire outlines, council numbers, Sydney inset, population-density hatching and separate railways. Provincial municipalities are represented by circles/squares, not complete polygons. PDF 399: Sydney and Suburbs map with explicit municipal boundary and metropolitan boundary keys, named former councils (including Alexandria, Annandale, Darlington, Glebe, Redfern and Waterloo) and numeric labels for small councils. Census metropolitan extent clips some LGAs (Holroyd labelled part); this is not complete outer-Sydney council coverage. Hatching is population density, not boundary type. Miles scale; CRS unconfirmed. Notes describe LGA geography at census and units or parts adopted for metropolitan area. Preserve the whole unchanged national report as the source of NSW maps; no interstate search expansion. Date: Census 30 June 1947; native report preface 10 November 1952; precise legal revision date of map plate not separately established.

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/abs1933_1947_statisticians_reports_nsw_lga_map_review.json`. Selected batch complete. The 1933 NSW dwelling volume (70 pages) was fully thumbnail-screened, with no map found, and was not registered. No claim of whole census-series coverage.


### Census 1911 and 1921 Statistician reports: Sydney municipal maps

Two unchanged source originals saved. Census nights and much later native report prefaces recorded separately. 1911 Sydney labels North Botany; 1921 labels Mascot. Label difference is not proof of a geometry change. 1911 statewide plate shows counties, not LGAs; 1921 has explicit LGA/state key maps. Sydney metropolitan coverage differs from present-day Sydney.

- 1921 Census Statistician’s Report — Sydney municipal boundary map and NSW shire maps: PDF394 NSW population-density map and PDF395 unhatched LGA index map with Sydney/Newcastle/Illawarra insets. Native PDF366 explains LGA outlines and municipality point symbols; provincial municipalities are not complete polygons. Hatched unincorporated western areas in PDF394 are not LGAs and lack matching boundaries on PDF395. PDF407 Sydney and Suburbs: separate municipal/metropolitan line keys, former councils named, small councils letter-indexed; Mascot label. Sydney coverage is the census metropolitan district, not all present-day Sydney councils. Population hatching is not boundary type. Native miles scale; CRS unconfirmed. Preserve unchanged national report as source for NSW maps; no interstate search expansion. Date: Census night 3–4 April 1921; native report preface 1 June 1927; precise legal revision date of map plates not separately established.
- 1911 Census Statistician’s Report — Sydney municipal boundary map: PDF457 Sydney and Suburbs, facing printed433: named municipalities and Ku Ring Gai shire, numeric small-council labels and density hatching. Native PDF459 (printed434) explicitly says map shows boundaries of municipalities and shire comprising census metropolitan area. Separate railway lines cross the council units; no boundary-line key identified on this plate. North Botany label. PDF444 statewide map is counties, explicitly confirmed by native PDF446 (printed427), and must not be treated as an LGA map. Small PDF page dimensions and blurred scan labels require careful rendering; source pixels have not been improved. Sydney coverage is the census metropolitan district, not all present-day Sydney councils. Population hatching is not boundary type. Native miles scale; CRS unconfirmed. Preserve unchanged national report as source for NSW maps; no interstate search expansion. Date: Census night 2–3 April 1911; native report preface 21 May 1917; precise legal revision date of map plates not separately established.

Checkpoint: `explore/output/2026-10-10_download-boundary-maps/abs1911_1921_statisticians_reports_nsw_lga_map_review.json`. Selected two-report batch complete. Thumbnail review is bounded as specified above; remaining body and appendices were not reviewed. No claim of whole census-series coverage.


### NSW Census 1891: Sydney municipal map in the 1894 General Report

- Unchanged report saved from the Cornell scan on Internet Archive. Native PDF7: publication 1894; PDF9: preface 16 August 1894; PDF23/25: census night 5 April 1891. These dates do not establish an exact legal boundary revision date.
- Sydney density of population (1891) in the various municipalities, PDF165/166: overlapping scans of a folded municipal plate, with named former councils including Prospect and Sherwood, Ermington and Rydalmere, North Botany, Eastwood and Dundas. Map distinguishes unincorporated parts of electorates from municipalities; these are not LGA polygons. Separate railways cross council areas. Population-density hatching is not boundary type. Edges clip parts of the title, scale and peripheral map; small dark inner-city units have hard-to-read labels. Treat as partial scan coverage; no reconstruction or improved source pixels. PDF133/134 comparative Sydney maps mix municipalities and electorates and are not accepted as four municipal boundary vintages. PDF13/14 statewide plate explicitly shows counties; PDF121/122 statewide comparisons explicitly show electorates, neither is LGA evidence. CRS and precise legal boundary date unconfirmed.
- All 384 PDF pages thumbnail-screened; whole map scans PDF13/14,121,133,145,165/166 visually inspected; native cover PDF7, preface PDF9, census date PDF23/25 and municipality table PDF149 read. Remaining map plates and body not reviewed in detail.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nsw1891_general_census_report_municipal_map_review.json`. One selected original accepted. Whole 1891/1901 census series coverage remains open.


### NSW 1901 census and fuller 1891 plate follow-up

- Cornell/Internet Archive `cu31924030376507`: all 866 PDF pages thumbnail-screened. Tables, text and covers; no map identified. Native part covers use 1902/1903 publication dates and census night 31 March 1901. Not registered in the boundary-map collection. This review covers this scan only.
- State Library Jules Ginswick papers, MLMSS 9034, Box 18, catalogue `110318441`: lists the 1891 Sydney municipal density map as Department of Lands, 1893. This is catalogue evidence, not an independently inspected new plate or proof of legal boundary date. No image/download link identified on the fetched catalogue page. Saved 1894 report scans remain partially clipped.
- Bounded Internet Archive search found only the already saved 1891 General Report scan. No alternate original accepted. Discovery and review: `explore/output/2026-10-10_download-boundary-maps/nsw1901_census_and_1891_municipal_plate_followup_review.json`.


### Early Wealth and Progress scan triage and NSW Deaths 1984 lead

- Bounded archive discovery returned18 Wealth and Progress records. Metadata/OCR checked for1886–87,1890–91,1900–01. PDF originals are0.7–2.6GB and were not fetched. OCR of1890–91 lists an Australasia map;1900–01 front map labels statistical regions such as Riverina and Western Plains. No municipal-map reference identified; visual maps/body unreviewed, so no whole-volume absence claim.
- Smaller scan `wealthandprogre00coghgoog` is miscatalogued: native PDF10 says Official Year Book NSW1905–6 Second Issue, published1907, despite archive1887–88 label. 893pages; first50/last30 thumbnails inspected. Whole PDF9 shows only a thin remnant of a folded plate; remainder missing. Not registered. Body unreviewed. Other smaller catalogue records remain unreviewed.
- NSW Deaths1984 ANU bitstream `4ee7c65b-f8ff-413f-a4e0-65d63ad60c10`: both API content and direct download routes reset. Web index lists a map inside back cover; boundary type/date/quality remain unverified. No original saved.
- Review: `explore/output/2026-10-10_download-boundary-maps/nsw_early_wealth_progress_and_deaths1984_map_review.json`. No new originals accepted.


### Wealth and Progress front plates and selected 2012 map links

- Native archive leaf2 preview visually checked:1890–91 shows Australasia;1900–01 shows counties and13 statistical regions. No LGA layer identified on either selected plate. Leaf3 native titles establish1891 and1902 publication dates respectively. These are1000px review previews, not accepted originals. Remaining bodies/maps unreviewed; leaf0 previews timed out.1890–91 page index fetched;1900–01 page index returned500.
- NSWEC2012 printed map URLs for Ashfield, Auburn and Holroyd returned404. Whole saved report PDF122 and127 checked: they contain map hyperlinks rather than embedded maps. Other printed map URLs remain unverified.
- APH1984 report `1984_pp226.pdf` indexed Sydney population-growth LGA map: shell/web fetch403. No source original or plate verified.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/wealth_front_plates_and_nswec2012_three_councils_review.json`. No new originals registered.


### Sydney Metropolitan CMA annual-report LGA maps:2005/06 and2007/08

- Sydney Metropolitan Catchment Management Authority Annual Report 2007/08 — Sydney LGA map: PDF8 printed8 Figure3 explicitly labels Local Government Areas and has separate keys for red LGA lines, rivers and green CMA area of operation. Named former councils include Baulkham Hills, Holroyd, Auburn, Ashfield, Leichhardt, Marrickville, Botany Bay, Rockdale, Hurstville and Kogarah. Native km scale and north arrow. CMA green fill/operational outline is not an LGA boundary; councils intersecting the catchment include areas outside it. Map frame clips some peripheral councils, so do not assume complete outer LGA polygons or whole current Sydney coverage. Publication dates do not prove a legal boundary revision date or distinct boundary vintages. CRS unconfirmed. Date: Report 2007/08; native publication October 2008; precise legal LGA boundary revision date unconfirmed. Native cover/title/publication PDF1/2 and selected contents/area notes read; whole PDF8 LGA plate visually inspected. Other map plates, body and appendices not visually reviewed in this batch.
- Sydney Metropolitan Catchment Management Authority Annual Report 2005/06 — Sydney LGA map: PDF8 printed4 Figure2 labels Sydney Metropolitan Catchment Management Area Local Government Areas, named former Sydney councils, red administrative outlines over a faint raster base. Low contrast and blurred small labels/legend limit digitising precision; source pixels unchanged. CMA green fill/operational outline is not an LGA boundary; councils intersecting the catchment include areas outside it. Map frame clips some peripheral councils, so do not assume complete outer LGA polygons or whole current Sydney coverage. Publication dates do not prove a legal boundary revision date or distinct boundary vintages. CRS unconfirmed. Date: Report 2005/06; native publication November 2006; precise legal LGA boundary revision date unconfirmed. Native cover/title/publication PDF1/2 and selected contents/area notes read; whole PDF8 LGA plate visually inspected. Other map plates, body and appendices not visually reviewed in this batch.
- Old indexed DataNSW PDF routes returned404; the current CKAN catalogue points to archived OpenGov originals. Both originals preserved unchanged from those official catalogue links.2009/10 Parliament copy returned403 and archived copy429; no original obtained. No claim of whole report-series coverage.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/smcma2005_2007_sydney_lga_map_review.json`.


### SMCMA2008–09 numbered Sydney council map;2004–05 checked

- PDF7 printed5 bottom Local Government areas map:39 numbered council polygons keyed to former councils including Baulkham Hills, Holroyd, Auburn, Ashfield, Leichhardt, Marrickville, Botany Bay, Rockdale, Hurstville and Kogarah. Top map is sub-catchments and must not be treated as council boundaries. Bottom LGA map is small over a photographic background, limiting precision; no visible scale or confirmed CRS. Most inner/central council units displayed, some peripheral outlines meet/extend beyond frame; do not assume every outer polygon is complete. Publication year does not establish a new or precise legal boundary vintage. Source pixels unchanged. Date: Report year1 July2008 to30 June2009; native publication October2009; legal LGA revision date unconfirmed. First20 of84 PDF pages thumbnail-screened; native cover/publication PDF1/2 read and whole PDF7 plate visually inspected. Remaining body and appendices not visually reviewed.
- 2004–05 archive original38pages: all thumbnails screened, cover/publication read. Text/tables, no boundary map identified; not registered. Native publication October2005.
- Both fetched from current official DataNSW catalogue archive links. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/smcma2004_2008_sydney_lga_map_review.json`. Whole series coverage remains open.


### HNCMA screening and UTS2014 schematic Sydney LGA map

- PDF28 printed27 Figure1 explicitly labels Sydney Metropolitan Area and its38 Local Government Areas. Thin black council boundaries separate named former councils including Baulkham Hills, Holroyd, Auburn, Bankstown, Canterbury, Rockdale, Hurstville, Kogarah and Botany Bay. Inner councils use numbered key, including Ashfield, Leichhardt and Marrickville. Peripheral council parts meet/extend beyond frame: do not assume complete polygons. No visible scale or confirmed CRS. Figure source is http://en.wikipedia.org/wiki/File:Sydney_councils.png; source image revision not resolved. Treat as a secondary schematic copy, not an authoritative surveyed/legal map or a new2014 boundary vintage. Original PDF saved unchanged. Date: Native working paper April2014; latest draft16 March2014; depicted legal boundary date unconfirmed. Native PDF1/2 cover and draft date read; whole PDF28 map visually inspected. Remaining pages not visually reviewed.
- Hawkesbury–Nepean CMA2004–05: all68 thumbnails screened; whole PDF4/24/39 viewed. PDF4 is catchment/national parks; PDF39 river reach assessment with catchment/subcatchments. PDF24 photo/text. No LGA map identified; not registered.2009–10: all148 thumbnails screened, whole PDF7/31/37/44 viewed. Catchment and landscape project maps, no council boundary key/polygons identified; not registered. Screening does not prove that alternate copies lack maps.
- ACCC indexed AttachmentD Sydney metropolitan LGA map: both download query and plain official URL return403; original and map remain unverified.2006 Jurnal Ilmiah Teknik Sipil indexed Figure1 Sydney LGA boundaries: publisher certificate expired; no original obtained. OLG2009/10 indexed result is already registered; not downloaded again.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/hncma_and_sydney_research_lga_map_review.json`. One accepted, two reviewed skips, two fetch failures. No claim of complete report-series coverage.


### BITRE132 Sydney2006 LGA maps; OLG repeats and Parliament2003 image leads

- PDF84 printed60 Map3.6 has five Sydney LGA choropleth panels with council polygons, selected council labels and legend. Native note explicitly states LGAs2006 ASGC. Periods1961–1971 through2001–2010 are population-growth periods, not historical boundary vintages. All use2006 geography; no claim of1961/1971/1981/1991 boundary maps. Colours encode growth, not administrative status. Small panels and selected labels limit tracing; no visible scale/confirmed CRS on this plate. Source credits BITRE analysis of ABS NSW Year Books and Regional Population Growth. PDF8 is2006 Statistical Local Areas plus sector/subregion lines, not an additional LGA map. PDF46 states2001 data concorded to2006 ASGC. Full original PDF saved unchanged. Date: Native publication October2012; Map3.6 uses2006 ASGC LGA boundaries for1961–2010 population-growth periods. Native title/publication/foreword PDF3–5, overview PDF8, map index PDF17, study geography PDF46 and whole LGA map PDF84 inspected. Whole PDF8 overview viewed separately. Other body and appendices not visually reviewed. PDF135/156/158 native captions checked only; not accepted as LGA evidence.
- OLG2007/08 and2008/09 duplicate-map classification revalidated.2010/11 report PDF20–22 also reuses all NSW map image strips and the Sydney/inner-Sydney images from saved2009/10 report byte-for-byte. No new raw originals registered for these three reports. Native copyright2009/2010/2012 respectively; notes report no amalgamations or major boundary changes during the reporting years. Those statements do not prove no minor change or establish map revision dates. Evidence: `explore/output/2026-10-10_download-boundary-maps/olg_four_report_map_image_comparison.json`.
- Parliament Occasional Paper1,2003 (Mark D’Arney), Local Government Areas and State Electoral Divisions: current official page describes2001 ABS census/CD-ROM geography and links seven GIF maps SED-LGA-A throughG. All seven direct original routes returned403; public web fetch cache misses. No original/plate accepted. ANU1986 candidate bitstream a0d0e9fa-a9e9-4313-915c-f39dde3ac660 read timeout; identity/map content unconfirmed. Two other1986 source scans already saved, not counted again.
- Current OLG index goes back to2006/07; DataNSW exact comparative phrase search returns one planning-monitoring dataset, no comparative report. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/olg_duplicates_bitre132_parliament2003_lga_review.json`.12 selected originals:1 accepted,3 map duplicates,8 fetch failures; no full-series coverage claim.


### Cooks River1999 council boundary segments; Turning the Tide2001 context

- PDF22 Figure2 Cooks River Catchment Location explicitly keys peach lines as Local Government Boundary, navy lines as Catchment Boundary, cyan creeks/drains and brown railway. Named former councils include Auburn, Ashfield, Canterbury, Marrickville, South Sydney, Rockdale, Hurstville, Kogarah and Botany; Strathfield, Burwood, Bankstown and Randwick also labelled. Council segments extend outside frame; not complete council polygons. Street/rail backdrop and0–2500m scale assist later georeferencing; confirmed CRS and exact legal revision date absent. PDF24 Figure3 landuse and PDF35 Figure4 infrastructure reuse peach council segments over thematic detail; their thematic colours are not LGA boundaries. Full unchanged report downloaded from Cooks River organisation; official NSW Flood Data Portal confirms22 September1999 publication and author PPK Environment & Infrastructure with Webb McKeown. URL filename1991 must not establish map date. Date: Native report September1999 RevC; footer22 September1999; exact legal boundary date unconfirmed. Download filename1991 is inconsistent with native document. First50 of262 PDF pages thumbnail-screened; native title/acknowledgements/map index PDF1/2/7 read; whole maps PDF22/24/35 visually inspected. Remaining212 pages not visually reviewed.
- Turning the Tide, Jim Colman July2001, electronic archive selected whole figures4/5/8 reviewed.4 Southern Sydney Catchment Management Board Area and5 Georges/Cooks/Botany catchments are hydrological/management perimeters, not individual LGAs.8 combined Southern Sydney Regional Organisation of Councils jurisdiction perimeter with twelve constituent council names; separate internal council boundaries not keyed/identified. No raw map registered for these selected figures. Other report figures not reviewed.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/cooksriver1999_turningtide2001_lga_map_review.json`. Four selected originals reviewed: one accepted report, three context-only skips. No whole-report-series coverage claim.


### Upper Parramatta April2003 exhibition report: former council lines

- PDF54 Figure4.1 and PDF101 Figure6.1 explicitly key magenta Local Government Boundary separately from green external/tributary catchment boundaries and flood/project layers. Plates label Baulkham Hills Shire Council, Blacktown City Council, Parramatta City Council and Holroyd City Council with street/river backdrop, north arrow,1:50000 and0–2km scale. These show partial council segments in the catchment region, not whole council polygons. Same-colour proposed project markers/flood overlays must not be traced as council lines. PDF18 Figure1.1 and PDF31 Figure2.4 are severely clipped folded maps: only narrow left/central strip reproduced; do not assume missing right geography.54/101 are substantially broader maps with frame/legend but outer council segments extend beyond frame. Native April2003 exhibition version differs from Flood Portal catalogue describing October2003 final series; do not label this scan final or adopt catalogue final date. Full original124-page council PDF saved unchanged; CRS unconfirmed. Dates: Native public exhibition report April2003/footer3 April2003. Figure4.1 date3 April2003; Figure6.1 date20 March2003. Exact legal LGA revision date unconfirmed. All124 pages thumbnail-screened; whole native title PDF2 and maps PDF18/31/54/101 visually inspected. Other text/body not read in detail. PDF is scanned without useful native searchable text; selected plate dates/key read visually.
- Lower Georges River stormwater plan official council route403; native report/map not verified.1986 Botany Bay draft SREP re-exhibition library record8114: indexed explicit LGA boundary map but route returns297byte HTML browser challenge, not PDF. No accepted original. Lower Parramatta1999 stormwater report catalogue upload resource exists, resource page/standard download probe403. Parramatta River Estuary Review indexed OurLivingRiver URL404; no map verified. Failures are route observations, not proof of general source unavailability.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/upperparramatta2003_and_adjacent_sydney_lga_map_review.json`. Five selected originals: one saved, four fetch failures. No report-series coverage claim; flood layers/project markers are not council boundaries.


### Parramatta2002–2012 flood reports: two explicit former LGA maps

- Lower Parramatta River Floodplain Risk Management Study and Plan Volume1 August2005 — former LGA heritage map: PDF32 printed23 Figure2-3 Heritage Areas within the Project Area explicitly keys coloured LGAs Auburn, Concord, Holroyd, Parramatta and Ryde. Black council edges separate coloured areas with street/river backdrop, north arrow and0–2000metre scale. Shows partial council segments, not whole polygons. Blue heritage sites/flood outline, red study area and road lines are distinct from council edges. Concord appears in this2005 report plate; do not assume2005 legal geography or silently rename it. PDF23 Figure1-1 council labels surround flood catchment colours, which are not LGA fills. CRS and original council layer vintage unconfirmed. Date: Native Final August2005. Plate legal LGA revision date unconfirmed; Concord is retained in the map key. All135 pages thumbnail-screened; selected whole maps and native title/date pages inspected. Other body text not read in detail. Full original PDF saved unchanged.
- Duck River Catchment Floodplain Risk Management Plan November2012 — September2011 LGA study-area map: PDF10 printed4 Figure1 Duck River Floodplain Risk Management Study — Study Area explicitly keys black LGA boundaries separately from red study area and blue rivers/creeks. Labels Parramatta LGA, Auburn LGA and Bankstown LGA on satellite backdrop; black lines extend outside red study boundary. North arrow and2810m Google map scale. Partial council segments, not whole LGA polygons. Plate dated20 September2011 within November2012 final report; image copyright2011 Sinclair Knight Merz/Google2010 do not establish LGA vintage. CRS unconfirmed. Date: Native November2012 final report; PDF10 Figure1 plate date20 September2011. Legal LGA revision date unconfirmed. All21 pages thumbnail-screened; selected whole maps and native title/date pages inspected. Other body text not read in detail. Full original PDF saved unchanged.
- Skipped 2002-floodplain-management-review-and-supplementary-plan-north-wentworthville: January2002 native cover; map footer11 January2002. WholePDF12/30/49/54 keys identify flood, cadastral and study boundaries; no explicit LGA evidence accepted. All pages thumbnail-screened; remaining plate keys not all read at full resolution.
- Skipped lower-parramatta-river-floodplain-risk-management-study-and-plan-review: Final March2005 native PDF2. WholePDF10/23/79/102/126 keys identify study area, catchments and flood levels; no explicit LGA evidence accepted. All pages thumbnail-screened; remaining plate keys not all read at full resolution.
- Skipped lower-parramatta-river-floodplain-risk-management-study-and-plan-volume-2: Final August2005 native PDF1/2. WholePDF9 Figure1-1 is Lower Parramatta catchment/study area. PDF16 LGA text is prose, not map. No explicit LGA evidence accepted. All pages thumbnail-screened; remaining plate keys not all read at full resolution.
- Skipped duck-river-and-duck-creek-flood-study-review: Final22 November2012 native revision page. WholePDF55/56/57/63/142 keys identify subcatchments, study area, ALS, hydraulic model and flood hazard; no explicit LGA evidence accepted. All pages thumbnail-screened; remaining plate keys not all read at full resolution.
- Six-source checkpoint: `explore/output/2026-10-10_download-boundary-maps/parramatta_six_2002_2012_reports_lga_map_review.json`. Two accepted, four skipped, no fetch failures. New saved hashes/page counts/map rendering and all registered paths/sizes pass. Older hashes not rerun; no whole-series coverage claim.
- Follow-up SMCMA2010/11 Part1 Parliament route49479 returned403. No original saved or map visually verified. Attempt checkpoint: `explore/output/2026-10-10_download-boundary-maps/smcma2010_2011_part1_lga_map_fetch_attempt.json`; this does not establish general source unavailability.


### Sydney environment reports:2003 LIC LGA map and1990-derived council panels

- NPWS Downy Wattle Recovery Plan2003 — Sydney LGA distribution map: PDF23 printed13 Figure1 Distribution of A.pubescens explicitly keys grey Local govt areas separately from green NPWS estate, blue coastline and red/hollow species sites. Labels Hawkesbury, Wollondilly, Penrith, Sutherland, Liverpool, Baulkham Hills, Camden, Blacktown, Fairfield, Parramatta, Holroyd, Auburn, Campbelltown and Canterbury. Map credits LGA boundaries from LIC. Projection explicitly Australian Map Grid Zone56; datum not specified. North/compass and0–12km scale; some outer councils clipped, not complete Sydney coverage. Plate printed22 January2003; April2002 copyright is not boundary layer date. Full78-page original saved unchanged. Dates: Native cover February2003, internal title March2003; PDF23 map printed22 January2003/copyrightApril2002. Exact LGA layer revision date unconfirmed. Native first4 pages and wholePDF23 inspected. Other77 pages/body not visually reviewed; whole-document text searched for explicit LGA key.
- Callan Park Master Plan November2011 Part1 — Sydney geology and vegetation maps with former LGA lines: PDF24 printed34 Figure10 Sydney Natural Vegetation1788 andFigure11 Sydney Geology explicitly key black Local Government Boundaries, separate from vegetation/geology fills, sea/watercourses and red Callan Park site. Both label Auburn, Concord, Drummoyne, Hunters Hill, Lane Cove, Leichhardt, Manly, Mosman, North Sydney, Randwick, Ryde, Strathfield, Sydney, Waverley, Willoughby, Woollahra, Burwood, Ashfield, Marrickville and Canterbury. Map headings citeBenson and Howell1990; footer says adapted fromBenson and Howell1990 andNSW NPWS200 (as printed, truncated year). Some outer polygons clipped; no scale/north/CRS printed on these panels.1788 is approximate pre-European vegetation, not LGA vintage. Separate council-published74-page chapter saved unchanged: map labels and key render clearly. Combined301-page PDF has blank/misencoded fonts in local renderer and was not registered; later site folder2025-12 is upload path, not report/map date. Dates: Council index November2011 chapter; full master report native final adopted11 November2011. PDF24 maps citeBenson and Howell1990. Exact council revision date unconfirmed;1788 describes vegetation, not council geography. WholePDF24 printed34 visually inspected; council index and full report nativePDF1/2 date/version read. Separate chapter other73 pages not thumbnail-screened; combined report first74 thumbnail-screened but bad font rendering.
- HNCMA2006/07 and2007/08 archive routes429; not re-tried immediately.2008/09 original downloaded and all132 pages thumbnail-screened, wholePDF7/57/58/59 maps viewed: landscape/project/catchment boundaries without explicit council key; skipped. EPA commercial inventory277-page PDF downloaded: activity year2008, publicationAugust2012. Whole-document text search and first4pages/wholemapPDF4 review found inventory-region rectangles, notLGAs; remaining273 pages not visually inspected. Skips are bounded reviews, not proof noLGAmapexists.
- Checkpoint `explore/output/2026-10-10_download-boundary-maps/hncma_epa_wattle_callan_sydney_lga_map_review.json`: seven selected originals, two accepted, three skipped, two fetch failures. Saved hashes/page counts/map renders and all1544 manifest IDs/paths/sizes pass. No final report asset produced or analysis definition changed.


### Nodding Geebung and Spiked Riceflower plans: 2005 western Sydney council maps

- Nodding Geebung approved recovery plan January2006 — September/October2005 western Sydney LGA maps: PDF 40 distribution map and PDF 15/16/45/46 habitat maps explicitly key red Local Govt Areas. Distribution labels Hawkesbury, Blacktown, Penrith, Holroyd, Fairfield, Bankstown, Liverpool and Campbelltown. North details show Penrith/Hawkesbury/Blacktown; south details show Liverpool/Fairfield/Campbelltown. Projection AMG Zone 56 (AGD66), compass and 0–4 km overview/0–2 km detail scales. Red soil hatching and species marks, green/cyan DEC estate, grey built-up areas, black roads and blue waterways are separate from red council edges. Outer council polygons are clipped. Main body habitat maps repeat appendix plates; these are not distinct boundary vintages. Full 50-page original saved unchanged. Dates: Native cover January 2006; citation/copyright 2005; DEC 2006/182. Distribution map 29 September 2005; north habitat maps 4 October 2005; south habitat maps 5 October 2005. Legal LGA revision date unconfirmed. Native PDF 2/3, whole cover PDF 1 and maps 15/16/40/45/46 inspected. Other body/appendices not visually reviewed. MuPDF warns No default Layer config, but selected map lines, labels and keys render visibly. No PDF repair performed.
- Spiked Riceflower approved recovery plan January2006 — February2005 western Sydney LGA map: PDF 43 Map 1 Western Sydney distribution explicitly keys red Local Govt Areas. Labels Hawkesbury, Blacktown, Penrith, Holroyd, Fairfield, Bankstown, Liverpool, Camden and Campbelltown. Projection AMG Zone 56 (AGD66), compass and 0–6 km scale. Green DEC estate, grey built-up areas, black roads and species marks are separate from red LGA lines. Outer council edges are clipped. Caption Updated December 2004 does not establish the legal boundary date. Full 51-page original saved unchanged; adjacent Illawarra map PDF 44 was not visually reviewed. Dates: Native cover January 2006; citation/copyright 2005; DEC 2006/181. Map caption Updated December 2004; plate printed 9 February 2005. Legal LGA revision date unconfirmed. Native PDF 2/3, whole cover PDF 1 and map 43 inspected. Other pages not visually reviewed. Whole-document text searched for explicit LGA keys.
- Draft Nodding Geebung Environment route timed out. Final NSW library route returned a 297-byte HTML browser challenge. Commonwealth final original saved; identity/hash comparison with the blocked library copy remains unverified. Four-route checkpoint: `explore/output/2026-10-10_download-boundary-maps/nutans_pimelea_sydney_lga_map_review.json`. Two accepted originals, two failed routes. New hashes/page counts/map renders and all 1,546 IDs/paths/sizes pass. Older hashes not rerun.


### Zieria plan: northern and western Sydney LGA map

- Zieria involucrata approved recovery plan January 2006 — northern and western Sydney LGA map: PDF 12, printed page 6, Figure 2 explicitly keys black Local Govt Areas. Labels include Lithgow, Hawkesbury, Gosford, Blue Mountains, Hornsby, Baulkham Hills, Penrith and Blacktown. Council lines are distinct from red species records, green NPWS estate/state forests, grey built-up areas and blue rivers/waterbodies. Compass and 0–8 km scale present; CRS not identified on the reviewed map. Outer council polygons are clipped; this is partial regional coverage. The small footer does not yield a reliable map date. Full 52-page original saved unchanged. Dates: Native cover January 2006; publication, copyright and citation 2006. Map print date and legal LGA revision date unconfirmed. Native cover, publication/citation page, executive summary, figure list and whole PDF 12 map inspected. Whole-document text searched for map/LGA references. Other pages not visually reviewed. MuPDF reports No default Layer config; the selected map key, lines and labels render visibly. No PDF repair performed.
- Selected seven-route batch: one accepted original; six failures. Zieria draft and repeat Nodding Geebung draft requests timed out. Caley’s Grevillea Environment route returned HTTP 200 without a PDF signature; Darwinia Environment route raised ConnectionError. Both NSW library copies returned HTTP 200, 297-byte non-PDF responses. These are route observations; they do not establish that the original sources are unavailable. No identity or hash comparison was possible for the blocked copies.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/zieria_northern_sydney_recovery_lga_map_review.json`. New fetch/copy hash, page count and selected map render pass; all 1547 registered IDs, paths and sizes pass. Older hashes were not recalculated. No full recovery-plan series coverage claimed.


### Council profile maps and March 1999 Lithgow–Rylstone map

- Grevillea obtusiflora approved recovery plan September 2001 — March 1999 Lithgow–Rylstone LGA map: PDF 20, printed page 8, Figure 3 explicitly keys grey Local Government Boundaries. Labels include former Rylstone, Mudgee, Greater Lithgow and Evans, plus Muswellbrook and Singleton. Map covers the Capertee/Cudgegong area west and north of Sydney; it is a regional NSW lead, not a Sydney metropolitan plate. Red roads, blue rivers, green estate labels and magenta species records are separate from council edges. Printed 30 March 1999; copyright March 1999; Australian Map Grid Zone 56, datum not stated, compass, 0–10 km scale and representative fraction 1:539683. Partial outer council polygons clipped. Full 67-page original saved unchanged. Dates: Native cover/internal title September 2001; copyright/citation 2001. PDF 20 map printed 30 March 1999, copyright March 1999. Legal LGA revision date unconfirmed. All 67 pages screened as thumbnails; whole cover/map PDF 1/20 and native publication/internal title PDF 2/3 inspected. Body text not fully reviewed. Source catalogue June 2001 differs from the downloaded native September 2001 title; native dates retained.
- NSW council comparative information 2012/13 — former Sydney LGA profile maps: PDF 44 Ashfield and PDF 46 Auburn council profile panels show the named council polygon in turquoise, with labelled black neighbouring council outlines. Ashfield panel includes Canada Bay, Burwood, Leichhardt, Marrickville, Canterbury and Rockdale; Auburn panel includes Holroyd, Parramatta, Ryde, Hills, Ku-ring-gai and Bankstown. Council profile headings and LGA table headings establish these are council areas. No map scale, compass or CRS on the reviewed panels. Small overview maps: surrounding polygons/labels clipped. Full original saved unchanged. Similar panels across annual reports do not establish distinct legal boundary vintages; no geometry comparison performed. Dates: Native cover June 2014, reporting period 2012/13, copyright 2014. Individual map print and legal boundary revision dates unconfirmed. URL upload folder 2026-02 is not map vintage. First 40 of 353 pages screened as thumbnails; whole PDF 42/44/46 profile panels and native PDF 1/2 dates inspected. Remaining 313 pages outside the thumbnail range not systematically reviewed; selected 42/44/46 inspected separately. Profile pages are raster images; native text search does not expose their council names.
- NSW council comparative information 2011/12 — former Sydney LGA profile maps: PDF 32 Ashfield and PDF 34 Auburn council profile panels show the named council polygon in turquoise, with labelled black neighbouring council outlines. Ashfield panel includes Canada Bay, Burwood, Leichhardt, Marrickville, Canterbury and Rockdale; Auburn panel includes Holroyd, Parramatta, Ryde, Hills, Ku-ring-gai and Bankstown. Council profile headings and LGA table headings establish these are council areas. No map scale, compass or CRS on the reviewed panels. Small overview maps: surrounding polygons/labels clipped. Full original saved unchanged. Similar panels across annual reports do not establish distinct legal boundary vintages; no geometry comparison performed. Dates: Native cover October 2013, reporting period 2011/12, copyright 2013. Individual map print and legal boundary revision dates unconfirmed. URL upload folder 2026-02 is not map vintage. First 40 of 338 pages screened as thumbnails; whole PDF 30/32/34 profile panels and native PDF 1/2 dates inspected. Remaining 298 pages not visually reviewed.
- BITRE Working Paper 67: PDF 24 Figure 1.1 keys SLA boundary and District boundary. PDF 27 explains that SLAs may subdivide LGAs. Do not relabel these edges as historical LGA boundaries. No explicit LGA plate verified. First 120 of 126 pages screened as thumbnails; whole PDF 24 map and native PDF 27 geography definition inspected. Final six pages and body text not fully reviewed. Not registered.
- Four-original checkpoint: `explore/output/2026-10-10_download-boundary-maps/olg2011_2013_obtusiflora1999_bitre67_lga_map_review.json`: three accepted, one skipped, no failed downloads. New fetch/copy hashes, page counts and selected map renders pass; all 1550 registered IDs, paths and sizes pass. Older hashes not recalculated. No full series or profile-page coverage claimed.


### Leichhardt and Canterbury planning reports: former Sydney LGA maps

- Leichhardt Employment Lands Study January 2011 — 2007 Sydney council location map: PDF 10, printed page 10, Figure 2 Leichhardt Location Map: black outlined Leichhardt council polygon, named neighbouring councils separated by white lines, and coloured planning subregions. Labels include former Baulkham Hills, Holroyd, Auburn, Ashfield, Leichhardt, Marrickville, Botany Bay, Rockdale, Hurstville and Warringah. White boundaries divide councils within same-colour subregions; subregion colours are not council polygons. Figure and surrounding scope identify the municipality, but no separate boundary legend, scale, compass or CRS is shown. Partial outer Sydney coverage and clipped labels. PDF 35 reproduces a 2007 draft Inner West strategy map; no boundary key on that reproduction, so do not treat its faint lines as independently verified LGA geometry. PDF 46 infrastructure plate is not a separately keyed LGA map. Full 184-page original saved unchanged. Dates: Native final report January 2011. PDF 10 source SGS 2007; PDF 35 source Draft Inner West Subregional Strategy 2007. Legal LGA revision dates unconfirmed. Upload folder 2026-02 is not map vintage. First 60 of 184 pages screened as thumbnails; whole PDF 10/35/46 maps and native title/disclaimer PDF 1/8 inspected. Remaining 124 pages not visually reviewed. Native extracted text repeats many times; this is not multiple maps or vintages. No PDF modification performed.
- Canterbury Residential Development Strategy October 2013 — former Canterbury and 2010 Sydney LGA maps: PDF 11, printed page 3, Figure 2.1 Location of Canterbury LGA shows the former Canterbury polygon with a thick dark outline on a street basemap; caption and native geography text identify the LGA. Source Atlas.id 2011. Suburb names on the basemap are location labels, not verified suburb boundaries. PDF 43, printed page 35, Figure 4.1 reproduces a 2010 Metropolitan Plan map headed Sydney’s subregions and local government areas: named former councils separated by thin lines within coloured subregions. Subregion colours and growth-centre markings are not council boundaries. Includes pre-amalgamation Canterbury, Marrickville, Leichhardt, Auburn, Holroyd and other former councils; inner Sydney labels are small. No map scale, compass or CRS on these reproduced plates. Full 144-page original saved unchanged. Dates: Native final report October 2013; page footer 1 October 2013. PDF 11 source Atlas.id 2011. PDF 43 source Metropolitan Plan for Sydney 2036, page 115, caption 2010 Metro Strategy. Legal LGA revision dates unconfirmed. First 60 of 144 pages screened as thumbnails; whole PDF 11/43 maps and native title/final-issue pages 1/2/3 inspected. Remaining 84 pages not visually reviewed. Other thematic plates in the screened range not assessed as distinct boundary vintages.
- 1994 Hawkesbury–Nepean draft SREP No. 20 Amendment No. 2 route returned HTTP 200, 297 bytes without a PDF signature. Search index describes a November 1994 LGA-boundary map; original and map remain unverified. Three-route checkpoint: `explore/output/2026-10-10_download-boundary-maps/leichhardt2011_canterbury2013_srep1994_lga_map_review.json`: two accepted, one failed. New hashes, PDF page counts and selected map renders pass; all 1552 IDs/paths/sizes pass. Older hashes not recalculated. No full series coverage claimed.


### 2010 Metropolitan Plan and NSROC 2007 alternate-route checks

- Five selected routes reviewed; no new raw originals registered. NSW Education resource page links to a 25-page PDF with native December 2010 title/copyright. It contains only the introduction, ending at printed page 21; contents refer to later absent chapters. All 25 thumbnails, native PDF 1/2 and whole PDF 22/23 map keys reviewed. Maps show transport/centres/land use; no explicit LGA-boundary key verified. It cannot supply the cited page 115 council map. Excerpt SHA-256 `9ccd14f66fefb3ceb53c92a0d2b0899ec7ef4f74aba32fa5956cb406df5de1bb`; 18,123,187 bytes. Not added to the boundary collection.
- Both APO resource routes returned HTTP 403. Hornsby’s indexed 2006–07 environment-report route returned HTTP 404; the NSROC alternative raised ConnectionError. Source identity, maps and copy hashes remain unverified for these routes. These observations do not establish general source unavailability.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/metro2036_nsroc2007_alternate_route_review.json`. Four failures, one screened excerpt skipped. Collection stays at 1,552 originals. Full 2010 plan and NSROC 2007 report remain unresolved; no live jobs.


### Cumberland BIO Map sheets and NSROC 2009/2010 LGA overview

- Saved unchanged all 16 linked Cumberland BIO Map LGA sheets: Bankstown, Blacktown, Camden, Campbelltown, Canterbury, Fairfield, Hawkesbury, Hornsby, Hurstville, Ku-ring-gai, Liverpool, Parramatta, Penrith, Ryde, The Hills and Wollondilly. White lines are explicitly keyed LGAs; black lines are the Cumberland IBRA subregion. Neighbour labels include former Auburn and Holroyd. North arrows and km scales present; CRS not printed. Some council extents are clipped. These overlapping sheets are not proof of 16 different geometry vintages.
- All 16 PDFs have metadata creation 13 May 2015 and modification 14 August 2015. These dates are not legal boundary revision dates. The 2024-09 URL directory is an upload path, not the map vintage. Each whole one-page map and native legend/title reviewed.
- NSROC 2009/2010 supplement: PDF 2 has seven bold black named council polygons and matching regional council caption. Pixelated overview limits digitising precision. Report period does not establish legal boundary vintage. First 30 thumbnails and full map reviewed; remaining 38 pages not visually reviewed.
- NSROC 2007/2008 Ryde-hosted report: PDF 2 map too blurred to verify line key; original not registered. First 30 thumbnails reviewed; remaining 64 pages not visually reviewed. No claim that the report lacks any LGA map.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/cumberland_biomap2015_nsroc2009_2010_lga_map_review.json`. 18 originals assessed; 17 accepted, one skipped, zero fetch failures. New original SHA-256, page counts, map renders and duplicate exclusion pass; all 1569 registered IDs/paths/sizes pass. Older hashes not recalculated.


### Cumberland BIO Map report and regional map: source review

- Full report is 85 PDF pages, native May 2015; catalogue says 175. All page thumbnails screened; enlarged map plates PDF 9, 13, 30, 38, 59–63, 69, 70, 72–74 reviewed. Keys identify Cumberland IBRA and ecological/investment features; no additional explicit LGA geometry verified. Not registered as an LGA map original.
- PDF 46 / printed 40 Appendix 2 identifies Land and Property Information as custodian of the Local Government Areas layer used to assist mapping. No boundary revision date stated. This supports series provenance, not legal date.
- Standalone regional map is one page, catalogue says two. Metadata creation 29 June 2015 and modification 20 July 2015; catalogue date 16 June 2021 does not establish vintage. Whole map/key reviewed: black border is Cumberland IBRA; no LGA key or named council polygons. Not registered.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/cumberland_biomap_full_report_regional_map_review.json`. Two successful downloads, two skipped for no verified LGA evidence. Collection remains 1,569 originals at this checkpoint.


### NSROC 2008/2009 seven-council map

- Unchanged Ryde-hosted 108-page report saved. Native cover identifies 2008/2009. PDF 2 has bold black named polygons for Hornsby, Ku-ring-gai, Ryde, Willoughby, Lane Cove, North Sydney and Hunters Hill, with matching council caption. Pixelated overview limits digitising precision. Similar to the 2009/2010 map; separate report original does not prove a new geometry vintage. Legal boundary date unknown. Whole PDF 2 and native cover date reviewed; remaining 106 pages not visually reviewed.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nsroc2008_2009_lga_map_review.json`. One accepted original; new SHA-256/page count/map render/duplicate exclusion pass. All 1570 registered IDs/paths/sizes pass; older hashes not recalculated.


### NSROC 2007 strategy and 2006 Ryde environment report

- Saved unchanged 27-page NSROC strategy. Source filename July 2007; PDF metadata creation 21 June 2007 and modification 8 August 2007. Cover planning period 2006–2031. PDF 12, 24, 27 have an explicit Council Areas colour key for the seven NSROC LGAs, and PDF 13 labels council fills under population 2001. North arrows; scale/CRS not verified for those plates. Statistical and forecast years do not establish legal boundary date. All 27 thumbnails screened; whole PDF 12, 13, 24, 27 reviewed; native contents/LGA definitions and metadata checked. Other plates reviewed only as thumbnails.
- Ryde-hosted 88-page environment report: native cover City of Ryde edition 2005/2006, heading 2006. All thumbnails screened and PDF 2 whole regional map reviewed. Map too blurred to verify LGA key; no other LGA plate verified. Not registered.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/nsroc2006_strategy2007_lga_map_review.json`. Two successful downloads; one accepted, one skipped. New hash/page count/selected map renders pass; all 1571 registered IDs/paths/sizes pass; older hashes not recalculated.


### BOCSAR 1984 report: older Sydney council geography

- Saved unchanged 60-page Intoxicated Persons 1981 report. Whole publication page PDF 2 gives 1984; data year is 1981. PDF 13 has named council polygons including former Colo, Gosford, Wyong, Hornsby, Warringah, Baulkham Hills, Blue Mountains, Penrith, Liverpool, Campbelltown, Sutherland and Wollondilly. Inner Sydney council polygons largely unlabelled. Heavier borders and A–G labels are statistical subdivisions, distinct from fine council borders. Legal boundary revision date unstated; publication/data years do not establish map vintage. No scale, CRS or north arrow verified for Sydney plate. PDF 12 statewide plate explicitly indexes statistical divisions/subdivisions; not independently counted as an LGA-keyed statewide map.
- All 60 thumbnails screened; whole PDF 2 publication page, PDF 11 geography explanation and PDF 12/13 maps reviewed. Scanned PDF has no native text. New hash/page count/Sydney map render pass; all 1572 registered IDs/paths/sizes pass; older hashes not recalculated.
- NSROC 2004/2005: all 68 thumbnails and whole PDF 2 and 17 maps reviewed. Regional map too blurred to verify boundary key; street map has no LGA evidence. Not registered. Older victimsservices BOCSAR route returned HTTP 200 non-PDF; current BOCSAR documents route succeeded. Parliamentary 1984 population report route returned HTTP 403. Four-route checkpoint: `explore/output/2026-10-10_download-boundary-maps/bocsar1984_nsroc2005_aph1984_lga_map_review.json`: one accepted, one skipped, two failed.
- Temporary storage filled during fetch. Removed task previews and temporary PDFs only after verifying matching registered SHA-256 copies; collection originals untouched. Current official BOCSAR fetch then succeeded.


### BOCSAR Waverley 1992 and Sydney 1980-data maps

- Mapping Crime in Local Government Areas: Assault and Break and Enter in Waverley: PDF 13 / printed 7 Figure 1 explicitly labels filled Waverley LGA; north arrow and 0–10 km scale. PDF 17 / printed 11 Figure 2 street map locates council outline relative to Old South Head Road, Oxford Street and Birrell Street, with 0–1 km scale. Internal census district boundaries in crime plates are not LGA boundaries. CRS unverified. Dates: Native publication 1992; legal boundary date unknown. All 40 thumbnails screened; whole PDF 2 publication page and PDF 13/17 maps reviewed. Other maps screened only as thumbnails.
- Intoxicated Persons 1980: Sydney council and statistical area map: PDF 10 Sydney map names council polygons including former Colo, Gosford, Wyong, Hornsby, Warringah, Baulkham Hills, Penrith, Blue Mountains, Liverpool, Campbelltown, Sutherland and Wollondilly. Thick borders and A-G labels identify statistical subdivisions; fine lines are council polygons. Inner council polygons largely unlabelled. Similar to the 1984 report map; separate original is not proof of new geometry. Scale/CRS/north arrow not verified on Sydney plate. Dates: Publisher catalogue 1982; native data period 17 March–31 December 1980; legal boundary date unknown. All 58 thumbnails screened; whole PDF 1/2/3 cover/front matter, PDF 8 geography explanation and PDF 10 map reviewed. Publication year taken from publisher catalogue, not printed on reviewed front matter.
- Crime in the Western Suburbs 1981 bulletin: all 11 thumbnails screened; no map found. Not registered. First guessed statistical-bulletin URL returned HTTP 200 non-PDF; publisher-linked sb path succeeded. Four-route checkpoint: `explore/output/2026-10-10_download-boundary-maps/bocsar1992_waverley1980_sydney_map_review.json`: two accepted originals, one skipped and one failed route. New SHA-256/page counts/selected map renders pass; all 1574 registered IDs/paths/sizes pass; older hashes not recalculated.


### Early Sydney coroners reports: no boundary maps found

- Publisher-linked reports for statistical years 1974 (13 pages), 1978 (14), 1979 (11) and 1981 (17) downloaded and fully screened as page thumbnails. No map found; none registered. Statistical year alone is not a publication or boundary date. This bounded four-report check does not cover the remaining coroners series.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/bocsar_coroners1974_1978_1979_1981_map_review.json`: four successful downloads, four skipped, zero accepted. Collection remains 1,574 originals at this checkpoint.


### BOCSAR Disadvantage and Crime 1991: Sydney and country LGAs

- Disadvantage and Crime in New South Wales: Sydney and country LGA maps: PDF 38 / printed 28 Map 8 explicitly titled Sydney LGAs for 1987/1988 convictions. PDF 56 / printed 46 Map 15 Sydney LGAs, 1986 Census. PDF 62 / printed 52 Map 18 NSW Country LGAs, 1986 Census. Unlabelled council polygons separated by fine boundaries; dense choropleth patterns obscure some segments. Statistical dates do not prove legal geometry date. No map scale, CRS or north arrow verified for selected plates. Dates: Native publication 1991; preface May 1991; mapped statistics 1986 Census and 1987/1988 convictions; legal boundary date unknown. All 89 page thumbnails screened; whole PDF 2 publication, PDF 4 preface and PDF 38/56/62 map plates reviewed. Other map plates thumbnail-screened only; scanned PDF has no native text.
- Crime and Place 1997: all 93 thumbnails screened; whole PDF 33 street crime maps and native PDF 16 study geography reviewed. Crime locations within Sydney police district, with five police patrols; no explicit LGA boundary map verified. Not registered. Two-original checkpoint: `explore/output/2026-10-10_download-boundary-maps/bocsar1991_disadvantage1997_crime_place_lga_map_review.json`: one accepted, one skipped, zero fetch failures. New hash/page count/selected map renders pass; all 1575 registered IDs/paths/sizes pass; older hashes not recalculated.


### BOCSAR Bulletin 114, May 2008: NSW LGAs and Sydney insets

- PDF 2 Map 1 and PDF 3 Map 2 explicitly identify Local Government Area arrest rates. NSW council polygon outlines and Newcastle-Sydney-Wollongong insets. North arrow and 0-400 km state scale; no CRS verified. Polygons largely unlabelled; small inset limits precision. Statistics span does not establish legal geometry date. Dates: Native publication May 2008; mapped arrest statistics January 1995 to September 2007; legal boundary date unknown. All eight page thumbnails screened; whole PDF 1 publication and PDF 2/3 maps reviewed, native map interpretation on PDF 3 read.
- One unchanged eight-page original registered. New SHA-256, page count, duplicate exclusion and map renders pass; all 1576 registered IDs/paths/sizes pass. Older hashes not recalculated. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/bocsar2008_cjb114_lga_map_review.json`.


### BOCSAR recorded crime reports 1990–1992: screened, not registered

- Three publisher-linked originals downloaded for review; zero fetch failures. First 20 and last 30 page thumbnails of each report screened; whole Sydney appendix maps on PDF 116 (1990), 122 (1991), and 126 (1992) reviewed. Native titles explicitly identify statistical subdivision boundaries. State companion titles identify statistical divisions. LGA lists in the next appendix do not supply individual council outlines. No LGA plate verified; originals not registered. Remaining body pages not visually reviewed. Statistical years are not independently verified publication or legal boundary dates. Three-source checkpoint: `explore/output/2026-10-10_download-boundary-maps/bocsar_rcs1990_1991_1992_map_review.json`.
- Urban Form and Commuting Behavior Change: Neliti direct PDF request redirected to HTTP 403. No original registered; indexed Sydney LGA map remains a lead, not verified evidence. Route checkpoint: `explore/output/2026-10-10_download-boundary-maps/urban_form_commuting_pdf_route_review.json`.


### BOCSAR Brief 60, April 2011: former Canterbury LGAs and suburbs

- PDF 4 Figure 4 explicit legend: blue LGA boundaries, purple suburb boundaries. Canterbury and neighbouring former LGAs named, including Bankstown, Hurstville, Kogarah, Rockdale, Marrickville, Ashfield, Burwood, Strathfield, Auburn, Canada Bay and Leichhardt. North arrow and kilometre scale. Street basemap and hotspot fills obscure some segments. PDF 8 Figure 12 repeats cropped council map; PDF 7 explicitly identifies blue lines as LGA boundaries. CRS legend not transcribed. 2009 crime date does not establish legal geometry date. Dates: Native publication April 2011; Figure 4 Canterbury hotspot 2009 Update; legal boundary date unknown. All eight page thumbnails screened; whole PDF 1 publication, PDF 4 full map, PDF 7 boundary explanation and PDF 8 cropped map reviewed. Other illustrations thumbnail-screened only.
- CJB34, native February 1997: all 20 thumbnails screened; whole PDF 5 and native cover/map title reviewed. PDF 5–8 map plates replaced by explicit under-construction placeholders. Indexed map titles alone do not establish that a plate survives. Not registered; complete original remains a lead.
- Two-original checkpoint: `explore/output/2026-10-10_download-boundary-maps/bocsar2011_bb60_1997_cjb34_lga_map_review.json`: one accepted, one skipped, zero fetch failures. New SHA-256/page count/duplicate exclusion/map renders pass; all 1577 registered IDs/paths/sizes pass; older hashes not recalculated.


### Western Sydney journal 2008 and Sydney modelling book 2009: LGA plates

- From Cowpastures to pigs heads: greater western Sydney LGA map: PDF 5 / printed 55 Map 1 explicitly identifies greater western Sydney LGAs, with white council outlines and names including former Baulkham Hills, Holroyd and Auburn. Small low-resolution coloured image; some labels overlap. No scale, north arrow or CRS verified. Adjacent statistical tables do not establish geometry date. Dates: Native journal publication December 2008; legal boundary date unknown. All 24 page thumbnails screened; whole PDF 5 map and native PDF 1 issue date reviewed. Only one map found in thumbnail screening.
- Modelling Urban Development with GIS and Cellular Automata: Sydney LGA planning overlays: PDF 101 / printed 86 Figure 4.1, PDF 109 / printed 94 Figure 4.6 and PDF 111 / printed 96 Figure 4.7 explicitly key LGA boundaries under Sydney planning-region/urban-growth overlays. Named council outlines, north arrows and kilometre scales. Figure 4.1 caption cites 2006 census products among sources. Planning years do not establish LGA boundary dates: Figure 4.6 keys the 1968 planning layer but labels Pittwater and South Sydney; councils are a separate composite layer. Dense central labels and planning hatching obscure some edges; no CRS verified. Dates: Native copyright/publication 2009; planning overlay dates 1948/1968/1988/1995/2005 and census source 2006; council boundary dates unknown. First ten and 14 native-text candidate page thumbnails screened (24 distinct pages); whole PDF 101/109/111 LGA map plates reviewed; native PDF 5 copyright date read. Other 180 pages not visually screened. PyMuPDF emitted No default Layer config warning; selected plates render successfully. Original unchanged.
- Two unchanged originals accepted, zero skipped or fetch failures. New SHA-256/page count/map renders/duplicate exclusion pass; all 1579 registered IDs/paths/sizes pass; older hashes not recalculated. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/sydneyjournal2008_liu2009_lga_map_review.json`.


### Sydney Region Outline Plan 1968: archive original

- PDF 116 Outline Plan, PDF 117 Phasing Plan, PDF 120 Development Constraints Map show fine council-area outlines with names including Colo, Windsor, Baulkham Hills, Blue Mountains, Penrith, Blacktown, Liverpool, Camden, Campbelltown, Wollondilly, Gosford and Wyong. North and mile scale. Council interpretation based on named areas and fine outlines; map keys do not explicitly identify the council line symbol. Heavy line keyed as Sydney region boundary must not be digitised as council boundary. Planning fills/roads obscure some segments. Map imprints read May 1968; planning horizon 1970–2000 is not geometry date; no CRS verified. Dates: Native report March 1968; selected map imprints May 1968; planning horizon 1970–2000; exact legal council boundary date unknown. All 123 page thumbnails screened; whole PDF 116/117/120 map plates reviewed; native PDF 4 March 1968 report date read. PDF 118/119 principles diagrams and other body maps thumbnail-screened only. Unchanged original fetched using public archive PDF asset link from download page.
- Direct requests to catalogue and guessed display-PDF route returned HTTP 403; browser guessed route returned HTTP 404. Public download page exposed full PDF asset 2939673, successfully downloaded. High-resolution original map TIFF assets 3940536–3940540 are exposed but not downloaded or reviewed yet. Browser requires existing `/tmp/trover-libs/root/usr/lib/x86_64-linux-gnu` and `/tmp/trover-browser/chrome-headless-shell-linux64/chrome-headless-shell`; no system packages installed.
- Parliament Sydney Future / Integrated Transport Strategy summary direct PDF route returned HTTP 403 (6398-byte non-PDF); not saved. This route failure does not establish that no copy exists.
- One unchanged original accepted. New SHA-256/page count/map renders/duplicate exclusion pass; all 1580 registered IDs/paths/sizes pass; older hashes not recalculated. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/city_sydney1968_outline_plan_lga_map_review.json`.


### 1968 Sydney Region original TIFF boundary sheets

- Three unchanged archive TIFFs saved: Outline Plan (PDF-equivalent 116), Phasing Plan (117), and Development Constraints Map (120). Full-resolution first frames are 6980×9246, 7069×9353, and 7068×9333 pixels. Each TIFF contains a second 121×160 pixel preview; it is not another map. Both frames decoded and inspected. Printed May 1968, planning horizon 1970–2000; legal boundary date and CRS unverified. Council outlines inferred from named areas and fine lines; heavy keyed Sydney region boundary is separate. Same plates as saved PDF; no claim of new geometry.
- Principles diagrams (118 and 119) downloaded and both frames inspected; no individual council outlines verified, so not registered. Five-sheet batch: three accepted, two skipped, no failures on successful bounded stream. Original bytes preserved with both frames. Initial whole-buffer transfer terminated before saving; old Chrome download worker is gone and left 227115243 partial bytes. Range requests returned 404 despite earlier accept-ranges header; partial was not appended. Fresh bounded full-response browser streams passed server-length and TIFF decode checks.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/sydney1968_original_tiff_boundary_sheet_review.json`. New SHA-256/copy/TIFF/frame-count/duplicate checks pass; all 1583 registered IDs/paths/sizes pass; older hashes not recalculated.
- After final registration checks, this batch’s verified temporary review copies and the 227115243-byte interrupted partial were removed. Registered originals were not modified. No download jobs remain live.


### Fingland 2014 thesis: western Sydney and Fairfield LGAs

- PDF 17 / printed 1 Figure 1.1: Greater Western Sydney sub-regions over fine council outlines; source credit Geoscience Australia and ABS, UWS Urban Research Centre 2008; north and kilometre scale. PDF 246 / printed 230 Figure 6.2 explicitly Fairfield LGA, map-layer legend keys blue LGA outline separately from CCD and small areas; id consultants from ABS Census 2006; street basemap. Census year is not verified boundary date. No CRS verified. PDF 187/189 reproduce 1988/1995 planning maps, but council boundary interpretation not independently verified for those plates. Dates: Native thesis 2014; western Sydney map credit UWS 2008; Fairfield map statistics ABS Census 2006; exact legal boundary dates unknown. 21 distinct PDF page thumbnails reviewed: first ten, native candidates 17/20/48/187/189/366, and added 21/45/47/245/246. Whole PDF 17/21/45/47/187/189/245/246 reviewed; native cover year 2014 read. Remaining 363 pages not visually reviewed; no full-thesis map inventory claim.
- Constructing Suburbs: copyright 1999, ebook edition 2005. First ten and four text candidates plus pages 29–46 / 113–119 thumbnail-screened (39 distinct pages); whole four maps PDF 36/38/46/117 reviewed. Regional/sector, housing-option and Rouse Hill development maps, no individual council-boundary plate verified; not registered. Remaining 175 pages unreviewed.
- City Archives 1988 Third Century catalogue node 1754118: public browser download page has no PDF/image download asset identified. Catalogue lists 72-page book; no original fetched from this record. Do not treat catalogue-only record as digitised map. Full 1988 and 1995 originals remain unresolved.
- Three-source checkpoint: `explore/output/2026-10-10_download-boundary-maps/wsu2014_fingland_forsyth1999_planning_map_review.json`: one accepted, two screened exclusions, zero fetch failures. New SHA-256/page count/map renders/duplicate exclusion pass; all 1584 registered IDs/paths/sizes pass; older hashes not recalculated.


### Epping March 2013: former Hornsby–Parramatta boundary segment

- PDF 7 / printed 4 Figure 3 distinguishes Parramatta LEP 2011 and Hornsby LEP 1994 zoning areas at Carlingford Road and railway. Native PDF 10 explicitly locates Parramatta LGA west of rail and south of Carlingford Road, with remaining precinct in Hornsby. PDF 25 / printed 22 Figure 22 labels Hornsby and Parramatta LGAs on combined proposed zoning map; locator inset also names Ryde. Partial council boundary segment only; thick outer Subject Land line is precinct, not LGA boundary. PDF 25 printed MGA Zone 56, GDA94 and scale 1:7000 at A3; north mark. Indicative proposed zoning/public-exhibition plan does not establish adoption or legal boundary date. Dates: Native March 2013 public-exhibition structure plan; PDF 25 cadastre 1 March 2013; legal LGA revision date unknown. All 29 page thumbnails screened; whole PDF 7/10/25 maps and locality text reviewed; native cover March 2013 read. Other mapped illustrations thumbnail-screened only.
- Wentworth Point Planning Report Appendix C: all 16 page thumbnails screened, no map. Contains discussion of 2007 West Central draft strategy, not the strategy original. Not registered; full 2007 strategy remains unresolved.
- Two-original checkpoint: `explore/output/2026-10-10_download-boundary-maps/epping2013_wentworth_planning_lga_map_review.json`: one accepted, one skipped, no failures. New SHA-256/page count/map renders/duplicate exclusion pass; all 1585 registered IDs/paths/sizes pass; older hashes not recalculated.


### Epping July 2011 JBA extract: explicit LGA boundary key

- Single PDF page / native printed 4, JBA Planning Epping Town Centre Study Volume 1 July 2011. Two panels explicitly key blue dashed/dotted LGA boundary along Carlingford Road and railway, distinct from red study-area perimeter and orange town-centre core. Aerial left and street/cadastre right panel; both 0–600 metre scales, compass marks visible. Partial former council boundary only; no CRS verified. Council names not on plate; Hornsby–Parramatta identification supported by separately saved March 2013 plan locality text, not independently named on this extract. Dates: Native July 2011 study Volume 1 printed page 4; legal LGA revision date unknown; Portal publication 2014 is not map date. Whole single-page map and native heading/key read. Both public publisher-linked copies have identical SHA-256; one original registered. Four bytes precede PDF magic; validated by PDF reader and preserved unchanged.
- Planning Portal PP-2020-1751 exposes the same map twice (applicable-land map and planning-proposal maps). Two document URLs return identical 2241805-byte originals and SHA-256. One retained. HTTP 200 application/pdf responses have four bytes before PDF header; initial strict prefix check was corrected, PDF parsed/rendered, all source bytes preserved. Direct catalogue HTTP 403 was resolved by reading the public page in browser.
- Council-hosted Terry Creek masterplan July2024-path PDF route returned HTTP 404, 150264-byte non-PDF page. Not registered; search index contents do not prove a currently downloadable copy or boundary vintage.
- Three-route checkpoint: `explore/output/2026-10-10_download-boundary-maps/epping2011_extract_terrys_creek_route_review.json`: one accepted, one duplicate excluded, one fetch failure. New SHA-256/page count/map render/duplicate exclusion pass; all 1586 registered IDs/paths/sizes pass; older hashes not recalculated.


### Older Hornsby reports and three NSWEC 2012 map-page leads

- Hornsby Annual/Sustainability Report 2009–2010 `_resources` PDF route and StateofShire2012 `__data/.../43073` PDF route both return HTTP 404 in direct requests and public-browser fetch. No PDF original downloaded; indexed content is not verified boundary evidence.
- 2012 election council index pages for Hornsby, Parramatta and Ryde respond HTTP 200 and link to `LGE2012/maps` HTML pages. These pages also respond HTTP 200 but expose ward/polling-place text and site furniture. No PDF, map-image or boundary-data asset reference identified in inspected HTML. Not registered. This does not establish that no archived boundary map exists, or coverage of the whole 2012 series.
- Checkpoint: `explore/output/2026-10-10_download-boundary-maps/hornsby2009_2012_reports_nswec2012_three_councils_review.json`. Five selected sources: three reviewed exclusions, two fetch failures, no accepted originals. Collection remains 1586 originals. No live download jobs.


### 1976 NSW preliminary census: original LGA map plates

- PDF 60 Map 1 NSW state council outlines under statistical divisions/subdivisions. PDF 61 and 62 together form Map 2 Sydney Statistical Division; 61 upper part, 62 lower part plus inner-Sydney inset and explicit Local Government Area Boundary key. Named former councils include Colo, Windsor, Baulkham Hills, Concord, Holroyd and South Sydney. Map 2 scales 1:625000 and inset 1:250000. PDF 63 Map 3 Newcastle/Wollongong explicitly keys LGAs separately from statistical districts. Map imprint 1976, used for 30 June 1976 census. Faint microfilm scan and split Sydney plate limit use; retain both halves. No CRS verified. Dates: Census 30 June 1976; map imprints 1976 and as used for 30 June 1976 census; native release 8 June 1978; exact legal boundary date not separately verified. 36 native-text candidate page thumbnails screened plus whole PDF 61 upper Sydney map (37 distinct pages); whole PDF 1 cover and 60/61/62/63 map plates reviewed. Native PDF 3 introductory comparison notes read. Remaining 27 pages not visually reviewed; PDF 64 map thumbnail-screened only.
- Native PDF 3 states 1971 totals were estimated on 1976 boundaries where LGAs changed. Do not treat comparison table years as separate geometry vintages. Whole report preserved unchanged; Sydney Map 2 spans PDF 61/62.
- 1976 NSW summary tables (38 pages; native release 19 November 1979) and 1976 LGA Descriptor File Technical Details (11 pages) fully thumbnail-screened. No boundary map found; neither registered. Descriptor is national file-format documentation, not a NSW boundary plate.
- Three-original checkpoint: `explore/output/2026-10-10_download-boundary-maps/anu1976_nsw_preliminary_summary_descriptor_map_review.json`: one accepted, two skipped, no fetch failures. New SHA-256/page count/map renders/duplicate exclusion pass; all 1587 registered IDs/paths/sizes pass; older hashes not recalculated.


### NSW census characteristics 1976/1981: screened sources

- ANU 1976 Characteristics of the Population: Local Government Areas (Preliminary), catalogue 2201.0, 305-page scan: first ten and last twelve thumbnails screened (22 pages); native title/introductory notes read. No boundary map verified in screened sections. Remaining 283 pages not visually reviewed. This is preliminary material, not the sought final LGA bulletin. Not registered as a boundary-map original.
- ANU 1981 Summary Characteristics of Persons and Dwellings NSW, 41-page scan: all page thumbnails screened, no map. Native PDF 2 release 22 April 1983, data census 30 June 1981. Tables and census forms; not registered.
- Two-source checkpoint: `explore/output/2026-10-10_download-boundary-maps/anu1976_1981_nsw_characteristics_map_review.json`: two downloaded and screened, two excluded, zero fetch failures; collection unchanged at 1587 originals. Bounded ANU catalogue query results saved alongside it; not a full catalogue coverage claim. Temporary review PDFs removed only after SHA-256 checks against fetch metadata.


### NSW Year Books 1981, 1983 and 1985: dated council map plates

- Official Year Book NSW 1981 — state and Sydney LGA maps: PDF 778 statewide plate explicitly keys thin council boundaries separately from statistical areas and states LGA boundaries as at 30 June 1979. PDF 779 Sydney index plate has council polygons numbered to numerical/alphabetical council lists; former boundaries visible. 1981 Sydney plate is very faint; its own boundary-date line not independently transcribed. State plate date verified. Kilometre scales on both plates; no CRS or north arrow verified. Heavy statistical-area borders are separate from thin LGA outlines. Other end maps thumbnail-screened only. Dates: Book year 1981; native preface January 1981; state LGA boundary date 30 June 1979; state map imprint December 1979. First 50 and last 30 PDF page thumbnails screened (80 distinct pages). Whole PDF 778/779 selected maps reviewed; native preface read. Remaining 711 body pages not visually reviewed; no full-book map inventory claim.
- Official Year Book NSW 1983 — state and Sydney LGA maps: PDF 785 statewide plate explicitly keys thin council boundaries separately from statistical areas and states LGA boundaries as at 30 June 1980. PDF 786 Sydney index plate has council polygons numbered to numerical/alphabetical council lists; former boundaries visible. Sydney plate also explicitly states boundaries as at 30 June 1980. Kilometre scales on both plates; no CRS or north arrow verified. Heavy statistical-area borders are separate from thin LGA outlines. Other end maps thumbnail-screened only. Dates: Book year 1983; native preface June 1983; state LGA boundary date 30 June 1980; state map imprint January 1981. First 50 and last 30 PDF page thumbnails screened (80 distinct pages). Whole PDF 785/786 selected maps reviewed; native preface read. Remaining 708 body pages not visually reviewed; no full-book map inventory claim.
- Official Year Book NSW 1985 — state and Sydney LGA maps: PDF 752 statewide plate explicitly keys thin council boundaries separately from statistical areas and states LGA boundaries as at 30 June 1983. PDF 753 Sydney index plate has council polygons numbered to numerical/alphabetical council lists; former boundaries visible. Sydney plate also explicitly states boundaries as at 30 June 1983. Kilometre scales on both plates; no CRS or north arrow verified. Heavy statistical-area borders are separate from thin LGA outlines. Other end maps thumbnail-screened only. Dates: Book year 1985; native preface January 1985; state LGA boundary date 30 June 1983; state map imprint November 1983. First 50 and last 30 PDF page thumbnails screened (80 distinct pages). Whole PDF 752/753 selected maps reviewed; native preface read. Remaining 675 body pages not visually reviewed; no full-book map inventory claim.
- Separate originals do not imply separate geometry dates. 1981 state plate date 30 June 1979 matches the period of prior 1979 material; no pixel/geometry identity asserted. 1983 maps retain former Colo and Windsor; 1985 Sydney index includes Hawkesbury. Small/faint council lines and key numbers require careful interpretation before digitising.
- Three-original checkpoint: `explore/output/2026-10-10_download-boundary-maps/abs_nsw_yearbooks1981_1983_1985_lga_map_review.json`: three accepted, no skipped/fetch failures. New SHA-256/page count/map render/duplicate exclusion pass; all 1590 registered IDs/paths/sizes pass; older hashes not recalculated.


### NSW Year Book 1982 council plates; 1994/1995 screening

- PDF 783 state plate explicitly keys thin LGA boundaries under heavier statistical agricultural areas/subdivisions; states council boundaries as at 30 June 1980. PDF 784 Sydney council index plate also states 30 June 1980 and numbers council polygons to numerical/alphabetical lists, including former Colo and Windsor. Kilometre scales; no CRS or north arrow verified. Same stated boundary date as 1983 book; distinct original does not establish new geometry. Other end plates thumbnail-screened only. Dates: Book year 1982; native preface March 1982; selected maps LGA boundaries 30 June 1980; state map imprint January 1981. First 50 and last 30 page thumbnails screened (80 distinct pages); whole PDF 783/784 selected maps reviewed; native PDF 16 preface March 1982 read. Remaining 706 pages not visually reviewed; no full-book map inventory claim.
- 1994 and 1995 Year Books: first 50 and last 30 thumbnails screened in each. Whole PDF 298 (1994) and 307 (1995) end maps explicitly show statistical divisions without individual council outlines. No LGA map verified in screened sections; not registered. Other 229/238 pages respectively not visually reviewed; no whole-book absence claim.
- Three-original checkpoint: `explore/output/2026-10-10_download-boundary-maps/abs_nsw_yearbooks1982_1994_1995_lga_map_review.json`: one accepted, two excluded, zero fetch failures. New SHA-256/page count/map renders/duplicate exclusion pass; all 1591 registered IDs/paths/sizes pass; older hashes not recalculated.


### NSW Year Books 1973/1974: 1972 LGA boundaries and older appended sheets

- Official Year Book NSW 1973 — dated state and Sydney LGA maps: PDF 1207 NSW statewide plate explicitly keys LGA boundaries separately from statistical agricultural areas and states 30 June 1972. PDF 1208 Sydney index plate numbers council polygons to numerical/alphabetical lists and also states 30 June 1972; former Colo, Windsor, Concord, Holroyd and other councils. Mile scales; no CRS verified. Sydney plate is faint with visible bleed-through; other end plates only thumbnail-screened. Dates: Book year 1973; native preface September 1973; principal maps boundaries 30 June 1972, imprint February 1973. First 50 and last 30 page thumbnails screened (80 distinct pages); whole selected PDF 1207/1208 maps reviewed; native preface read. Remaining 1129 pages not visually reviewed; no full-book map inventory claim.
- Official Year Book NSW 1974 — dated state and Sydney LGA maps: PDF 1200 NSW statewide plate explicitly keys LGA boundaries separately from statistical agricultural areas and states 30 June 1972. PDF 1201 Sydney index plate numbers council polygons to numerical/alphabetical lists and also states 30 June 1972; former Colo, Windsor, Concord, Holroyd and other councils. Mile scales; no CRS verified. PDF 1202 extra NSW colour plate explicitly states boundaries 30 June 1965 and is headed Year Book No.59, 1966, although appended to this 1974 PDF. PDF 1203 companion Metropolis of Sydney colour map keys LGA borders; its own date line not independently transcribed. Collation of these extra older sheets is unverified; do not assign them 1974 geometry. Scan folds and bleed-through obscure some details; compass mark visible on older Sydney map. Dates: Book year 1974; native preface June 1975; principal maps boundaries 30 June 1972, imprint February 1973; appended 1966-labelled NSW plate boundaries 30 June 1965; collation unverified. First 50 and last 30 page thumbnails screened (80 distinct pages); whole selected PDF 1200/1201/1202/1203 maps reviewed; native preface read. Remaining 1123 pages not visually reviewed; no full-book map inventory claim.
- Both principal pairs have the same stated 30 June 1972 boundary date. Different book originals/scans do not prove different geometry. The 1974 ABS PDF appends a plate explicitly headed Year Book No.59, 1966 with 30 June 1965 council boundaries; preserve as delivered but its inclusion/collation is not independently explained. The companion older Sydney plate is present; its own date line not independently transcribed.
- Two-original checkpoint: `explore/output/2026-10-10_download-boundary-maps/abs_nsw_yearbooks1973_1974_lga_map_review.json`: two accepted, no skipped/fetch failures. New SHA-256/page count/map render/duplicate exclusion pass; all 1593 registered IDs/paths/sizes pass; older hashes not recalculated.


### NSW Year Book1986 ANU scan and1966 full thumbnail review

- NSW Year Book 1986 — split statewide LGA boundary maps: PDF752/753 together statewide Statistical Divisions/Subdivisions map; PDF754/755 together statewide Statistical Agricultural Areas map. Both right halves explicitly key LGA lines separately from heavier statistical boundaries and state30June1984; imprintJanuary1985. Thin polygons numbered for council codes. Preserve both halves of each plate. Sydney statistical region at statewide scale; detailed Sydney council plate not located in screened pages. Legends refer to overleaf numerical/alphabetical indexes, but an index plate was not verified in this PDF. Kilometre scale; no CRS or north mark independently verified. Monochrome microfilm with black borders, clipped fold split and abrasion; some tiny lines difficult to trace. Same stated1984 vintage as saved Births1984 original; different publication is not proof of new geometry. Dates: Book No.70 1986; native preface March1986; LGA boundaries30June1984; map imprintJanuary1985. First50 and last30 page thumbnails screened:80 distinct pages. Whole PDF752–755 maps reviewed; native preface PDF11 read. Remaining675 pages not visually reviewed. No full-book map inventory claim.
- Original1986 PDF copied unchanged:48,620,075bytes,755pages. New SHA-256/page count/selected map renders pass; all registered IDs/paths/sizes pass; older hashes not recalculated. Checkpoint: `explore/output/2026-10-10_download-boundary-maps/anu_nsw_yearbook1986_lga_map_review.json`.
- Revisited fetched1966 ABS original:24,804,447bytes,1082pages,SHA-256a2b969cc033635c4314535b7dba901101e9307834dcd4a53c3583d8e10d82d2f. All1082 pages screened at thumbnail scale; whole PDF16 configuration/rainfall,17 primary production regions,829 Snowy Mountains scheme reviewed; no LGA plate verified. Native preface PDF6 April1967; frontispiece references PDF18/61/869; no embedded attachments. This strengthens the prior bounded screen but is not a detailed cartographic inventory.1966-labelled plates in registered1974 PDF remain available; their collation is unexplained.1966 original remains excluded. Checkpoint:`abs_nsw_yearbook1966_full_thumbnail_review.json`.
- Selected ABS DetailsPage queries1984/1986/1987/1988 returned no publisher PDF links. These are failed download-discovery routes, not evidence that editions or map plates do not exist. ANU1986 catalogue ORIGINAL bundle provides bitstream8d82ab55-a38f-436a-a2cc-4102e5b38bea. Route checkpoint:`abs_nsw_yearbooks1984_1986_1987_1988_route_review.json`.


### ANU NSW Year Books1988/1990: screened exclusions

- 1988: PDF295 printed226 irrigation/dam/water-resource map; infrastructure/state edges, no LGA key verified. No LGA map appendix located. Some pages are spreads and some show adjacent-page slivers; PDF page count does not equal printed-page count. All686 pages screened at thumbnail scale; wholePDF295 water resources map reviewed. No verified LGA boundary plate; thumbnail screening is not a detailed cartographic inventory. Source:https://openresearch-repository.anu.edu.au/items/f5fe42d9-b736-4304-bbbf-49e6cc62d069; bytes:103637619; SHA-256:f7f285f2c30b5ff475b8e0f918dbb2c90ed9cfa2e5ed12fbc0228fb8fc67fba6. Original not registered in boundary collection.
- 1990: PDF322 printed297 statewide statistical area map;PDF323 printed298 Sydney statistical subdivision map;PDF324 printed299 statewide statistical area map. Keys specify SD/SSD, not individual LGAs. Sydney region names such as Blacktown-Baulkham Hills do not establish an individual council boundary layer. First50 and last30 pages screened at thumbnail scale:80 distinct pages; wholePDF322,323,324 reviewed. Remaining256 pages not visually reviewed; no full-book map inventory. Source:https://openresearch-repository.anu.edu.au/items/229bff7e-6161-498e-bf9c-d6b5655c3fd9; bytes:20339760; SHA-256:51786103e87a9318c5fe3216b42bf2244350d929608000b45e0952496017efa5. Original not registered in boundary collection.
- Bounded catalogue searches found ANU1985/1986/1988/1990/1993/1994 editions; no1966 original identified in selected result sets. This does not establish complete catalogue coverage or absence. Query evidence:`anu_nsw_yearbook1966_catalogue_followup.json`.
- Exclusion checkpoint:`anu_nsw_yearbooks1988_1990_lga_map_review.json`:two completed exclusions,no fetch failures.


### ANU NSW Year Book1985: distinct split Sydney/statewide scan

- NSW Year Book1985 ANU scan — statewide and Sydney LGA maps: PDF736/737 together statewide Statistical Agricultural Areas map, with explicit thin LGA boundary key on737 and boundaries30June1983; imprintNovember1983. PDF738 contains Sydney Statistical Division index-to-LGAs map and part alphabetical index; PDF739 contains lower map sliver plus numerical/remaining alphabetical council indexes. Sydney key explicitly distinguishes LGA boundaries from statistical subdivision borders and states30June1983. Former Auburn, Holroyd, Concord and other councils indexed. Preserve split scans for complete map/index reading. Kilometre scales; no CRS or north mark independently verified. Monochrome microfilm, black borders, paper abrasion, F1/F2 holding labels and cropped split; tiny inner-council lines remain hard to trace. Different-byte original scan of edition already saved from ABS; same date is not proof of a geometry change. ANU Sydney first large page image1320x1020; saved ABS Sydney image3264x4688; extra segmented images/masks not separate maps or a resolution guarantee. Dates:BookNo.69 1985; native prefaceJanuary1985; LGA boundaries30June1983; statewide map imprintNovember1983. First50 and last30 PDF pages screened at thumbnail scale:80 distinct pages. WholePDF736–739 map/index plates reviewed; native prefacePDF11 read. Remaining659 pages not visually reviewed. No full-book map inventory claim.
- Unchanged original:46,014,024bytes,739pages,SHA-256ca89dffbea8f8d37cc381150a1a70b151429fcc6feaa98fc15abf91cc3a9d93a. New SHA-256/page counts/map renders and registered-hash duplicate exclusion pass. All registered IDs/paths/sizes pass; older hashes not recalculated. Checkpoint:`anu_nsw_yearbook1985_lga_map_review.json`. ANU catalogue provides research-use image; catalogue requires permission before reproduction.


### Births NSW1987: 1986 Census LGA/SLA maps; selected vital-statistics exclusions

- Births NSW1987 — 1986 Census Sydney and statewide LGA/SLA maps: PDF37/38 together NSW sheet1;PDF39/40 together Sydney Statistical Division sheet2 with inner Sydney inset. Map legends label statistical local area lines; LGA/SLA code columns link named council polygons to LGAs. Sydney City LGA7200 is split into SLA7201 Inner and7202 Remainder; aggregate these for council outline, not two councils. State LGAs also have splits including Blayney, Cabonne, Evans, Inverell, Newcastle and Tweed. NativePDF9 explains ASGC Edition3 and legal LGAs comprising one or several SLAs. Keep thicker statistical region edges separate from thin council/SLA lines. Former Auburn, Holroyd, Concord, Drummoyne, Warringah and other Sydney councils listed. Sheets explicitly labelled1986 Census, prepared National Mapping1987; no independent exact legal boundary date. PDF36 lists Hawkesbury lost to Penrith28November1986 and other post1July1986 changes; this does not demonstrate the appended1986-labelled map includes those changes. State scale1:4000000, Newcastle enlargement1:500000;Sydney1:600000, inner inset1:250000; native kilometre scales/north arrows. No CRS verified. Very faint microfilm, abrasion, clipped split and tiny inner boundaries constrain tracing. Same1986 cartographic series already saved in census originals; new publication/scan is not proof of new geometry. Dates:Data year1987; native explanatory-note signatureOctober1988; maps labelled1986 Census, National Mapping imprint1987; exact legal boundary date not independently verified. All42 PDF pages screened at thumbnail scale; whole map pages37–40 reviewed; native titlePDF2, explanatory notesPDF9 and change appendixPDF36 read. Thumbnail screening is not a detailed inventory of every table.
- Marriages, New South Wales, 1983: Tables/charts, no LGA map verified; report year1983 differs from native release1985. All15 PDF pages screened at thumbnail scale; native coverPDF1 read:1March1985. No maps identified. OriginalSHA-256:af67fc442c312b8340eeccd3c0c115f1287f8eec1ba716d3874ec70207a2edc1; 1300780bytes; 15pages. No original registered.
- Deaths, New South Wales, 1991: PDF27 printed22 explicitly Statistical Divisions of NSW; no individual LGA layer or council key. Excluded from boundary collection. All30 PDF pages screened at thumbnail scale; whole mapPDF27 reviewed; native coverPDF2 read. Embargo OCR January1993; exact day not independently transcribed. OriginalSHA-256:3dc57018567da4ebe7816112584c6b9f52b987729a66b0f98802317083dff365; 2837542bytes; 30pages. No original registered.
- One unchanged original saved; two screened exclusions. New SHA-256, PDF page count, selected map renders and registered-hash duplicate exclusion pass. All registered IDs/paths/sizes pass; older hashes not recalculated. Checkpoint:`anu_vital1983_1987_1991_lga_map_review.json`. ANU catalogue provides research-use scans and requires permission before reproduction. Catalogue discovery is three selected queries of at most30 results each, not complete series coverage.


### Births NSW1988: explicit back-cover map date;1989 screened exclusion

- Births NSW1988 — 30June1986 Sydney and statewide LGA/SLA maps: PDF37/38 together Sydney sheet2 with inner Sydney inset; PDF39/40/41 together statewide sheet1, with overlaps. Preserve all split portions. Explicit LGA/SLA code columns link thin SLA polygons to named councils; Sydney City LGA7200 comprises SLA7201 Inner and7202 Remainder. State LGAs also split into SLAs; use code aggregation rather than treating each SLA as a council. NativePDF35 ASGC Edition3 text explicitly states tables6/7 boundaries1January1988 and back-cover maps boundaries30June1986. This dated distinction is verified in this source, not inferred from report year. Native scales Sydney1:600000, inset1:250000; statewide1:4000000, Newcastle inset1:500000; kilometre bars and north arrows. National Mapping imprint1987; no CRS verified. Faint monochrome microfilm, abrasion and clipped overlaps constrain tracing. NativePDF6 Sydney andPDF7 balanceNSW are crude-birth-rate SLA thematic maps linked to table6 and back-cover key; statistical/table vintage differs from back-cover map vintage, so do not assign thematic polygons the1986 map date without further verification. Heavy dark fills obscure some thematic edges. Cartographic series already represented in saved1987 births and1986 census originals; new original scan is not proof of new geometry. Dates:Data year1988; native release20October1989; back-cover maps boundaries30June1986 perPDF35; tables boundaries1January1988; National Mapping imprint1987. All43 PDF pages screened at thumbnail scale. Whole selected mapsPDF6/7/37–41 reviewed; native title/releasePDF2 and boundary definitionPDF35 read. No detailed table audit.
- Births, New South Wales, 1989: Tables, text and charts; no LGA map verified in this downloaded scan. Report data year1989 differs from release1990. All38 PDF pages screened at thumbnail scale; native coverPDF2 read, release11December1990. No maps identified. Thumbnail screen is not a detailed cartographic inventory. OriginalSHA-256:ab6965d8afd31f070ed36620544054bcafb4448605b24794fc06dd6e2014b055; 3855792bytes; 38pages. No original registered.
- One unchanged original saved; one screened exclusion. New SHA-256, PDF page count, selected map renders and registered-hash duplicate exclusion pass. All registered IDs/paths/sizes pass; older hashes not recalculated. Checkpoint:`anu_births1988_1989_lga_map_review.json`. ANU catalogue provides research-use scans and requires permission before reproduction. Selected two-publication batch; no complete births-series coverage claim.


### Births NSW1985/1986: dated LGA and LGA/SLA appendices

- Births NSW1985 — 30June1985 Sydney and statewide LGA maps: PDF39 upperSydney LGA index map and alphabetical list;PDF40 lower map/legend and numerical/alphabetical indexes; together complete Sydney plate. Explicit thin LGA boundary reference and30June1985 date on40. PDF41 whole statewide Statistical Divisions/Subdivisions map explicitly keys LGA boundaries separately from heavier regional edges and states30June1985; imprintJanuary1986. Native contentsPDF4 also specifiesLGAs/statistical divisions30June1985; notePDF7 repeats map boundary date. Former Auburn, Holroyd, Concord, Drummoyne and Warringah councils present. Kilometre scale bars; no CRS or north mark independently verified. Faint monochrome Sydney scan, bleed-through, paper abrasions and split affect fine boundaries; preserve both index portions. Native report date and map date recorded separately. Dates:Data year1985; native explanatory-note signatureNovember1986; LGA boundaries30June1985; statewide map imprintJanuary1986. All43 PDF pages screened at thumbnail scale; whole map/indexPDF39–41 reviewed; native titlePDF2, contentsPDF4 and geography notesPDF7 read. No detailed table audit.
- Births NSW1986 — 30June1986 statewide LGA/SLA map: PDF29/30 together statewide1986 Census sheet1; LGA/SLA code columns link thin SLA polygons to named councils; Newcastle enlargement splits Newcastle LGA5900 into SLA5901 Inner/5902 Remainder. Other statewide LGAs also split into SLAs; use code aggregation for council outlines. Legend distinguishes SD/SSD from SLA boundaries; nativePDF7 explains ASGC Edition3/legalLGAs comprising one or severalSLAs. ContentsPDF3 specifies map statistical local areas30June1986, confirming map date in this report. Prepared by National Mapping1987. Map says SeeSheet2 in Sydney, but no Sydney sheet2 is present in this32-page downloaded scan; reviewed all pages, preserve incomplete cartographic appendix as delivered. Detailed Sydney counterpart already represented in saved1987/1988 births and1986 census originals; do not imply this source contains it. State scale1:4000000, Newcastle inset1:500000, kilometre bars and north arrows; no CRS verified. Very faint microfilm and clipped split constrain tracing. Same1986 cartographic series, new original is not proof of new geometry. Dates:Data year1986; native explanatory-note signatureJanuary1988; contents specify map statistical local areas30June1986; maps labelled1986 Census, National Mapping imprint1987. All32 PDF pages screened at thumbnail scale; whole mapPDF29/30 reviewed; native titlePDF2, contentsPDF3 and geography notesPDF7 read. No detailed table audit.
- Two unchanged originals saved; no exclusions or fetch failures. New SHA-256, PDF page count, selected map renders and registered-hash duplicate exclusion pass. All registered IDs/paths/sizes pass; older hashes not recalculated. Checkpoint:`anu_births1985_1986_lga_map_review.json`. ANU catalogue provides research-use scans and requires permission before reproduction. Selected two-publication batch; no complete births-series coverage claim.


### Regional Statistics NSW1987/1988/1989: dated Sydney/statewide map appendices

- Regional Statistics NSW1987 — 30June1985 Sydney/statewide LGA maps: PDF94/95 together statewide Statistical Divisions/Subdivisions map explicitly keys thin LGA lines separately from heavier regional borders; native30June1985 LGA date andJanuary1986 imprint on95. PDF96/97 together Sydney Index to Local Government Areas plate with numbered council polygons and numerical/alphabetical lists; its own legend states30June1985. Kilometre scales; no CRS or north mark independently verified. Very faint monochrome Sydney plate, abrasion and split/overlap constrain inner council tracing. PDF93 labour-force region diagram only thumbnail-screened and not accepted as individual-LGA evidence. These map vintages already occur in other saved reports; separate original scans do not prove new geometry. Dates:Edition1987; native introductionFebruary1987; maps LGAs30June1985; statewide map imprintJanuary1986. All97 PDF pages screened at thumbnail scale; whole selected map panels94,95,96,97 reviewed; native titlePDF2, contentsPDF4, introductionPDF5 and cited geography notes read. No detailed table audit.
- Regional Statistics NSW1988 — 30June1986 Sydney/statewide LGA/SLA maps: Statewide1986 Census sheet1 spans PDF80/81; Sydney1986 Census sheet2 with inner Sydney inset spans PDF86/87. Explicit LGA/SLA code columns map thin SLA polygons to named councils; Sydney CityLGA7200 splits intoSLA7201 Inner and7202 Remainder. Other statewide LGAs have multipleSLAs; aggregate codes for council outlines. Native contentsPDF4 explicitly dates both map sheets30June1986. Native geography notes PDF6 state SLAs comprise legal LGAs or splits. Keep statistical regional edges separate from council/SLA lines. National Mapping imprint1987. State1:4000000, Newcastle inset1:500000; Sydney1:600000, inner inset1:250000; kilometre bars and north arrows; no CRS verified. Faint monochrome microfilm, clipped overlaps and abrasion constrain tracing. Report/table data use later dates; do not assign report year1988 to map geometry. These map vintages already occur in other saved reports; separate original scans do not prove new geometry. Dates:Edition1988; native introductionSeptember1988; contents maps statistical local areas30June1986; map labels1986 Census; National Mapping imprint1987. All87 PDF pages screened at thumbnail scale; whole selected map panels80,81,86,87 reviewed; native titlePDF2, contentsPDF4, introductionPDF5 and cited geography notes read. No detailed table audit.
- Regional Statistics NSW1989 — 30June1986 Sydney/statewide LGA/SLA maps: Statewide1986 Census sheet1 spans PDF80/81/82; Sydney1986 Census sheet2 with inner Sydney inset spans PDF83/84. Explicit LGA/SLA code columns map thin SLA polygons to named councils; Sydney CityLGA7200 splits intoSLA7201 Inner and7202 Remainder. Other statewide LGAs have multipleSLAs; aggregate codes for council outlines. Native contentsPDF4 explicitly dates both map sheets30June1986. Native geography notes PDF67 state SLAs comprise legal LGAs or splits. Keep statistical regional edges separate from council/SLA lines. National Mapping imprint1987. State1:4000000, Newcastle inset1:500000; Sydney1:600000, inner inset1:250000; kilometre bars and north arrows; no CRS verified. Faint monochrome microfilm, clipped overlaps and abrasion constrain tracing. Report/table data use later dates; nativePDF68 states differing table geography dates, including30June1988 and30June1986; do not assign report year1989 to map geometry. These map vintages already occur in other saved reports; separate original scans do not prove new geometry. Dates:Edition1989; native introductionOctober1989; contents maps statistical local areas30June1986; map labels1986 Census; National Mapping imprint1987. All85 PDF pages screened at thumbnail scale; whole selected map panels80,81,82,83,84 reviewed; native titlePDF2, contentsPDF4, introductionPDF5 and cited geography notes read. No detailed table audit.
- Three unchanged originals saved; no exclusions or fetch failures. Earlier1988/1989 connection-reset failures recovered through public ANU API; earlier failure checkpoint retained as history. New SHA-256, PDF page count, selected map renders and registered-hash duplicate exclusion pass. All registered IDs/paths/sizes pass; older hashes not recalculated. Checkpoint:`anu_regional1987_1988_1989_lga_map_review.json`. ANU catalogue provides research-use scans and requires permission before reproduction. Selected three-publication batch; no complete regional-series coverage claim.


### NSW Regional Statistics1991/1992: screened exclusions

- Regional Statistics, New South Wales, 1991: PDF13 explicitly Sydney Statistical Division solid silhouette, no individual council polygons. Other statistical-division silhouettes and statewide SD overview visible in thumbnails; no individual LGA map appendix verified. LGA/SLA statistical lists are not boundary map evidence. All87 PDF pages screened at thumbnail scale; wholePDF13 printed7 Sydney silhouette reviewed; native titlePDF2 and contentsPDF4 read. Thumbnail screen is not a detailed cartographic inventory. Original:8979510bytes; SHA-256:0f9df73cd558cdf52849d8e5a2ecab52b6c95ef935ef10a5a4ad4183b23db401. No original registered.
- Regional Statistics, New South Wales, 1992: PDF13 explicitly Sydney Statistical Division solid silhouette, no individual council polygons. Other statistical-division silhouettes and statewide SD overview visible in thumbnails; no individual LGA map appendix verified. LGA/SLA statistical lists are not boundary map evidence. All95 PDF pages screened at thumbnail scale; wholePDF13 printed7 Sydney silhouette reviewed; native titlePDF2 and contentsPDF4 read. Thumbnail screen is not a detailed cartographic inventory. Original:8937824bytes; SHA-256:082f1062ceb7362e2d808c0a40afd0657af8ac93d4265913c9b8900cb229e4a3. No original registered.
-1992 prior connection-reset route recovered through public item API. Earlier failure checkpoint retained as history. The1990 edition was not identified in one bounded query of40 results; not proof of absence. Discovery:`anu_regional1990_catalogue_discovery.json`. Review:`anu_regional1991_1992_lga_map_review.json`:two completed exclusions,no fetch failures.


### Deaths NSW1984/1985: dated Sydney/statewide LGA map originals

- Deaths NSW1984 — 30June1984 Sydney and statewide LGA maps: PDF32 whole statewide Statistical Divisions/Subdivisions map explicitly keys thin LGA borders separately from heavier statistical boundaries and states30June1984; imprintJanuary1985. PDF33/34 together Sydney Index to Local Government Areas map with numbered council polygons and numerical/alphabetical indexes. Own Sydney legend explicitly states30June1984 and identifies LGA line separately from statistical subdivision border. Former Auburn, Holroyd, Concord, Drummoyne, Warringah and other councils indexed. Preserve both split/overlapping Sydney portions. ContentsPDF3 and geography notesPDF5 also state map boundary date. Native kilometre bars; no CRS or north mark independently verified. Monochrome microfilm with faint Sydney lines, abrasion, show-through and scan splits constrain fine tracing; dark state statistical edges are not council borders. Same1984 map vintage already appears in saved births/other originals; separate report scan does not prove new geometry. Dates:Data year1984; native explanatory-note signatureApril1986; map LGAs30June1984; statewide imprintJanuary1985. All36 PDF pages screened at thumbnail scale; whole selected map/indexPDF32,33,34 reviewed; native titlePDF2, contentsPDF3 and geography notesPDF5 read. Some1984 PDF pages are spreads: PDF count does not equal printed-page count. No detailed table audit.
- Deaths NSW1985 — 30June1985 Sydney and statewide LGA maps: PDF45 whole statewide Statistical Divisions/Subdivisions map explicitly keys thin LGA borders separately from heavier statistical boundaries and states30June1985; imprintJanuary1986. PDF43/44 together Sydney Index to Local Government Areas map with numbered council polygons and numerical/alphabetical indexes. Own Sydney legend explicitly states30June1985 and identifies LGA line separately from statistical subdivision border. Former Auburn, Holroyd, Concord, Drummoyne, Warringah and other councils indexed. Preserve both split/overlapping Sydney portions. ContentsPDF3 and geography notesPDF6 also state map boundary date. Native kilometre bars; no CRS or north mark independently verified. Monochrome microfilm with faint Sydney lines, abrasion, show-through and scan splits constrain fine tracing; dark state statistical edges are not council borders. Same1985 map vintage already appears in saved births/other originals; separate report scan does not prove new geometry. Dates:Data year1985; native explanatory-note signatureNovember1986; map LGAs30June1985; statewide imprintJanuary1986. All47 PDF pages screened at thumbnail scale; whole selected map/indexPDF43,44,45 reviewed; native titlePDF2, contentsPDF3 and geography notesPDF6 read. Some1984 PDF pages are spreads: PDF count does not equal printed-page count. No detailed table audit.
- Two unchanged originals saved; no exclusions or fetch failures. New SHA-256, PDF page count, selected map renders and registered-hash duplicate exclusion pass. All registered IDs/paths/sizes pass; older hashes not recalculated. Checkpoint:`anu_deaths1984_1985_lga_map_review.json`. ANU catalogue provides research-use scans and requires permission before reproduction. Selected two-publication batch; no complete deaths-series coverage claim.


### Deaths NSW1983/1986/1988: LGA maps and catalogue date conflict

- Deaths NSW1983 — 30June1983 Sydney/statewide LGA maps: PDF33/34 together statewide SD/SSD map explicitly keys thin LGA lines and dates them30June1983; imprintNovember1983. PDF35/36 split Sydney LGA index plate has numbered council polygons, numerical/alphabetical lists and own30June1983 date. ContentsPDF3 and notesPDF6 confirm map date. Faint scan, cropped overlap and abrasion constrain tracing. Kilometre bars; no CRS or north mark independently verified. Same map vintages already represented elsewhere; distinct source does not prove new geometry. Dates:Native report1983; explanatory-note signatureJune1985; map LGAs30June1983; state imprintNovember1983. All38 PDF pages screened at thumbnail scale; whole selected maps/indexesPDF33,34,35,36 reviewed; native title, contents and cited geography notes read. No detailed table audit.
- Deaths NSW1986 — 30June1986 statewide LGA/SLA map: PDF32/33 together statewide1986 Census sheet1 with explicit LGA/SLA code columns and SD/SSD/SLA line references. ContentsPDF3 dates map statistical local areas30June1986; imprintNational Mapping1987. No Sydney sheet2 in this35-page scan despite map reference to it. State1:4000000, Newcastle inset1:500000, north/kilometre bars; no CRS verified. Faint/clipped microfilm; original appendix incomplete as delivered. Same map vintages already represented elsewhere; distinct source does not prove new geometry. Dates:Native report1986; explanatory-note signatureFebruary1988; contents map30June1986; imprint1987. All35 PDF pages screened at thumbnail scale; whole selected maps/indexesPDF32,33 reviewed; native title, contents and cited geography notes read. No detailed table audit.
- Deaths NSW1988 — 30June1986 Sydney/statewide LGA/SLA maps: Catalogue title/year1987 conflicts with native titlePDF2 Deaths NSW1988 and release12December1989. Register printed title1988; retain source catalogue mismatch. PDF34/35 together Sydney1986 Census sheet2 with inner inset; PDF36/37 statewide sheet1. ContentsPDF4 explicitly dates both sheets30June1986. LGA/SLA code columns link named councils to thin SLA lines. SydneyLGA7200 comprisesSLA7201/7202; Newcastle5900 also splits into5901/5902; other state LGAs split. Aggregate SLA codes for council outlines, not every SLA as a council. PDF30 explains relation of SLAs to legal LGAs. PDF7/8 death-rate SLA thematic maps link to table7; its geography1January1988 differs from1986 back-cover sheets, so keep dates separate. State1:4000000, Newcastle inset1:500000; Sydney1:600000, inner inset1:250000; north/kilometre bars; imprintNational Mapping1987; no CRS verified. Dark thematic fills hide some edges; grayscale abrasion/folds/clipping remain. Same map vintages already represented elsewhere; distinct source does not prove new geometry. Dates:Catalogue1987 conflicts with printed report1988; native release12December1989; contents maps30June1986; imprint1987; table7 geography1January1988. All39 PDF pages screened at thumbnail scale; whole selected maps/indexesPDF7,8,34,35,36,37 reviewed; native title, contents and cited geography notes read. No detailed table audit.
- Three unchanged originals saved; no exclusions or fetch failures. New SHA-256, PDF page count, selected map renders and registered-hash duplicate exclusion pass. All registered IDs/paths/sizes pass; older hashes not recalculated. Checkpoint:`anu_deaths1983_1986_1987_lga_map_review.json`. ANU catalogue provides research-use scans and requires permission before reproduction. Selected two-publication batch; no complete deaths-series coverage claim.


### Initial census-year source coverage check

- User benchmark: each historical census year. Initial source index:`nsw_lga_census_source_coverage_initial.csv`, selected1891–1986 census years only. Earlier/later census years and other registered map series still require matching; not a complete census-year audit. Sources and known caveats traced to manifest and existing reviews. No council-by-council coverage denominator or completed-outline count exists, so no completeness percentage is supported. Statewide shire maps in1921/1933/1947 omit provincial municipal outlines through point symbols.1954 has conflicting map/notes dates.1981 council map date differs from census night. Presence of a source is not complete legible council coverage.


### NSW census LGA panel: first indexed years and digital endpoint

- Script:`explore/2026-10-14_nsw-lga-census-panel.py`; outputs in matching script folder.1911:324 council rows from reviewed existing extraction(190 municipalities,134 shires). Same-name municipality/shire pairs Barraba,Muswellbrook,Tenterfield remain distinct.
- Official ABS1981 GeoPackage contains NSW179 features/codes; published table1PDF7–9 supplies176 whole council rows, plus two unincorporated units and Migratory. Part A/B/C detail rows excluded in favour of whole-LGA subtotals. Published geography1January1981 precedes census30June1981.
- Digital code10041 is labelled Jerrabomberra but printed table identifies Coolamon(S); other digital labels have OCR-like spellings, Part labels and type differences. Published Lake Macquarie is(M),digital(C); preserve conflict. Native Jerilderie/Leeton OCR corrected from inspected strips in `1981_roster_name_review.png`. Digital geometry not audited; do not claim176 verified polygon matches.
- Official source:https://data.gov.au/data/dataset/9eb34d32-5548-46ae-8668-851217428731 ; raw original89475072bytes and SHA in generated verification. Census dates through1981 checked against ABS Population Estimates ConceptsSourcesMethods2009 Table1.1.
- Superseded the 500-row seed with 2,558 council-year rows across all ten censuses. Counts: 1911 324; 1921 321; 1933 319; 1947 289; 1954 241; 1961 225; 1966 224; 1971 225; 1976 214; 1981 176. All rosters extracted; some name reviews and all individual-outline audits remain open. No map-completeness percentage is supported yet.
- Historical source-row input: `data/intermediate/nsw_lga_census_panel/historical_roster_source_rows.csv`. It records source PDF page, printed row/index number or text position, raw label and extraction/review status. Do not treat text positions as LGA codes. Only 1976/1981 codes enter the panel code field; codes are year-specific.
- 1921 source PDF 366–371: municipal rows 1–185, shire rows 186–321. 1933 PDF 444–448: municipal rows 1–181, shires 182–319. 1947 PDF 368–372: municipal rows 1–152, shires 153–289. Complete printed row sequences checked. These category headings group cities with municipalities; no legal city classification inferred for those years.
- 1954 Table 1 PDF 5–7 has 110 municipal and 131 shire rows. Notes PDF 4 date the published geography to 30 September 1953; map captions use June 1954. Keep the published roster, including footnoted councils, and flag the conflict. Counts are extraction totals, not an independent council-register check.
- 1961 map index PDF 130: 202 regional index entries collapse to 194 distinct councils because eight councils repeat across regions. Table 1 PDF 6 adds 31 metropolitan councils absent from that index. Result: 225 councils, including 133 shires and 92 municipal units (20 printed cities plus 72 municipalities), matching the notes PDF 4. Image checks corrected Talbragar/Wellington and Balranald labels.
- 1966 typed alphabetical index PDF 501–506 includes localities and urban centres. Keep C/M/S entries only; merge repeated statistical parts. Result 224 councils. Newcastle's type was joined to other text in the native layer and was restored from the printed index/OCR evidence. Cross-year comparison caught the omission. Further independent name review remains flagged.
- 1971 Table 1 PDF 4–6 supplies 225 councils after merging Blue Mountains, Greater Cessnock and Macintyre parts. Source name columns visually reviewed. Parramatta and Penrith are printed M, while the 1966 index prints C. Retain 1971 M and flag the publication conflict; no legal downgrade inferred. Preserve printed Rylestone spelling rather than forcing a later spelling.
- 1976 Table 1 PDF 7–10 has whole-council codes 001–214, checked without gaps. Use whole-LGA subtotal rows, not Part A/B detail rows. Retrospective 1971 columns use 1976 geography and do not define the 1971 roster.
- `council_gap_priorities.csv` is an action queue, not a list of proven missing boundaries: early municipal outlines first, other historical outlines next, then 1981 digital geometry checks. All outlines are marked not audited. `name_review_queue.csv` retains the five earlier/native-text rosters for further independent label review. `non_council_units.csv` records identified special units; it is not yet an exhaustive special-unit inventory for every year.


### Sydney census map panel — 14 October 2026

- User chose each census's published Sydney metropolitan/statistical region. Retain whole LGAs that intersect it; flag published council parts. Same names across years do not imply stable council identity or boundaries.
- Membership source input: `data/intermediate/nsw_lga_census_panel/sydney_membership_source_rows.csv`. The existing NSW panel builder joins on census year, name and type. Result: 424 council-year rows. Counts: 1911 42; 1921 42; 1933 50; 1947 50; 1954 35; 1961 35; 1966 40; 1971 41; 1976 45; 1981 44.
- Membership evidence: 1911 Statistician's Report PDF 459; 1921 PDF 386–387; 1933 PDF 463; 1947 PDF 386–387. These are dedicated NSW metropolitan LGA tables, separate from statewide council rosters. 1933/1947 include Holroyd part. The 1947 metropolitan table prints Erskinville while the NSW roster uses Erskineville; preserve the label conflict.
- 1954 Table 1 PDF 9/11 and 1961 Table 1 PDF 6 give 35 metropolitan councils. Parts: Baulkham Hills, Blacktown, Liverpool, Hornsby. Councils visible outside the metropolitan boundary on the map are not automatically included. The 1954 preferred map calls Blacktown a municipality, while the published census tables call it a shire; retain this conflict with the existing September 1953/June 1954 date conflict.
- 1966 alphabetical index PDF 501–506: filter typed C/M/S rows whose statistical division is Sydney. Independent extraction matches all 40 selected councils. Blue Mountains part is included. The native text drops the l in Waverley; source image/OCR supports the corrected name.
- 1971 field-count Table 3 PDF 11/12: 41 Sydney SD councils, including Blue Mountains part. Outer Sydney is a separate SD in PDF 12: Blue Mountains balance, Colo, Gosford, Wollondilly and Wyong. Do not add these council parts/areas to the main Sydney region. 1976 Table 2 PDF 11/12 includes 45 councils in Sydney SD, now including Gosford–Wyong and the former Outer Sydney area. Do not interpret region-count changes solely as council creation/abolition.
- 1981 Table 2 PDF 10/11: 44 Sydney SD councils, matched by publication code to the NSW roster and ABS GeoPackage. Exact source-table dates retained; no gazetted council list reconstructed.
- Sydney map source pages: 1911 PDF 457; 1921 407; 1933 476; 1947 399; 1954 196; 1961 131; 1966 509; 1971 colour Bulletin 13 PDF 21; 1976 PDF 61/62; 1981 PDF 64. PDF 65 of the 1981 source is blank and was excluded after preview inspection. `sydney_map_preview.pdf` has 11 pages for the ten censuses; 1976 is a two-panel scan. It is a review aid, not georeferenced imagery or proof that every outline is traceable.
- Preferred higher-resolution sources already saved: 1954 SLNSW record 74VKdrqKvk7A, original 8405×9891 JPG; 1961 ANU metropolitan map, original 7884×8611 JPG. Both explicitly reference the respective census's LGA geography. Panel preferred-source fields point to these originals; census report plates remain in the preview. `sydney_map_source_candidates.csv` indexes 12 source originals. No new downloads in this work block.
- `sydney_lga_1981.gpkg`, layer `sydney_lga_1981`: 44 whole-LGA candidate features. Original ABS geometry blobs preserved in EPSG:4283 (GDA94); no clipping, repair, projection change or replacement of source labels. `published_boundary_date` is the census publication's 1 January 1981 geography date; it does not independently verify the digital geometry's legal date. All 44 are non-empty and topologically valid. Gosford is labelled Cosford in the digital source; preserve both names and the conflict flag. Validity is not a geometry-to-council identity or boundary-accuracy audit.
- All 424 records have council-level next actions. Twelve council-year entries use only a council part in the published Sydney region; those require full-LGA outline checks outside the region. Historical geometry remains not digitised. Individual full-outline checks are not audited; unknown verified counts stay blank. NSW name-review flags remain inherited and separate from reviewed Sydney membership.

### Other-state census LGA panel — 16 October 2026

- Sources: ABS AUSSTATS per-state LGA census volumes (1921–1981), 1911 Part XIII table 68 and table 65, 1954 and 1961 national Statistician's Reports, 1976 ANU preliminary volumes, 1971 Field Count Statements, and the 1981 ABS GeoPackage. Manifest with sizes and SHA-256 hashes: `explore/output/2026-10-16_download-other-states-lga-census-maps/manifest.csv` (77 files).
- Map candidates per state and census year are recorded in `explore/output/2026-10-16_other-states-lga-census-panel/map_source_candidates.csv`. 1911–1947 statewide plates come from the national Statistician's Report map sections (1911 PDF 444/445/448/449/452/453/456 plus metropolitan plates 457/460/461/464/465/468; 1921 PDF 396–406 plus 408/409; 1933 PDF 469–475 plus 476–481; 1947 PDF 390–398 plus 399–404). 1971 maps come from the national Bulletin 13 sheet set (PDF 1–22). 1954–1981 maps sit near the end of each state volume; page lists are in the panel outputs.
- 1954 and 1961 national Statistician's Reports carry a full statewide map series (1961: Australia 499, NSW 501, VIC 503, QLD 505, SA 507, WA 509, TAS 511, NT and ACT 513, then capital-city plates 514–519). The 1954 report series (PDF 426–447) is only provisionally identified.
- 1976 LGA bulletins (catalogue 24270–24340) are example-table bulletins: no LGA rows and no maps. 1976 rosters and boundary maps come from the ANU copies of the preliminary population/dwellings volumes (catalogue 20_084–20_091, one per state/territory). Their OCR quality is poor; the panel merges spelling variants within edit distance 1 (2 for long names) and lists them in `name_alternates`.
- 1981 GeoPackage coverage check (whole-LGA names, edit distance ≤ 2): VIC 96%, QLD 99%, SA 96%, WA 98%, TAS 96% of ABS 1981 whole-LGA names matched by panel rows. Queensland's 1981 layer holds 308 features because the City of Brisbane is divided into statistical areas (134 whole LGAs).
- NT and ACT panel rows are published divisions and districts, not municipal councils; `unit_class` marks this. The 1961 ACT volume contains no maps (blank plates only); the ACT appears on the NT/ACT plate of the 1961 Statistician's Report (PDF 513). Panel rows: 6,650 across 59 state-year pairs; every row links to a map source file and plate pages (checked in range).
- Counts in the panel are a lower bound where OCR loses rows: 1947 SA/QLD and 1954/1961 SA remain visibly short. Every row carries `name_review_required` and its source page; `name_review_queue.csv` lists rows waiting for scan review.

### Candidate map digitisation readiness — 17 October 2026

- Every candidate plate in both panels is rated A (digitise now) to D (not digitiable as LGA polygons) with the blocker and a named better source: `explore/output/2026-10-17_map-digitisation-readiness/digitisation_readiness.csv` (240 plates: 98 A, 72 B, 66 C, 4 D; 70 weak plates, all annotated).
- Resolution drives most ratings. 1911 statewide plates are 375-600 px (unusable); 1921/1947 statewide plates are 2067-3541 px; 1933 is 992-2176 px; 1954/1961 state-volume plates are 474-1144 px while the national Statistician's Report plates are 1127-2176 px; 1966 regional series are 288-1749 px; 1971 field-count metro maps are 3500x4960 px; 1976/1981 are 1792-5824 px.
- Plate-level caveats found by inspection: 1911-1947 statewide plates show counties, census districts or statistical districts in some states, and provincial municipalities can be point symbols rather than polygons; 1971 Bulletin 13 sheets mix statistical-division and LGA lines in colour; 1981 monochrome scans lose the urban shading.
- Rescues registered in raw and linked in the panels: 1954 and 1961 Statistician's Report map series (sharper for every state); 1966 TAS Bulletin No 6.8 page 16; 1966 NT and ACT from ANU Field Count Statements No 12 and No 5; 1971 metropolitan maps inside the per-state Field Count Statements (Melbourne PDF 32, Brisbane 31, Adelaide 26, Hobart 17).
- Still unsourced after search: 1911 VIC/QLD/SA/WA/TAS statewide municipal maps (no digitised year book or statistical register for 1911; the ABS Year Book Queensland series starts 1937), 1954 VIC statewide, and the 1966 VIC/QLD/SA/WA regional sheets where ABS Bulletins duplicate the same raster.
- 1981 needs no tracing at all: the official ABS GeoPackage supplies digital geometry for every state and territory.
