import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BASE_DIR / "dataset" / "rwl_tel_hr_assam_999_2021_2025.csv"

STATION = "NH15 Crossing Fakirpara Tangni"
TIME_COL = "Data Acquisition Time"
LEVEL_COL = "River Water Level Telemetry Hourly (meter)"

print("=" * 65)
print("FAKIRPARA TIMESTAMP RE-AUDIT")
print("=" * 65)

df = pd.read_csv(CSV_PATH, low_memory=False)

station_df = df[df["Station"].astype(str).str.strip() == STATION].copy()

# Parse using the confirmed source format: DD-MM-YYYY HH:MM
station_df["Parsed_Time"] = pd.to_datetime(
    station_df[TIME_COL].astype(str).str.strip(),
    format="%d-%m-%Y %H:%M",
    errors="coerce",
)

station_df["Water_Level"] = pd.to_numeric(station_df[LEVEL_COL], errors="coerce")

valid_time = station_df["Parsed_Time"].notna()
valid_level = station_df["Water_Level"].notna()

print("\n1. TIMESTAMP PARSING")
print("-" * 65)
print("Raw rows:", len(station_df))
print("Valid timestamps:", valid_time.sum())
print("Failed timestamps:", (~valid_time).sum())
print("Parsing success:", round(valid_time.mean() * 100, 2), "%")

print("\nFailed timestamp examples:")
print(station_df.loc[~valid_time, TIME_COL].head(20).to_string(index=False))

print("\n2. WATER LEVELS")
print("-" * 65)
print("Valid readings:", valid_level.sum())
print("Missing readings:", (~valid_level).sum())
print(station_df["Water_Level"].describe())

print("\n3. VALID TIME + LEVEL COMBINATIONS")
print("-" * 65)
print("Both valid:", (valid_time & valid_level).sum())
print("Valid level, invalid time:", ((~valid_time) & valid_level).sum())
print("Valid time, missing level:", (valid_time & (~valid_level)).sum())

# Only rows with valid timestamps are used for duplicate analysis
valid_df = station_df.loc[valid_time].copy()

counts = valid_df.groupby("Parsed_Time").size()

print("\n4. DUPLICATE TIMESTAMPS")
print("-" * 65)
print("Unique timestamps:", len(counts))
print("Duplicate timestamp groups:", (counts > 1).sum())
print("\nGroup size distribution:")
print(counts.value_counts().sort_index())

# Identify timestamp groups containing different readings
unique_readings = valid_df.groupby("Parsed_Time")["Water_Level"].nunique(dropna=True)

conflicts = unique_readings[unique_readings > 1]

print("\n5. CONFLICTING READINGS")
print("-" * 65)
print("Conflicting timestamp groups:", len(conflicts))

for timestamp in conflicts.head(30).index:
    print(f"\n{timestamp}")
    print(
        valid_df.loc[
            valid_df["Parsed_Time"] == timestamp, [TIME_COL, LEVEL_COL]
        ].to_string(index=False)
    )

print("\n6. EXTREME READINGS ABOVE 100 METRES")
print("-" * 65)

extreme = valid_df[valid_df["Water_Level"] > 100]

print("Count:", len(extreme))

if len(extreme):
    print(extreme[[TIME_COL, LEVEL_COL]].to_string(index=False))

print("\n7. DATE RANGE")
print("-" * 65)
print("First:", valid_df["Parsed_Time"].min())
print("Last:", valid_df["Parsed_Time"].max())

print("\n" + "=" * 65)
print("RE-AUDIT COMPLETE — NO FILES MODIFIED")
print("=" * 65)
