import os
import joblib
import pandas as pd

from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
)

# --------------------------------------------------
# 1. LOAD DATA
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "dataset", "flood_events_joined_audit.csv")

df = pd.read_csv(DATA_PATH)

# --------------------------------------------------
# 2. PREPARE TARGET
# --------------------------------------------------

target_map = {"Flood": 0, "Severe Flood": 1}

df["Flood Type"] = df["Flood Type"].astype(str).str.strip()
df = df[df["Flood Type"].isin(target_map)].copy()
df["Target"] = df["Flood Type"].map(target_map)

# --------------------------------------------------
# 3. SELECT FEATURES
# --------------------------------------------------

rainfall_features = [f"T{i}d" for i in range(1, 11)]

catchment_features = [
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

numeric_features = [
    col for col in rainfall_features + catchment_features if col in df.columns
]

for col in numeric_features:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Remove columns with no available values
numeric_features = [col for col in numeric_features if df[col].notna().any()]

df = df.dropna(subset=rainfall_features + ["GaugeID"]).copy()

X = df[numeric_features]
y = df["Target"]
groups = df["GaugeID"]

print("Records:", len(df))
print("Stations:", groups.nunique())
print("Features:", len(numeric_features))

# --------------------------------------------------
# 4. GROUP-BASED TRAIN/TEST SPLIT
# --------------------------------------------------

splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)

train_idx, test_idx = next(splitter.split(X, y, groups=groups))

X_train = X.iloc[train_idx]
X_test = X.iloc[test_idx]

y_train = y.iloc[train_idx]
y_test = y.iloc[test_idx]

# --------------------------------------------------
# 5. BUILD MODEL
# --------------------------------------------------

candidate_model = Pipeline(
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

# --------------------------------------------------
# 6. TRAIN AND EVALUATE
# --------------------------------------------------

print("\nTraining candidate model...")

candidate_model.fit(X_train, y_train)

predictions = candidate_model.predict(X_test)

print("\n========== HELD-OUT RESULTS ==========")

print("Accuracy:", round(accuracy_score(y_test, predictions), 4))

print("Balanced Accuracy:", round(balanced_accuracy_score(y_test, predictions), 4))

print("\nClassification Report:")
print(
    classification_report(
        y_test, predictions, target_names=["Flood", "Severe Flood"], zero_division=0
    )
)

print("Confusion Matrix:")
print(confusion_matrix(y_test, predictions))

# --------------------------------------------------
# 7. PERMUTATION FEATURE IMPORTANCE
# --------------------------------------------------

print("\nCalculating feature importance...")

importance = permutation_importance(
    candidate_model,
    X_test,
    y_test,
    scoring="balanced_accuracy",
    n_repeats=10,
    random_state=42,
    n_jobs=-1,
)

importance_df = pd.DataFrame(
    {
        "Feature": numeric_features,
        "Importance Mean": importance.importances_mean,
        "Importance SD": importance.importances_std,
    }
)

importance_df = importance_df.sort_values("Importance Mean", ascending=False)

print("\n========== FEATURE IMPORTANCE ==========")
print(importance_df.round(5).to_string(index=False))

importance_path = os.path.join(BASE_DIR, "feature_importance.csv")

importance_df.to_csv(importance_path, index=False)

# --------------------------------------------------
# 8. TRAIN FINAL CANDIDATE ON ALL DATA
# --------------------------------------------------

print("\nTraining final candidate on all records...")

candidate_model.fit(X, y)

MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "flood_severity_model.joblib")

joblib.dump(
    {
        "model": candidate_model,
        "features": numeric_features,
        "target_mapping": target_map,
        "training_scope": "INDOFLOODS multi-state historical events",
        "validation": "GaugeID group-held-out evaluation",
        "model_type": "Random Forest",
        "feature_set": "Rainfall + numerical catchment",
    },
    MODEL_PATH,
)

print("\nCandidate model saved:", MODEL_PATH)
print("Feature importance saved:", importance_path)
