from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data folders
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Output folders
OUTPUT_DIR = PROJECT_ROOT / "outputs"
MODEL_DIR = PROJECT_ROOT / "models"
LOG_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_FILE = MODEL_DIR / "xgboost.pkl"
FEATURE_COLUMNS_FILE = CONFIG_DIR / "feature_columns.json"

SIGNAL_FILE = OUTPUT_DIR / "strong_buy_signals.csv"
GLOBAL_CONTEXT_FILE = PROCESSED_DATA_DIR / "global_context.csv"
NEWS_FILE = PROCESSED_DATA_DIR / "news_sentiment.csv"
MARKET_SUMMARY_FILE = PROCESSED_DATA_DIR / "market_summary.csv"
ALL_PREDICTIONS_FILE = OUTPUT_DIR / "all_predictions.csv"

# Automatically create folders
for folder in [
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    OUTPUT_DIR,
    MODEL_DIR,
    LOG_DIR,
]:
    folder.mkdir(parents=True, exist_ok=True)

# ==========================================
# Stock Universe Configuration
# ==========================================

STOCK_UNIVERSE = "TOP500"

TOP_PICKS = 5

AI_CONFIDENCE_THRESHOLD = 0.60

STRONG_BUY_SCORE = 85
BUY_SCORE = 75
BUY_CANDIDATE_SCORE = 60

MODEL_NAME = "XGBoost"

UNIVERSE_NAME = "NIFTY 500"

STRATEGY_NAME = "Momentum + Trend"

BOT_VERSION = "v1.0.0"
