# The Loop

Key decisions and things to keep in mind. Data facts live in `data-notes.md`; the
long-form history is in git.

## Source handling (all documents)

- Keep raw sources unchanged; derivatives go to `data/intermediate/`.
- Inventory printed rows, sections, units and column grids before mapping model proposals.
- A valid total is not evidence of correct digits. Never balance residuals, infer zeros or
  guess digits; distinguish printed absence, missing extraction, source damage and
  publication conflict.
- Keep row/column provenance; keep model labels distinct from source-linked labels.
  Model output is a candidate until source review accepts the table.
- For split tables, join panels by table, section and row identity, and continue headings
  across pages only when the page is identified as the same numbered table.

## 1911 tables (Volumes II-III)

- Analysis uses the reviewed page map, index and spans in
  `output/build_abs_1911_table_spans/`; contents-derived spans only generate candidates.
- The 108 accepted human decisions in
  `data/intermediate/page_inventory/abs_1911_manual_page_overrides.csv` outrank model and
  source-inspection records. The local QA dashboard writes a separate decision layer and
  makes no API calls.
- Dwellings PDF page 186's printed `69` is a numbering anomaly inside indexed Table 68;
  page 149 is Table 65 (counties), not LGA data; LGA data is Table 68. Table 68 keeps its
  acres-versus-square-miles units explicit and never shares one area heading.
- Dwellings workbook: one worksheet per contents-indexed table, source strings not
  reconstructed numeric types, no summary/QA sheets; `dwellings_numeric_checked.xlsx`
  keeps visible formula checks. Rebuilds are deterministic (pinned runtime, hashed inputs,
  code and outputs).

## Paid extraction

- Pilot table-cell extraction: DeepSeek V4.1 Flash, US$5 ceiling, exploratory only.
- 1911 Dwellings source-region extraction: OpenRouter GPT-6 Luna, cumulative project spend
  raised to US$20, US$0.50 reserved per unknown charge; the US$8.35 of holds was released
  without asserting zero provider charges. No other document inherits paid permission.
- OpenCode Go first while Zen overage is disabled; a Go HTTP 402 does not authorise paid
  fallback. Azure regional Luna route for Dwellings only; pause on upstream 429 rather than
  spending unknown-charge reserves, and never re-pay for a page whose mapping was later
  corrected.

## Historical maps

- First GIS target: 1911 NSW local government areas (municipalities and shires); ward
  extraction is deferred. Approved trial mapping: GDA2020 / MGA zone 56.
- Keep scans unchanged in `data/raw/historical_boundary_maps/`; manifests carry source URLs,
  catalogue dates, dimensions and hashes. Prioritise external LGA boundaries; add ward maps
  only where they also carry LGA perimeter evidence.
- Keep editions and copies distinct, and keep proposed, parish, county, planning and native
  digital exports as separate kinds. Check dates before joining boundaries to census areas;
  a publication date is not a boundary date.
- City of Sydney extracts: "1901 onwards" includes the regime active at 1901 (council period
  from 1870-1908); the layer does not supply standalone pre-absorption polygons for
  surrounding municipalities.

## Census LGA panels (NSW and other states, 1911-1981)

- Use published census LGAs up to the 1981 digital endpoint (official ABS GeoPackage).
- Keep council type in keys; merge statistical parts to whole councils; flag date conflicts
  and non-council units. The full census-year roster is the map-audit denominator; name
  review and individual-outline checks stay visible.
- Sydney follows each census's published metropolitan/statistical region: include whole
  intersecting councils, flag published parts, never impose a modern footprint or the
  separate Outer Sydney division.
- Other states use the same source family - census volumes for rosters, census plates for
  candidate maps - and every row links to a map source. NT and ACT rows are published
  divisions and districts, not councils (`unit_class` records this); where a source has no
  map (ACT 1911/1921/1961) the gap is recorded, not substituted.
- Rebuild with `explore/2026-10-16_download-other-states-lga-census-maps.py` then
  `explore/2026-10-16_other-states-lga-census-panel.py`. The 1976 LGA bulletins carry no
  data; the ANU preliminary volumes are the 1976 source. OCR bounds the rosters: names are
  flagged for review, OCR variants merge by edit distance, counts are a lower bound.

## Map digitisation readiness (17 October 2026)

- 240 candidate plates rated A-D with blockers and a named better source.
- Rescues registered: 1954 and 1961 Statistician's Report series, 1971 field-count
  metropolitan maps, 1966 territory maps from ANU field counts, 1966 Tasmania Bulletin 6.8.
- Open gaps: 1911 statewide municipal maps for VIC/QLD/SA/WA/TAS are not digitised anywhere
  reachable; 1966 VIC/QLD/SA/WA stay low resolution. 1981 needs no tracing, because the
  GeoPackage already carries the geometry.
