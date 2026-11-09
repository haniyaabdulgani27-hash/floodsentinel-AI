import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "dataset" / "assam_river_levels_cleaned.csv"

df = pd.read_csv(DATA_PATH)

print("COLUMN NAMES:")
for col in df.columns:
    print(repr(col))

print("\nFIRST 3 ROWS:")
print(df.head(3).to_string())
