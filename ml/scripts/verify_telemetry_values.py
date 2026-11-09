import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

RAW_PATH = BASE_DIR / "dataset" / "rwl_tel_hr_assam_999_2021_2025.csv"
CLEAN_PATH = BASE_DIR / "dataset" / "assam_river_levels_cleaned.csv"

TIME = "Data Acquisition Time"
LEVEL = "River Water Level Telemetry Hourly (meter)"
STATION = "Station"


def load_fakirpara(path):
    df = pd.read_csv(path)

    df = df[
        df[STATION].astype(str).str.contains("Fakirpara", case=False, na=False)
    ].copy()

    df[TIME] = pd.to_datetime(df[TIME], errors="coerce")
    df[LEVEL] = pd.to_numeric(df[LEVEL], errors="coerce")

    return df.dropna(subset=[TIME, LEVEL]).sort_values(TIME)


raw = load_fakirpara(RAW_PATH)
clean = load_fakirpara(CLEAN_PATH)


# Compare original and cleaned datasets
for name, df in [("ORIGINAL", raw), ("CLEANED", clean)]:

    print(f"\n{name} DATA")
    print("=" * 45)

    print("Total readings:", len(df))

    print("\nFrequency of suspicious values:")

    for value in [5.763, 32.700, 14.300, 60.650]:
        count = (df[LEVEL] == value).sum()
        print(f"{value}: {count} readings")

    print("\nMost frequent exact readings:")
    print(df[LEVEL].value_counts().head(10).to_string())

    # Find long consecutive runs of identical readings
    same_value = df[LEVEL].eq(df[LEVEL].shift())

    consecutive_time = df[TIME].diff().eq(pd.Timedelta(hours=1))

    new_run = ~(same_value & consecutive_time)
    df["Run_ID"] = new_run.cumsum()

    runs = df.groupby("Run_ID").agg(
        Start=(TIME, "min"),
        End=(TIME, "max"),
        Reading=(LEVEL, "first"),
        Count=(LEVEL, "size"),
    )

    print("\nLongest repeated-value runs:")

    print(
        runs[runs["Count"] >= 24]
        .sort_values("Count", ascending=False)
        .head(15)
        .to_string(index=False)
    )


# Inspect original records around major transitions
print("\nORIGINAL RECORDS AROUND MAJOR TRANSITIONS")
print("=" * 55)

for date in ["2024-06-01 15:00", "2025-03-02 13:00", "2025-04-16 17:00"]:

    timestamp = pd.Timestamp(date)

    nearby = raw[
        (raw[TIME] >= timestamp - pd.Timedelta(hours=3))
        & (raw[TIME] <= timestamp + pd.Timedelta(hours=3))
    ]

    print(f"\nAround {date}:")

    print(nearby[[TIME, LEVEL]].to_string(index=False))

print("\nVERIFICATION COMPLETE")
