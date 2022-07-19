import logging

logger = logging.getLogger(__name__)


def setup(dispatcher):
    logger.info("Setup handlers...")

    import bot.handlers.help as help
    import bot.handlers.plans as plans

    plans.init_handlers(dispatcher)
    help.init_handlers(dispatcher)
