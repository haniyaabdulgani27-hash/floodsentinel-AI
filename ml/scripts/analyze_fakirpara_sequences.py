import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "dataset" / "fakirpara_hourly.csv"

df = pd.read_csv(DATA_PATH)

df["Data Acquisition Time"] = pd.to_datetime(df["Data Acquisition Time"])

# A continuous sequence requires consecutive timestamps
# with no missing water-level readings.
valid = df.dropna(subset=["Water_Level"]).copy()
valid = valid.sort_values("Data Acquisition Time")

time_diff = valid["Data Acquisition Time"].diff()

# Start a new segment whenever there is a gap
valid["Segment"] = (time_diff != pd.Timedelta(hours=1)).cumsum()

# Count observations in each continuous segment
segments = valid.groupby("Segment").size()

print("\nCONTINUOUS SEQUENCE ANALYSIS")
print("--------------------------------")
print("Total valid readings:", len(valid))
print("Number of continuous segments:", len(segments))
print("Longest continuous segment:", segments.max(), "hours")
print("Segments with at least 7 hours:", (segments >= 7).sum())
print("Segments with at least 24 hours:", (segments >= 24).sum())
print("Segments with at least 168 hours:", (segments >= 168).sum())

print("\nTop 10 longest segments:")
print(segments.sort_values(ascending=False).head(10).to_string())
