"""Data models for the application."""
from dataclasses import dataclass
from typing import Dict, Any, List
from datetime import datetime

import pandas as pd


@dataclass
class NewsArticle:
    """Represents a news article with relevant information."""
    title: str
    url: str
    date: str
    
    def to_markdown(self) -> str:
        """Convert article to markdown format."""
        return "📰 [{}]({})\n📅 {}\n".format(
            self.title,
            self.url,
            self.date
        )


@dataclass
class MarketAnalysis:
    """Container for market analysis results."""
    current_price: float
    start_price: float
    short_ma: float
    long_ma: float
    historical_data: pd.DataFrame
    is_bullish: bool

    def __post_init__(self):
        """Ensure historical_data is properly structured."""
        if not isinstance(self.historical_data, pd.DataFrame):
            if isinstance(self.historical_data, dict):
                # Convert dictionary to DataFrame
                df = pd.DataFrame(self.historical_data['data'])
                if 'dates' in self.historical_data:
                    df.index = pd.to_datetime(self.historical_data['dates'])
                self.historical_data = df
            else:
                raise ValueError("historical_data must be a DataFrame or a properly structured dictionary")

    def calculate_price_change(self) -> float:
        """Calculate price change percentage."""
        return ((self.current_price - self.start_price) / self.start_price) * 100
    
    def analyze_momentum(self) -> Dict[str, Any]:
        """Analyze market momentum using moving averages."""
        return {
            'is_bullish': self.is_bullish,
            'short_ma': self.short_ma,
            'long_ma': self.long_ma
        }
    
    def to_markdown(self) -> str:
        """Generate markdown report using Telegram Markdown V1 format."""
        from stunk.config import SHORT_MA_PERIOD, LONG_MA_PERIOD
        
        price_change = self.calculate_price_change()
        momentum = self.analyze_momentum()
        
        # Determine emoji based on price change
        price_emoji = '📈' if price_change > 0 else '📉'
        trend_emoji = '📈' if self.is_bullish else '📉'
        
        # Format the report using Telegram Markdown V1 compatible formatting
        report = [
            '*Market Analysis*',
            '',
            f'*Price Change* {price_emoji}',
            f'Current Price: `${self.current_price:.2f}`',
            f'Change: `{price_change:+.2f}%`',
            '',
            '*Market Momentum*',
            f'Short MA ({SHORT_MA_PERIOD}d): `${self.short_ma:.2f}`',
            f'Long MA ({LONG_MA_PERIOD}d): `${self.long_ma:.2f}`',
            f'Trend: _{self.is_bullish and "Bullish" or "Bearish"} {trend_emoji}_'
        ]
        
        return '\n'.join(report)
