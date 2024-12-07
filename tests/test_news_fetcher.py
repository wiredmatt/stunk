"""Unit tests for news fetcher functionality."""
import os
from datetime import datetime
import pytest
from unittest.mock import patch, MagicMock

from stunk.news_fetcher import NewsArticle, NewsFetcher
from stunk.config import NEWS_QUERIES, NEWS_RESULTS_LIMIT


@pytest.fixture
def sample_news_article():
    """Create a sample news article."""
    return NewsArticle(
        title="Test Market News",
        url="http://example.com/news",
        date="2024-12-01"
    )


@pytest.fixture
def mock_news_api_response():
    """Create a mock news API response."""
    return {
        'status': 'ok',
        'articles': [
            {
                'title': 'Bullish Market Trends',
                'url': 'http://example.com/bullish',
                'publishedAt': '2024-12-01T12:00:00Z'
            },
            {
                'title': 'Economic Growth',
                'url': 'http://example.com/growth',
                'publishedAt': '2024-12-02T15:30:00Z'
            }
        ]
    }


@pytest.fixture
def mock_cache():
    """Create a mock cache."""
    cache = MagicMock()
    cache.get_news.return_value = None
    return cache


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = MagicMock()
    session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    return session


def test_news_article_to_markdown(sample_news_article):
    """Test NewsArticle markdown formatting."""
    markdown = sample_news_article.to_markdown()
    assert "📰 [Test Market News](http://example.com/news)" in markdown
    assert "📅 2024-12-01" in markdown


def test_news_fetcher_init_no_api_key():
    """Test NewsFetcher initialization with missing API key."""
    with patch.dict(os.environ, clear=True):
        with pytest.raises(ValueError) as exc_info:
            NewsFetcher()
        assert "NEWS_API_KEY environment variable not set" in str(exc_info.value)


def test_news_fetcher_init_with_api_key():
    """Test NewsFetcher initialization with API key."""
    with patch.dict(os.environ, {'NEWS_API_KEY': 'test_key'}):
        fetcher = NewsFetcher()
        assert fetcher.api_key == 'test_key'


def test_get_news_bullish(mock_news_api_response, mock_cache, mock_db_session):
    """Test fetching bullish news articles."""
    with patch.dict(os.environ, {'NEWS_API_KEY': 'test_key'}):
        with patch('stunk.news_fetcher.Cache', return_value=mock_cache), \
             patch('stunk.news_fetcher.DBSession', return_value=mock_db_session):
            fetcher = NewsFetcher()
            with patch.object(fetcher.client, 'get_everything', return_value=mock_news_api_response):
                articles = fetcher.get_news(is_bullish=True)

                assert len(articles) == 2
                assert all(isinstance(article, NewsArticle) for article in articles)
                # Verify bullish query was used
                fetcher.client.get_everything.assert_called_once()
                args = fetcher.client.get_everything.call_args[1]
                assert NEWS_QUERIES['bullish'] in args['q']


def test_get_news_bearish(mock_news_api_response, mock_cache, mock_db_session):
    """Test fetching bearish news articles."""
    with patch.dict(os.environ, {'NEWS_API_KEY': 'test_key'}):
        with patch('stunk.news_fetcher.Cache', return_value=mock_cache), \
             patch('stunk.news_fetcher.DBSession', return_value=mock_db_session):
            fetcher = NewsFetcher()
            with patch.object(fetcher.client, 'get_everything', return_value=mock_news_api_response):
                articles = fetcher.get_news(is_bullish=False)

                assert len(articles) == 2
                assert all(isinstance(article, NewsArticle) for article in articles)
                # Verify bearish query was used
                fetcher.client.get_everything.assert_called_once()
                args = fetcher.client.get_everything.call_args[1]
                assert NEWS_QUERIES['bearish'] in args['q']


def test_get_news_api_error(mock_cache, mock_db_session):
    """Test handling of API errors."""
    with patch.dict(os.environ, {'NEWS_API_KEY': 'test_key'}):
        with patch('stunk.news_fetcher.Cache', return_value=mock_cache), \
             patch('stunk.news_fetcher.DBSession', return_value=mock_db_session):
            fetcher = NewsFetcher()
            with patch.object(fetcher.client, 'get_everything', side_effect=Exception("API Error")):
                articles = fetcher.get_news(is_bullish=True)
                assert articles == []


def test_get_news_date_parsing(mock_cache, mock_db_session):
    """Test correct parsing of API date format."""
    api_response = {
        'status': 'ok',
        'articles': [{
            'title': 'Test Article',
            'url': 'http://example.com',
            'publishedAt': '2024-12-01T15:30:00.123Z'  # Complex timestamp
        }]
    }
    
    with patch.dict(os.environ, {'NEWS_API_KEY': 'test_key'}):
        with patch('stunk.news_fetcher.Cache', return_value=mock_cache), \
             patch('stunk.news_fetcher.DBSession', return_value=mock_db_session):
            fetcher = NewsFetcher()
            with patch.object(fetcher.client, 'get_everything', return_value=api_response):
                articles = fetcher.get_news(is_bullish=True)
                assert len(articles) == 1
                assert articles[0].date == '2024-12-01'  # Should be formatted as YYYY-MM-DD
