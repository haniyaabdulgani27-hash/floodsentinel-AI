import pandas as pd
import numpy as np
import joblib

from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "dataset" / "fakirpara_features.csv"
MODEL_PATH = BASE_DIR / "models" / "fakirpara_rf_model.joblib"

df = pd.read_csv(DATA_PATH)
df["Data Acquisition Time"] = pd.to_datetime(df["Data Acquisition Time"])

df = df.sort_values("Data Acquisition Time").reset_index(drop=True)

split_index = int(len(df) * 0.80)

train = df.iloc[:split_index].copy()
test = df.iloc[split_index:].copy()

# Keep only test segments not present in training
test = test[~test["segment_id"].isin(set(train["segment_id"]))].copy()

# Load model
saved = joblib.load(MODEL_PATH)
model = saved["model"]
features = saved["features"]

X_test = test[features]
actual = test["target_next_hour"].to_numpy()
predicted = model.predict(X_test)

baseline = test["lag_1"].to_numpy()

print("\n1. TARGET DISTRIBUTION")
print("----------------------")

print("Training target:")
print(train["target_next_hour"].describe())

print("\nTesting target:")
print(test["target_next_hour"].describe())

print("\n2. FEATURE RANGE CHECK")
print("----------------------")

for col in features:
    print(
        col,
        "| Train:",
        round(train[col].min(), 3),
        "to",
        round(train[col].max(), 3),
        "| Test:",
        round(test[col].min(), 3),
        "to",
        round(test[col].max(), 3),
    )

print("\n3. PREDICTION RANGE")
print("------------------")

print("Actual:", round(actual.min(), 3), "to", round(actual.max(), 3))
print("Random Forest:", round(predicted.min(), 3), "to", round(predicted.max(), 3))
print("Persistence:", round(baseline.min(), 3), "to", round(baseline.max(), 3))

print("\n4. ERROR COMPARISON")
print("-------------------")

rf_errors = np.abs(actual - predicted)
baseline_errors = np.abs(actual - baseline)

print("RF MAE:", round(mean_absolute_error(actual, predicted), 4))
print("Persistence MAE:", round(mean_absolute_error(actual, baseline), 4))

print("\n5. WORST 10 RANDOM FOREST PREDICTIONS")

diagnostics = test[["Data Acquisition Time", "target_next_hour", "lag_1"]].copy()

diagnostics["RF_Prediction"] = predicted
diagnostics["RF_Absolute_Error"] = rf_errors
diagnostics["Persistence_Error"] = baseline_errors

print(
    diagnostics.sort_values("RF_Absolute_Error", ascending=False)
    .head(10)
    .to_string(index=False)
)
