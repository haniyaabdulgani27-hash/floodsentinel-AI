import os
import numpy as np
import pandas as pd

from sklearn.model_selection import GroupKFold, cross_validate
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier

# 1. Load data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "dataset", "flood_events_joined_audit.csv")

df = pd.read_csv(DATA_PATH)

# 2. Target
target_map = {"Flood": 0, "Severe Flood": 1}

df["Flood Type"] = df["Flood Type"].astype(str).str.strip()
df = df[df["Flood Type"].isin(target_map)].copy()
df["Target"] = df["Flood Type"].map(target_map)

# 3. Features
rainfall = [f"T{i}d" for i in range(1, 11)]

numeric_candidates = [
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

categorical_candidates = [
    "KoppenGeiger Climate Type",
    "Land cover",
    "Soil type",
    "lithology type",
]

numeric_features = [c for c in rainfall + numeric_candidates if c in df.columns]

categorical_features = [c for c in categorical_candidates if c in df.columns]

for col in numeric_features:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=rainfall + ["GaugeID"])

# Remove entirely missing columns
numeric_features = [c for c in numeric_features if df[c].notna().any()]
categorical_features = [c for c in categorical_features if df[c].notna().any()]

features = numeric_features + categorical_features
X = df[features]
y = df["Target"]
groups = df["GaugeID"]

# 4. Preprocessing
numeric_preprocessor = Pipeline(
    [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
)

categorical_preprocessor = Pipeline(
    [
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ]
)

preprocessor = ColumnTransformer(
    [
        ("num", numeric_preprocessor, numeric_features),
        ("cat", categorical_preprocessor, categorical_features),
    ]
)

# 5. Models
models = {
    "Dummy": DummyClassifier(strategy="most_frequent"),
    "Logistic Regression": LogisticRegression(max_iter=2000, class_weight="balanced"),
    "Random Forest": RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    ),
    "Extra Trees": ExtraTreesClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    ),
}

# 6. Group cross-validation
cv = GroupKFold(n_splits=5)

scoring = {
    "accuracy": "accuracy",
    "balanced_accuracy": "balanced_accuracy",
    "severe_recall": "recall",
    "severe_precision": "precision",
}

results = []

for name, classifier in models.items():

    pipeline = Pipeline([("preprocessor", preprocessor), ("classifier", classifier)])

    scores = cross_validate(
        pipeline, X, y, groups=groups, cv=cv, scoring=scoring, n_jobs=-1
    )

    results.append(
        {
            "Model": name,
            "Accuracy": scores["test_accuracy"].mean(),
            "Balanced Accuracy": scores["test_balanced_accuracy"].mean(),
            "Severe Recall": scores["test_severe_recall"].mean(),
            "Severe Precision": scores["test_severe_precision"].mean(),
        }
    )

    print(f"\nCompleted: {name}")

# 7. Display results
results_df = pd.DataFrame(results)

print("\n========== MODEL COMPARISON ==========")
print(
    results_df.sort_values("Balanced Accuracy", ascending=False)
    .round(4)
    .to_string(index=False)
)
