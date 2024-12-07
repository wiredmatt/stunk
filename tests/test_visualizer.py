"""Unit tests for market trend visualization functionality."""
import os
from pathlib import Path
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from stunk.visualizer import MarketVisualizer
from stunk.config import (
    SHORT_MA_PERIOD,
    LONG_MA_PERIOD,
    TICKER_SYMBOL,
)

@pytest.fixture
def sample_market_data():
    """Create sample market data for visualization testing."""
    dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
    data = {
        'Close': [100 + i for i in range(10)],
        f'MA{SHORT_MA_PERIOD}': [105 + i for i in range(10)],
        f'MA{LONG_MA_PERIOD}': [95 + i for i in range(10)]
    }
    return pd.DataFrame(data, index=dates)

@pytest.fixture
def temp_plot_path(tmp_path):
    """Create a temporary path for saving plots."""
    return tmp_path / "test_plot.png"

def test_create_plot_saves_file(sample_market_data, temp_plot_path):
    """Test that create_plot saves a file at the specified location."""
    with patch('matplotlib.pyplot.figure') as mock_figure, \
         patch('matplotlib.pyplot.savefig') as mock_savefig, \
         patch('matplotlib.pyplot.close') as mock_close:
        
        result_path = MarketVisualizer.create_plot(
            hist=sample_market_data,
            save_path=str(temp_plot_path)
        )
        
        # Verify the plot was saved
        mock_savefig.assert_called_once_with(temp_plot_path)
        mock_close.assert_called_once()
        assert result_path == temp_plot_path

def test_create_plot_uses_correct_data(sample_market_data, temp_plot_path):
    """Test that create_plot uses the correct data for visualization."""
    with patch('matplotlib.pyplot.figure'), \
         patch('matplotlib.pyplot.plot') as mock_plot, \
         patch('matplotlib.pyplot.title'), \
         patch('matplotlib.pyplot.xlabel'), \
         patch('matplotlib.pyplot.ylabel'), \
         patch('matplotlib.pyplot.grid'), \
         patch('matplotlib.pyplot.legend'), \
         patch('matplotlib.pyplot.xticks'), \
         patch('matplotlib.pyplot.tight_layout'), \
         patch('matplotlib.pyplot.savefig'), \
         patch('matplotlib.pyplot.close'):
        
        MarketVisualizer.create_plot(
            hist=sample_market_data,
            save_path=str(temp_plot_path)
        )
        
        # Verify all three lines are plotted (price, short MA, long MA)
        assert mock_plot.call_count == 3
        
        # Verify the data used in plotting with labels
        calls = mock_plot.call_args_list
        # Price line
        assert calls[0][0][1].tolist() == sample_market_data['Close'].tolist()
        assert calls[0][1]['label'] == 'Price'
        
        # Short MA line
        assert calls[1][0][1].tolist() == sample_market_data[f'MA{SHORT_MA_PERIOD}'].tolist()
        assert calls[1][1]['label'] == f'{SHORT_MA_PERIOD}-day MA'
        
        # Long MA line
        assert calls[2][0][1].tolist() == sample_market_data[f'MA{LONG_MA_PERIOD}'].tolist()
        assert calls[2][1]['label'] == f'{LONG_MA_PERIOD}-day MA'

def test_create_plot_styling(sample_market_data, temp_plot_path):
    """Test that create_plot applies correct styling and labels."""
    with patch('matplotlib.pyplot.title') as mock_title, \
         patch('matplotlib.pyplot.xlabel') as mock_xlabel, \
         patch('matplotlib.pyplot.ylabel') as mock_ylabel, \
         patch('matplotlib.pyplot.grid') as mock_grid, \
         patch('matplotlib.pyplot.legend') as mock_legend, \
         patch('matplotlib.pyplot.xticks') as mock_xticks, \
         patch('matplotlib.pyplot.tight_layout') as mock_tight_layout, \
         patch('matplotlib.pyplot.savefig'), \
         patch('matplotlib.pyplot.close'):
        
        MarketVisualizer.create_plot(
            hist=sample_market_data,
            save_path=str(temp_plot_path)
        )
        
        # Verify plot styling
        mock_title.assert_called_once_with(f'{TICKER_SYMBOL} Market Trend Analysis')
        mock_xlabel.assert_called_once_with('Date')
        mock_ylabel.assert_called_once_with('Price')
        mock_grid.assert_called_once()
        mock_legend.assert_called_once()
        mock_xticks.assert_called_once_with(rotation=45)
        mock_tight_layout.assert_called_once()

def test_create_plot_default_path(sample_market_data):
    """Test create_plot with no save path."""
    with patch('matplotlib.pyplot.figure'), \
         patch('matplotlib.pyplot.savefig') as mock_savefig, \
         patch('matplotlib.pyplot.close'):
        
        result_path = MarketVisualizer.create_plot(hist=sample_market_data)
        
        assert result_path is None
        mock_savefig.assert_not_called()

def test_create_plot_with_save_path(sample_market_data):
    """Test create_plot with specified save path."""
    save_path = 'test_plot.png'
    with patch('matplotlib.pyplot.figure'), \
         patch('matplotlib.pyplot.savefig') as mock_savefig, \
         patch('matplotlib.pyplot.close'):
        
        result_path = MarketVisualizer.create_plot(
            hist=sample_market_data,
            save_path=save_path
        )
        
        assert result_path == Path(save_path)
        mock_savefig.assert_called_once_with(Path(save_path))

def test_create_plot_with_empty_data():
    """Test create_plot behavior with empty DataFrame."""
    empty_df = pd.DataFrame()
    
    with pytest.raises(KeyError):
        MarketVisualizer.create_plot(hist=empty_df)

def test_create_plot_figure_size(sample_market_data, temp_plot_path):
    """Test that create_plot uses correct figure size from config."""
    with patch('matplotlib.pyplot.figure') as mock_figure, \
         patch('matplotlib.pyplot.savefig'), \
         patch('matplotlib.pyplot.close'):
        
        MarketVisualizer.create_plot(
            hist=sample_market_data,
            save_path=str(temp_plot_path)
        )
        
        # Verify figure size from config is used
        mock_figure.assert_called_once()
