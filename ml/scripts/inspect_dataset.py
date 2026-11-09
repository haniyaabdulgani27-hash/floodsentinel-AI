import pandas as pd
import os
import re

DATA_DIR = "ml/dataset"

files = {
    "events": "floodevents_indofloods.csv",
    "rainfall": "precipitation_variables_indofloods.csv",
    "metadata": "metadata_indofloods.csv",
    "catchment": "catchment_characteristics_indofloods.csv",
}

print("\n========== FLOODSENTINEL AI ==========")
print("       DATASET INSPECTION REPORT")
print("======================================")

# 1. Load datasets
data = {}

for name, filename in files.items():
    path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")

    data[name] = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)

    print(f"\n{name.upper()}")
    print("Shape:", data[name].shape)
    print("Columns:", data[name].columns.tolist())

# 2. Inspect flood severity labels
events = data["events"]

print("\n========== FLOOD SEVERITY ==========")

print(events["Flood Type"].value_counts(dropna=False))

# 3. Extract gauge ID from EventID
events["GaugeID"] = events["EventID"].str.extract(r"(INDOFLOODS-gauge-\d+)")

# 4. Join rainfall data
combined = events.merge(
    data["rainfall"], on="EventID", how="left", validate="one_to_one"
)

# 5. Join geographical metadata
combined = combined.merge(
    data["metadata"], on="GaugeID", how="left", validate="many_to_one"
)

# 6. Join catchment characteristics
combined = combined.merge(
    data["catchment"], on="GaugeID", how="left", validate="many_to_one"
)

print("\n========== COMBINED DATA ==========")
print("Combined shape:", combined.shape)

print("\nMissing values:")
print(combined.isnull().sum().sort_values(ascending=False).head(15))

print("\n========== STATE DISTRIBUTION ==========")
print(combined["State"].value_counts(dropna=False).head(15))

print("\n========== MAHARASHTRA DATA ==========")

maharashtra = combined[combined["State"].str.strip().str.lower() == "maharashtra"]

print("Maharashtra flood events:", len(maharashtra))
print("Maharashtra stations:")
print(
    maharashtra[["Station", "River Name/ Tributory/ SubTributory"]]
    .drop_duplicates()
    .to_string(index=False)
)

# 7. Save joined dataset for further analysis
output_path = os.path.join(DATA_DIR, "flood_events_joined_audit.csv")
combined.to_csv(output_path, index=False)

print("\nSaved:", output_path)
print("\nDataset inspection completed!")
