"""Market analysis functionality."""
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any, Union

import pandas as pd
import yfinance as yf
from redis import Redis
from sqlalchemy.orm import Session

from stunk.config import (
    TICKER_SYMBOL,
    ANALYSIS_PERIOD_DAYS,
    SHORT_MA_PERIOD,
    LONG_MA_PERIOD,
)
from stunk.models import MarketAnalysis
from stunk.storage.cache import Cache
from stunk.storage.models import MarketDataModel
from stunk.storage.connections import ConnectionManager
from stunk.utils import convert_numpy_types

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    """Analyzes market trends using historical price data."""

    def __init__(self):
        """Initialize market analyzer."""
        conn_manager = ConnectionManager.get_instance()
        self.db = conn_manager.db
        self.cache = conn_manager.cache

    def __del__(self):
        """Clean up resources."""
        try:
            ConnectionManager.get_instance().close()
        except Exception as e:
            logger.error(f"Error closing connections: {e}")

    def get_historical_data(self) -> Optional[pd.DataFrame]:
        """Fetch historical market data for analysis."""
        logger = logging.getLogger(__name__)
        
        # Try cache first
        cached_data = self.cache.get_market_data()
        if cached_data is not None:
            try:
                # cached_data is a MarketAnalysis object
                return cached_data.historical_data
            except Exception as e:
                logger.error(f"Error processing cache data: {e}", exc_info=True)

        # Try database next
        try:
            db_data = self.db.query(MarketDataModel).order_by(
                MarketDataModel.timestamp.desc()
            ).first()
            if db_data and db_data.historical_data:
                df = pd.DataFrame(db_data.historical_data['data'])
                df.index = pd.to_datetime(db_data.historical_data['dates'])
                
                # Save to cache as MarketAnalysis object
                market_analysis = MarketAnalysis(
                    current_price=db_data.price,
                    start_price=float(df['Close'].iloc[0]),
                    short_ma=db_data.short_ma,
                    long_ma=db_data.long_ma,
                    historical_data=df,
                    is_bullish=db_data.is_bullish
                )
                self.cache.set_market_data(analysis=market_analysis)
                return df
        except Exception as e:
            logger.error(f"Error fetching from database: {e}", exc_info=True)

        # Finally, fetch from yfinance
        try:
            ticker = yf.Ticker(TICKER_SYMBOL)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=ANALYSIS_PERIOD_DAYS + 10)
            
            hist = ticker.history(start=start_date, end=end_date)
            
            if not hist.empty:
                if len(hist) > ANALYSIS_PERIOD_DAYS:
                    hist = hist.tail(ANALYSIS_PERIOD_DAYS)
                # Calculate moving averages
                hist = self.calculate_moving_averages(hist)
                
                # Create MarketAnalysis object
                market_analysis = MarketAnalysis(
                    current_price=float(hist['Close'].iloc[-1]),
                    start_price=float(hist['Close'].iloc[0]),
                    short_ma=float(hist[f'MA{SHORT_MA_PERIOD}'].iloc[-1]),
                    long_ma=float(hist[f'MA{LONG_MA_PERIOD}'].iloc[-1]),
                    historical_data=hist,
                    is_bullish=bool(float(hist[f'MA{SHORT_MA_PERIOD}'].iloc[-1]) > float(hist[f'MA{LONG_MA_PERIOD}'].iloc[-1]))
                )
                
                # Save to cache
                self.cache.set_market_data(analysis=market_analysis)
                
                # Save to database
                hist_dict = self.prepare_historical_data(hist)
                self.db.add(MarketDataModel(
                    timestamp=datetime.now(),
                    symbol=TICKER_SYMBOL,
                    price=market_analysis.current_price,
                    short_ma=market_analysis.short_ma,
                    long_ma=market_analysis.long_ma,
                    is_bullish=market_analysis.is_bullish,
                    historical_data=hist_dict
                ))
                self.db.commit()
                return hist
            return None
        except Exception as e:
            logger.error(f"Error fetching from yfinance: {e}", exc_info=True)
            return None

    @staticmethod
    def calculate_moving_averages(data: pd.DataFrame) -> pd.DataFrame:
        """Calculate short and long-term moving averages."""
        logger = logging.getLogger(__name__)
        try:
            df = data.copy()
            df[f'MA{SHORT_MA_PERIOD}'] = df['Close'].rolling(window=SHORT_MA_PERIOD, min_periods=1).mean()
            df[f'MA{LONG_MA_PERIOD}'] = df['Close'].rolling(window=LONG_MA_PERIOD, min_periods=1).mean()
            return df
        except Exception as e:
            logger.error(f"Error calculating moving averages: {e}", exc_info=True)
            raise

    @staticmethod
    def prepare_historical_data(hist: pd.DataFrame) -> Dict[str, Any]:
        """Convert DataFrame to a database-friendly format."""
        logger = logging.getLogger(__name__)
        try:
            result = {
                'dates': hist.index.strftime('%Y-%m-%d %H:%M:%S%z').tolist(),
                'data': {}
            }
            
            for column in hist.columns:
                result['data'][column] = convert_numpy_types(hist[column].tolist())
            
            return result
        except Exception as e:
            logger.error(f"Error preparing historical data: {e}", exc_info=True)
            raise

    def analyze(self) -> Optional[MarketAnalysis]:
        """Perform market analysis."""
        # Get historical data
        hist = self.get_historical_data()
        if hist is None or hist.empty:
            logger.error("No historical data available")
            return None

        # Calculate moving averages if not already present
        if f'MA{SHORT_MA_PERIOD}' not in hist.columns:
            hist = self.calculate_moving_averages(hist)

        # Get latest values
        try:
            current_price = float(hist['Close'].iloc[-1])
            start_price = float(hist['Close'].iloc[0])
            short_ma = float(hist[f'MA{SHORT_MA_PERIOD}'].iloc[-1])
            long_ma = float(hist[f'MA{LONG_MA_PERIOD}'].iloc[-1])
        except Exception as e:
            logger.error(f"Error getting values: {e}", exc_info=True)
            raise

        analysis = MarketAnalysis(
            current_price=current_price,
            start_price=start_price,
            short_ma=short_ma,
            long_ma=long_ma,
            historical_data=hist,
            is_bullish=short_ma > long_ma
        )
        return analysis
