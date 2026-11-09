import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "dataset" / "fakirpara_hourly.csv"
OUTPUT_PATH = BASE_DIR / "dataset" / "fakirpara_features.csv"

df = pd.read_csv(DATA_PATH)

df["Data Acquisition Time"] = pd.to_datetime(df["Data Acquisition Time"])

df = df.sort_values("Data Acquisition Time").reset_index(drop=True)

# Keep only continuous hourly segments
valid = df.dropna(subset=["Water_Level"]).copy()

time_diff = valid["Data Acquisition Time"].diff()

valid["Segment"] = (time_diff != pd.Timedelta(hours=1)).cumsum()

features = []

# Build features independently within each segment
for segment_id, group in valid.groupby("Segment"):

    group = group.copy()

    # Previous six hourly readings
    for lag in range(1, 7):
        group[f"lag_{lag}"] = group["Water_Level"].shift(lag)

    # Rolling averages using only past observations
    group["rolling_mean_3h"] = group["Water_Level"].shift(1).rolling(3).mean()

    group["rolling_mean_6h"] = group["Water_Level"].shift(1).rolling(6).mean()

    # Predict the next hour
    group["target_next_hour"] = group["Water_Level"].shift(-1)

    group["segment_id"] = segment_id

    features.append(group)

result = pd.concat(features, ignore_index=True)

# Remove rows without complete input history or target
feature_columns = [f"lag_{i}" for i in range(1, 7)] + [
    "rolling_mean_3h",
    "rolling_mean_6h",
]

result = result.dropna(subset=feature_columns + ["target_next_hour"])

result.to_csv(OUTPUT_PATH, index=False)

print("\nFEATURE ENGINEERING COMPLETE")
print("--------------------------------")
print("Total training examples:", len(result))
print("Number of segments:", result["segment_id"].nunique())
print("Features:", feature_columns)
print("Target: target_next_hour")
print("Saved to:", OUTPUT_PATH)

print("\nSample:")
print(result[["Data Acquisition Time"] + feature_columns + ["target_next_hour"]].head())
