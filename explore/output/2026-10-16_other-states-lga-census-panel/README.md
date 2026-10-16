# Other-state census LGA roster and map-gap panel

Published census local government areas for Victoria, Queensland, South Australia, Western
Australia, Tasmania, the Northern Territory and the Australian Capital Territory, 1911–1981,
in the same shape as the NSW panel. Every roster row links to a candidate map source for its
state and census year.

Rebuild from the repository root (requires Python, PyMuPDF and Pillow):

```bash
python3 explore/2026-10-16_download-other-states-lga-census-maps.py   # raw sources (resumable)
python3 explore/2026-10-16_detect-map-plates.py                       # plate inventory (optional refresh)
python3 explore/2026-10-16_other-states-lga-census-panel.py           # panel build
```

| Census | VIC | QLD | SA | WA | TAS | NT | ACT | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1911 | 246 | 171 | 153 | 55 | 58 | 0 | 0 | 683 |
| 1921 | 154 | 152 | 171 | 100 | 71 | 0 | 0 | 648 |
| 1933 | 153 | 147 | 158 | 154 | 25 | 0 | 0 | 637 |
| 1947 | 148 | 132 | 88 | 136 | 34 | 0 | 0 | 538 |
| 1954 | 136 | 93 | 129 | 96 | 45 | 0 | 0 | 499 |
| 1961 | 192 | 121 | 54 | 97 | 28 | 44 | 0 | 536 |
| 1966 | 221 | 141 | 145 | 151 | 63 | 77 | 67 | 865 |
| 1971 | 148 | 94 | 33 | 102 | 14 | 27 | 57 | 475 |
| 1976 | 361 | 187 | 52 | 166 | 67 | 6 | 122 | 961 |
| 1981 | 210 | 139 | 134 | 144 | 47 | 4 | 130 | 808 |

6,650 rows; 59 state-year pairs; 5,266 rows flagged for OCR name review. NT and ACT rows are
published divisions and districts, not municipal councils (`unit_class` records this).
Counts are a lower bound where OCR loses rows (1954/1961 SA and 1961/1971 TAS are the weakest).

## Outputs

- `lga_census_panel.csv`: one row per published unit and census year, with source page,
  published type, unit class, OCR review flag, merged name variants, the linked map source
  (`map_source_id`, `map_source_pdf`, `map_pdf_pages`) and, for 1954 and 1961, an alternate
  national Statistician's Report plate (`map_source_alternate_id`, `map_source_alternate_file`,
  `map_pdf_pages_alternate`).
- `census_year_state_summary.csv`: row counts by state and census year plus the map source.
- `map_source_candidates.csv`: candidate map sources per state-year (statewide plates,
  metropolitan plates, national-report plates, 1971 Bulletin 13 sheets), with plate page lists
  and evidence notes. 88 of 91 rows carry plate pages; the three without are the ACT in 1911,
  1921 and 1961 (no ACT LGA map exists in those sources).
- `map_plate_inventory.csv`, `map_plate_ocr.txt`: every candidate plate page found by the
  detector with OCR of the plate title, kept as the audit trail for the page lists.
- `coverage_vs_1981_geopackage.csv`: 1981 panel names matched against the ABS 1981 GeoPackage
  whole-LGA names (edit distance ≤ 2): VIC 202/210 (96%), QLD 133/134 (99%), SA 123/128 (96%),
  WA 135/138 (98%), TAS 47/49 (96%).
- `name_review_queue.csv`: rows whose names come from OCR and need checking against the scan.
- `status.json`, `verification.json`, `panel_build.log`: build state and checks.

## Digitisation readiness

Every candidate plate is rated A-D for digitisation likelihood, with blockers and a named
better candidate where one exists:
[`map digitisation readiness`](../2026-10-17_map-digitisation-readiness/README.md).
## Rules and limits

- Rosters come from the census publications for each year, not modern reconstructions.
  Methods differ by publication generation: 1911 national table 68 and table 65; 1921–1947
  national Statistician's Report tables; 1954 and 1961 printed index of cities, towns,
  boroughs and shires; 1966 state volumes; 1971 Field Count Statements; 1976 ANU preliminary
  volumes; 1981 state bulletins plus the 1981 GeoPackage for the digital check.
- Every row carries the map source for its state-year. Plate pages were identified by image
  geometry and OCR of plate titles. Individual full-LGA outlines remain **not audited**;
  feature presence is not verified geometry. No completeness percentage is claimed.
- The 1911, 1921, 1933 and 1947 maps are national Statistician's Report plates; the 1911
  statewide plates show counties, census districts or statistical districts in some states,
  not complete municipal polygons, and provincial municipalities can be point symbols.
  Provincial coverage is therefore weaker than the metropolitan plates for those years.
- 1976 LGA bulletins (catalogue 24270–24340) are example-table bulletins with no LGA rows and
  no maps; the ANU preliminary volumes are the 1976 roster and map source.
- OCR noise is real, especially in the 1976 ANU scans and the 1971 field count statements.
  Variants within edit distance 1 (2 for long names) are merged and listed in
  `name_alternates`; obvious OCR debris is dropped before assembly.
- Seek independent review before using this panel in report claims.
