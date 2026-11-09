import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

FILE = BASE_DIR / "dataset" / "rwl_tel_hr_assam_999_2021_2025.csv"

df = pd.read_csv(FILE)

TIME_COL = "Data Acquisition Time"
LEVEL_COL = "River Water Level Telemetry Hourly (meter)"

df["Timestamp"] = pd.to_datetime(
    df[TIME_COL].astype(str).str.strip(), format="%d-%m-%Y %H:%M", errors="coerce"
)

df["Water_Level"] = pd.to_numeric(df[LEVEL_COL], errors="coerce")

stations = [
    "NH15 Crossing Fakirpara Tangni",
    "NH15 Crossing Dhansirighat",
    "NH17 Crossing Boko",
]

windows = [
    ("June 2024 transition", "2024-05-30", "2024-06-05"),
    ("April 2025 transition", "2025-04-14", "2025-04-21"),
]

for title, start, end in windows:

    print("\n" + "=" * 75)
    print(title.upper())
    print("=" * 75)

    start = pd.Timestamp(start)
    end = pd.Timestamp(end)

    for station in stations:

        subset = df[
            (df["Station"] == station)
            & (df["Timestamp"] >= start)
            & (df["Timestamp"] < end)
        ].copy()

        subset = subset.sort_values("Timestamp")

        print("\n" + "-" * 65)
        print("STATION:", station)
        print("Records:", len(subset))

        print(subset[["Data Acquisition Time", "Water_Level"]].to_string(index=False))

        print("\nDuplicate timestamps:")
        duplicates = subset[subset.duplicated("Timestamp", keep=False)]

        if duplicates.empty:
            print("None")
        else:
            print(duplicates[["Timestamp", "Water_Level"]].to_string(index=False))

print("\nInvestigation completed.")
