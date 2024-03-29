import asyncio
import contextlib
import logging
import re
from enum import IntEnum
from typing import Any

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
    error,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    InlineQueryHandler,
    MessageHandler,
    filters,
)
from telegram.helpers import escape_markdown
from telegram_bot_pagination import InlineKeyboardPaginator

from bot.models.education_direction import EducationDirection
from bot.models.education_plan import EducationPlan
from bot.plans_parser.constants import ControlFormType

logger = logging.getLogger(__name__)

RE_CODE = r"^[0-9]{2}.[0-9]{2}.[0-9]{2}$"

CONTROL_FORMS = {
    ControlFormType.EXAM: "экзамен",
    ControlFormType.TEST: "зачёт",
    ControlFormType.COURSEWORK: "курсовая работа",
    ControlFormType.COURSEPROJECT: "курсовой проект",
    ControlFormType.TEST_WITH_MARK: "зачёт с оценкой",
}


class GetPlanStates(IntEnum):
    SELECT_YEAR = 1
    SELECT_PROFILE = 2


async def on_any_message(update: Update, context: CallbackContext) -> GetPlanStates:
    # User.create_if_not_exists(update.effective_user.id)
    if update.callback_query:
        text = update.callback_query.data.split("#")[1]
    else:
        text = update.effective_message.text.replace(" ", "")

    if re.match(RE_CODE, text):
        education_direction = EducationDirection.get_by_code(text)

        if education_direction is None:
            await update.message.reply_text(
                "В моей базе данных нет ни одного направления обучения с таким кодом."
            )
            # logging
            print(f'Bad direction: "{text}" by {update.message.from_user.to_json()}')
            return None

        education_plans = education_direction.education_plans

        text = f'Я нашёл направление "{education_direction.name}" для кода {text}'

        if update.message:
            await update.message.reply_text(text)
        else:
            await update.callback_query.edit_message_text(text)

        # logging
        user = (
            update.message.from_user.to_json()
            if update.message
            else update.callback_query.from_user.to_json()
        )
        print(f'Successful direction: "{text}" by {user}')

        if update.message:
            logger.info(update.message.to_json())
        else:
            logger.info(update.callback_query.to_json())

        years = []
        for education_plan in education_plans:
            if education_plan.year not in years:
                years.append(education_plan.year)

        years = sorted(years)

        keyboard = [
            [
                InlineKeyboardButton(
                    str(year),
                    callback_data=f"year#{year}#{education_direction.id}",
                )
            ]
            for year in years
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "Выберите год поступления, для которого нужно отобразить траекторию обучения."
        if update.message:
            await update.message.reply_text(text, reply_markup=reply_markup)
        else:
            await asyncio.sleep(1)
            await update.callback_query.edit_message_text(
                text, reply_markup=reply_markup
            )
        return GetPlanStates.SELECT_YEAR


async def on_year_selected(update: Update, context: CallbackContext) -> int:
    year = int(update.callback_query.data.split("#")[1])
    education_direction_id = int(update.callback_query.data.split("#")[2])
    education_direction = EducationDirection.get_by_id(education_direction_id)
    education_plans = education_direction.education_plans
    education_plans = [e for e in education_plans if e.year == year]

    # logging
    data = {
        "year": year,
        "education_direction_id": education_direction.id,
        "education_direction_code": education_direction.code,
    }
    print(
        f'Selected direction year: "{data}" by {update.callback_query.from_user.to_json()}'
    )

    logger.info(update.callback_query.to_json())

    keyboard = []
    for education_plan in education_plans:
        name = education_plan.profile
        if name is None:
            name = "Показать"
        keyboard.append(
            [
                InlineKeyboardButton(
                    name,
                    callback_data=f"profile#{education_plan.id}",
                )
            ]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    if len(education_plans) == 1 and education_plans[0].profile is None:
        await update.callback_query.edit_message_text(
            "Найдена траектория обучения для одного направления (без профиля).",
            reply_markup=reply_markup,
        )
    else:
        await update.callback_query.edit_message_text(
            "Выберите профиль, для которого нужно отобразить траекторию обучения.",
            reply_markup=reply_markup,
        )
    return GetPlanStates.SELECT_PROFILE


def get_disciplines_data(
    show_load: bool,
    education_plan_id: int = None,
) -> dict[Any, list[Any]]:
    education_plan = EducationPlan.get_by_id(education_plan_id)

    semesters = {}
    for discipline in education_plan.disciplines:
        if discipline.semester not in semesters:
            semesters[discipline.semester] = []
        semesters[discipline.semester].append(discipline)

    semesters = sorted(semesters.items())

    result = {}

    for semester, disciplines in semesters:
        result[semester] = []
        for i in range(len(disciplines)):
            discipline = disciplines[i]
            additional_text = ""
            if discipline.is_optional:
                additional_text += " (факультатив)"
            if discipline.is_practice:
                additional_text += " (практика)"
            if discipline.by_choice:
                additional_text += " (по выбору)"

            time_text = ""
            if show_load:
                time_text = "Количество часов:"
                if discipline.lek:
                    time_text += f" лекции - {str(discipline.lek)}"
                if discipline.lab:
                    if time_text:
                        time_text += ", "
                    time_text += f" лабораторные - {str(discipline.lab)}"
                if discipline.pr:
                    if time_text:
                        time_text += ", "
                    time_text += f" практика - {str(discipline.pr)}"
                if discipline.sr:
                    if time_text:
                        time_text += ", "
                    time_text += f" самостоятельная работа - {str(discipline.sr)}"
                time_text += "."

            control_forms_text = ", ".join(
                [CONTROL_FORMS[cf.type] for cf in discipline.control_forms]
            )

            if control_forms_text == "":
                control_forms_text = "нет"

            text = (
                f"{i + 1}\. *{escape_markdown(discipline.name.text, version=2)}*"
                + escape_markdown(
                    f", вид оценивания: {control_forms_text}. {time_text} {additional_text}\n\n",
                    version=2,
                )
            )
            text = text.replace("  ", " ")
            result[semester].append(text)

    return result


async def on_profile_selected(update: Update, context: CallbackContext) -> int:
    education_plan_id = int(update.callback_query.data.split("#")[1])
    education_plan = EducationPlan.get_by_id(education_plan_id)

    text = f"Выбран профиль: {education_plan.profile}\n\n"
    text += f"Учебный план: {education_plan.url}\n"

    if education_plan.annot_url:
        text += f"Описание дисциплин: {education_plan.annot_url}"

    if update.effective_message:
        await update.effective_message.reply_text(text)
    else:
        await update.callback_query.edit_message_text(text)
        await asyncio.sleep(1)

    # logging
    data = {
        "education_plan_id": education_plan.id,
        "education_plan_profile": education_plan.profile,
        "education_direction_id": education_plan.education_direction_id,
        "education_direction_code": EducationDirection.get_by_id(
            education_plan.education_direction_id
        ).code,
    }
    print(f'Profile: "{data}" by {update.callback_query.from_user.to_json()}')

    logger.info(update.callback_query.to_json())

    disciplines_data = get_disciplines_data(False, education_plan_id)

    pages_count = len(disciplines_data)

    paginator = InlineKeyboardPaginator(
        pages_count,
        data_pattern="page#{page}#" + str(education_plan_id),
    )

    paginator.add_after(
        InlineKeyboardButton(
            "Показать нагрузку", callback_data=f"show_load#1#{education_plan_id}"
        ),
    )

    text = "".join(disciplines_data[1])

    if update.effective_message:
        await update.effective_message.edit_text(
            text,
            reply_markup=paginator.markup,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    else:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=paginator.markup,
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    await update.callback_query.answer()

    return ConversationHandler.END


async def page_callback(update: Update, context: CallbackContext) -> None:
    with contextlib.suppress(error.BadRequest):
        query = update.callback_query
        page = int(query.data.split("#")[1])
        education_plan_id = int(query.data.split("#")[2])

        # logging
        education_plan = EducationPlan.get_by_id(education_plan_id)
        data = {
            "data": query.data,
            "education_plan_id": education_plan.id,
            "education_plan_profile": education_plan.profile,
            "education_direction_id": education_plan.education_direction_id,
            "education_direction_code": EducationDirection.get_by_id(
                education_plan.education_direction_id
            ).code,
        }
        print(f'Page callback: "{data}" by {update.callback_query.from_user.to_json()}')

        logger.info(update.callback_query.to_json())

        if query.data.startswith("show_load"):
            disciplines_data = get_disciplines_data(True, education_plan_id)
            paginator = InlineKeyboardPaginator(
                len(disciplines_data),
                current_page=page,
                data_pattern="page#{page}#" + str(education_plan_id),
            )
            context.user_data["show_load"] = True
            paginator.add_after(
                InlineKeyboardButton(
                    "Скрыть нагрузку",
                    callback_data=f"hide_load#{page}#{education_plan_id}",
                ),
            )
        elif query.data.startswith("hide_load"):
            disciplines_data = get_disciplines_data(False, education_plan_id)
            paginator = InlineKeyboardPaginator(
                len(disciplines_data),
                current_page=page,
                data_pattern="page#{page}#" + str(education_plan_id),
            )
            context.user_data["show_load"] = False
            paginator.add_after(
                InlineKeyboardButton(
                    "Показать нагрузку",
                    callback_data=f"show_load#{page}#{education_plan_id}",
                ),
            )
        else:
            if "show_load" not in context.user_data:
                context.user_data["show_load"] = False
            disciplines_data = get_disciplines_data(
                context.user_data["show_load"], education_plan_id
            )
            paginator = InlineKeyboardPaginator(
                len(disciplines_data),
                current_page=page,
                data_pattern="page#{page}#" + str(education_plan_id),
            )
            if context.user_data["show_load"]:
                paginator.add_after(
                    InlineKeyboardButton(
                        "Скрыть нагрузку",
                        callback_data=f"hide_load#{page}#{education_plan_id}",
                    ),
                )
            else:
                paginator.add_after(
                    InlineKeyboardButton(
                        "Показать нагрузку",
                        callback_data=f"show_load#{page}#{education_plan_id}",
                    ),
                )

        await query.answer()
        await query.edit_message_text(
            text="".join(disciplines_data[page]),
            reply_markup=paginator.markup,
            parse_mode=ParseMode.MARKDOWN_V2,
        )


async def inline_query(update: Update, context: CallbackContext) -> None:
    if not (query := update.inline_query.query):
        return

    if len(query) < 3:
        return

    if query[0].isdigit():
        directions_by_code = EducationDirection.search_by_code(query)

        if len(directions_by_code) == 0:
            return

        results = [
            InlineQueryResultArticle(
                id=str(direction.id),
                title=direction.name,
                description=f"Код: {direction.code}",
                input_message_content=InputTextMessageContent(
                    f"Направление: {direction.name}\n" f"Код: {direction.code}"
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Выбрать профиль",
                                callback_data=f"direction#{direction.code}",
                            )
                        ]
                    ]
                ),
            )
            for direction in directions_by_code
        ]

    else:
        if len(query) < 5:
            return

        education_profiles = EducationPlan.search_by_profile(query)
        directions_by_name = EducationDirection.search_by_name(query)

        if len(education_profiles) == 0 and len(directions_by_name) == 0:
            return

        results = [
            InlineQueryResultArticle(
                id=str(profile.id),
                title=profile.profile,
                description=f"Код: {profile.education_direction.code}\n"
                f"Год: {profile.year}\n"
                f"{profile.education_direction.name}",
                input_message_content=InputTextMessageContent(
                    f"Профиль: {profile.profile}\n\n"
                    f"Направление: {profile.education_direction.name}\n\n"
                    f"Код: {profile.education_direction.code}; Год: {profile.year}"
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Показать план",
                                callback_data=f"profile#{profile.id}",
                            )
                        ]
                    ]
                ),
            )
            for profile in education_profiles
        ]

        results += [
            InlineQueryResultArticle(
                id=str(direction.id),
                title=direction.name,
                description=f"Код: {direction.code}",
                input_message_content=InputTextMessageContent(
                    f"Направление: {direction.name}\nКод: {direction.code}"
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Выбрать профиль",
                                callback_data=f"direction#{direction.code}",
                            )
                        ]
                    ]
                ),
            )
            for direction in directions_by_name
        ]

    await update.inline_query.answer(results=results[:50], cache_time=1)


def init_handlers(app: Application) -> None:
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_any_message))
    app.add_handler(
        CallbackQueryHandler(
            on_any_message, pattern=r"^direction#\d{2}\.\d{2}\.\d{2}$"
        ),
    )
    app.add_handler(
        CallbackQueryHandler(
            on_year_selected,
            pattern="^year#",
        ),
    )
    app.add_handler(
        CallbackQueryHandler(
            on_profile_selected,
            pattern="^profile#\d+$",
        ),
    )
    app.add_handler(
        CallbackQueryHandler(
            page_callback,
            pattern="^(page#)|(show_load#)|(hide_load#)",
        )
    )
    app.add_handler(
        InlineQueryHandler(
            inline_query,
        )
    )
