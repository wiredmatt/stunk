"""Database session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import logging

from stunk.config import DATABASE_URL


logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def DBSession() -> Session:
    """Create a new database session.
    
    Returns:
        SQLAlchemy Session object
    """
    try:
        session = SessionLocal()
        return session
    except Exception as e:
        logger.error(f"Failed to connect to database at {DATABASE_URL}: {e}")
        raise
