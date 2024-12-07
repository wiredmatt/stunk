"""Unit tests for market trend functionality."""
import re
from datetime import datetime
from pathlib import Path
from io import BytesIO
import pytest
from unittest.mock import patch, MagicMock

import pandas as pd
import matplotlib.pyplot as plt

from stunk.market_trend import generate_market_report
from stunk.market_analyzer import MarketAnalysis, MarketAnalyzer
from stunk.news_fetcher import NewsArticle, NewsFetcher


def test_generate_market_report_success_no_save(sample_market_data, mock_redis, mock_db_session):
    """Test successful market report generation without saving plot."""
    with patch.object(MarketAnalyzer, 'get_historical_data') as mock_get_data, \
         patch.object(NewsFetcher, 'get_news') as mock_get_news:
        
        # Set up mocks
        mock_get_data.return_value = sample_market_data
        mock_get_news.return_value = [
            NewsArticle(
                title="Test Article 1",
                url="http://example.com/1",
                date="2024-12-01"
            ),
            NewsArticle(
                title="Test Article 2",
                url="http://example.com/2",
                date="2024-12-02"
            )
        ]
        
        # Generate report
        report, viz = generate_market_report(should_save_file=False)
        
        # Verify report content
        assert "*Market Analysis*" in report
        assert "Current Price: `$109.00`" in report  # Last price from sample_market_data
        assert "_Bullish 📈_" in report
        assert "*Recent Market News*" in report
        assert "Test Article 1" in report
        assert "Test Article 2" in report
        
        # Verify visualization is a BytesIO object
        assert isinstance(viz, BytesIO)
        
        # Clean up
        viz.close()
        plt.close()


def test_generate_market_report_success_with_save(sample_market_data, mock_redis, mock_db_session):
    """Test successful market report generation with plot saving."""
    with patch.object(MarketAnalyzer, 'get_historical_data') as mock_get_data, \
         patch.object(NewsFetcher, 'get_news') as mock_get_news:
        
        # Set up mocks
        mock_get_data.return_value = sample_market_data
        mock_get_news.return_value = [
            NewsArticle(
                title="Test Article 1",
                url="http://example.com/1",
                date="2024-12-01"
            )
        ]
        
        # Generate report
        report, viz = generate_market_report(should_save_file=True)
        
        # Verify report content
        assert "*Market Analysis*" in report
        assert "Current Price: `$109.00`" in report
        assert "_Bullish 📈_" in report
        assert "*Recent Market News*" in report
        assert "Test Article 1" in report
        
        # Verify visualization is saved as a file
        assert isinstance(viz, Path)
        assert viz.exists()
        assert viz.name == 'viz.png'
        assert viz.parent.name.isdigit()  # Timestamp directory should be all digits
        
        # Clean up
        report_path = viz.parent / "report.md"
        report_path.unlink()  # Delete report file
        viz.unlink()  # Delete visualization file
        viz.parent.rmdir()  # Delete the reports directory
        plt.close()


def test_generate_market_report_no_data(mock_redis, mock_db_session):
    """Test report generation when no market data is available."""
    with patch.object(MarketAnalyzer, 'get_historical_data', return_value=None):
        report, viz = generate_market_report()
        assert "❌ Failed to fetch market data." in report
        assert viz is None


def test_generate_market_report_no_news(sample_market_data, mock_redis, mock_db_session):
    """Test report generation when no news articles are found."""
    with patch.object(MarketAnalyzer, 'get_historical_data') as mock_get_data, \
         patch.object(NewsFetcher, 'get_news', return_value=[]) as mock_get_news:
        
        mock_get_data.return_value = sample_market_data
        
        report, viz = generate_market_report(should_save_file=False)
        assert "⚠️ No relevant news articles found." in report
        assert isinstance(viz, BytesIO)
        
        # Clean up
        viz.close()
        plt.close()
