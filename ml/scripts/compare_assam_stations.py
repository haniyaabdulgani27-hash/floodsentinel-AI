import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT = BASE_DIR / "dataset" / "rwl_tel_hr_assam_999_2021_2025.csv"

df = pd.read_csv(INPUT)

TIME_COL = "Data Acquisition Time"
LEVEL_COL = "River Water Level Telemetry Hourly (meter)"

df["Timestamp"] = pd.to_datetime(
    df[TIME_COL].astype(str).str.strip(), format="%d-%m-%Y %H:%M", errors="coerce"
)

df["Water_Level"] = pd.to_numeric(df[LEVEL_COL], errors="coerce")

df = df.dropna(subset=["Station", "Timestamp", "Water_Level"]).copy()

print("=" * 70)
print("ASSAM THREE-STATION COMPARISON")
print("=" * 70)

# --------------------------------------------------
# 1. STATION SUMMARY
# --------------------------------------------------

print("\n1. STATION SUMMARY")

for station, group in df.groupby("Station"):

    print("\n" + "-" * 60)
    print("STATION:", station)
    print("District:", group["District"].iloc[0])
    print("Rows:", len(group))
    print("Start:", group["Timestamp"].min())
    print("End:", group["Timestamp"].max())

    print("\nWater-level statistics:")
    print(group["Water_Level"].describe())

    print("\nMost frequent readings:")
    print(group["Water_Level"].value_counts().head(10).to_string())

# --------------------------------------------------
# 2. MONTHLY COMPARISON
# --------------------------------------------------

df["Month"] = df["Timestamp"].dt.to_period("M").astype(str)

monthly = (
    df.groupby(["Station", "Month"])
    .agg(
        Records=("Water_Level", "count"),
        Mean=("Water_Level", "mean"),
        Median=("Water_Level", "median"),
        Minimum=("Water_Level", "min"),
        Maximum=("Water_Level", "max"),
        Unique_Readings=("Water_Level", "nunique"),
    )
    .reset_index()
)

monthly.to_csv(
    BASE_DIR / "results" / "assam_station_monthly_comparison.csv", index=False
)

print("\n\n2. MONTHLY COMPARISON")
print(monthly.to_string(index=False))

# --------------------------------------------------
# 3. SUDDEN CHANGES
# --------------------------------------------------

print("\n\n3. SUDDEN CHANGES ABOVE 5 METRES")

for station, group in df.groupby("Station"):

    group = group.sort_values("Timestamp").drop_duplicates(subset=["Timestamp"]).copy()

    group["Change"] = group["Water_Level"].diff()

    changes = group[group["Change"].abs() > 5]

    print("\nStation:", station)
    print("Number of changes:", len(changes))

    if not changes.empty:
        print(changes[["Timestamp", "Water_Level", "Change"]].to_string(index=False))

# --------------------------------------------------
# 4. CORRECT SUB-HOURLY INTERVAL AUDIT
# --------------------------------------------------

print("\n\n4. SUB-HOURLY INTERVAL CHECK")

for station, group in df.groupby("Station"):

    timestamps = group["Timestamp"].drop_duplicates().sort_values()

    gaps = timestamps.diff().dt.total_seconds() / 60

    sub_hourly = gaps[gaps.notna() & (gaps < 60)]

    print("\nStation:", station)
    print("Intervals below 60 minutes:", len(sub_hourly))
    print("Most frequent sub-hourly intervals:")
    print(sub_hourly.value_counts().head(10).to_dict())

print("\nComparison completed.")
