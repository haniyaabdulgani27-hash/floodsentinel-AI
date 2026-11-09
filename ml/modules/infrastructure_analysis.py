from pathlib import Path
import geopandas as gpd
import pandas as pd

BASE = Path("ml/outputs")
GIS = BASE / "pilot_geospatial"

BOUNDARIES = BASE / "pilot_district_boundaries.gpkg"


def calculate_infrastructure_summary():
    districts = gpd.read_file(BOUNDARIES)

    buildings = gpd.read_file(GIS / "pilot_buildings.gpkg")
    roads = gpd.read_file(GIS / "pilot_roads.gpkg")

    # Use a projected CRS so road lengths and areas use metres.
    districts = districts.to_crs("EPSG:32646")
    buildings = buildings.to_crs("EPSG:32646")
    roads = roads.to_crs("EPSG:32646")

    results = []

    for _, district in districts.iterrows():
        name = district["name"]
        boundary = district.geometry

        district_buildings = buildings[buildings.geometry.intersects(boundary)]

        district_roads = roads[roads.geometry.intersects(boundary)]

        road_length_km = (
            district_roads.geometry.intersection(boundary).length.sum() / 1000
        )

        results.append(
            {
                "district": name,
                "building_footprints": len(district_buildings),
                "road_segments": len(district_roads),
                "road_length_km": round(road_length_km, 2),
            }
        )

    summary = pd.DataFrame(results)

    output = BASE / "infrastructure_summary.csv"
    summary.to_csv(output, index=False)

    return summary


if __name__ == "__main__":
    result = calculate_infrastructure_summary()
    print(result.to_string(index=False))
    print("\nSaved: ml/outputs/infrastructure_summary.csv")
