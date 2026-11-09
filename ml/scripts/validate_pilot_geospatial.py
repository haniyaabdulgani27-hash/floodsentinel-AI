import geopandas as gpd
from pathlib import Path

folder = Path("ml/outputs/pilot_geospatial")

for file in sorted(folder.glob("*.gpkg")):
    print(f"\n{'='*50}")
    print("FILE:", file.name)

    df = gpd.read_file(file)

    print("Features:", len(df))
    print("CRS:", df.crs)
    print("Geometry types:")
    print(df.geometry.geom_type.value_counts().to_dict())
    print("Missing geometries:", df.geometry.isna().sum())
    print("Invalid geometries:", (~df.geometry.is_valid).sum())

print("\nValidation completed.")
