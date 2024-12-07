"""Telegram bot for market trend analysis."""
import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional, Union
from io import BytesIO

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode

from stunk.config import TELEGRAM_TOKEN, ALLOWED_CHAT_IDS, COMMANDS
from stunk.market_trend import generate_market_report


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("stunk_debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def send_market_analysis(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Send market analysis report with visualization."""
    # Security check
    if update.effective_chat.id not in ALLOWED_CHAT_IDS:
        await update.message.reply_text(
            "⚠️ Sorry, you are not authorized to use this bot."
        )
        logger.warning(
            f"Unauthorized access attempt from chat_id: {update.effective_chat.id}"
        )
        return

    try:
        # Show typing indicator
        await context.application.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        # Generate the report (don't save to disk)
        report, viz = generate_market_report(should_save_file=False)
        
        if viz:
            # Send the visualization
            await update.message.reply_photo(
                photo=viz,  # Works with both Path and BytesIO
                caption="Market Trend Visualization"
            )
            
            # Close buffer if it's a BytesIO object
            if isinstance(viz, BytesIO):
                viz.close()
        
        # Send the analysis report
        await update.message.reply_text(
            text=report,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error in send_market_analysis: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Sorry, an error occurred while generating the market analysis."
        )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "🤖 *Market Analysis Bot Commands*\n\n"
        f"{COMMANDS}"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def error_handler(
    update: Optional[Update],
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Log errors caused by updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Sorry, something went wrong."
        )


async def shutdown(application: Application) -> None:
    """Perform cleanup before shutdown."""
    await application.stop()
    await application.shutdown()
    logger.info("Bot shutdown complete")


def signal_handler(application: Application) -> None:
    """Handle system signals for graceful shutdown."""
    loop = asyncio.get_event_loop()
    loop.create_task(shutdown(application))
    sys.exit(0)


def run_bot() -> None:
    """Start the bot."""
    try:
        # Create application
        application = Application.builder().token(TELEGRAM_TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("market", send_market_analysis))
        application.add_handler(CommandHandler("help", help_command))
        application.add_error_handler(error_handler)

        # Set up signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, lambda s, f: signal_handler(application))

        # Start the bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        sys.exit(1)
