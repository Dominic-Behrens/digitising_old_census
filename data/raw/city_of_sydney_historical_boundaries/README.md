# City of Sydney historical boundaries

Downloaded from City of Sydney public ArcGIS Feature Services on 2026-06-19.

These are source extracts for historical City of Sydney council and ward
boundaries relevant from 1901 onwards. The first records in each extract may
start before 1901 because they are the boundary regimes active at 1901.

## Files

- `historic_council_boundaries_1901_onwards.geojson`: City of Sydney council
  boundary polygons where `DateOrder >= 2`, covering `1870-1908` through
  `2004-present`.
- `historic_ward_boundaries_1901_onwards.geojson`: ward boundary polygons with
  `Date_Order` in `3` to `11`, covering the ward regimes active at/after 1901.
- `historic_ward_assessment_books_1901_onwards.json`: related assessment book
  table records where `Assessment_Book_Year >= '1901'`.
- `*_metadata.json`: ArcGIS item, service, layer, or table metadata captured at
  download time.

## Sources

- Historic council boundaries Feature Service:
  `https://services1.arcgis.com/cNVyNtjGVZybOQWZ/arcgis/rest/services/Historical_Atlas_of_Sydney/FeatureServer`
- Historic ward boundaries Feature Service:
  `https://services1.arcgis.com/cNVyNtjGVZybOQWZ/arcgis/rest/services/HistoricWardBoundaries_A/FeatureServer`

Both source items are marked as City of Sydney Open Data under CC BY 4.0.

## Notes

- The council dataset provides City of Sydney LGA boundary regimes, not all
  separate inner-Sydney municipalities before they were absorbed.
- The ward dataset includes a related assessment-book table, useful if dwelling
  digitisation later links to City assessment books.
