from telegram import ParseMode, Update
from telegram.ext import CallbackContext, CommandHandler, Dispatcher
from telegram.utils.helpers import escape_markdown


# f"👋 Привет, {update.message.from_user.first_name}\!\n\n"
# "Этот бот позволяет вам получать траекторию обучения из базы данных по коду направления\. "
# 'Например, отправьте "09\.03\.04", чтобы получить профили направления "Программная инженерия" '
# "и посмотреть учебный план для соответствующего профиля\.\n\n"
# "Вы также можете найти профили или направления по названию или же вы можете искать направления "
# "по преподаваемой дисциплины\.\n\n"
# "*Примеры использования\:*\n"
# "`09.03.04`\n"
# "`Программная инженерия`\n"
# "`Дизайн`",
def help_callback(update: Update, context: CallbackContext) -> None:
    update.effective_message.reply_text(
        escape_markdown(
            f"👋 Привет, {update.message.from_user.first_name}!\n\n"
            "Этот бот позволяет вам получать траекторию обучения из базы данных по коду направления. "
            'Например, отправьте "09.03.04", чтобы получить профили направления "Программная инженерия" '
            "и посмотреть учебный план для соответствующего профиля.\n\n",
            version=2,
        )
        + "*Примеры использования\:*\n"
        "`09.03.04`\n",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


def init_handlers(dispatcher: Dispatcher):
    # show about information
    dispatcher.add_handler(CommandHandler("help", help_callback), group=4)
    dispatcher.add_handler(CommandHandler("start", help_callback), group=4)
