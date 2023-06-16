import json
import logging

import logging_loki
from telegram import Update
from telegram.ext import Application

from bot import config

if config.USE_LOKI_LOGGER:
    loki_handler = logging_loki.LokiHandler(
        url=config.LOKI_URL,
        auth=(config.LOKI_AUTH_LOGIN, config.LOKI_AUTH_PASSWORD),
        tags={"app": "learning-roadmap-bot", "env": "production"},
        version="1",
    )

    logging.basicConfig(
        level=logging.INFO,
        handlers=[loki_handler],
    )
else:
    logging.basicConfig(
        level=logging.INFO,
    )


logger = logging.getLogger(__name__)


async def process_update(event, application):
    await application.update_queue.put(
        Update.de_json(data=json.loads(event["body"]), bot=application.bot)
    )


async def handler(event, context):
    """Yandex.Cloud functions handler."""
    logger.info("Process event: " + str(event["httpMethod"]))

    """Start the bot."""
    from bot import handlers

    logger.info("Starting bot")

    # Here we set updater to None because we want our custom webhook server to handle the updates
    # and hence we don't need an Updater instance
    application = (
        Application.builder().token(config.TELEGRAM_TOKEN).updater(None).build()
    )

    # Setup command and message handlers
    handlers.setup(application)
    logger.info("Setup handlers")

    # Run application and webserver together
    async with application:
        await application.start()
        await process_update(event, application)
        await application.stop()

    return {"statusCode": 200, "body": "ok"}
