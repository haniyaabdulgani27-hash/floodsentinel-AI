import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT = BASE_DIR / "dataset" / "rwl_tel_hr_assam_999_2021_2025.csv"

df = pd.read_csv(INPUT)

station = "NH15 Crossing Fakirpara Tangni"

df = df[df["Station"] == station].copy()

df["Timestamp"] = pd.to_datetime(
    df["Data Acquisition Time"].astype(str).str.strip(),
    format="%d-%m-%Y %H:%M",
    errors="coerce",
)

df["Water_Level"] = pd.to_numeric(
    df["River Water Level Telemetry Hourly (meter)"], errors="coerce"
)

df = df.sort_values("Timestamp")

print("=" * 65)
print("FAKIRPARA GAUGE INVESTIGATION")
print("=" * 65)

# --------------------------------------------------
# 1. STATION METADATA
# --------------------------------------------------

print("\n1. STATION METADATA")

metadata_cols = [
    "Station",
    "District",
    "River",
    "Latitude",
    "Longitude",
    "RL_of_zeroGauge",
    "MeanSeaLevel",
    "Is_DischargeDataAvailable",
]

for col in metadata_cols:
    if col in df.columns:
        print(f"\n{col}:")
        print(df[col].value_counts(dropna=False).head(20))

# --------------------------------------------------
# 2. READINGS AROUND MAJOR CHANGES
# --------------------------------------------------

print("\n\n2. READINGS AROUND MAJOR CHANGES")

dates = ["2024-06-01 15:00", "2025-03-02 13:00", "2025-04-16 17:00"]

for date in dates:
    target = pd.Timestamp(date)

    print("\n" + "-" * 60)
    print("TARGET:", target)

    window = df[
        (df["Timestamp"] >= target - pd.Timedelta(hours=12))
        & (df["Timestamp"] <= target + pd.Timedelta(hours=12))
    ]

    print(
        window[
            ["Data Acquisition Time", "Water_Level", "RL_of_zeroGauge", "MeanSeaLevel"]
        ].to_string(index=False)
    )

# --------------------------------------------------
# 3. FREQUENT WATER LEVEL VALUES
# --------------------------------------------------

print("\n\n3. MOST FREQUENT WATER LEVEL VALUES")

print(df["Water_Level"].value_counts().head(20).to_string())

# --------------------------------------------------
# 4. MONTHLY VALUE CONCENTRATION
# --------------------------------------------------

df["Month"] = df["Timestamp"].dt.to_period("M").astype(str)

print("\n\n4. MONTHLY MOST FREQUENT VALUES")

for month, group in df.groupby("Month"):
    print(
        month,
        "| rows:",
        len(group),
        "| most frequent:",
        group["Water_Level"].mode().head(5).tolist(),
    )

# --------------------------------------------------
# 5. SUB-HOURLY INTERVALS
# --------------------------------------------------

unique_times = (
    df.dropna(subset=["Timestamp"])
    .drop_duplicates(subset=["Timestamp"])
    .sort_values("Timestamp")
)

unique_times["Gap_Minutes"] = unique_times["Timestamp"].diff().dt.total_seconds() / 60

sub_hourly = unique_times[
    unique_times["Gap_Minutes"] < 60 & unique_times["Gap_Minutes"].notna()
]

print("\n\n5. INTERVALS BELOW 60 MINUTES")
print("Count:", len(sub_hourly))

print(
    sub_hourly[["Timestamp", "Gap_Minutes", "Water_Level"]]
    .head(30)
    .to_string(index=False)
)

print("\nInvestigation completed.")
