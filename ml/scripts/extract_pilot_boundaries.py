import pyogrio
import geopandas as gpd
from pathlib import Path

source = Path("ml/dataset/geospatial/north-eastern-zone.gpkg")
output = Path("ml/outputs/pilot_district_boundaries.gpkg")

layer = "gis_osm_adminareas_a_free"

df = pyogrio.read_dataframe(source, layer=layer)

districts = ["Darrang", "Udalguri", "Kamrup Metropolitan"]

selected = df[df["name"].isin(districts) & (df["fclass"] == "admin_level5")].copy()

print("Selected districts:")
print(selected[["name", "fclass"]])

if set(selected["name"]) != set(districts):
    raise ValueError("One or more pilot district boundaries are missing.")

selected.to_file(output, driver="GPKG")

print(f"\nSaved boundaries to: {output}")
print(f"Total features: {len(selected)}")
