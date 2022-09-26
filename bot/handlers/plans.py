import re
from enum import IntEnum

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    Dispatcher,
    Filters,
    MessageHandler,
)
from telegram.utils.helpers import escape_markdown
from telegram_bot_pagination import InlineKeyboardPaginator

from bot.models.education_direction import EducationDirection
from bot.models.education_plan import EducationPlan
from bot.models.user import User
from bot.plans_parser.constants import ControlFormType

RE_CODE = r"^[0-9]{2}.[0-9]{2}.[0-9]{2}$"


class GetPlanStates(IntEnum):
    SELECT_YEAR = 1
    SELECT_PROFILE = 2


def on_any_message(update: Update, context: CallbackContext) -> int:
    User.create_if_not_exists(update.effective_user.id)

    text = update.message.text.replace(" ", "")

    if re.match(RE_CODE, text):
        education_direction = EducationDirection.get_by_code(text)

        if education_direction is None:
            update.message.reply_text(
                "В моей базе данных нет ни одного направления обучения с таким кодом."
            )
            return None

        education_plans = education_direction.education_plans

        update.message.reply_text(
            f'Я нашёл направление "{education_direction.name}" для кода {text}'
        )


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
        update.message.reply_text(
            "Выберите год поступления, для которого нужно отобразить траекторию обучения.",
            reply_markup=reply_markup,
        )
        return GetPlanStates.SELECT_YEAR


def on_year_selected(update: Update, context: CallbackContext) -> int:
    year = int(update.callback_query.data.split("#")[1])
    education_direction_id = int(update.callback_query.data.split("#")[2])
    education_direction = EducationDirection.get_by_id(education_direction_id)
    education_plans = education_direction.education_plans
    education_plans = [e for e in education_plans if e.year == year]

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
        update.callback_query.edit_message_text(
            "Найдена траектория обучения для одного направления (без профиля).",
            reply_markup=reply_markup,
        )
    else:
        update.callback_query.edit_message_text(
            "Выберите профиль, для которого нужно отобразить траекторию обучения.",
            reply_markup=reply_markup,
        )
    return GetPlanStates.SELECT_PROFILE


def get_disciplines_data(
    show_load: bool,
    education_plan_id: int = None,
) -> dict[int, str]:
    control_forms = {
        ControlFormType.EXAM: "экзамен",
        ControlFormType.TEST: "зачёт",
        ControlFormType.COURSEWORK: "курсовая работа",
        ControlFormType.COURSEPROJECT: "курсовой проект",
        ControlFormType.TEST_WITH_MARK: "зачёт с оценкой",
    }

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
                [control_forms[cf.type] for cf in discipline.control_forms]
            )

            if not control_forms_text:
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


def on_profile_selected(update: Update, context: CallbackContext) -> int:
    education_plan_id = int(update.callback_query.data.split("#")[1])
    education_plan = EducationPlan.get_by_id(education_plan_id)

    update.effective_message.reply_text(
        f"Выбран профиль: {education_plan.profile}"
    )


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

    update.effective_message.edit_text(
        text="".join(disciplines_data[1]),
        reply_markup=paginator.markup,
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    update.callback_query.answer()

    return ConversationHandler.END


def page_callback(update: Update, context: CallbackContext) -> None:
    try:
        query = update.callback_query
        page = int(query.data.split("#")[1])
        education_plan_id = int(query.data.split("#")[2])

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

        query.answer()
        query.edit_message_text(
            text="".join(disciplines_data[page]),
            reply_markup=paginator.markup,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    except telegram.error.BadRequest:
        pass


def init_handlers(dispatcher: Dispatcher):
    dispatcher.add_handler(
        MessageHandler(Filters.text & ~Filters.command, on_any_message, run_async=True)
    )
    dispatcher.add_handler(
        CallbackQueryHandler(
            on_year_selected,
            pattern="^year#",
            run_async=True,
        ),
    )
    dispatcher.add_handler(
        CallbackQueryHandler(
            on_profile_selected,
            pattern="^profile#\d+$",
            run_async=True,
        ),
    )
    dispatcher.add_handler(
        CallbackQueryHandler(
            page_callback, pattern="^(page#)|(show_load#)|(hide_load#)", run_async=True
        )
    )
