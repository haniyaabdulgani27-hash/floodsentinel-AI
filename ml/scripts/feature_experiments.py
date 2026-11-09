import os
import pandas as pd

from sklearn.model_selection import GroupKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import make_scorer, recall_score, precision_score

# 1. Load dataset
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "dataset", "flood_events_joined_audit.csv")

df = pd.read_csv(DATA_PATH)

# 2. Prepare target
target_map = {"Flood": 0, "Severe Flood": 1}

df["Flood Type"] = df["Flood Type"].astype(str).str.strip()
df = df[df["Flood Type"].isin(target_map)].copy()
df["Target"] = df["Flood Type"].map(target_map)

# 3. Define feature groups
rainfall = [f"T{i}d" for i in range(1, 11)]

catchment_numeric = [
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

catchment_categorical = [
    "KoppenGeiger Climate Type",
    "Land cover",
    "Soil type",
    "lithology type",
]

# Keep columns that exist
rainfall = [c for c in rainfall if c in df.columns]
catchment_numeric = [c for c in catchment_numeric if c in df.columns]
catchment_categorical = [c for c in catchment_categorical if c in df.columns]

for col in rainfall + catchment_numeric:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=rainfall + ["GaugeID"])

# Remove entirely missing features
catchment_numeric = [c for c in catchment_numeric if df[c].notna().any()]
catchment_categorical = [c for c in catchment_categorical if df[c].notna().any()]

# 4. Feature experiments
experiments = {
    "Rainfall only": (rainfall, []),
    "Rainfall + numerical catchment": (rainfall + catchment_numeric, []),
    "Rainfall + all catchment": (rainfall + catchment_numeric, catchment_categorical),
}

# 5. Grouped cross-validation
cv = GroupKFold(n_splits=5)

scoring = {
    "balanced_accuracy": "balanced_accuracy",
    "accuracy": "accuracy",
    "severe_recall": make_scorer(recall_score, pos_label=1, zero_division=0),
    "severe_precision": make_scorer(precision_score, pos_label=1, zero_division=0),
}

groups = df["GaugeID"]
y = df["Target"]

results = []

for experiment_name, feature_groups in experiments.items():

    numeric_cols, categorical_cols = feature_groups
    selected_cols = numeric_cols + categorical_cols

    X = df[selected_cols].copy()

    transformers = [("numeric", SimpleImputer(strategy="median"), numeric_cols)]

    if categorical_cols:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_cols,
            )
        )

    preprocessor = ColumnTransformer(transformers)

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

    scores = cross_validate(
        model, X, y, groups=groups, cv=cv, scoring=scoring, n_jobs=-1
    )

    results.append(
        {
            "Experiment": experiment_name,
            "Balanced Accuracy": scores["test_balanced_accuracy"].mean(),
            "Balanced Accuracy SD": scores["test_balanced_accuracy"].std(),
            "Severe Recall": scores["test_severe_recall"].mean(),
            "Severe Precision": scores["test_severe_precision"].mean(),
        }
    )

    print("Completed:", experiment_name)

# 6. Display results
result_df = pd.DataFrame(results)

print("\n========== FEATURE EXPERIMENTS ==========")
print(result_df.round(4).to_string(index=False))

# Save results
output_path = os.path.join(BASE_DIR, "feature_experiment_results.csv")
result_df.to_csv(output_path, index=False)

print("\nResults saved to:", output_path)
