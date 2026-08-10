from config.logger import logger
from scripts.threshold_engine import get_dynamic_threshold
from scripts.reason_engine import generate_reasons, generate_no_trade_reasons
from scripts.forward_tracking import log_predictions

from telegram import Bot
import asyncio
import pandas as pd
from datetime import datetime
import os
from config.secrets import BOT_TOKEN, CHAT_ID
from scripts.update_outcomes import get_performance_summary
from scripts.portfolio_manager import allocate_portfolio


from config.config import (
    SIGNAL_FILE,
    GLOBAL_CONTEXT_FILE,
    NEWS_FILE,
    MARKET_SUMMARY_FILE,
    STRONG_BUY_SCORE,
    BUY_SCORE,
    BUY_CANDIDATE_SCORE,
    MODEL_NAME,
    UNIVERSE_NAME,
    STRATEGY_NAME,
    BOT_VERSION,
    ALL_PREDICTIONS_FILE
)

logger.info("Preparing Telegram message")


## ==========================================================
# BUILD TELEGRAM MESSAGE + RETURN DATA
# ==========================================================
def build_message():
    today = datetime.now().strftime("%d %b %Y")

    # ------------------------
    # Load AI Signals
    # ------------------------
    try:

        df = pd.read_csv(SIGNAL_FILE)
        all_predictions = pd.read_csv(ALL_PREDICTIONS_FILE)

    except FileNotFoundError:
        return (
            "⚠️ *AI Stock Bot Error*\n\nSignal file not found.",
            pd.DataFrame(),
            "Unknown",
            None
        )

    # ------------------------
    # Load Global Context
    # ------------------------
    global_regime = "Unknown"
    if os.path.exists(GLOBAL_CONTEXT_FILE):
        global_df = pd.read_csv(GLOBAL_CONTEXT_FILE)
        if not global_df.empty:
            global_regime = global_df.iloc[0]["Global_Regime"]

    global_trade_block = (global_regime != "Risk-On")

    # ------------------------
    # Load News Sentiment
    # ------------------------
    news_summary = "Neutral / Positive"
    if os.path.exists(NEWS_FILE):
        news_df = pd.read_csv(NEWS_FILE)
        if not news_df.empty:
            if not news_df[news_df["News_Sentiment"] < -0.1].empty:
                news_summary = "Negative"

    # ------------------------
    # Load Market Summary
    # ------------------------
    nifty_trend = "Unknown"
    market_breadth = "Unknown"

    if os.path.exists(MARKET_SUMMARY_FILE):
        ms_df = pd.read_csv(MARKET_SUMMARY_FILE)
        if not ms_df.empty:
            nifty_trend = ms_df.iloc[0]["NIFTY_Trend"]
            market_breadth = ms_df.iloc[0]["Market_Breadth"]

    # ------------------------
    # Dynamic Threshold (Day 12)
    # ------------------------
    dynamic_threshold = get_dynamic_threshold(
        global_regime,
        nifty_trend,
        market_breadth
    )

    universe_scanned = len(all_predictions)

    passed_ai_model = len(
        all_predictions[
            all_predictions["Bullish_Probability"] >= dynamic_threshold
            ]
    )

    if dynamic_threshold is not None and not df.empty:
        df = df[df["Bullish_Probability"] >= dynamic_threshold]

    if not df.empty:
        df = allocate_portfolio(df)

    # ------------------------
    # Header
    # ------------------------
    message = (
        f"📊 *AI STOCK BOT – EOD REPORT*\n"
        f"📅 {today}\n"

        f"\n━━━━━━━━━━━━━━━━━━━━━━\n\n"

        f"🌍 *Market Regime*   : {global_regime}\n"
        f"📰 *News Sentiment*  : {news_summary}\n"
        f"📈 *NIFTY Trend*     : {nifty_trend}\n"
        f"📊 *Market Breadth*  : {market_breadth}\n"

        f"\n━━━━━━━━━━━━━━━━━━━━━━\n\n"

        f"🤖 *AI Engine*\n"
        f"• 🧠 Model      : {MODEL_NAME}\n"
        f"• 📦 Universe   : {UNIVERSE_NAME}\n"
        f"• 📈 Strategy   : {STRATEGY_NAME}\n"
        f"• 🎯 Threshold  : {dynamic_threshold:.2f}\n"

        f"\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    # ------------------------
    # Trade Results
    # ------------------------
    if global_trade_block:
        reasons = generate_no_trade_reasons(global_regime, news_summary)
        message += "🛑 *Trades blocked due to global risk*\n\n*WHY?*\n"
        for r in reasons:
            message += f"• {r}\n"
        message += "\n🛡️ Capital protection mode ON"

    elif df.empty:
        reasons = generate_no_trade_reasons(global_regime, news_summary)
        message += (
            "🛑 *NO HIGH-CONFIDENCE TRADES TODAY*\n\n"
            "📋 *Reason*\n"
        )
        for r in reasons:
            message += f"• {r}\n"

        message += "\n"

        message += (
            "🛡️ *Capital Protection Mode: ON*\n\n"
            f"No stocks met today's AI threshold ({dynamic_threshold:.2f})\n"
            "or market quality filters.\n"
        )

        message += "\n━━━━━━━━━━━━━━━━━━━━━━\n\n"


    else:

        message += "🏆 *TODAY'S AI RANKINGS*\n\n"

        message += "━━━━━━━━━━━━━━━━━━\n\n"

        for i, (_, row) in enumerate(df.iterrows(), start=1):

            # Today's Ranking Medal
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}️⃣"

            confidence = row["Bullish_Probability"] * 100

            technical_score = row["Technical_Score"]
            final_score = row["Final_Score"]
            entry_price = float(row["Close"])
            atr = float(row["ATR_14"])
            stop_loss = entry_price - atr * 1.5
            risk = entry_price - stop_loss
            target_price = entry_price + (risk * 2)
            reward = target_price - entry_price
            risk_reward = reward / risk if risk != 0 else 0

            if final_score >= STRONG_BUY_SCORE:
                signal = "🟢 STRONG BUY"
                stars = "⭐⭐⭐⭐⭐"

            elif final_score >= BUY_SCORE:
                signal = "🟢 BUY"
                stars = "⭐⭐⭐⭐☆"

            elif final_score >= BUY_CANDIDATE_SCORE:
                signal = "🟡 BUY CANDIDATE"
                stars = "⭐⭐⭐☆☆"

            else:
                signal = "🔵 WATCHLIST"
                stars = "⭐⭐☆☆☆"

            message += (
                f"{medal} *{row['Symbol']}*\n\n"

                f"{signal}\n"
                f"{stars}\n\n"
                

                f"🤖 AI Confidence : *{confidence:.1f}%*\n"
                f"⭐ Final Score   : *{final_score:.1f}*\n"
                f"⚙️ Technical     : *{technical_score:.0f}*\n\n"
                f"💰 Allocation    : {row['Allocation_%']:.1f}%\n\n"

                f"🎯 Entry Price   : ₹{entry_price:.2f}\n"
                f"🛑 Stop Loss     : ₹{stop_loss:.2f}\n"
                f"💹 Target Price  : ₹{target_price:.2f}\n"
                f"⚖️ Risk:Reward   : 1 : {risk_reward:.1f}\n\n"

                "📋 *Why Selected*\n"
            )

            reasons = generate_reasons(row, global_regime, news_summary)

            for r in reasons:
                message += f"✅ {r}\n"

            message += "\n━━━━━━━━━━━━━━━━━━━━━━\n\n"

    market_status = (
        "🛡️ Capital Protection"
        if df.empty
        else f"{global_regime} ✅"
    )

    message += (
        "📊 *Today's Summary*\n\n"
        f"• Universe Scanned : {universe_scanned}\n"
        f"• Passed AI Model  : {passed_ai_model}\n"
        f"• Qualified Stocks : {len(df)}\n"
        f"• Market Regime    : {market_status}\n"
    )

    stats = get_performance_summary()

    avg_return = stats["avg_return"]

    if pd.isna(avg_return):
        avg_return = 0.0

    message += "\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    message += "📈 *AI Performance*\n"

    if stats["tracked"] == 0:
        message += (
            "• No completed predictions yet.\n"
            "• Performance statistics will appear\n"
            "  after the first completed trade.\n"
        )
    else:
        pending = (
                stats["tracked"]
                - stats["wins"]
                - stats["losses"]
                - stats["breakeven"]
        )

        completed = (
                stats["wins"] +
                stats["losses"] +
                stats["breakeven"]
        )

        message += (
            f"• Completed Trades : {completed}\n\n"
            f"✅ Wins            : {stats['wins']}\n"
            f"❌ Losses          : {stats['losses']}\n"
            f"➖ Break Even       : {stats['breakeven']}\n\n"
            f"🎯 Win Rate        : {stats['win_rate']}%\n"
            f"📊 Avg Return      : {avg_return:.2f}%\n"
        )

    generated_time = datetime.now().strftime("%d %b %Y %I:%M %p IST")

    message += (
        "\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🤖 Bot Version : {BOT_VERSION}\n\n"
        f"🕒 Generated  : {generated_time}\n"
    )

    message += (
        "\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ Educational purpose only.\n"
        "This is an AI-generated report and not financial advice."
    )

    return message, df, global_regime, dynamic_threshold


# ==========================================================
# SEND TELEGRAM + FORWARD TRACKING
# ==========================================================
async def send_telegram_message():
    print("Starting Telegram Bot...")
    try:
        bot = Bot(token=BOT_TOKEN)

        message, df, global_regime, dynamic_threshold = build_message()

        print("Telegram message built successfully.")
        print(message[:500])

        # -------- Day 14 Forward Tracking --------
        try:
            log_predictions(
                df=df,
                global_regime=global_regime,
                threshold=dynamic_threshold
            )
        except Exception as e:
            logger.error(f"Forward tracking failed: {e}")

        print("Sending Telegram Message...")

        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode="Markdown"
        )

        logger.info("Telegram message sent successfully")
        print("Telegram EOD message sent successfully.")


    except Exception as e:

        print(f"Telegram Error: {e}")

        logger.info("⚠️ Telegram send failed.")

        logger.info(str(e))


if __name__ == "__main__":
    asyncio.run(send_telegram_message())