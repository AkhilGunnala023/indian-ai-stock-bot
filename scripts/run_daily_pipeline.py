import subprocess
import sys
from pathlib import Path

from config.logger import logger

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


def run_script(script_name):
    script_path = BASE_DIR / script_name

    logger.info(f"Running {script_name}")
    print(f"\n▶ Running {script_name}")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    # Print script output to console
    if result.stdout:
        print(result.stdout)

    # If script failed
    if result.returncode != 0:
        logger.error(f"{script_name} failed.")
        logger.error(result.stderr)

        print(result.stderr)

        raise RuntimeError(f"{script_name} execution failed")

    logger.info(f"{script_name} completed successfully")


def main():
    logger.info("========== DAILY AI PIPELINE STARTED ==========")

    try:

        # ============================================
        # STEP 1 : Update Previous Trade Outcomes
        # ============================================
        print("\n==============================")
        print("STEP 1 : UPDATE OUTCOMES")
        print("==============================")

        try:
            run_script("update_outcomes.py")
        except Exception as e:
            print("⚠ update_outcomes.py failed")
            print(e)
            logger.warning("update_outcomes.py failed. Continuing pipeline...")

        # ============================================
        # STEP 2 : Fetch Historical Stock Data
        # ============================================
        print("\n==============================")
        print("STEP 2 : FETCH HISTORICAL DATA")
        print("==============================")

        run_script("fetch_historical_eod.py")

        # ============================================
        # STEP 3 : Fetch NIFTY Market Context
        # ============================================
        print("\n==============================")
        print("STEP 3 : FETCH MARKET CONTEXT")
        print("==============================")

        run_script("fetch_market_context.py")

        # ============================================
        # STEP 4 : Merge Market Context
        # ============================================
        print("\n==============================")
        print("STEP 4 : MERGE MARKET CONTEXT")
        print("==============================")

        run_script("merge_market_context.py")

        # ============================================
        # STEP 5 : Train AI Model
        # ============================================
        print("\n==============================")
        print("STEP 5 : TRAIN AI MODEL")
        print("==============================")

        run_script("train_ai_model.py")

        # ============================================
        # STEP 6 : Filter Strong Signals
        # ============================================
        print("\n==============================")
        print("STEP 6 : FILTER STRONG SIGNALS")
        print("==============================")

        run_script("filter_strong_signals.py")

        # ============================================
        # STEP 7 : News Sentiment
        # ============================================
        print("\n==============================")
        print("STEP 7 : NEWS SENTIMENT")
        print("==============================")

        run_script("news_sentiment.py")

        # ============================================
        # STEP 8 : Global Context
        # ============================================
        print("\n==============================")
        print("STEP 8 : GLOBAL CONTEXT")
        print("==============================")

        run_script("global_context.py")

        # ============================================
        # STEP 9 : Market Summary
        # ============================================
        print("\n==============================")
        print("STEP 9 : MARKET SUMMARY")
        print("==============================")

        run_script("market_summary.py")

        # ============================================
        # STEP 10 : Telegram Report
        # ============================================
        print("\n==============================")
        print("STEP 10 : TELEGRAM REPORT")
        print("==============================")

        run_script("send_telegram_alert.py")

        print("\n===============================================")
        print("✅ DAILY AI PIPELINE COMPLETED SUCCESSFULLY")
        print("===============================================\n")

        logger.info("Daily AI Pipeline Completed Successfully")

    except Exception:
        logger.exception("Daily AI Pipeline Failed")
        raise


if __name__ == "__main__":
    main()