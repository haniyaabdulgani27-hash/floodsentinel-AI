import pandas as pd
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "dataset" / "assam_river_levels_cleaned.csv"
OUTPUT_PATH = BASE_DIR / "dataset" / "fakirpara_hourly.csv"

# Actual column names from the CSV
STATION_COL = "Station"
TIME_COL = "Data Acquisition Time"
LEVEL_COL = "River Water Level Telemetry Hourly (meter)"

# Load data
df = pd.read_csv(DATA_PATH)

# Select Fakirpara Tangni station
df = df[
    df[STATION_COL].astype(str).str.contains("Fakirpara", case=False, na=False)
].copy()

# Convert timestamp and water level
df[TIME_COL] = pd.to_datetime(df[TIME_COL], errors="coerce")
df[LEVEL_COL] = pd.to_numeric(df[LEVEL_COL], errors="coerce")

# Keep valid records
df = df[(df["Data_Quality"] == "Valid") & df[TIME_COL].notna() & df[LEVEL_COL].notna()]

# Sort chronologically
df = df.sort_values(TIME_COL)

# Group duplicate timestamps using median
series = df.groupby(TIME_COL)[LEVEL_COL].median().sort_index()

# Resample to hourly intervals; don't fill missing hours
hourly = series.resample("1h").mean()

# Save
hourly_df = hourly.rename("Water_Level").reset_index()
hourly_df.to_csv(OUTPUT_PATH, index=False)

print("\nFAKIRPARA DATA PREPARATION COMPLETE")
print("-----------------------------------")
print("Output file:", OUTPUT_PATH)
print("Hourly rows:", len(hourly_df))
print("Available readings:", hourly_df["Water_Level"].notna().sum())
print("Missing hourly readings:", hourly_df["Water_Level"].isna().sum())

print("\nFirst five rows:")
print(hourly_df.head())

print("\nLast five rows:")
print(hourly_df.tail())
