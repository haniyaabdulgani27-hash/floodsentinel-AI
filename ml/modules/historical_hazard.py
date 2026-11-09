import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / "outputs" / "historical_hazard_summary.csv"

DATA = [
    {
        "district": "Darrang",
        "very_high": 50,
        "high": 23,
        "moderate": 40,
        "low": 44,
        "very_low": 317,
    },
    {
        "district": "Udalguri",
        "very_high": 0,
        "high": 0,
        "moderate": 14,
        "low": 14,
        "very_low": 597,
    },
    {
        "district": "Kamrup Metropolitan",
        "very_high": 42,
        "high": 4,
        "moderate": 14,
        "low": 8,
        "very_low": 77,
    },
]


def get_historical_hazard_summary():
    df = pd.DataFrame(DATA)

    hazard_columns = ["very_high", "high", "moderate", "low", "very_low"]

    df["total_villages"] = df[hazard_columns].sum(axis=1)

    df["high_or_very_high_villages"] = df["very_high"] + df["high"]

    df.to_csv(OUTPUT, index=False)

    return df


if __name__ == "__main__":
    print(get_historical_hazard_summary().to_string(index=False))
    print(f"\nSaved to: {OUTPUT}")
