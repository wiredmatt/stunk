"""Connection management for database and cache."""
from typing import Optional
import logging

from sqlalchemy.orm import Session

from stunk.storage.database import DBSession
from stunk.storage.cache import Cache


logger = logging.getLogger(__name__)


class ConnectionManager:
    """Singleton manager for database and cache connections."""
    
    _instance: Optional['ConnectionManager'] = None
    _db: Optional[Session] = None
    _cache: Optional[Cache] = None
    
    def __new__(cls) -> 'ConnectionManager':
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'ConnectionManager':
        """Get the singleton instance."""
        return cls()
    
    @classmethod
    def reset(cls):
        """Reset the singleton instance. Mainly used for testing."""
        if cls._instance:
            cls._instance.close()
        cls._instance = None
        cls._db = None
        cls._cache = None
    
    @classmethod
    def set_test_instances(cls, db: Optional[Session] = None, cache: Optional[Cache] = None):
        """Set test instances for database and cache. Used for testing."""
        cls.reset()
        instance = cls.get_instance()
        if db is not None:
            cls._db = db
        if cache is not None:
            cls._cache = cache
    
    @property
    def db(self) -> Session:
        """Get database session, creating if needed."""
        if self._db is None:
            self._db = DBSession()
            logger.debug("Created new database session")
        return self._db
    
    @property
    def cache(self) -> Cache:
        """Get cache connection, creating if needed."""
        if self._cache is None:
            self._cache = Cache()
            logger.debug("Created new cache connection")
        return self._cache
    
    def close(self):
        """Close all connections."""
        if self._db:
            try:
                self._db.close()
                logger.debug("Closed database session")
            except Exception as e:
                logger.error(f"Error closing database session: {e}")
            self._db = None
            
        if self._cache:
            try:
                self._cache.close()
                logger.debug("Closed cache connection")
            except Exception as e:
                logger.error(f"Error closing cache connection: {e}")
            self._cache = None
