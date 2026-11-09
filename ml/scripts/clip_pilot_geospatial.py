import pyogrio
import geopandas as gpd
from pathlib import Path

source = Path("ml/dataset/geospatial/north-eastern-zone.gpkg")
boundary_file = Path("ml/outputs/pilot_district_boundaries.gpkg")
output_dir = Path("ml/outputs/pilot_geospatial")

output_dir.mkdir(parents=True, exist_ok=True)

boundaries = pyogrio.read_dataframe(boundary_file)

layers = {
    "roads": "gis_osm_roads_free",
    "buildings": "gis_osm_buildings_a_free",
    "waterways": "gis_osm_waterways_free",
    "water_bodies": "gis_osm_water_a_free",
    "places": "gis_osm_places_free",
}

for name, layer in layers.items():
    print(f"\nProcessing {name}...")

    data = pyogrio.read_dataframe(source, layer=layer)

    # Match coordinate systems
    if data.crs != boundaries.crs:
        data = data.to_crs(boundaries.crs)

    # Spatially filter features to the combined pilot district area
    pilot_area = boundaries.geometry.union_all()
    clipped = data[data.geometry.intersects(pilot_area)].copy()

    output = output_dir / f"pilot_{name}.gpkg"
    clipped.to_file(output, driver="GPKG")

    print(f"Features saved: {len(clipped)}")
    print(f"Output: {output}")

print("\nAll pilot GIS layers processed.")
