from urllib.parse import quote
import feedparser
import pandas as pd
from textblob import TextBlob

from config.config import PROCESSED_DATA_DIR
from config.logger import logger

logger.info("Fetching financial news")

STOCK_KEYWORDS = {
    "RELIANCE": "Reliance Industries",
    "TCS": "TCS Tata Consultancy",
    "INFY": "Infosys",
    "HDFCBANK": "HDFC Bank",
    "ICICIBANK": "ICICI Bank",
    "ITC": "ITC Limited",
}

def fetch_news(query):
    encoded_query = quote(f"{query} India stock")
    url = f"https://news.google.com/rss/search?q={encoded_query}"
    return feedparser.parse(url).entries[:5]


def analyze_sentiment(text):
    return TextBlob(text).sentiment.polarity


def build_news_sentiment():
    results = []

    for symbol, keyword in STOCK_KEYWORDS.items():
        news = fetch_news(keyword)
        scores = []

        for article in news:
            score = analyze_sentiment(article.title)
            scores.append(score)

        avg_score = sum(scores) / len(scores) if scores else 0

        results.append({
            "Symbol": symbol,
            "News_Sentiment": round(avg_score, 3)
        })

    df = pd.DataFrame(results)
    df.to_csv(PROCESSED_DATA_DIR / "news_sentiment.csv", index=False)
    logger.info("News sentiment saved.")


if __name__ == "__main__":
    build_news_sentiment()
