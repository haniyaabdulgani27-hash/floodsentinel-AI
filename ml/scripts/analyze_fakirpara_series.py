import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
INPUT = BASE_DIR / "results" / "fakirpara_model_candidate.csv"
OUTPUT = BASE_DIR / "results"

df = pd.read_csv(INPUT, parse_dates=["Timestamp"])
df = df.sort_values("Timestamp").reset_index(drop=True)

# --------------------------------------------------
# 1. BASIC CHECKS
# --------------------------------------------------

print("=" * 65)
print("FAKIRPARA TIME-SERIES ANALYSIS")
print("=" * 65)

print("\n1. BASIC INFORMATION")
print("Rows:", len(df))
print("First timestamp:", df["Timestamp"].min())
print("Last timestamp:", df["Timestamp"].max())

print("Duplicate timestamps:", df["Timestamp"].duplicated().sum())

print("\n2. WATER LEVEL DISTRIBUTION")
print(df["Water_Level"].describe())

# --------------------------------------------------
# 2. TIME INTERVAL ANALYSIS
# --------------------------------------------------

df["Time_Gap_Hours"] = df["Timestamp"].diff().dt.total_seconds() / 3600

print("\n3. TIME INTERVAL DISTRIBUTION")
print(df["Time_Gap_Hours"].value_counts().head(15))

print("\nIntervals in hours:")
print(df["Time_Gap_Hours"].describe())

# --------------------------------------------------
# 3. MISSING HOUR ANALYSIS
# --------------------------------------------------

gaps = df[df["Time_Gap_Hours"] > 1].copy()

gaps["Missing_Hours"] = gaps["Time_Gap_Hours"] - 1

print("\n4. TIME GAPS")
print("Number of gaps:", len(gaps))
print("Total missing hours:", int(gaps["Missing_Hours"].sum()))

print("\nLargest gaps:")
print(
    gaps.nlargest(15, "Missing_Hours")[
        ["Timestamp", "Time_Gap_Hours", "Missing_Hours"]
    ].to_string(index=False)
)

# --------------------------------------------------
# 4. CONTINUOUS HOURLY SEGMENTS
# --------------------------------------------------

df["New_Segment"] = (df["Time_Gap_Hours"] != 1) | df["Time_Gap_Hours"].isna()

df["Segment_ID"] = df["New_Segment"].cumsum()

segments = (
    df.groupby("Segment_ID")
    .agg(
        Start=("Timestamp", "min"),
        End=("Timestamp", "max"),
        Observations=("Timestamp", "size"),
    )
    .reset_index()
)

segments["Duration_Hours"] = (
    segments["End"] - segments["Start"]
).dt.total_seconds() / 3600 + 1

print("\n5. CONTINUOUS SEGMENTS")
print("Total segments:", len(segments))

print("\nSegment length distribution:")
print(segments["Observations"].describe())

print(
    "\nSegments with at least 24 observations:", (segments["Observations"] >= 24).sum()
)

print(
    "Segments with at least 168 observations:", (segments["Observations"] >= 168).sum()
)

print("Longest segments:")
print(
    segments.nlargest(10, "Observations")[["Start", "End", "Observations"]].to_string(
        index=False
    )
)

# --------------------------------------------------
# 5. MONTHLY DATA COVERAGE
# --------------------------------------------------

df["Month"] = df["Timestamp"].dt.to_period("M").astype(str)

monthly = (
    df.groupby("Month")
    .agg(
        Observations=("Water_Level", "count"),
        Mean_Level=("Water_Level", "mean"),
        Min_Level=("Water_Level", "min"),
        Max_Level=("Water_Level", "max"),
    )
    .reset_index()
)

monthly.to_csv(OUTPUT / "fakirpara_monthly_coverage.csv", index=False)

print("\n6. MONTHLY COVERAGE")
print(monthly.to_string(index=False))

# --------------------------------------------------
# 6. SUDDEN CHANGES
# --------------------------------------------------

df["Level_Change"] = df["Water_Level"].diff().abs()

print("\n7. SUDDEN LEVEL CHANGES")
print("Changes above 5 m:", (df["Level_Change"] > 5).sum())

print("Changes above 10 m:", (df["Level_Change"] > 10).sum())

print("\nLargest consecutive changes:")
print(
    df.nlargest(15, "Level_Change")[
        ["Timestamp", "Water_Level", "Level_Change"]
    ].to_string(index=False)
)

# --------------------------------------------------
# 7. SAVE SEGMENTS
# --------------------------------------------------

segments.to_csv(OUTPUT / "fakirpara_continuous_segments.csv", index=False)

print("\nAnalysis files saved:")
print("fakirpara_monthly_coverage.csv")
print("fakirpara_continuous_segments.csv")

print("\nAnalysis completed.")
