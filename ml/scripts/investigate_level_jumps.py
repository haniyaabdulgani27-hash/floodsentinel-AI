import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "dataset" / "assam_river_levels_cleaned.csv"

df = pd.read_csv(DATA_PATH)

# Select Fakirpara Tangni
df = df[
    df["Station"].astype(str).str.contains("Fakirpara", case=False, na=False)
].copy()

time_col = "Data Acquisition Time"
level_col = "River Water Level Telemetry Hourly (meter)"

df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
df[level_col] = pd.to_numeric(df[level_col], errors="coerce")

df = df[
    (df["Data_Quality"] == "Valid") & df[time_col].notna() & df[level_col].notna()
].sort_values(time_col)

# Monthly statistics
df["Month"] = df[time_col].dt.to_period("M")

print("\nMONTHLY WATER LEVEL SUMMARY")
print("----------------------------")

print(
    df.groupby("Month")[level_col]
    .agg(["count", "min", "median", "max"])
    .round(3)
    .to_string()
)

# Compare consecutive actual observations
df["Previous_Level"] = df[level_col].shift(1)
df["Level_Change"] = df[level_col] - df["Previous_Level"]
df["Time_Gap"] = df[time_col].diff()

# Find changes greater than 5 metres
jumps = df[df["Level_Change"].abs() > 5].copy()

print("\nLARGE LEVEL CHANGES (> 5 METRES)")
print("--------------------------------")

print("Number of changes:", len(jumps))

print(
    jumps[
        [
            time_col,
            "Previous_Level",
            level_col,
            "Level_Change",
            "Time_Gap",
            "RL_of_zeroGauge",
            "MeanSeaLevel",
        ]
    ].to_string(index=False)
)

# Inspect gauge reference metadata
print("\nGAUGE REFERENCE VALUES")
print("----------------------")

print("RL_of_zeroGauge:")
print(df["RL_of_zeroGauge"].value_counts(dropna=False).head(10))

print("\nMeanSeaLevel:")
print(df["MeanSeaLevel"].value_counts(dropna=False).head(10))
