# Candidate map digitisation readiness

Ratings for all 263 candidate census map plates held for the NSW panel (29 usable) and the other-state panel:
how likely it can be digitised, what blocks it, and the better source where one was found or is
needed. **176 plates are rated A/B (digitisation-ready) and 161 of those carry local
government or statistical-area polygons** (the rest are index pages, county/district plates or
NT/ACT district sheets). Plates were rendered and inspected; the metrics and the judgements are reproducible.

Rebuild from the repository root:

```bash
python3 explore/2026-10-17_measure-map-plates.py   # resolution, colour, contrast per plate
python3 explore/2026-10-17_rate-map-plates.py      # ratings, blockers, better candidates
```

## Rating scale

- **A (107 plates)** — digitise now: LGA boundary line work with a printed key, enough resolution
  (short edge 1800 px or more), coastline/river/town references and a scale bar.
- **B (69)** — digitiable with care: legible boundaries but moderate resolution, colour
  separation needed, or extra line work (railways, statistical divisions) to separate.
- **C (82)** — hard: low resolution, ambiguous boundary type, or hatching obscures the lines.
  Tracing would be unreliable without a better scan.
- **D (5)** — not digitiable as LGA polygons: no boundary line work (counties, statistical
  districts, printed index pages) or point symbols only.

| Census | Plates | A | B | C | D | Comment |
|---|---:|---:|---:|---:|---:|---|
| 1911 | 12 | 0 | 1 | 8 | 3 | Statewide plates are 375–600 px: too coarse. Only the Sydney plate is usable. |
| 1921 | 14 | 11 | 2 | 0 | 1 | Statewide LGA index plates at 2067–3541 px with numbered councils. |
| 1933 | 13 | 2 | 9 | 2 | 0 | 992–2176 px; boundaries clear, Victoria the sharpest. |
| 1947 | 13 | 11 | 0 | 2 | 0 | 1520–2848 px; the strongest early series. |
| 1954 | 40 | 1 | 29 | 10 | 0 | Statistician's Report plates (1127–2176 px) beat the small colour state plates. |
| 1961 | 38 | 28 | 4 | 6 | 0 | National report plates (1810–2176 px) are the better scan for every state. |
| 1966 | 47 | 0 | 10 | 37 | 0 | Regional series 288–1749 px; no larger copies held except NSW (ANU). |
| 1971 | 18 | 13 | 4 | 1 | 0 | Field Count Statement metro maps 3500×4960 px with LGA boundary keys. |
| 1976 | 22 | 12 | 10 | 0 | 0 | ANU preliminary sheets 1792–3600 px monochrome with council names. |
| 1981 | 23 | 20 | 3 | 0 | 0 | 2496–5824 px; and the ABS 1981 GeoPackage removes the need to trace at all. |

## Unlikely to digitise, and the better candidate

| Weak candidate | Rating | Problem | Better candidate |
|---|---|---|---|
| 1911 VIC statewide (PDF 445) | D | 500×375 px | Not held. Needs the Victorian municipal map of 1911 (Lands Department or a library scan); the ABS has no digitised Victorian Year Book for 1911. |
| 1911 QLD/SA/WA/TAS statewide + metropolitan plates | C | 563–600 px | Not held. Digitised state year books start later (Queensland 1937 onward, catalogue 1301.3); state statistical registers are not digitised. |
| 1911 NT | D | no LGA polygons exist | none needed — the 1911 panel has no NT councils. |
| 1921 NT (PDF 406), 1933/1947 NT and ACT plates | C/D | districts only, no councils | none needed for LGA digitising; keep for district context. |
| 1954 VIC statewide (state volume p158, report PDF 431) | C | 483–976 px | No sharper plate held. |
| 1954 QLD/SA/WA/TAS state-volume plates | C | 480–1125 px colour | 1954 Statistician's Report plates PDF 433/435/437/439 (1760–2176 px, complete series 429–447). |
| 1961 all state-volume plates | C | 728–1144 px colour | 1961 Statistician's Report plates PDF 501–519 (1810–2176 px). |
| 1961 NT and ACT | — | no maps in the territory volumes | 1961 Statistician's Report plate PDF 513 (NT and ACT panels). |
| 1966 VIC/QLD/SA/WA regional series | C | 288–1749 px | None found: ABS Bulletins No 2.8/3.8/5.8 duplicate the series at the same resolution; ANU holds larger copies for NSW only. |
| 1966 TAS statewide (p158) | B | 1674 px | ABS Bulletin No 6.8 page 16 (2161 px) — registered as an alternate. |
| 1966 NT and ACT | — | Volume 4 Part 7 has no maps | ANU Field Count Statements: NT police districts (No 12, 3240 px) and ACT administrative divisions (No 5, 2712 px). Registered for 1966. |
| 1971 statewide sheets (Bulletin 13, colour) | B/C | 878–2897 px; statistical and LGA lines share colour fills | Field Count Statement metropolitan maps: Melbourne PDF 32, Brisbane 31, Adelaide 26, Hobart 17 (3500×4960 px monochrome, explicit LGA boundary key). Registered for 1971. No field-count map was found for WA, NT or the ACT; the Bulletin 13 sheets remain their candidates. |
| 1976 statistical-division sheets | B | divisions, not LGAs | Use the detailed LGA sheets in the same ANU volume. |
| 1981 plates generally | A/B | urban shading largely lost in the monochrome scans | The official 1981 ABS GeoPackage already supplies digital geometry for every state (no tracing needed): `data/raw/nsw_lga_census_panel/census1981.gpkg`. |
| NSW 1954 (p196), 1961 (p131), 1966 (509–520), 1971 sheet | C | 845–946 px | Already-held alternatives: SLNSW 1954 JPG (8405×9891 px), ANU 1961 Sydney JPG (7884×8611 px), ANU 1966 Bulletin 1.8 (2024×3088 px), 1971 Field Count Statement No 3 sheets. |

## Files

- `digitisation_readiness.csv`: one row per plate — source, page, native size, contrast, rating,
  rating basis, digitisation target (statewide / metropolitan / districts / not-LGA) and the
  better candidate.
- `summary_by_year.csv`: plate counts by rating for each census year and scope.
- `plate_metrics.csv`: measured resolution, page size, colour mode, contrast, text-layer map cues.

## Limits

- Ratings are plate-level judgements from rendering every candidate plate; they are not
  digitisation attempts, and no geometric accuracy is claimed.
- `digitisation_target` records what a plate can supply: statewide LGA polygons, metropolitan
  polygons only, or published districts that are not councils.
- Where the better candidate is a plate already in `data/raw/`, the two panels link it; where the
  table says "not held", the source still has to be acquired.
