"""Configuration settings for the market trend analyzer."""
from datetime import timedelta
from pathlib import Path
from typing import Final, List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Market Analysis Settings
TICKER_SYMBOL: Final[str] = "VWRA.L"
ANALYSIS_PERIOD_DAYS: Final[int] = 30
NEWS_LOOKBACK_DAYS: Final[int] = 7
SHORT_MA_PERIOD: Final[int] = 5
LONG_MA_PERIOD: Final[int] = 10

# Visualization Settings
FIGURE_SIZE: Final[tuple[float, float]] = (6.4, 4.8)  # Default matplotlib size
COLORS: Final[dict[str, str]] = {
    'price': 'blue',
    'short_ma': 'red',
    'long_ma': 'green',
    'grid': '#E0E0E0'
}

# News API Settings
NEWS_QUERIES: Final[dict[str, str]] = {
    'bullish': 'global market growth OR stock market rally OR economic growth',
    'bearish': 'market decline OR economic concerns OR stock market drop'
}
NEWS_RESULTS_LIMIT: Final[int] = 5

# Telegram Settings
TELEGRAM_TOKEN: Final[str] = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")

ALLOWED_CHAT_IDS: Final[List[int]] = [
    int(id_) for id_ in os.getenv('TELEGRAM_ALLOWED_CHAT_IDS', '').split(',')
    if id_.strip()
]

# Command settings
COMMANDS: Final[dict[str, str]] = {
    'market': 'Get current market analysis',
    'help': 'Show available commands'
}

# Database Settings
DATABASE_URL: Final[str] = os.getenv('DATABASE_URL', 'postgresql://localhost/stunk')

# Cache Settings
REDIS_URL: Final[str] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
NEWS_TTL_CACHE: Final[timedelta] = timedelta(hours=6)
MARKET_CACHE_TTL: Final[timedelta] = timedelta(minutes=5)