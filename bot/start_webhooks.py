import logging

import logging_loki
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse, Response
from telegram import Update
from telegram.ext import AIORateLimiter, Application

from bot.config import (
    BOT_URL,
    LOKI_AUTH_LOGIN,
    LOKI_AUTH_PASSWORD,
    LOKI_URL,
    TELEGRAM_TOKEN,
    USE_LOKI_LOGGER,
)

if USE_LOKI_LOGGER:
    loki_handler = logging_loki.LokiHandler(
        url=LOKI_URL,
        auth=(LOKI_AUTH_LOGIN, LOKI_AUTH_PASSWORD),
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


application = (
    Application.builder()
    .token(TELEGRAM_TOKEN)
    .rate_limiter(AIORateLimiter(max_retries=2))
    .read_timeout(40)
    .write_timeout(40)
    .updater(None)
    .build()
)


async def telegram(request: Request):
    """Handle incoming Telegram updates by putting them into the `update_queue`"""

    await application.update_queue.put(
        Update.de_json(data=(await request.json()), bot=application.bot)
    )
    return Response(status_code=200)


async def health(request: Request):
    return JSONResponse({"status": "ok"})


async def setup_webhook():
    from bot import handlers

    handlers.setup(application)

    await application.bot.set_webhook(
        url=f"{BOT_URL}/telegram", allowed_updates=Update.ALL_TYPES
    )


app = FastAPI()


# Set up webserver
app.add_route("/telegram", telegram, methods=["POST"])
app.add_route("/health", health, methods=["GET"])


async def run() -> None:
    """Start the bot."""
    await setup_webhook()

    await application.initialize()
    await application.start()


@app.middleware("http")
async def on_any_request(request: Request, call_next):
    if not application.running:
        await run()

    response = await call_next(request)

    return response
