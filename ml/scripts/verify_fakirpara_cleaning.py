import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS = BASE_DIR / "results"

audit = pd.read_csv(RESULTS / "fakirpara_quality_audit.csv")

candidate = pd.read_csv(RESULTS / "fakirpara_model_candidate.csv")

conflicts = pd.read_csv(RESULTS / "fakirpara_conflicts.csv")

extremes = pd.read_csv(RESULTS / "fakirpara_extreme_readings.csv")

LEVEL_COL = "Water_Level"

print("=" * 60)
print("FAKIRPARA CLEANING VERIFICATION")
print("=" * 60)

print("\n1. QUALITY LABEL COUNTS")
print(audit["Data_Quality"].value_counts(dropna=False))

print("\n2. EXTREME READING CHECK")
print("Audit readings above 100 m:", (audit[LEVEL_COL] > 100).sum())

print("Extreme output rows:", len(extremes))

print("\n3. MODEL CANDIDATE CHECK")
print("Candidate rows:", len(candidate))
print("Candidate readings above 100 m:", (candidate[LEVEL_COL] > 100).sum())

print("Candidate maximum:", candidate[LEVEL_COL].max())

print("\n4. CONFLICT CHECK")
print("Conflict output rows:", len(conflicts))

print("\n5. DUPLICATE CHECK")
print(
    "Duplicate timestamp-level pairs in candidate:",
    candidate.duplicated(subset=["Timestamp", LEVEL_COL]).sum(),
)

print("\n6. MISSING VALUE CHECK")
print("Missing timestamps:", candidate["Timestamp"].isna().sum())
print("Missing levels:", candidate[LEVEL_COL].isna().sum())

print("\nVerification completed.")
