import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / "outputs"

hazard = pd.read_csv(OUTPUT / "historical_hazard_summary.csv")

infrastructure = pd.read_csv(OUTPUT / "infrastructure_summary.csv")

combined = hazard.merge(infrastructure, on="district", how="inner")

combined.to_csv(OUTPUT / "district_risk_profile.csv", index=False)

print(combined.to_string(index=False))
print("\nSaved: ml/outputs/district_risk_profile.csv")
