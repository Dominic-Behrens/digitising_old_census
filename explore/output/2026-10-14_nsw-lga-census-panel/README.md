# NSW census LGA roster and map-gap panel

Published NSW census LGAs, 1911–1981: all ten rosters extracted, 2,558 council-year rows. 1981 is the first official historical digital boundary edition found and downloaded in this work. It is a working cutoff, not proof that no earlier digital edition exists.

Rebuild from the repository root:

Requires Python, PyMuPDF and Shapely 2 or later.

```bash
python3 explore/2026-10-14_nsw-lga-census-panel.py
```

In WSL, pass `--project-root` with the writable lowercase mount spelling if needed. The tested command is in `status.json`. The builder uses original census PDFs, the reviewed 1911 extraction, the retained historical source-row CSV and the official 1981 GeoPackage. OCR tools and image crops in this output folder were extraction aids; the rebuild does not require them.

| Census | Council rows |
|---|---:|
| 1911 | 324 |
| 1921 | 321 |
| 1933 | 319 |
| 1947 | 289 |
| 1954 | 241 |
| 1961 | 225 |
| 1966 | 224 |
| 1971 | 225 |
| 1976 | 214 |
| 1981 | 176 |

Outputs:

- `nsw_lga_census_panel.csv`: one row per council and census, with source page, published geography date and review/conflict flags.
- `census_year_priorities.csv`: roster counts and next action by year.
- `council_gap_priorities.csv`: council-level map work queue. Early municipal outlines rank first because statewide historical maps often use municipal point symbols. A priority is an audit action, not proof that a boundary is missing.
- `name_review_queue.csv`: five rosters retained for further independent name checks. Extraction counts and sequence checks do not prove every label correct.
- `non_council_units.csv`: identified unincorporated and non-spatial units, excluded from council counts. Special-unit inventory remains incomplete for some years.
- `digital_label_conflicts.csv`: 13 published 1981 labels that differ from the digital layer.
- `status.json`, `verification.json`: extraction progress and verification evidence.

Rules and limits:

- Keep council type in the key. Same names can denote separate municipality/shire councils. No stable identity across years is inferred.
- Merge statistical parts to whole councils; retain their source references. Use contemporary rosters, not retrospective columns restated on later boundaries.
- Historical headings sometimes include cities within municipalities. Type records the publication's category, not a reconstructed legal classification.
- Missing geography dates remain blank. Keep the 1954 notes/map-date conflict and the 1981 January boundary date separate from census night.
- All individual map outlines remain not audited. Digital feature presence is not verified geometry. No map-completeness percentage is calculated.
- Full source-row name review remains open for 1921, 1933, 1947, 1954 and 1966. Numbered roster sequences are complete for 1921, 1933, 1947, 1976 and 1981; the 1961 total matches published notes.

See `data-notes.md` for source locations and caveats. Seek independent review before using this provisional panel in report claims.


## Digitisation readiness

Candidate plates for each NSW census are rated A-D for digitisation likelihood in
[`map digitisation readiness`](../2026-10-17_map-digitisation-readiness/README.md) (NSW rows
cover the statewide and Sydney plates, with the sharpest held alternatives named).

## Sydney map panel

The panel uses each census's published Sydney metropolitan/statistical region, including whole councils that intersect it and flagging council parts. It has 424 council-year entries across all ten censuses. Counts in year order: 42, 42, 50, 50, 35, 35, 40, 41, 45, 44. The separate 1971 Outer Sydney division is excluded; Gosford–Wyong enters the published Sydney SD by 1976. This is a changing footprint, so counts and totals are not directly comparable on a fixed geography.

- `sydney_lga_census_panel.csv`: council roster, published region/part flags, primary and preferred map sources, date/type/label conflicts and next action.
- `sydney_census_year_summary.csv`: counts and map pages by census. Blank verified-outline counts mean unknown. Digital feature counts are features exported into this panel, not a global availability claim.
- `sydney_map_source_candidates.csv`: ten census report map sources plus two higher-resolution census maps. Preferred 1954/1961 JPGs are already in raw; the preview uses the report plates.
- `sydney_map_preview.pdf`: 11 annotated source pages for ten censuses, including both 1976 panels. Sources stay unchanged in raw. No georeferencing or historical digitisation performed.
- `sydney_lga_1981.gpkg`: 44 whole-LGA polygons in layer `sydney_lga_1981`, original ABS EPSG:4283 geometry. Original digital labels and separate published labels are retained. The published boundary date is 1 January 1981; digital legal-date/identity checks remain open.
- `sydney_1981_geometry_audit.json`: per-feature validity, extent and label checks. All 44 are non-empty and valid; Gosford/Cosford is the one label conflict. These checks do not establish exact boundary accuracy.

Twelve entries represent councils only partly in Sydney; verify full-LGA outlines outside the region before tracing. All historical geometry remains not digitised, and individual full outlines remain not audited. Seek independent review before report use.
