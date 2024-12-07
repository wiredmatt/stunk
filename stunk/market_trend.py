"""Market trend analysis and reporting."""
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple, Union
import logging
import os
import re

import matplotlib.pyplot as plt

from stunk.market_analyzer import MarketAnalyzer
from stunk.models import NewsArticle
from stunk.news_fetcher import NewsFetcher
from stunk.config import SHORT_MA_PERIOD, LONG_MA_PERIOD


def telegram_to_standard_markdown(text: str) -> str:
    """Convert Telegram markdown to standard markdown format.
    
    Args:
        text: Text in Telegram markdown format
        
    Returns:
        Text in standard markdown format
    """
    # Convert Telegram's *bold* to standard markdown **bold**
    text = re.sub(r'(?<!\\)\*(.+?)(?<!\\)\*', r'**\1**', text)
    
    # Convert Telegram's _italic_ to standard markdown *italic*
    text = re.sub(r'(?<!\\)_(.+?)(?<!\\)_', r'*\1*', text)
    
    # Add newlines to paragraphs
    text = re.sub(r'(?<!\\)\n(?!\n)', '\n\n', text)
    return text


def generate_market_report(should_save_file: bool = True) -> Tuple[str, Optional[Union[Path, BytesIO]]]:
    """Generate market analysis report with visualization.
    
    Args:
        should_save_file: If True, save visualization to disk. If False, return in-memory buffer.
    
    Returns:
        Tuple of (report text, visualization path or buffer)
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Get market analysis
        analyzer = MarketAnalyzer()
        analysis = analyzer.analyze()
        if not analysis:
            logger.error("Failed to get market analysis")
            return "❌ Failed to fetch market data.", None

        # Get news articles based on market trend
        news_fetcher = NewsFetcher()
        news_articles = news_fetcher.get_news(analysis.is_bullish)
        news_warning = ""
        if not news_articles:
            news_warning = "\n⚠️ No relevant news articles found."
            
        # Create visualization
        plt.figure(figsize=(12, 6))
        
        # Plot price and moving averages
        hist_data = analysis.historical_data
        plt.plot(hist_data.index, hist_data['Close'], label='Price')
        plt.plot(hist_data.index, hist_data[f'MA{SHORT_MA_PERIOD}'], label=f'{SHORT_MA_PERIOD}-day MA')
        plt.plot(hist_data.index, hist_data[f'MA{LONG_MA_PERIOD}'], label=f'{LONG_MA_PERIOD}-day MA')
        
        plt.title('Market Trend Analysis')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        
        # Save the plot to file or buffer
        if should_save_file:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            reports_dir = Path("reports") / timestamp
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Save visualization
            plot_path = reports_dir / "viz.png"
            plt.savefig(plot_path)
            plt.close()
            viz_output = plot_path
        else:
            # Save to in-memory buffer for Telegram
            buf = BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            viz_output = buf
        
        # Build the complete report
        report_parts = [
            # Market Analysis
            analysis.to_markdown(),
            
            # News Warning (if any)
            news_warning,
            
            # News Section
            "\n*Recent Market News*" if news_articles else "",
            *[article.to_markdown() for article in news_articles]
        ]
        
        # Join all parts, filtering out empty strings
        report = "\n".join(part for part in report_parts if part)
        
        # Save report to file if requested
        if should_save_file:
            report_path = reports_dir / "report.md"
            # Convert to standard markdown before saving to file
            standard_md = telegram_to_standard_markdown(report)
            # Add image link to the markdown report
            standard_md += f"\n\n![Market Trend Analysis](viz.png)\n"
            report_path.write_text(standard_md)
        
        return report, viz_output
    except Exception as e:
        logger.error(f"Error generating market report: {e}", exc_info=True)
        return "❌ Failed to generate market report.", None
    finally:
        # Connections will be cleaned up by MarketAnalyzer.__del__
        pass


def main():
    """Run the market trend analysis."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Generating market trend report...")
        report, viz_path = generate_market_report(should_save_file=True)
        
        if viz_path and isinstance(viz_path, Path):
            logger.info(f"Report saved to {viz_path.parent}")
            logger.info(f"Report: {viz_path.parent / 'report.md'}")
            logger.info(f"Vizualization: {viz_path}")
        else:
            logger.error("Failed to generate report")
            
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)


if __name__ == "__main__":
    main()
