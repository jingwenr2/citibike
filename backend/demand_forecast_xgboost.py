"""
CitiBike Station Demand Forecasting — XGBoost baseline
--------------------------------------------------------
Predicts daily trip counts per station. Feeds the "optimal expansion
station" output for Layer 1 of the capstone.

Expected input: cleaned CitiBike trip data (from data/processed/),
one row per trip, with at least:
    started_at, start_station_id, start_station_name,
    start_lat, start_lng, rideable_type, member_casual

Run: python demand_forecast_xgboost.py
"""

import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt

# ---------------------------------------------------------------
# 1. Load + aggregate to daily station-level counts
# ---------------------------------------------------------------
# Replace with your actual processed file(s). If you have multiple
# monthly CSVs, glob + concat them first.
DATA_PATH = "data/processed/citibike_trips.parquet"  # or .csv

def load_trips(path: str) -> pd.DataFrame:
    if path.endswith(".parquet"):
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path, parse_dates=["started_at"])
    return df

def to_daily_station_counts(df: pd.DataFrame) -> pd.DataFrame:
    df["date"] = pd.to_datetime(df["started_at"]).dt.date
    daily = (
        df.groupby(["start_station_id", "start_station_name", "date"])
        .size()
        .reset_index(name="trip_count")
    )
    # attach station lat/lng (first observed value per station)
    station_loc = df.groupby("start_station_id")[["start_lat", "start_lng"]].first()
    daily = daily.merge(station_loc, on="start_station_id", how="left")
    daily["date"] = pd.to_datetime(daily["date"])
    return daily

# ---------------------------------------------------------------
# 2. Feature engineering
# ---------------------------------------------------------------
def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    # swap in a real US-holiday calendar (e.g. `holidays` package) before final run
    df["is_holiday"] = 0
    return df

def add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["start_station_id", "date"])
    grp = df.groupby("start_station_id")["trip_count"]
    df["lag_1d"] = grp.shift(1)
    df["lag_7d"] = grp.shift(7)
    df["roll_mean_7d"] = grp.shift(1).rolling(7).mean().reset_index(level=0, drop=True)
    return df

# ---------------------------------------------------------------
# 3. Train / test split — CHRONOLOGICAL, not random
# ---------------------------------------------------------------
def chronological_split(df: pd.DataFrame, test_days: int = 60):
    cutoff = df["date"].max() - pd.Timedelta(days=test_days)
    train = df[df["date"] <= cutoff]
    test = df[df["date"] > cutoff]
    return train, test

FEATURES = [
    "start_lat", "start_lng", "day_of_week", "month",
    "is_weekend", "is_holiday", "lag_1d", "lag_7d", "roll_mean_7d",
]
TARGET = "trip_count"

# ---------------------------------------------------------------
# 4. Train + evaluate
# ---------------------------------------------------------------
def train_model(train: pd.DataFrame):
    X_train = train[FEATURES]
    y_train = train[TARGET]
    model = XGBRegressor(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
    )
    model.fit(X_train, y_train)
    return model

def evaluate(model, test: pd.DataFrame):
    X_test = test[FEATURES]
    y_test = test[TARGET]
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    print(f"MAE:  {mae:.2f} trips/day")
    print(f"RMSE: {rmse:.2f} trips/day")
    return preds

def plot_feature_importance(model):
    importances = pd.Series(model.feature_importances_, index=FEATURES).sort_values()
    importances.plot(kind="barh", figsize=(8, 5), title="XGBoost Feature Importance")
    plt.tight_layout()
    plt.savefig("report/feature_importance.png")
    print("Saved report/feature_importance.png")

# ---------------------------------------------------------------
# 5. Expansion candidate ranking
# ---------------------------------------------------------------
def rank_expansion_candidates(test: pd.DataFrame, preds: np.ndarray, dock_counts: pd.DataFrame):
    """
    dock_counts: DataFrame with [start_station_id, num_docks]
    Flags stations where predicted demand is high relative to
    current dock capacity — these are your expansion candidates.
    """
    out = test.copy()
    out["predicted_demand"] = preds
    summary = (
        out.groupby(["start_station_id", "start_station_name"])["predicted_demand"]
        .mean()
        .reset_index()
        .merge(dock_counts, on="start_station_id", how="left")
    )
    summary["demand_per_dock"] = summary["predicted_demand"] / summary["num_docks"]
    return summary.sort_values("demand_per_dock", ascending=False)

# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
if __name__ == "__main__":
    trips = load_trips(DATA_PATH)
    daily = to_daily_station_counts(trips)
    daily = add_calendar_features(daily)
    daily = add_lag_features(daily)
    daily = daily.dropna(subset=FEATURES)  # drop rows without full lag history

    train, test = chronological_split(daily, test_days=60)
    model = train_model(train)
    preds = evaluate(model, test)
    plot_feature_importance(model)

    # Uncomment once you have a dock-count dataset (from GBFS station_information):
    # dock_counts = pd.read_csv("data/processed/station_dock_counts.csv")
    # ranked = rank_expansion_candidates(test, preds, dock_counts)
    # ranked.to_csv("report/expansion_candidates.csv", index=False)
