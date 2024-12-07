"""Test configuration and fixtures."""
import os
from datetime import datetime
from unittest.mock import MagicMock

import pandas as pd
import pytest
from redis import Redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from stunk.storage.models import Base


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis_mock = MagicMock(spec=Redis)
    redis_mock.get.return_value = None
    return redis_mock


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session_mock = MagicMock(spec=Session)
    session_mock.query.return_value.filter.return_value.first.return_value = None
    return session_mock


@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    from stunk.config import SHORT_MA_PERIOD, LONG_MA_PERIOD

    dates = pd.date_range(start='2024-01-01', end='2024-01-10')
    data = {
        'Close': [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
    }
    df = pd.DataFrame(data, index=dates)
    
    # Calculate moving averages - short MA should be higher than long MA for bullish trend
    df[f'MA{SHORT_MA_PERIOD}'] = df['Close'] + 1.0  # Higher than close
    df[f'MA{LONG_MA_PERIOD}'] = df['Close'] - 1.0   # Lower than close
    
    return df


@pytest.fixture
def sample_news_data():
    """Sample news data for testing."""
    return [
        {
            'title': 'Test Article 1',
            'url': 'http://example.com/1',
            'publishedAt': '2024-01-01T12:00:00Z'
        },
        {
            'title': 'Test Article 2',
            'url': 'http://example.com/2',
            'publishedAt': '2024-01-01T13:00:00Z'
        }
    ]


@pytest.fixture
def test_db():
    """Create a test database."""
    # Use SQLite in-memory database for testing
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)
