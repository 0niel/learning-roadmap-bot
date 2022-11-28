import logging

from telegram.ext import Application

from bot import config

logger = logging.getLogger(__name__)
logger.setLevel("INFO")


def main() -> None:
    """Start the bot."""
    from bot import handlers

    # logger.info("Starting bot")
    # Here we set updater to None because we want our custom webhook server to handle the updates
    # and hence we don't need an Updater instance
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()

    # Setup command and message handlers
    handlers.setup(application)
    logger.info("Setup handlers")

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    application.run_polling()
