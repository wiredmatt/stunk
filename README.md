# Market Trend Analyzer

A Python tool that analyzes global market trends using the VWRA.L ETF (Vanguard FTSE All-World UCITS ETF) and provides relevant market news.

## Features

- Market trend analysis using price movement and moving averages
- Visual representation of market trends
- Relevant news articles based on market sentiment
- Configurable analysis parameters

## Installation

1. Clone the repository
2. Install dependencies using Poetry:
```bash
poetry install
```

3. Set up your NewsAPI key:
   - Sign up at [NewsAPI](https://newsapi.org) to get a free API key
   - Create a `.env` file in the project root
   - Add your API key: `NEWS_API_KEY=your_api_key_here`

## Usage

Run the analysis:
```bash
poetry run market_trend
```

The tool will:
1. Analyze the market trend using VWRA.L data
2. Generate a visualization (saved as market_trend.png)
3. Display relevant market news

## Project Structure

- `stunk/`
  - `config.py`: Configuration settings
  - `market_trend.py`: Main entry point
  - `market_analyzer.py`: Market trend analysis logic
  - `visualizer.py`: Market visualization tools
  - `news_fetcher.py`: News fetching functionality
  - `utils.py`: Utility functions
  - `telegram_bot.py`: Telegram bot integration
  - `models.py`: Data Models and Utility classes
  - `storage/`
    - `init_db.py`: Database initialization script
    - `models.py`: Actual Database Models
    - `database.py`: SQLAlchemy session management
    - `cache.py`: Cache implementation
    - `connections.py`: Database & Cache connection management

## Configuration

Adjust analysis parameters in `config.py`:
- Analysis period
- Moving average periods
- Visualization settings
- News search queries