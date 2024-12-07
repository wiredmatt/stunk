"""Database models for the application."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine
import os
from stunk.config import DATABASE_URL

class Base(DeclarativeBase):
    """Base class for all models."""
    pass

class NewsArticleModel(Base):
    """Database model for news articles."""
    __tablename__ = 'news_articles'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    publish_date = Column(DateTime, nullable=False)
    sentiment = Column(Boolean, nullable=False)  # True for bullish, False for bearish
    created_at = Column(DateTime, default=datetime.utcnow)

class MarketDataModel(Base):
    """Database model for market data."""
    __tablename__ = 'market_data'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    symbol = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    short_ma = Column(Float)
    long_ma = Column(Float)
    is_bullish = Column(Boolean)
    historical_data = Column(JSON)  # Store DataFrame as JSON
    created_at = Column(DateTime, default=datetime.utcnow)

# Create database engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(engine)
