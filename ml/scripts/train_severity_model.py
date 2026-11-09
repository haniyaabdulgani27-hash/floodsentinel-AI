import os
import joblib
import pandas as pd

from sklearn.model_selection import GroupShuffleSplit
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    balanced_accuracy_score,
)

# --------------------------------------------------
# 1. LOAD DATA
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "dataset", "flood_events_joined_audit.csv")

df = pd.read_csv(DATA_PATH)

print("Dataset loaded:", df.shape)

# --------------------------------------------------
# 2. DEFINE TARGET
# --------------------------------------------------

df["Flood Type"] = df["Flood Type"].astype(str).str.strip()

# Flood = 0, Severe Flood = 1
target_map = {"Flood": 0, "Severe Flood": 1}

df = df[df["Flood Type"].isin(target_map)].copy()
df["Target"] = df["Flood Type"].map(target_map)

# --------------------------------------------------
# 3. SELECT SAFE INPUT FEATURES
# --------------------------------------------------

rainfall_features = [f"T{i}d" for i in range(1, 11)]

catchment_numeric = [
    "Stream Order",
    "Maximal Flow Length",
    "Downvalley Length",
    "Drainage Area",
    "Catchment Relief",
    "Catchment Length",
    "Catchment Perimeter",
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

catchment_categorical = [
    "KoppenGeiger Climate Type",
    "Land cover",
    "Soil type",
    "lithology type",
]

# Keep only columns actually present in the dataset
numeric_features = [
    col for col in rainfall_features + catchment_numeric if col in df.columns
]

categorical_features = [col for col in catchment_categorical if col in df.columns]

feature_columns = numeric_features + categorical_features

if not feature_columns:
    raise ValueError("No usable input features found.")

# Convert numeric columns safely
for col in numeric_features:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Remove rows without rainfall information
available_rainfall = [col for col in rainfall_features if col in df.columns]

df = df.dropna(subset=available_rainfall)

# Remove features that are entirely missing
numeric_features = [col for col in numeric_features if df[col].notna().any()]

categorical_features = [col for col in categorical_features if df[col].notna().any()]

feature_columns = numeric_features + categorical_features

# --------------------------------------------------
# 4. PREPARE X, Y AND GROUPS
# --------------------------------------------------

X = df[feature_columns].copy()
y = df["Target"].copy()

# GaugeID is used only to keep stations separate
# during validation. It is NOT a model input.
groups = df["GaugeID"].copy()

valid = groups.notna()
X = X.loc[valid]
y = y.loc[valid]
groups = groups.loc[valid]

print("\nUsable records:", len(X))
print("Number of stations:", groups.nunique())
print("Features:", feature_columns)

print("\nTarget distribution:")
print(y.value_counts().rename(index={0: "Flood", 1: "Severe Flood"}))

# --------------------------------------------------
# 5. STATION-HELD-OUT TRAIN/TEST SPLIT
# --------------------------------------------------

splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)

train_idx, test_idx = next(splitter.split(X, y, groups=groups))

X_train = X.iloc[train_idx]
X_test = X.iloc[test_idx]
y_train = y.iloc[train_idx]
y_test = y.iloc[test_idx]

print("\nTraining records:", len(X_train))
print("Testing records:", len(X_test))
print("Training stations:", groups.iloc[train_idx].nunique())
print("Testing stations:", groups.iloc[test_idx].nunique())

if y_train.nunique() < 2 or y_test.nunique() < 2:
    raise ValueError(
        "The split does not contain both classes. " "Try another random_state."
    )

# --------------------------------------------------
# 6. BUILD PREPROCESSING PIPELINE
# --------------------------------------------------

numeric_pipeline = Pipeline([("imputer", SimpleImputer(strategy="median"))])

categorical_pipeline = Pipeline(
    [
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ]
)

preprocessor = ColumnTransformer(
    [
        ("numeric", numeric_pipeline, numeric_features),
        ("categorical", categorical_pipeline, categorical_features),
    ]
)

# --------------------------------------------------
# 7. TRAIN RANDOM FOREST MODEL
# --------------------------------------------------

model = Pipeline(
    [
        ("preprocessor", preprocessor),
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

print("\nTraining model...")
model.fit(X_train, y_train)

# --------------------------------------------------
# 8. EVALUATE MODEL
# --------------------------------------------------

predictions = model.predict(X_test)

print("\n========== MODEL RESULTS ==========")

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
# 9. SAVE MODEL
# --------------------------------------------------

MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "flood_severity_model.joblib")

joblib.dump(
    {
        "model": model,
        "features": feature_columns,
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "target_mapping": target_map,
        "training_scope": "INDOFLOODS multi-state historical events",
        "validation": "GaugeID group-held-out split",
    },
    MODEL_PATH,
)

print("\nModel saved successfully:")
print(MODEL_PATH)
