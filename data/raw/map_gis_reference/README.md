# Strathfield map reference snapshots

Unchanged public NSW Spatial Services responses saved on 10 October 2026 for
the historical-map GIS pilot. These are modern road references, not historical
LGA boundaries.

- `strathfield_roads_2026-10-10.json`: 371 road segments returned by
  [RoadSegment layer 5](https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Transport_Theme_multiCRS/MapServer/5).
- `strathfield_roads_request.json`: exact endpoint and query parameters.
  The bounding box is in GDA2020 longitude/latitude; output is GDA2020 / MGA
  zone 56 (EPSG:7856). The named-road filter deliberately selects a subset.
  The saved response does not report a transfer-limit overflow.
- `nsw_roadsegment_layer.json`: source schema and metadata snapshot.

The first broader discovery query exceeded the service limit and was not used.
The narrower saved query is complete for its filter. Current road positions
do not prove that every historic intersection occupied exactly the same place.

Trial inputs record the response SHA-256 and the OBJECTIDs behind each control
point. Original maps remain in `data/raw/historical_boundary_maps/`.
