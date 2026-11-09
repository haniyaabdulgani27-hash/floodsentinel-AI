
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "dataset" / "fakirpara_hourly.csv"
OUTPUT_PATH = BASE_DIR / "results" / "fakirpara_water_level_timeline.png"

df = pd.read_csv(DATA_PATH)

df["Data Acquisition Time"] = pd.to_datetime(
    df["Data Acquisition Time"]
)

df = df.dropna(subset=["Water_Level"])

plt.figure(figsize=(15, 6))

plt.plot(
    df["Data Acquisition Time"],
    df["Water_Level"],
    linewidth=0.7
)

plt.axvline(
    pd.Timestamp("2024-12-17"),
    linestyle="--",
    label="Training cutoff"
)

plt.title("Fakirpara Tangni — River Water Level (2022–2025)")
plt.xlabel("Date")
plt.ylabel("Water Level (metres)")
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(OUTPUT_PATH, dpi=150)
plt.show()

print("Graph saved to:", OUTPUT_PATH)
