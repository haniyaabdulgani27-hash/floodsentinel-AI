import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

RAW_PATH = BASE_DIR / "dataset" / "rwl_tel_hr_assam_999_2021_2025.csv"
CLEAN_PATH = BASE_DIR / "dataset" / "assam_river_levels_cleaned.csv"

TIME = "Data Acquisition Time"
LEVEL = "River Water Level Telemetry Hourly (meter)"
STATION = "Station"


def inspect_file(path, label):
    df = pd.read_csv(path)

    print(f"\n{'=' * 60}")
    print(label)
    print("=" * 60)

    print("Total rows:", len(df))

    print("\nStation names and row counts:")
    print(df[STATION].value_counts(dropna=False).to_string())

    print("\nDistricts and row counts:")
    if "District" in df.columns:
        print(df["District"].value_counts(dropna=False).to_string())

    # Select Fakirpara records
    mask = df[STATION].astype(str).str.contains("Fakirpara", case=False, na=False)
    station_df = df[mask].copy()

    station_df[TIME] = pd.to_datetime(station_df[TIME], errors="coerce")
    station_df[LEVEL] = pd.to_numeric(station_df[LEVEL], errors="coerce")

    print("\nFakirpara audit:")
    print("Rows:", len(station_df))
    print("Valid timestamps:", station_df[TIME].notna().sum())
    print("Valid water levels:", station_df[LEVEL].notna().sum())
    print("Unique timestamps:", station_df[TIME].nunique())

    print("First timestamp:", station_df[TIME].min())
    print("Last timestamp:", station_df[TIME].max())

    print("\nFakirpara district counts:")
    print(station_df["District"].value_counts(dropna=False).to_string())

    print("\nFakirpara readings by year:")
    print(
        station_df.groupby(station_df[TIME].dt.year)[LEVEL]
        .agg(["count", "min", "median", "max"])
        .round(3)
        .to_string()
    )


inspect_file(RAW_PATH, "ORIGINAL DATASET")
inspect_file(CLEAN_PATH, "CLEANED DATASET")
