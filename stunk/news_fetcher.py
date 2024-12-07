"""News fetching functionality."""
from datetime import datetime, timedelta
import os
from typing import List, Optional

from newsapi import NewsApiClient

from stunk.config import NEWS_QUERIES, NEWS_RESULTS_LIMIT, NEWS_LOOKBACK_DAYS
from stunk.models import NewsArticle
from stunk.storage.cache import Cache
from stunk.storage.models import NewsArticleModel, Session as DBSession


class NewsFetcher:
    """Fetches relevant news articles based on market trend."""
    
    def __init__(self):
        self.api_key = os.getenv('NEWS_API_KEY')
        if not self.api_key:
            raise ValueError("NEWS_API_KEY environment variable not set")
        
        self.client = NewsApiClient(api_key=self.api_key)
        self.cache = Cache()
        self.db = DBSession()
    
    def get_news(self, is_bullish: bool) -> List[NewsArticle]:
        """Fetch news articles based on market sentiment."""
        # Try cache first
        cached_news = self.cache.get_news(is_bullish)
        if cached_news:
            return cached_news

        # Try database next
        db_news = self._get_from_db(is_bullish)
        if db_news:
            # Cache the database results
            self.cache.set_news(db_news, is_bullish)
            return db_news

        # Finally, fetch from API
        return self._fetch_from_api(is_bullish)

    def _get_from_db(self, is_bullish: bool) -> List[NewsArticle]:
        """Get news articles from database."""
        week_ago = datetime.now() - timedelta(days=NEWS_LOOKBACK_DAYS)
        articles = (
            self.db.query(NewsArticleModel)
            .filter(
                NewsArticleModel.sentiment == is_bullish,
                NewsArticleModel.publish_date >= week_ago
            )
            .order_by(NewsArticleModel.publish_date.desc())
            .limit(NEWS_RESULTS_LIMIT)
            .all()
        )
        return [
            NewsArticle(
                title=article.title,
                url=article.url,
                date=article.publish_date.strftime('%Y-%m-%d')
            ) for article in articles
        ]

    def _fetch_from_api(self, is_bullish: bool) -> List[NewsArticle]:
        """Fetch news from API and store in database and cache."""
        try:
            query = NEWS_QUERIES['bullish'] if is_bullish else NEWS_QUERIES['bearish']
            week_ago = (datetime.now() - timedelta(days=NEWS_LOOKBACK_DAYS)).strftime('%Y-%m-%d')
            
            response = self.client.get_everything(
                q=query,
                from_param=week_ago,
                language='en',
                sort_by='relevancy',
                page_size=NEWS_RESULTS_LIMIT
            )
            
            articles = []
            for article in response['articles']:
                # Parse the datetime, handling any ISO format
                published_at = article['publishedAt'].replace('Z', '+00:00')
                if '.' in published_at:  # Handle milliseconds
                    published_at = published_at.split('.')[0] + '+00:00'
                publish_date = datetime.fromisoformat(published_at)

                # Create NewsArticle instance
                news_article = NewsArticle(
                    title=article['title'],
                    url=article['url'],
                    date=publish_date.strftime('%Y-%m-%d')
                )
                articles.append(news_article)

                # Store in database
                db_article = NewsArticleModel(
                    title=article['title'],
                    url=article['url'],
                    publish_date=publish_date,
                    sentiment=is_bullish
                )
                self.db.add(db_article)
            
            self.db.commit()
            
            # Store in cache
            self.cache.set_news(articles, is_bullish)
            
            return articles
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []

    def close(self):
        """Close database session."""
        if hasattr(self, 'db'):
            self.db.close()

    def __del__(self):
        """Clean up resources."""
        self.close()
