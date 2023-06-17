import logging

logger = logging.getLogger(__name__)


def setup(dispatcher, fastapi_app=None):
    logger.info("Setup handlers...")

    import bot.handlers.help as help
    import bot.handlers.plans as plans

    plans.init_handlers(dispatcher)
    help.init_handlers(dispatcher)

    if fastapi_app:
        import bot.handlers.web_app.compare as compare

        compare.init_web_app_handlers(dispatcher, fastapi_app)
