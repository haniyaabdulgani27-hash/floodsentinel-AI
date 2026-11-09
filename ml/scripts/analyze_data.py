import pandas as pd

path = "ml/dataset/flood_events_joined_audit.csv"

df = pd.read_csv(path, low_memory=False)

print("\n========== FLOODSENTINEL DATA ANALYSIS ==========")

# 1. Overall target distribution
print("\n1. OVERALL FLOOD SEVERITY")
print(df["Flood Type"].value_counts())
print("\nPercentages:")
print(df["Flood Type"].value_counts(normalize=True) * 100)

# 2. Maharashtra severity distribution
mh = df[df["State"].str.strip().str.lower() == "maharashtra"].copy()

print("\n2. MAHARASHTRA SEVERITY")
print("Total events:", len(mh))
print(mh["Flood Type"].value_counts())
print("\nPercentage:")
print(mh["Flood Type"].value_counts(normalize=True) * 100)

# 3. Station distribution
print("\n3. STATION DISTRIBUTION")
print("Unique Maharashtra stations:", mh["GaugeID"].nunique())
print(mh["Station"].value_counts().head(15))

# 4. Duplicate checks
print("\n4. DUPLICATE CHECKS")
print("Duplicate EventIDs:", df["EventID"].duplicated().sum())
print("Duplicate complete rows:", df.duplicated().sum())

# 5. Date coverage
print("\n5. DATE COVERAGE")

df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce", dayfirst=True)

print("Earliest event:", df["Start Date"].min())
print("Latest event:", df["Start Date"].max())

print("\nMaharashtra date coverage:")
print("Earliest:", mh["Start Date"].min())
print("Latest:", mh["Start Date"].max())

# 6. Rainfall feature analysis
rainfall_cols = [f"T{i}d" for i in range(1, 11)]

print("\n6. RAINFALL STATISTICS")
print(df[rainfall_cols].describe().round(2))

# 7. Missing-value analysis
print("\n7. MISSING VALUE PERCENTAGES")

missing = (df.isnull().mean() * 100).sort_values(ascending=False)

print(missing[missing > 0].head(25).round(2))

# 8. Check Maharashtra missing values
print("\n8. MAHARASHTRA MISSING VALUES")

mh_missing = (mh.isnull().mean() * 100).sort_values(ascending=False)

print(mh_missing[mh_missing > 0].head(20).round(2))

# 9. Feature availability
print("\n9. IMPORTANT FEATURE AVAILABILITY")

for col in [
    "T1d",
    "T2d",
    "T3d",
    "T5d",
    "T10d",
    "Warning Level",
    "Danger Level",
    "Latitude",
    "Longitude",
    "Catchment Area",
    "Population Density",
]:
    if col in df.columns:
        print(f"{col}: {df[col].notna().sum()} " f"available / {len(df)} total")

print("\n========== ANALYSIS COMPLETED ==========")
