"""
Citi Bike Station Demand Forecasting — XGBoost (v3)
----------------------------------------------------
Predicts daily trip counts per NYC Citi Bike station.
Compares against a seasonal-naive (lag-7) baseline.

Features (23):
  - Station: lat, lon, capacity
  - Calendar: day_of_week, month, quarter, year, is_weekend, is_holiday
  - Lag / rolling: lag_1d, lag_7d, roll_mean_7d, roll_mean_28d, roll_std_7d
  - Composition: electric_share, member_share
  - Transit (MTA): mta_daily_riders, mta_delay_rate, nearest_mta_distance_km
  - Hourly pattern: peak_hour_share (share of trips in rush hours)
  - Weather (deviation-based): temp_deviation, precip_deviation, is_bad_weather
    Uses deviation from monthly climate normals so weather impact scales
    with seasonal context (e.g. 15°C in Jan ≠ 15°C in Jul).

Bay Wheels/San Francisco is excluded — used only as a benchmark for the
DOT investment case, never as training data for NYC decisions.

Input:  data/processed/bike_share_daily.parquet
        data/processed/bike_share_hourly.parquet  (optional — peak hour feature)
        data/processed/mta_bike_opportunity.parquet (optional — MTA features)
        data/processed/nyc_weather_daily.parquet  (optional — weather features)
Output: models/  (saved model + metrics)
        report/  (feature importance plots)

Run: python backend/demand_forecast_xgboost.py
     python backend/demand_forecast_xgboost.py --city "New York City" --test-days 60
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
HOURLY_PATH = Path("data/processed/bike_share_hourly.parquet")
MTA_PATH = Path("data/processed/mta_bike_opportunity.parquet")
WEATHER_PATH = Path("data/processed/nyc_weather_daily.parquet")
MODELS_DIR = Path("models")
REPORT_DIR = Path("report")

FEATURES = [
    # Station location & infrastructure
    "lat",
    "lon",
    "capacity",
    # Calendar
    "day_of_week",
    "month",
    "quarter",
    "year",
    "is_weekend",
    "is_holiday",
    # Lag / rolling window
    "lag_1d",
    "lag_7d",
    "roll_mean_7d",
    "roll_mean_28d",
    "roll_std_7d",
    # Ridership composition
    "electric_share",
    "member_share",
    # Transit proximity (MTA)
    "mta_daily_riders",
    "mta_delay_rate",
    "nearest_mta_distance_km",
    # Hourly demand pattern
    "peak_hour_share",
    # Weather (deviation from monthly normals)
    "temp_deviation",
    "precip_deviation",
    "is_bad_weather",
]
TARGET = "trips"


# ---------------------------------------------------------------
# 1. Load and prepare
# ---------------------------------------------------------------
US_HOLIDAYS = {
    "2023-01-01", "2023-01-16", "2023-02-20", "2023-05-29",
    "2023-07-04", "2023-09-04", "2023-10-09", "2023-11-23", "2023-12-25",
    "2024-01-01", "2024-01-15", "2024-02-19", "2024-05-27",
    "2024-07-04", "2024-09-02", "2024-10-14", "2024-11-28", "2024-12-25",
    "2025-01-01", "2025-01-20", "2025-02-17", "2025-05-26",
    "2025-07-04", "2025-09-01", "2025-10-13", "2025-11-27", "2025-12-25",
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-05-25",
    "2026-07-04", "2026-09-07", "2026-10-12", "2026-11-26", "2026-12-25",
}

PEAK_HOURS = {7, 8, 9, 17, 18, 19}


def load_daily(path: Path, city: str | None = None) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["date"] = pd.to_datetime(df["date"])
    if city:
        df = df[df["city"] == city].copy()

    # Aggregate rider types into one row per station-day
    station_rider = df.groupby(
        ["date", "station_name", "rider_type"], as_index=False
    )["trips"].sum()
    member = station_rider[station_rider["rider_type"] == "Member"].rename(
        columns={"trips": "member_trips"}
    )

    agg = (
        df.groupby(
            ["date", "city", "system", "station_name", "lat", "lon", "capacity"],
            as_index=False,
        )
        .agg(trips=("trips", "sum"), electric_trips=("electric_trips", "sum"))
    )
    agg = agg.merge(
        member[["date", "station_name", "member_trips"]],
        on=["date", "station_name"],
        how="left",
    )
    agg["member_trips"] = agg["member_trips"].fillna(0)
    agg["electric_share"] = (agg["electric_trips"] / agg["trips"]).replace(
        [np.inf, -np.inf], 0
    ).fillna(0)
    agg["member_share"] = (agg["member_trips"] / agg["trips"]).replace(
        [np.inf, -np.inf], 0
    ).fillna(0)

    return agg.sort_values(["station_name", "date"]).reset_index(drop=True)


def load_mta_features(path: Path) -> pd.DataFrame:
    """Load MTA transit proximity features per station."""
    if not path.exists():
        print("  MTA data not found — skipping transit features")
        return pd.DataFrame()
    mta = pd.read_parquet(path)
    return mta[["station_name", "mta_daily_riders", "mta_delay_rate",
                "nearest_mta_distance_km"]].copy()


def load_peak_hour_share(path: Path) -> pd.DataFrame:
    """Compute per-date peak-hour share from hourly data."""
    if not path.exists():
        print("  Hourly data not found — skipping peak_hour_share feature")
        return pd.DataFrame()
    hourly = pd.read_parquet(path)
    hourly["date"] = pd.to_datetime(hourly["date"])

    daily_total = hourly.groupby("date", as_index=False)["trips"].sum().rename(
        columns={"trips": "total_trips"}
    )
    peak = (
        hourly[hourly["hour"].isin(PEAK_HOURS)]
        .groupby("date", as_index=False)["trips"]
        .sum()
        .rename(columns={"trips": "peak_trips"})
    )
    merged = daily_total.merge(peak, on="date", how="left")
    merged["peak_trips"] = merged["peak_trips"].fillna(0)
    merged["peak_hour_share"] = (
        merged["peak_trips"] / merged["total_trips"]
    ).replace([np.inf, -np.inf], 0).fillna(0)

    return merged[["date", "peak_hour_share"]]


def load_weather(path: Path) -> pd.DataFrame:
    """Load weather data with deviation-based features.

    Uses deviation from monthly climate normals so the model learns
    that the *same* temperature has different impact depending on
    the time of year (the sliding-scale approach).
    """
    if not path.exists():
        print("  Weather data not found — skipping weather features")
        return pd.DataFrame()
    weather = pd.read_parquet(path)
    weather["date"] = pd.to_datetime(weather["date"])
    return weather[["date", "temp_deviation", "precip_deviation", "is_bad_weather"]]


# ---------------------------------------------------------------
# 2. Feature engineering
# ---------------------------------------------------------------
def add_features(
    df: pd.DataFrame,
    mta_df: pd.DataFrame | None = None,
    peak_df: pd.DataFrame | None = None,
    weather_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    df = df.copy()

    # Calendar features
    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["quarter"] = df["date"].dt.quarter
    df["year"] = df["date"].dt.year
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["is_holiday"] = (
        df["date"].dt.strftime("%Y-%m-%d").isin(US_HOLIDAYS).astype(int)
    )

    # Capacity — fill missing with median
    df["capacity"] = df["capacity"].replace(0, np.nan)
    median_cap = df["capacity"].median()
    df["capacity"] = df["capacity"].fillna(median_cap)

    # Lag / rolling features per station
    df = df.sort_values(["station_name", "date"])
    grp = df.groupby("station_name")["trips"]
    df["lag_1d"] = grp.shift(1)
    df["lag_7d"] = grp.shift(7)
    df["roll_mean_7d"] = (
        grp.shift(1).rolling(7, min_periods=3).mean()
        .reset_index(level=0, drop=True)
    )
    df["roll_mean_28d"] = (
        grp.shift(1).rolling(28, min_periods=7).mean()
        .reset_index(level=0, drop=True)
    )
    df["roll_std_7d"] = (
        grp.shift(1).rolling(7, min_periods=3).std()
        .reset_index(level=0, drop=True)
    )
    df["roll_std_7d"] = df["roll_std_7d"].fillna(0)

    # MTA transit features
    if mta_df is not None and not mta_df.empty:
        df = df.merge(mta_df, on="station_name", how="left")
        df["mta_daily_riders"] = df["mta_daily_riders"].fillna(0)
        df["mta_delay_rate"] = df["mta_delay_rate"].fillna(
            df["mta_delay_rate"].median()
        )
        df["nearest_mta_distance_km"] = df["nearest_mta_distance_km"].fillna(
            df["nearest_mta_distance_km"].max()
        )
        print(f"  MTA features merged — {df['mta_daily_riders'].gt(0).sum():,} rows with MTA data")
    else:
        df["mta_daily_riders"] = 0.0
        df["mta_delay_rate"] = 0.0
        df["nearest_mta_distance_km"] = 0.0

    # Peak hour share
    if peak_df is not None and not peak_df.empty:
        df = df.merge(peak_df, on="date", how="left")
        df["peak_hour_share"] = df["peak_hour_share"].fillna(
            df["peak_hour_share"].median()
        )
        print(f"  Peak hour share merged — median {df['peak_hour_share'].median():.2%}")
    else:
        df["peak_hour_share"] = 0.0

    # Weather deviation features
    if weather_df is not None and not weather_df.empty:
        df = df.merge(weather_df, on="date", how="left")
        df["temp_deviation"] = df["temp_deviation"].fillna(0)
        df["precip_deviation"] = df["precip_deviation"].fillna(0)
        df["is_bad_weather"] = df["is_bad_weather"].fillna(0).astype(int)
        bad_pct = df["is_bad_weather"].mean()
        print(f"  Weather features merged — {bad_pct:.1%} bad weather days, "
              f"temp deviation range [{df['temp_deviation'].min():+.1f}, {df['temp_deviation'].max():+.1f}]°C")
    else:
        df["temp_deviation"] = 0.0
        df["precip_deviation"] = 0.0
        df["is_bad_weather"] = 0

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

    # Hold out the last 20% of training data chronologically for early stopping
    es_cutoff = train["date"].quantile(0.8)
    es_mask = train["date"] > es_cutoff
    X_es, y_es = X_train[es_mask], y_train[es_mask]
    X_fit, y_fit = X_train[~es_mask], y_train[~es_mask]

    model = XGBRegressor(
        n_estimators=1000,
        max_depth=7,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        early_stopping_rounds=30,
    )
    model.fit(
        X_fit, y_fit,
        eval_set=[(X_es, y_es)],
        verbose=False,
    )
    print(f"  Early stopping: best iteration {model.best_iteration} / {model.n_estimators}")
    return model


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    wape = (
        float(np.sum(np.abs(y_true - y_pred)) / np.sum(np.abs(y_true)))
        if np.sum(np.abs(y_true)) > 0
        else 0.0
    )
    return {"MAE": round(mae, 2), "RMSE": round(rmse, 2), "WAPE": round(wape, 4)}


def evaluate(model: XGBRegressor, test: pd.DataFrame, city: str) -> dict:
    X_test = test[FEATURES]
    y_test = test[TARGET].values

    xgb_preds = model.predict(X_test)
    xgb_preds = np.clip(xgb_preds, 0, None)
    xgb_metrics = compute_metrics(y_test, xgb_preds)

    naive_preds = seasonal_naive_predict(test)
    naive_metrics = compute_metrics(y_test, naive_preds)

    print(f"\n{'='*55}")
    print(f"  {city} — Test Set Results ({len(test):,} station-days)")
    print(f"{'='*55}")
    print(f"  {'Metric':<8} {'XGBoost':>10} {'Naive(7d)':>10} {'Improvement':>12}")
    print(f"  {'-'*42}")
    for metric in ["MAE", "RMSE", "WAPE"]:
        xgb_val = xgb_metrics[metric]
        naive_val = naive_metrics[metric]
        improvement = (naive_val - xgb_val) / naive_val * 100 if naive_val else 0
        print(f"  {metric:<8} {xgb_val:>10.2f} {naive_val:>10.2f} {improvement:>+10.1f}%")

    # Save actual vs predicted for dashboard visualization
    predictions_df = test[["date", "station_name", "lat", "lon", TARGET]].copy()
    predictions_df["predicted"] = xgb_preds
    predictions_df["residual"] = predictions_df[TARGET] - predictions_df["predicted"]
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    pred_path = MODELS_DIR / "forecast_predictions.parquet"
    predictions_df.to_parquet(pred_path, index=False)
    print(f"  Saved predictions to {pred_path}")

    # Save feature importance as JSON for dashboard
    importance = dict(zip(FEATURES, [float(v) for v in model.feature_importances_]))
    importance_path = MODELS_DIR / "feature_importance.json"
    with open(importance_path, "w") as f:
        json.dump(importance, f, indent=2)
    print(f"  Saved feature importance to {importance_path}")

    return {
        "city": city,
        "test_station_days": len(test),
        "features_used": FEATURES,
        "n_features": len(FEATURES),
        "xgboost": xgb_metrics,
        "seasonal_naive": naive_metrics,
    }


def time_series_cv(df: pd.DataFrame, n_splits: int = 3, test_days: int = 60) -> list[dict]:
    """Run time-series cross-validation with expanding window."""
    dates = sorted(df["date"].unique())
    total_test = n_splits * test_days
    if len(dates) < total_test + 90:
        print("  Insufficient data for cross-validation — skipping")
        return []

    results = []
    for i in range(n_splits):
        # Each fold's test end moves backward
        test_end_idx = len(dates) - (n_splits - 1 - i) * test_days
        test_start_idx = test_end_idx - test_days
        cutoff_date = dates[test_start_idx]
        end_date = dates[min(test_end_idx, len(dates) - 1)]

        train_fold = df[df["date"] < cutoff_date].dropna(subset=FEATURES)
        test_fold = df[(df["date"] >= cutoff_date) & (df["date"] <= end_date)].dropna(subset=FEATURES)

        if train_fold.empty or test_fold.empty:
            continue

        model = train_model(train_fold)
        preds = np.clip(model.predict(test_fold[FEATURES]), 0, None)
        metrics = compute_metrics(test_fold[TARGET].values, preds)
        metrics["fold"] = i + 1
        metrics["train_rows"] = len(train_fold)
        metrics["test_rows"] = len(test_fold)
        results.append(metrics)
        print(f"  Fold {i+1}: MAE={metrics['MAE']:.2f}, RMSE={metrics['RMSE']:.2f}, WAPE={metrics['WAPE']:.4f}")

    return results


def save_feature_importance(model: XGBRegressor, city: str) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        importances = pd.Series(
            model.feature_importances_, index=FEATURES
        ).sort_values()
        fig, ax = plt.subplots(figsize=(9, 6))
        colors = ["#2D7FF9" if v < importances.quantile(0.75) else "#F59E0B"
                  for v in importances.values]
        importances.plot(kind="barh", ax=ax, color=colors)
        ax.set_title(f"XGBoost Feature Importance — {city}", fontsize=14)
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
    parser.add_argument("--hourly", type=Path, default=HOURLY_PATH)
    parser.add_argument("--mta", type=Path, default=MTA_PATH)
    parser.add_argument("--weather", type=Path, default=WEATHER_PATH)
    parser.add_argument(
        "--city",
        type=str,
        default="New York City",
        help="City to train on (default: New York City)",
    )
    parser.add_argument("--test-days", type=int, default=60)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.data.exists():
        print(f"Data file not found: {args.data}")
        print("Run scripts/ingest_bike_data.py first.")
        return

    print(f"\n>>> Loading {args.city} data...")
    daily = load_daily(args.data, city=args.city)
    if daily.empty:
        print(f"  No data for {args.city}")
        return

    print(f"  {len(daily):,} station-day rows, "
          f"{daily['station_name'].nunique()} stations, "
          f"{daily['date'].min().date()} to {daily['date'].max().date()}")

    # Load auxiliary data
    print("\n>>> Loading auxiliary features...")
    mta_df = load_mta_features(args.mta)
    peak_df = load_peak_hour_share(args.hourly)
    weather_df = load_weather(args.weather)

    # Engineer features
    print("\n>>> Engineering features...")
    daily = add_features(daily, mta_df=mta_df, peak_df=peak_df, weather_df=weather_df)

    print(f"\n  Final feature set ({len(FEATURES)} features):")
    for f in FEATURES:
        print(f"    - {f}")

    train, test = chronological_split(daily, test_days=args.test_days)

    if train.empty or test.empty:
        print("  Insufficient data for train/test split")
        return

    print(f"\n  Train: {len(train):,} rows | Test: {len(test):,} rows")

    model = train_model(train)
    results = evaluate(model, test, args.city)
    save_feature_importance(model, args.city)

    # Time-series cross-validation
    print("\n>>> Running time-series cross-validation...")
    cv_results = time_series_cv(daily, n_splits=3, test_days=args.test_days)
    if cv_results:
        avg_mae = np.mean([r["MAE"] for r in cv_results])
        avg_rmse = np.mean([r["RMSE"] for r in cv_results])
        avg_wape = np.mean([r["WAPE"] for r in cv_results])
        print(f"\n  CV Average: MAE={avg_mae:.2f}, RMSE={avg_rmse:.2f}, WAPE={avg_wape:.4f}")
        results["cv_results"] = cv_results
        results["cv_avg"] = {"MAE": round(avg_mae, 2), "RMSE": round(avg_rmse, 2), "WAPE": round(avg_wape, 4)}

    # Save model
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    slug = args.city.lower().replace(" ", "_")
    model_path = MODELS_DIR / f"xgboost_{slug}.json"
    model.save_model(str(model_path))
    print(f"  Saved model to {model_path}")

    # Save metrics
    metrics_path = MODELS_DIR / "forecast_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump([results], f, indent=2)
    print(f"  Saved metrics to {metrics_path}")


if __name__ == "__main__":
    main()
