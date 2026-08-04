"""
CitiBike + Bay Wheels Station Demand Forecasting — XGBoost
----------------------------------------------------------
Predicts daily trip counts per station. Trains separate city models.
Compares against a seasonal-naive (lag-7) baseline.

Input:  data/processed/bike_share_daily.parquet
Output: models/  (saved model + metrics)
        report/  (feature importance plots)

Run: python demand_forecast_xgboost.py
     python demand_forecast_xgboost.py --city "New York City"
     python demand_forecast_xgboost.py --city "San Francisco"
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor

DATA_PATH = Path("data/processed/bike_share_daily.parquet")
MODELS_DIR = Path("models")
REPORT_DIR = Path("report")

FEATURES = [
    "lat",
    "lon",
    "day_of_week",
    "month",
    "is_weekend",
    "is_holiday",
    "lag_1d",
    "lag_7d",
    "roll_mean_7d",
    "roll_mean_28d",
    "electric_share",
    "member_share",
]
TARGET = "trips"


# ---------------------------------------------------------------
# 1. Load and prepare
# ---------------------------------------------------------------
def load_daily(path: Path, city: str | None = None) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["date"] = pd.to_datetime(df["date"])
    if city:
        df = df[df["city"] == city].copy()

    # Aggregate rider types into a single row per station-day
    agg = (
        df.groupby(["date", "city", "system", "station_name", "lat", "lon", "capacity"],
                    as_index=False)
        .agg(
            trips=("trips", "sum"),
            electric_trips=("electric_trips", "sum"),
            member_trips=("trips", lambda x: x.iloc[0] if df.loc[x.index, "rider_type"].iloc[0] == "Member" else 0),
        )
    )
    # Recompute member/electric shares properly
    station_rider = df.groupby(["date", "station_name", "rider_type"], as_index=False)["trips"].sum()
    member = station_rider[station_rider["rider_type"] == "Member"].rename(columns={"trips": "member_trips_actual"})
    agg2 = (
        df.groupby(["date", "city", "system", "station_name", "lat", "lon", "capacity"],
                    as_index=False)
        .agg(trips=("trips", "sum"), electric_trips=("electric_trips", "sum"))
    )
    agg2 = agg2.merge(
        member[["date", "station_name", "member_trips_actual"]],
        on=["date", "station_name"],
        how="left",
    )
    agg2["member_trips_actual"] = agg2["member_trips_actual"].fillna(0)
    agg2["electric_share"] = (agg2["electric_trips"] / agg2["trips"]).fillna(0)
    agg2["member_share"] = (agg2["member_trips_actual"] / agg2["trips"]).fillna(0)

    return agg2.sort_values(["station_name", "date"]).reset_index(drop=True)


# ---------------------------------------------------------------
# 2. Feature engineering
# ---------------------------------------------------------------
US_HOLIDAYS = {
    # Major US federal holidays (approximate — add more as needed)
    "2024-01-01", "2024-01-15", "2024-02-19", "2024-05-27",
    "2024-07-04", "2024-09-02", "2024-10-14", "2024-11-28", "2024-12-25",
    "2025-01-01", "2025-01-20", "2025-02-17", "2025-05-26",
    "2025-07-04", "2025-09-01", "2025-10-13", "2025-11-27", "2025-12-25",
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-05-25",
    "2026-07-04", "2026-09-07", "2026-10-12", "2026-11-26", "2026-12-25",
}


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["is_holiday"] = df["date"].dt.strftime("%Y-%m-%d").isin(US_HOLIDAYS).astype(int)

    # Lag features per station
    df = df.sort_values(["station_name", "date"])
    grp = df.groupby("station_name")["trips"]
    df["lag_1d"] = grp.shift(1)
    df["lag_7d"] = grp.shift(7)
    df["roll_mean_7d"] = grp.shift(1).rolling(7, min_periods=3).mean().reset_index(level=0, drop=True)
    df["roll_mean_28d"] = grp.shift(1).rolling(28, min_periods=7).mean().reset_index(level=0, drop=True)

    return df


# ---------------------------------------------------------------
# 3. Train / test split — CHRONOLOGICAL
# ---------------------------------------------------------------
def chronological_split(df: pd.DataFrame, test_days: int = 60):
    cutoff = df["date"].max() - pd.Timedelta(days=test_days)
    train = df[df["date"] <= cutoff].dropna(subset=FEATURES)
    test = df[df["date"] > cutoff].dropna(subset=FEATURES)
    return train, test


# ---------------------------------------------------------------
# 4. Seasonal naive baseline
# ---------------------------------------------------------------
def seasonal_naive_predict(test: pd.DataFrame) -> np.ndarray:
    """Use lag_7d as the seasonal naive forecast."""
    return test["lag_7d"].values


# ---------------------------------------------------------------
# 5. Train + evaluate
# ---------------------------------------------------------------
def train_model(train: pd.DataFrame) -> XGBRegressor:
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
    model.fit(X_train, y_train, verbose=False)
    return model


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    wape = float(np.sum(np.abs(y_true - y_pred)) / np.sum(np.abs(y_true))) if np.sum(np.abs(y_true)) > 0 else 0.0
    return {"MAE": round(mae, 2), "RMSE": round(rmse, 2), "WAPE": round(wape, 4)}


def evaluate(model: XGBRegressor, test: pd.DataFrame, city: str) -> dict:
    X_test = test[FEATURES]
    y_test = test[TARGET].values

    # XGBoost predictions
    xgb_preds = model.predict(X_test)
    xgb_metrics = compute_metrics(y_test, xgb_preds)

    # Seasonal naive baseline
    naive_preds = seasonal_naive_predict(test)
    naive_metrics = compute_metrics(y_test, naive_preds)

    print(f"\n{'='*50}")
    print(f"  {city} — Test Set Results ({len(test):,} station-days)")
    print(f"{'='*50}")
    print(f"  {'Metric':<8} {'XGBoost':>10} {'Naive(7d)':>10} {'Improvement':>12}")
    print(f"  {'-'*42}")
    for metric in ["MAE", "RMSE", "WAPE"]:
        xgb_val = xgb_metrics[metric]
        naive_val = naive_metrics[metric]
        improvement = (naive_val - xgb_val) / naive_val * 100 if naive_val else 0
        print(f"  {metric:<8} {xgb_val:>10.2f} {naive_val:>10.2f} {improvement:>+10.1f}%")

    return {
        "city": city,
        "test_station_days": len(test),
        "xgboost": xgb_metrics,
        "seasonal_naive": naive_metrics,
    }


def save_feature_importance(model: XGBRegressor, city: str) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        importances = pd.Series(model.feature_importances_, index=FEATURES).sort_values()
        fig, ax = plt.subplots(figsize=(8, 5))
        importances.plot(kind="barh", ax=ax, color="#2D7FF9")
        ax.set_title(f"XGBoost Feature Importance — {city}")
        ax.set_xlabel("Importance")
        plt.tight_layout()

        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        slug = city.lower().replace(" ", "_")
        path = REPORT_DIR / f"feature_importance_{slug}.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        print(f"  Saved {path}")
    except ImportError:
        print("  matplotlib not available, skipping plot")


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--city", type=str, default=None, help="Train for one city only")
    parser.add_argument("--test-days", type=int, default=60)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.data.exists():
        print(f"Data file not found: {args.data}")
        print("Run scripts/ingest_bike_data.py first.")
        return

    cities = [args.city] if args.city else ["New York City", "San Francisco"]
    all_results = []

    for city in cities:
        print(f"\n>>> Loading {city} data...")
        daily = load_daily(args.data, city=city)
        if daily.empty:
            print(f"  No data for {city}, skipping")
            continue

        print(f"  {len(daily):,} station-day rows, "
              f"{daily['station_name'].nunique()} stations, "
              f"{daily['date'].min().date()} to {daily['date'].max().date()}")

        daily = add_features(daily)
        train, test = chronological_split(daily, test_days=args.test_days)

        if train.empty or test.empty:
            print(f"  Insufficient data for train/test split, skipping")
            continue

        print(f"  Train: {len(train):,} rows | Test: {len(test):,} rows")

        model = train_model(train)
        results = evaluate(model, test, city)
        all_results.append(results)
        save_feature_importance(model, city)

        # Save model
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        slug = city.lower().replace(" ", "_")
        model_path = MODELS_DIR / f"xgboost_{slug}.json"
        model.save_model(str(model_path))
        print(f"  Saved model to {model_path}")

    # Save combined metrics
    if all_results:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        metrics_path = MODELS_DIR / "forecast_metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\nSaved metrics to {metrics_path}")


if __name__ == "__main__":
    main()
