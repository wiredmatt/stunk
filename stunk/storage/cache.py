"""Cache implementation using Redis."""
import json
from datetime import datetime, timedelta
from typing import Optional, List, Any, Dict, Union

import redis
import pandas as pd
import logging

from stunk.models import NewsArticle, MarketAnalysis
from stunk.config import REDIS_URL, NEWS_TTL_CACHE, MARKET_CACHE_TTL
from stunk.utils import convert_numpy_types

logger = logging.getLogger(__name__)

class Cache:
    """Redis cache wrapper for storing market and news data."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize cache with optional Redis client.
        
        Args:
            redis_client: Optional Redis client instance. If not provided,
                         creates a new client using REDIS_URL.
        """
        self.redis = redis_client if redis_client else redis.from_url(REDIS_URL)
        try:
            # Test Redis connection
            self.redis.ping()
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis at {REDIS_URL}: {e}")
            raise

    def close(self):
        """Close Redis connection."""
        try:
            self.redis.close()
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
    
    def _serialize_news(self, articles: List[NewsArticle]) -> str:
        """Serialize news articles to JSON."""
        return json.dumps([{
            'title': article.title,
            'url': article.url,
            'date': article.date
        } for article in articles])
    
    def _deserialize_news(self, data: str) -> List[NewsArticle]:
        """Deserialize JSON to news articles."""
        articles_data = json.loads(data)
        return [NewsArticle(**article) for article in articles_data]
    
    def _serialize_market_data(self, analysis: MarketAnalysis) -> str:
        """Serialize market analysis to JSON."""
        hist_data = analysis.historical_data
        hist_dict = {
            'dates': hist_data.index.strftime('%Y-%m-%d %H:%M:%S%z').tolist(),
            'data': {}
        }
        
        for column in hist_data.columns:
            values = hist_data[column].tolist()
            # Convert NaN to None for JSON compatibility
            values = [None if pd.isna(v) else float(v) for v in values]
            hist_dict['data'][column] = values

        return json.dumps({
            'current_price': float(analysis.current_price),
            'start_price': float(analysis.start_price),
            'short_ma': float(analysis.short_ma),
            'long_ma': float(analysis.long_ma),
            'historical_data': hist_dict,
            'is_bullish': bool(analysis.is_bullish)
        })
    
    def _deserialize_market_data(self, data: Optional[bytes]) -> Optional[Dict[str, Any]]:
        """Deserialize JSON to market data dictionary.
        
        Args:
            data: JSON string from Redis
            
        Returns:
            Market data dictionary if successful, None otherwise
        """
        if not data:
            return None
            
        try:
            # Decode bytes to string and parse JSON
            market_data = json.loads(data.decode('utf-8'))
            
            # Validate structure
            required_keys = {'current_price', 'start_price', 'short_ma', 'long_ma', 'historical_data', 'is_bullish'}
            if not all(key in market_data for key in required_keys):
                return None
                
            return market_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from cache: {e}")
            return None
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode bytes from cache: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error deserializing market data: {e}", exc_info=True)
            return None
    
    def get_news(self, is_bullish: bool) -> Optional[List[NewsArticle]]:
        """Get cached news articles."""
        key = f'news:{"bullish" if is_bullish else "bearish"}'
        data = self.redis.get(key)
        return self._deserialize_news(data) if data else None
    
    def set_news(self, articles: List[NewsArticle], is_bullish: bool):
        """Cache news articles."""
        key = f'news:{"bullish" if is_bullish else "bearish"}'
        self.redis.setex(
            key,
            NEWS_TTL_CACHE,
            self._serialize_news(articles)
        )
    
    def get_market_data(self, symbol: Optional[str] = None) -> Optional[MarketAnalysis]:
        """Get cached market data.
        
        Args:
            symbol: Optional stock symbol. If not provided, uses default symbol.
                   
        Returns:
            Market analysis if found in cache, None otherwise.
        """
        try:
            key = f"market:{symbol}" if symbol else "market"
            data = self.redis.get(key)
            if data:
                try:
                    market_data = self._deserialize_market_data(data)
                    if market_data is None:
                        return None
                    hist_dict = market_data.pop('historical_data')
                    
                    # Reconstruct DataFrame
                    dates = pd.to_datetime(hist_dict['dates'])
                    df = pd.DataFrame(hist_dict['data'], index=dates)
                    market_data['historical_data'] = df
                    
                    return MarketAnalysis(**market_data)
                except Exception as e:
                    logger.error(f"Error deserializing cached data: {e}", exc_info=True)
                    # If deserialization fails, treat it as a cache miss
                    return None
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting market data from cache: {e}", exc_info=True)
            return None
    
    def set_market_data(self, symbol: Optional[str] = None, analysis: MarketAnalysis = None, data: Dict[str, Any] = None, ttl: Optional[int] = None) -> None:
        """Cache market data.
        
        Args:
            symbol: Optional stock symbol. If not provided, uses default symbol.
            analysis: Market analysis to cache
            data: Market data dictionary to cache
            ttl: Optional time-to-live in seconds. If not provided, uses default TTL.
        """
        if analysis and data:
            raise ValueError("Only one of analysis or data can be provided")
        
        try:
            if analysis:
                data = self._serialize_market_data(analysis)
            elif data:
                # Validate data structure
                required_keys = {'current_price', 'start_price', 'short_ma', 'long_ma', 'historical_data', 'is_bullish'}
                if not all(key in data for key in required_keys):
                    missing = required_keys - set(data.keys())
                    raise ValueError(f"Missing required keys in market data: {missing}")
                data = json.dumps(data)
            else:
                raise ValueError("Either analysis or data must be provided")
            
            key = f"market:{symbol}" if symbol else "market"
            # Convert timedelta to seconds for Redis
            ttl_seconds = int(ttl or MARKET_CACHE_TTL.total_seconds())
            self.redis.setex(key, ttl_seconds, data)
        except Exception as e:
            logger.error(f"Error setting market data in cache: {e}", exc_info=True)
            raise
