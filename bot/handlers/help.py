from telegram import Update
from telegram.ext import Application, CallbackContext, CommandHandler


async def help_callback(update: Update, context: CallbackContext) -> None:
    await update.effective_message.reply_text(
        f"👋 Привет, {update.message.from_user.first_name}!\n\n"
        "Этот бот позволяет вам получать траекторию обучения (учебный план) по коду направления. "
        'Например, отправьте "09.03.04", чтобы получить профили направления "Программная инженерия" '
        "и посмотреть учебный план для соответствующего профиля.\n\n"
        "<b>Примеры использования:</b>\n"
        "<code>09.03.04</code>\n"
        "С инлайн режимом:\n"
        "<code>@learning_roadmap_bot 09.03.04</code>\n"
        "<code>@learning_roadmap_bot Программная инженерия</code>\n"
        "<code>@learning_roadmap_bot Разработка</code>\n\n\n"
        "Бот поддерживает инлайн режим, чтобы использовать его, просто начните вводить "
        "код направления, название профиля или название направления.\n\n"
        "👉 <b>Что делать, если не знаешь свой профиль?</b>\n"
        "Если вы на первом курсе, ваше направление имеет профили, но вы не выбирали профиль при поступлении, "
        "то распределение будет потом. В таких случаях программа обучения 1-2 семестра для всех профилей одинаковая.\n\n"
        "Вы можете посмотреть профиль в ЛК через наше <a href='https://github.com/mirea-ninja/university-app'>мобильное приложение</a>.",
        parse_mode="HTML",
    )


def init_handlers(app: Application) -> None:
    # show about information
    app.add_handler(CommandHandler("help", help_callback), group=4)
    app.add_handler(CommandHandler("start", help_callback), group=4)
