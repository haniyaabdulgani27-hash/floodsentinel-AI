import geopandas as gpd
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

SOURCE = BASE / "dataset/geospatial/north-eastern-zone.gpkg"
BOUNDARY = BASE / "outputs/pilot_district_boundaries.gpkg"
OUTPUT = BASE / "outputs/candidate_facilities.csv"

facilities = gpd.read_file(SOURCE, layer="gis_osm_pois_free")

districts = gpd.read_file(BOUNDARY)

categories = [
    "school",
    "college",
    "university",
    "hospital",
    "community_centre",
    "shelter",
    "fire_station",
    "police",
]

facilities = facilities[facilities["fclass"].isin(categories)].copy()

if facilities.crs != districts.crs:
    facilities = facilities.to_crs(districts.crs)

results = []

for _, district in districts.iterrows():
    boundary = district.geometry

    selected = facilities[facilities.geometry.intersects(boundary)].copy()

    selected["district"] = district["name"]
    results.append(selected)

if results:
    final = gpd.GeoDataFrame(pd.concat(results, ignore_index=True), crs=districts.crs)

    final["name"] = final["name"].fillna("Unnamed facility")

    final.drop(columns="geometry").to_csv(OUTPUT, index=False)
    final["longitude"] = final.geometry.x
    final["latitude"] = final.geometry.y

    final.to_file(BASE / "outputs/candidate_facilities.gpkg", driver="GPKG")

    print("Facilities by district:")
    print(final.groupby(["district", "fclass"]).size().to_string())

    print("\nTotal candidate facilities:", len(final))
    print("Saved:", OUTPUT)

else:
    print("No matching facilities found.")
