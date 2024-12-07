"""Unit tests for market analyzer functionality."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, ANY

from stunk.market_analyzer import MarketAnalysis, MarketAnalyzer
from stunk.config import SHORT_MA_PERIOD, LONG_MA_PERIOD, TICKER_SYMBOL, ANALYSIS_PERIOD_DAYS
from stunk.storage.models import MarketDataModel
from stunk.storage.connections import ConnectionManager


@pytest.fixture
def sample_market_data():
    """Create sample market data for testing."""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    data = {
        'Close': [100 + i * 0.1 for i in range(100)],  # Upward trend
        f'MA{SHORT_MA_PERIOD}': [105 + i * 0.1 for i in range(100)],
        f'MA{LONG_MA_PERIOD}': [95 + i * 0.1 for i in range(100)]
    }
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def mock_redis():
    """Mock Redis client that always returns cache miss."""
    redis = MagicMock()
    redis.get.return_value = None  # Simulate cache miss
    redis.get_market_data = MagicMock(return_value=None)  # Ensure cache miss
    return redis


@pytest.fixture
def mock_db_session():
    """Mock database session that always returns no data."""
    session = MagicMock()
    # Setup query chain to return None
    query = MagicMock()
    order_by = MagicMock()
    order_by.first.return_value = None
    query.order_by.return_value = order_by
    session.query.return_value = query
    session.add = MagicMock()
    session.commit = MagicMock()
    return session


@pytest.fixture(autouse=True)
def setup_test_connections(mock_redis, mock_db_session):
    """Setup test connections before each test and cleanup after."""
    ConnectionManager.set_test_instances(db=mock_db_session, cache=mock_redis)
    yield
    ConnectionManager.reset()


def test_market_analysis_price_change(sample_market_data):
    """Test price change calculation."""
    analysis = MarketAnalysis(
        current_price=110.0,
        start_price=100.0,
        short_ma=105.0,
        long_ma=95.0,
        historical_data=sample_market_data,
        is_bullish=True
    )
    assert analysis.calculate_price_change() == 10.0


def test_market_analysis_momentum(sample_market_data):
    """Test momentum analysis."""
    analysis = MarketAnalysis(
        current_price=110.0,
        start_price=100.0,
        short_ma=105.0,
        long_ma=95.0,
        historical_data=sample_market_data,
        is_bullish=True
    )
    assert analysis.is_bullish is True


def test_market_analysis_to_markdown(sample_market_data):
    """Test markdown report generation."""
    analysis = MarketAnalysis(
        current_price=110.0,
        start_price=100.0,
        short_ma=105.0,
        long_ma=95.0,
        historical_data=sample_market_data,
        is_bullish=True
    )
    markdown = analysis.to_markdown()
    assert "Current Price" in markdown
    assert "Price Change" in markdown
    assert "Trend" in markdown


@patch('yfinance.Ticker')
def test_market_analyzer_get_historical_data(mock_ticker, caplog):
    """Test historical data fetching."""
    import logging
    caplog.set_level(logging.DEBUG)
    
    # Setup mock ticker with datetime index
    end_date = datetime.now()
    start_date = end_date - timedelta(days=ANALYSIS_PERIOD_DAYS + 10)
    dates = pd.date_range(start=start_date, end=end_date, periods=ANALYSIS_PERIOD_DAYS)
    
    # Create test data with linear trend for easy verification
    close_prices = np.linspace(100, 200, len(dates))
    mock_hist = pd.DataFrame({
        'Close': close_prices,
        'Open': close_prices - 1,
        'High': close_prices + 2,
        'Low': close_prices - 2,
        'Volume': np.ones_like(close_prices) * 1000,
        'Dividends': np.zeros_like(close_prices),
        'Stock Splits': np.zeros_like(close_prices)
    }, index=dates)
    
    # Configure mock to return our test data
    mock_ticker_instance = MagicMock()
    mock_ticker_instance.history = MagicMock(return_value=mock_hist)
    mock_ticker.return_value = mock_ticker_instance
    
    # Get historical data through MarketAnalyzer
    analyzer = MarketAnalyzer()
    result = analyzer.get_historical_data()
    
    # Print debug info
    print("\nTest Debug Info:")
    print(f"Mock ticker called with symbol: {TICKER_SYMBOL}")
    print(f"Mock history called: {mock_ticker_instance.history.called}")
    print(f"Mock history call args: {mock_ticker_instance.history.call_args}")
    print(f"Mock history call count: {mock_ticker_instance.history.call_count}")
    print("\nMock data shape:", mock_hist.shape)
    print("Mock data columns:", mock_hist.columns)
    print("Mock data head:")
    print(mock_hist.head())
    print("\nResult data shape:", result.shape if result is not None else None)
    print("Result columns:", result.columns if result is not None else None)
    print("Result head:")
    print(result.head() if result is not None else None)
    print("\nLog messages:")
    for record in caplog.records:
        print(f"{record.levelname}: {record.message}")
    
    # Basic assertions
    assert result is not None, "Result should not be None"
    assert isinstance(result, pd.DataFrame), "Result should be a DataFrame"
    assert not result.empty, "Result should not be empty"
    assert 'Close' in result.columns, "Result should have Close column"
    assert f'MA{SHORT_MA_PERIOD}' in result.columns, f"Result should have MA{SHORT_MA_PERIOD} column"
    assert f'MA{LONG_MA_PERIOD}' in result.columns, f"Result should have MA{LONG_MA_PERIOD} column"
    
    # Verify Close prices match input
    pd.testing.assert_series_equal(
        result['Close'],
        mock_hist['Close'],
        check_names=False,
        check_dtype=False
    )
    
    # Calculate and verify moving averages
    expected_ma_short = mock_hist['Close'].rolling(window=SHORT_MA_PERIOD, min_periods=1).mean()
    expected_ma_long = mock_hist['Close'].rolling(window=LONG_MA_PERIOD, min_periods=1).mean()
    
    pd.testing.assert_series_equal(
        result[f'MA{SHORT_MA_PERIOD}'],
        expected_ma_short,
        check_names=False,
        check_dtype=False
    )
    pd.testing.assert_series_equal(
        result[f'MA{LONG_MA_PERIOD}'],
        expected_ma_long,
        check_names=False,
        check_dtype=False
    )
    
    # Verify yfinance was called correctly
    mock_ticker.assert_called_once_with(TICKER_SYMBOL)
    mock_ticker_instance.history.assert_called_once()
    call_args = mock_ticker_instance.history.call_args[1]  # Get kwargs
    assert 'start' in call_args, "start date should be provided"
    assert 'end' in call_args, "end date should be provided"


@patch('stunk.market_analyzer.MarketAnalyzer.get_historical_data')
def test_market_analyzer_analyze(mock_get_data, sample_market_data):
    """Test full market analysis."""
    mock_get_data.return_value = sample_market_data
    
    analyzer = MarketAnalyzer()
    result = analyzer.analyze()
    
    assert isinstance(result, MarketAnalysis)
    assert result.is_bullish is True
    assert result.current_price == sample_market_data['Close'].iloc[-1]
    assert result.start_price == sample_market_data['Close'].iloc[0]


@patch('yfinance.Ticker')
def test_market_analyzer_analyze_no_data(mock_ticker):
    """Test analysis behavior when no data is available."""
    # Configure yfinance mock to return empty DataFrame
    mock_ticker_instance = MagicMock()
    mock_ticker_instance.history = MagicMock(return_value=pd.DataFrame())
    mock_ticker.return_value = mock_ticker_instance
    
    analyzer = MarketAnalyzer()
    result = analyzer.analyze()
    assert result is None


def test_market_analyzer_calculate_moving_averages(sample_market_data):
    """Test moving average calculations."""
    analyzer = MarketAnalyzer()
    result = analyzer.calculate_moving_averages(sample_market_data)

    assert f'MA{SHORT_MA_PERIOD}' in result.columns
    assert f'MA{LONG_MA_PERIOD}' in result.columns
    assert len(result) == len(sample_market_data)
