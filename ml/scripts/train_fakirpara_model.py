
import pandas as pd
import numpy as np
import joblib

from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "dataset" / "fakirpara_features.csv"
MODEL_DIR = BASE_DIR / "models"
RESULTS_DIR = BASE_DIR / "results"

MODEL_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# Load features
df = pd.read_csv(DATA_PATH)

df["Data Acquisition Time"] = pd.to_datetime(
    df["Data Acquisition Time"]
)

feature_columns = [
    "lag_1", "lag_2", "lag_3",
    "lag_4", "lag_5", "lag_6",
    "rolling_mean_3h", "rolling_mean_6h"
]

target_column = "target_next_hour"

# Chronological split
df = df.sort_values("Data Acquisition Time").reset_index(drop=True)

split_index = int(len(df) * 0.80)

train = df.iloc[:split_index].copy()
test = df.iloc[split_index:].copy()

# Prevent segment overlap across the train/test boundary.
# Remove test examples belonging to segments also found in training.
train_segments = set(train["segment_id"])
test = test[~test["segment_id"].isin(train_segments)].copy()

X_train = train[feature_columns]
y_train = train[target_column]

X_test = test[feature_columns]
y_test = test[target_column]

print("TRAINING DATA:", len(train))
print("TEST DATA:", len(test))
print("Train date range:", train["Data Acquisition Time"].min(), "to", train["Data Acquisition Time"].max())
print("Test date range:", test["Data Acquisition Time"].min(), "to", test["Data Acquisition Time"].max())

if len(test) == 0:
    raise ValueError("No independent test segments available.")

# Model 1: Persistence baseline
baseline_predictions = test["lag_1"].to_numpy()

# Model 2: Random Forest
model = RandomForestRegressor(
    n_estimators=300,
    max_depth=12,
    min_samples_leaf=3,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)

# Evaluation function
def evaluate(name, actual, predicted):
    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    r2 = r2_score(actual, predicted)

    print(f"\n{name}")
    print("MAE:", round(mae, 4))
    print("RMSE:", round(rmse, 4))
    print("R2 Score:", round(r2, 4))

    return {
        "Model": name,
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2
    }

results = []

results.append(
    evaluate("Persistence Baseline", y_test, baseline_predictions)
)

results.append(
    evaluate("Random Forest", y_test, predictions)
)

# Save results
results_df = pd.DataFrame(results)

results_path = RESULTS_DIR / "fakirpara_model_comparison.csv"
results_df.to_csv(results_path, index=False)

# Save model and feature names
joblib.dump(
    {
        "model": model,
        "features": feature_columns
    },
    MODEL_DIR / "fakirpara_rf_model.joblib"
)

print("\nMODEL TRAINING COMPLETE")
print("Results saved:", results_path)
print("Model saved:", MODEL_DIR / "fakirpara_rf_model.joblib")
