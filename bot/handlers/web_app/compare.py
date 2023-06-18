from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from bot.models.education_plan import EducationPlan

router = APIRouter()

templates = Jinja2Templates(directory="bot/handlers/web_app/static")


@router.get("/compare", response_class=HTMLResponse)
async def read_item(request: Request):
    plans = EducationPlan.get_all()

    plans = map(
        lambda plan: {
            "profile": plan.profile,
            "education_direction": plan.education_direction.name,
            "year": plan.year,
        },
        plans,
    )

    return templates.TemplateResponse(
        "compare.html", {"request": request, "plans": list(plans)}
    )


async def compare(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot = context.bot
    await update.message.reply_text(
        "Давайте откроем веб-приложение! Нажмите на прямую ссылку ниже.\n\n"
        f"https://t.me/{bot.username}/compare",
    )


@router.post("/getCompareResult")
async def get_compare_result(request: Request):
    data = await request.json()

    first_plan = EducationPlan.get_by_year_profile_direction(
        int(data["year1"]), data["profile1"], data["direction1"]
    )
    second_plan = EducationPlan.get_by_year_profile_direction(
        int(data["year2"]), data["profile2"], data["direction2"]
    )

    # Serialize to json
    print(first_plan)

    return {"first_plan": first_plan, "second_plan": second_plan}


async def any_update_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(update)


def init_web_app_handlers(app: Application, fastapi_app: FastAPI) -> None:
    app.add_handler(CommandHandler("compare", compare))
    fastapi_app.include_router(router)
