"""Canonical file paths for the citibike project."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Processed data
DATA_DIR = ROOT / "data" / "processed"
DAILY_DATA_PATH = DATA_DIR / "bike_share_daily.parquet"
HOURLY_DATA_PATH = DATA_DIR / "bike_share_hourly.parquet"
MTA_DATA_PATH = DATA_DIR / "mta_bike_opportunity.parquet"

# Models
MODELS_DIR = ROOT / "models"
NYC_MODEL_PATH = MODELS_DIR / "xgboost_new_york_city.json"
FORECAST_METRICS_PATH = MODELS_DIR / "forecast_metrics.json"
FORECAST_PREDICTIONS_PATH = MODELS_DIR / "forecast_predictions.parquet"
FEATURE_IMPORTANCE_PATH = MODELS_DIR / "feature_importance.json"

# Config
CONFIG_DIR = ROOT / "backend" / "config"
PRICING_CONFIG_PATH = CONFIG_DIR / "pricing_assumptions.json"
PRICE_HISTORY_PATH = CONFIG_DIR / "citibike_price_history.json"
SCENARIO_CONFIG_PATH = CONFIG_DIR / "scenario_assumptions.json"
OPPORTUNITY_WEIGHTS_PATH = CONFIG_DIR / "opportunity_weights.json"

# Case studies
CASE_STUDIES_PATH = ROOT / "data" / "case_studies" / "bike_share_success_stories.json"
