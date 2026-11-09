import pandas as pd
import numpy as np
from pathlib import Path

# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = BASE_DIR / "dataset" / "rwl_tel_hr_assam_999_2021_2025.csv"

OUTPUT_DIR = BASE_DIR / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

STATION = "NH15 Crossing Fakirpara Tangni"

TIME_COL = "Data Acquisition Time"
LEVEL_COL = "River Water Level Telemetry Hourly (meter)"

# --------------------------------------------------
# LOAD ORIGINAL DATA
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

station_df = df[df["Station"] == STATION].copy()

print("=" * 60)
print("FAKIRPARA DATA CLEANING")
print("=" * 60)

print("Original station rows:", len(station_df))

# Preserve original row number for auditing
station_df["Original_Row_ID"] = station_df.index

# --------------------------------------------------
# PARSE TIMESTAMPS AND WATER LEVELS
# --------------------------------------------------

station_df["Timestamp"] = pd.to_datetime(
    station_df[TIME_COL].astype(str).str.strip(),
    format="%d-%m-%Y %H:%M",
    errors="coerce",
)

station_df["Water_Level"] = pd.to_numeric(station_df[LEVEL_COL], errors="coerce")

# --------------------------------------------------
# IDENTIFY MISSING AND INVALID RECORDS
# --------------------------------------------------

station_df["Data_Quality"] = "Valid"

station_df.loc[station_df["Timestamp"].isna(), "Data_Quality"] = "Invalid_Timestamp"

station_df.loc[
    station_df["Water_Level"].isna() & station_df["Timestamp"].notna(), "Data_Quality"
] = "Missing_Level"

# --------------------------------------------------
# IDENTIFY EXTREME READINGS
# --------------------------------------------------

extreme_mask = station_df["Timestamp"].notna() & station_df["Water_Level"].gt(100)

station_df.loc[extreme_mask, "Data_Quality"] = "Review_Extreme"

# --------------------------------------------------
# IDENTIFY CONFLICTING TIMESTAMPS
# --------------------------------------------------

valid_timestamp = station_df[station_df["Timestamp"].notna()].copy()

timestamp_counts = valid_timestamp.groupby("Timestamp")["Water_Level"].nunique(
    dropna=True
)

conflict_timestamps = timestamp_counts[timestamp_counts > 1].index

conflict_mask = station_df["Timestamp"].isin(conflict_timestamps)

station_df.loc[conflict_mask, "Data_Quality"] = "Review_Conflict"

# --------------------------------------------------
# REMOVE EXACT DUPLICATE RECORDS
# --------------------------------------------------

before = len(station_df)

dedup_columns = ["Timestamp", "Water_Level"]

# Keep first copy of exact timestamp-level duplicates
station_df = station_df.drop_duplicates(subset=dedup_columns, keep="first").copy()

exact_duplicates_removed = before - len(station_df)

# --------------------------------------------------
# CREATE SEPARATE OUTPUTS
# --------------------------------------------------

# Full audit file: keeps all unique records and quality labels
audit_file = OUTPUT_DIR / "fakirpara_quality_audit.csv"

station_df.to_csv(audit_file, index=False)

# Model-ready candidate:
# only valid, non-conflicting, non-extreme observations
model_df = station_df[station_df["Data_Quality"] == "Valid"].copy()

model_df = model_df.sort_values("Timestamp")

model_file = OUTPUT_DIR / "fakirpara_model_candidate.csv"

model_df.to_csv(model_file, index=False)

# Conflicting records for manual inspection
conflict_file = OUTPUT_DIR / "fakirpara_conflicts.csv"

station_df[station_df["Data_Quality"] == "Review_Conflict"].to_csv(
    conflict_file, index=False
)

# Extreme records for manual inspection
extreme_file = OUTPUT_DIR / "fakirpara_extreme_readings.csv"

station_df[station_df["Data_Quality"] == "Review_Extreme"].to_csv(
    extreme_file, index=False
)

# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

print("\nCLEANING SUMMARY")
print("-" * 60)

print("Original rows:", before)
print("Exact duplicates removed:", exact_duplicates_removed)
print("Unique records remaining:", len(station_df))

print("\nQuality distribution:")
print(station_df["Data_Quality"].value_counts())

print("\nModel candidate rows:", len(model_df))

print("\nDate range:")
print("Start:", model_df["Timestamp"].min())
print("End:", model_df["Timestamp"].max())

print("\nOUTPUT FILES")
print("-" * 60)

print(audit_file)
print(model_file)
print(conflict_file)
print(extreme_file)

print("\nCleaning completed.")
print("Original dataset was not modified.")
