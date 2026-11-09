import os
import pandas as pd

from sklearn.model_selection import LeaveOneGroupOut
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    recall_score,
    precision_score,
)

# Load dataset
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "dataset", "flood_events_joined_audit.csv")

df = pd.read_csv(DATA_PATH)

# Target
target_map = {"Flood": 0, "Severe Flood": 1}

df["Flood Type"] = df["Flood Type"].astype(str).str.strip()
df = df[df["Flood Type"].isin(target_map)].copy()
df["Target"] = df["Flood Type"].map(target_map)

# Numeric features
rainfall = [f"T{i}d" for i in range(1, 11)]

catchment = [
    "Stream Order",
    "Maximal Flow Length",
    "Downvalley Length",
    "Drainage Area",
    "Catchment Relief",
    "Catchment Length",
    "CatchmentPerimeter",
    "Sinuosity Index",
    "Form Factor",
    "Relief Ratio",
    "Elongation Ratio",
    "Circularity Ratio",
    "Drainage Density",
    "Compactness Coefficient",
    "Annual Mean Temperature",
    "Mean Diurnal Range",
    "Annual Precipitation",
    "Precipitation Seasonality",
]

features = [c for c in rainfall + catchment if c in df.columns]

for col in features:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Remove unusable records
df = df.dropna(subset=rainfall + ["State", "GaugeID"]).copy()

# Remove entirely missing features
features = [c for c in features if df[c].notna().any()]

X = df[features]
y = df["Target"]
states = df["State"].astype(str)

# Model
model = Pipeline(
    [
        ("imputer", SimpleImputer(strategy="median")),
        (
            "classifier",
            RandomForestClassifier(
                n_estimators=300,
                max_depth=12,
                min_samples_leaf=2,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            ),
        ),
    ]
)

# Leave one entire state out at a time
logo = LeaveOneGroupOut()
results = []

for train_idx, test_idx in logo.split(X, y, groups=states):

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]

    held_out_state = states.iloc[test_idx].iloc[0]

    if y_train.nunique() < 2:
        print("Skipped:", held_out_state, "- training has one class")
        continue

    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    results.append(
        {
            "Held-out State": held_out_state,
            "Test Records": len(test_idx),
            "Test Stations": df.iloc[test_idx]["GaugeID"].nunique(),
            "Flood Records": int((y_test == 0).sum()),
            "Severe Records": int((y_test == 1).sum()),
            "Accuracy": accuracy_score(y_test, predictions),
            "Balanced Accuracy": balanced_accuracy_score(y_test, predictions),
            "Severe Recall": recall_score(
                y_test, predictions, pos_label=1, zero_division=0
            ),
            "Severe Precision": precision_score(
                y_test, predictions, pos_label=1, zero_division=0
            ),
        }
    )

    print("Completed:", held_out_state)

# Results
results_df = pd.DataFrame(results)

print("\n========== STATE-HELD-OUT RESULTS ==========")
print(results_df.round(4).to_string(index=False))

output_path = os.path.join(BASE_DIR, "state_validation_results.csv")

results_df.to_csv(output_path, index=False)

print("\nSaved:", output_path)
