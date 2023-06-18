import logging
from contextlib import asynccontextmanager

import logging_loki
import sentry_sdk
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from telegram import Update
from telegram.ext import Application
from yappa.handlers.asgi import call_app
from yappa.handlers.common import patch_response

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


application = Application.builder().token(TELEGRAM_TOKEN).updater(None).build()


async def error_handler(update: object, context) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)

    await sentry_sdk.capture_exception(context.error)


webhook_setup_done = False


async def setup_webhook():
    global webhook_setup_done
    if webhook_setup_done:
        return

    from bot import handlers

    handlers.setup(application, app)

    await application.bot.set_webhook(
        url=f"{BOT_URL}/telegram", allowed_updates=Update.ALL_TYPES
    )

    webhook_setup_done = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    await setup_webhook()
    await application.initialize()
    await application.start()
    yield
    await application.stop()


app = FastAPI(lifespan=lifespan)

app.mount(
    "/static", StaticFiles(directory="bot/handlers/web_app/static"), name="static"
)


@app.post("/telegram")
async def telegram(request: Request):
    """Handle incoming Telegram updates by putting them into the `update_queue`"""

    await application.update_queue.put(
        Update.de_json(data=(await request.json()), bot=application.bot)
    )
    return Response(status_code=200)


@app.get("/health")
async def health(request: Request):
    return JSONResponse({"status": "ok"})


async def handle(event, context):
    if not event:
        return {
            "statusCode": 500,
            "body": "got empty event",
        }

    async with application:
        await setup_webhook()
        await application.start()
        response = await call_app(app, event)
        await application.stop()
        return patch_response(response)
