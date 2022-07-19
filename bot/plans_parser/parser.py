import os
from multiprocessing import Process
from pathlib import Path

import requests

from bot.models.control_form import ControlForm
from bot.models.discipline import Discipline
from bot.models.discipline_name import DisciplineName
from bot.models.education_direction import EducationDirection
from bot.models.education_plan import EducationPlan

from .constants import EducationLevel
from .pdf_parser import parse_pdf
from .web_parser import get_plans

app_dir: Path = Path(__file__).parent


def parse_plans(plans: list):
    for plan in plans:
        try:
            if (
                plan.education_level == EducationLevel.SECONDARY
                or plan.education_level == EducationLevel.POSTGRADUATE
            ):
                continue

            plan_filename = plan.url.split("/")[-1]
            path = "pdf_files\\"
            path = os.path.join(app_dir, path)

            if not os.path.exists(path):
                os.makedirs(path)

            path = os.path.join(path, plan_filename)
            print("Parsing plan: ", plan_filename)
            # path = os.path.join(path, "ucheb_plan_05.03.03_GSK_2020.pdf")
            with open(path, "wb") as f:
                f.write(requests.get(plan.url).content)

            # Parse file
            disciplines = parse_pdf(path)
            if disciplines is None:
                continue
            discipline_objs = []

            # Save to database
            for discipline in disciplines:
                # Save to database
                discipline_name = DisciplineName.get_or_create(discipline.name)

                control_forms = [
                    ControlForm.get_or_create(control_form.value)
                    for control_form in discipline.control_forms
                ]

                # Save to database
                discipline_obj = Discipline.get_or_create(
                    discipline_name.id,
                    discipline.semester,
                    discipline.by_choice,
                    discipline.is_optional,
                    discipline.is_practice,
                    discipline.lek,
                    discipline.lab,
                    discipline.pr,
                    discipline.sr,
                    control_forms,
                )

                discipline_objs.append(discipline_obj)

            education_direction = EducationDirection.get_or_create(plan.name, plan.code)

            # Save to database
            education_plan = EducationPlan.get_or_create(
                plan.profile,
                education_direction.id,
                plan.year,
                plan.education_level.value,
                discipline_objs,
            )
        except Exception as e:
            print(
                "============================================================================="
            )
            print("Error: ", e)
            print(
                "============================================================================="
            )


def parse():
    plans = get_plans()

    start_index = 0
    for i in range(len(plans)):
        start_plan_name = "ucheb_plan_09.03.02_GS_2020.pdf"
        if plans[i].url.split("/")[-1] == start_plan_name:
            start_index = i
            break
    plans = plans[start_index:]
    # Разделить plans на 5 списков
    plans_list = []
    for i in range(5):
        plans_list.append(plans[i::5])

    # Парсить планы из каждого списка в отдельном процессе
    for plans in plans_list:
        Process(target=parse_plans, args=(plans,)).start()
