"""Unit tests for telegram bot functionality."""
import logging
from pathlib import Path
from io import BytesIO
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, Chat
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from stunk.telegram_bot import (
    send_market_analysis,
    help_command,
    error_handler,
)
from stunk.config import ALLOWED_CHAT_IDS, COMMANDS


@pytest.fixture
def mock_update():
    """Create a mock telegram update."""
    update = MagicMock(spec=Update)
    update.effective_chat = MagicMock(spec=Chat)
    update.effective_chat.id = ALLOWED_CHAT_IDS[0] if ALLOWED_CHAT_IDS else 12345
    update.message = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    """Create a mock telegram context."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.application = MagicMock()
    context.application.bot = AsyncMock()
    return context


@pytest.mark.asyncio
async def test_send_market_analysis_unauthorized(mock_update, mock_context):
    """Test market analysis command with unauthorized user."""
    # Set unauthorized chat_id
    mock_update.effective_chat.id = -1
    
    await send_market_analysis(mock_update, mock_context)
    
    # Verify unauthorized message
    mock_update.message.reply_text.assert_awaited_once_with(
        "⚠️ Sorry, you are not authorized to use this bot."
    )
    # Verify no other actions were taken
    mock_context.application.bot.send_chat_action.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_market_analysis_success_file(mock_update, mock_context):
    """Test successful market analysis command with file visualization."""
    mock_report = "Test Market Report"
    mock_plot_path = Path("test_plot.png")
    
    with patch("stunk.telegram_bot.generate_market_report") as mock_generate:
        mock_generate.return_value = (mock_report, mock_plot_path)
        
        await send_market_analysis(mock_update, mock_context)
        
        # Verify typing indicator was shown
        mock_context.application.bot.send_chat_action.assert_awaited_once()
        
        # Verify plot was sent
        mock_update.message.reply_photo.assert_awaited_once()
        args = mock_update.message.reply_photo.await_args
        assert args[1]['caption'] == "Market Trend Visualization"
        
        # Verify report was sent with markdown
        mock_update.message.reply_text.assert_awaited_once_with(
            text=mock_report,
            parse_mode=ParseMode.MARKDOWN
        )


@pytest.mark.asyncio
async def test_send_market_analysis_success_buffer(mock_update, mock_context):
    """Test successful market analysis command with BytesIO visualization."""
    mock_report = "Test Market Report"
    mock_buffer = BytesIO(b"test image data")
    
    with patch("stunk.telegram_bot.generate_market_report") as mock_generate:
        mock_generate.return_value = (mock_report, mock_buffer)
        
        await send_market_analysis(mock_update, mock_context)
        
        # Verify typing indicator was shown
        mock_context.application.bot.send_chat_action.assert_awaited_once()
        
        # Verify plot was sent
        mock_update.message.reply_photo.assert_awaited_once()
        args = mock_update.message.reply_photo.await_args
        assert args[1]['caption'] == "Market Trend Visualization"
        
        # Verify report was sent with markdown
        mock_update.message.reply_text.assert_awaited_once_with(
            text=mock_report,
            parse_mode=ParseMode.MARKDOWN
        )


@pytest.mark.asyncio
async def test_send_market_analysis_no_visualization(mock_update, mock_context):
    """Test market analysis command when no visualization is generated."""
    mock_report = "Test Market Report"
    
    with patch("stunk.telegram_bot.generate_market_report") as mock_generate:
        mock_generate.return_value = (mock_report, None)
        
        await send_market_analysis(mock_update, mock_context)
        
        # Verify only report was sent
        mock_update.message.reply_photo.assert_not_awaited()
        mock_update.message.reply_text.assert_awaited_once_with(
            text=mock_report,
            parse_mode=ParseMode.MARKDOWN
        )


@pytest.mark.asyncio
async def test_send_market_analysis_error(mock_update, mock_context):
    """Test market analysis command error handling."""
    with patch("stunk.telegram_bot.generate_market_report", 
              side_effect=Exception("Test error")):
        
        await send_market_analysis(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_awaited_once_with(
            "❌ Sorry, an error occurred while generating the market analysis."
        )


@pytest.mark.asyncio
async def test_help_command(mock_update, mock_context):
    """Test help command."""
    await help_command(mock_update, mock_context)
    
    expected_text = "🤖 *Market Analysis Bot Commands*\n\n{}".format(COMMANDS)
    mock_update.message.reply_text.assert_awaited_once_with(
        expected_text,
        parse_mode=ParseMode.MARKDOWN
    )


@pytest.mark.asyncio
async def test_error_handler(mock_context, caplog):
    """Test error handler with logging."""
    mock_update = None
    test_error = Exception("Test error")
    mock_context.error = test_error
    
    with caplog.at_level(logging.ERROR):
        await error_handler(mock_update, mock_context)
    
    # Verify error was logged
    assert "Exception while handling an update:" in caplog.text
    assert str(test_error) in caplog.text
