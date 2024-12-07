"""Market trend visualization functionality."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from stunk.config import (
    FIGURE_SIZE,
    COLORS,
    SHORT_MA_PERIOD,
    LONG_MA_PERIOD,
    TICKER_SYMBOL,
)

class MarketVisualizer:
    """Creates visualizations of market trends."""
    
    @staticmethod
    def create_plot(
        hist: pd.DataFrame,
        save_path: str | None = None
    ) -> Path:
        """Create and save a visualization of the market trend."""
        plt.figure(figsize=FIGURE_SIZE)
        
        # Plot price and moving averages
        plt.plot(hist.index, hist['Close'], label='Price', color=COLORS['price'])
        plt.plot(hist.index, hist[f'MA{SHORT_MA_PERIOD}'], 
                label=f'{SHORT_MA_PERIOD}-day MA', color=COLORS['short_ma'])
        plt.plot(hist.index, hist[f'MA{LONG_MA_PERIOD}'], 
                label=f'{LONG_MA_PERIOD}-day MA', color=COLORS['long_ma'])
        
        # Customize the plot
        plt.title(f'{TICKER_SYMBOL} Market Trend Analysis')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.grid(True, linestyle='--', alpha=0.7, color=COLORS['grid'])
        plt.legend()
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Save the plot
        if save_path:
            save_path = Path(save_path)
            plt.savefig(save_path)
        plt.close()
        
        return save_path
