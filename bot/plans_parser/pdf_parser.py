import logging
import re

import camelot

camelot.logger.setLevel(logging.ERROR)

from .constants import ControlFormType
from .education_plan_discipline import EducationPlanDiscipline

REGULAR_DISCIPLINES_TITLE = "Блок 1.Дисциплины (модули)"
PRACTICE_DISCIPLINES_TITLES = ["Блок 2.Практика", "Блок 2.Практики", "Блок 2.Практики"]
OPTIONAL_DISCIPLINES_TITLES = ["ФТД.Факультативные дисциплины", "ФТД.Факультативы"]

OPTIONAL_PART_TITLE = "Дисциплины по выбору"


BLACKLIST_NAMES = [
    "Базовая часть",
    "Вариативная часть",
    "Обязательная часть",
    "Часть, формируемая участниками образовательных отношений",
    "Атлетическая гимнастика",
    "Баскетбол",
    "Волейбол",
    "Футбол",
    "Рукопашный бой",
    "Бокс",
    "Борьба",
    "Общая физическая подготовка",
    "Адаптивная физическая культура",
]


def _compare_strings(string1: str, string2: str) -> bool:
    string1 = string1.lower().strip()
    string2 = string2.lower().strip()
    string1 = re.sub(r"[^\w\s]", "", string1)
    string2 = re.sub(r"[^\w\s]", "", string2)
    string1 = re.sub(r"\d+", "", string1).strip()
    string2 = re.sub(r"\d+", "", string2).strip()
    string1 = re.sub(r"\s+", " ", string1)
    string2 = re.sub(r"\s+", " ", string2)
    return string1 == string2


def _parse_row(
    name_index,
    semester_intervals: list,
    header_row: list,
    row: list,
    by_choice: bool,
    is_optional: bool,
    is_practice: bool,
) -> list[EducationPlanDiscipline]:
    result = []

    name = row[name_index].replace("\n", " ").strip()
    name = re.sub(r"\d+", "", name).strip()
    name = re.sub(r"\s+", " ", name)

    # indexes: 1 - exam, 2 - test, 3 - test with mark, 4 - courseproject, 5 - coursework
    control_forms_all = [
        ControlFormType.EXAM,
        ControlFormType.TEST,
        ControlFormType.TEST_WITH_MARK,
        ControlFormType.COURSEPROJECT,
        ControlFormType.COURSEWORK,
    ]

    for k in range(len(semester_intervals)):
        semester = k + 1
        lek, lab, pr, sr = None, None, None, None
        if semester_intervals[k][1] <= len(row):
            is_current_semester = False
            for i in range(semester_intervals[k][0], semester_intervals[k][1]):
                if row[i].strip() != "":
                    is_current_semester = True
                    if _compare_strings(header_row[i], "Лек"):
                        lek = float(row[i])
                    elif _compare_strings(header_row[i], "лаб"):
                        lab = float(row[i])
                    elif _compare_strings(header_row[i], "пр"):
                        pr = float(row[i])
                    elif _compare_strings(header_row[i], "ср"):
                        sr = float(row[i])

            if is_current_semester:
                control_forms = []
                for i in range(1, 6):
                    if row[i].strip() != "":
                        if str(semester) in row[i]:
                            control_forms.append(control_forms_all[i - 1])
                        elif (
                            "A" in row[i]
                            and semester == 10
                            or "B" in row[i]
                            and semester == 11
                            or "C" in row[i]
                            and semester == 12
                        ):
                            control_forms.append(control_forms_all[i - 1])

                result.append(
                    EducationPlanDiscipline(
                        name=name,
                        semester=semester,
                        by_choice=by_choice,
                        is_optional=is_optional,
                        is_practice=is_practice,
                        lek=lek,
                        lab=lab,
                        pr=pr,
                        sr=sr,
                        control_forms=control_forms,
                    )
                )

    return result


def _is_blacklisted(name: str) -> bool:
    return any(
        _compare_strings(name, blacklisted_name) for blacklisted_name in BLACKLIST_NAMES
    )


def _is_in_optional_titles(title: str) -> bool:
    return any(
        _compare_strings(title, optional_title)
        for optional_title in OPTIONAL_DISCIPLINES_TITLES
    )


def _is_in_practice_titles(title: str) -> bool:
    title = re.sub(r"[^\w\s]", "", title)
    for practice_title in PRACTICE_DISCIPLINES_TITLES:
        practice_title = re.sub(r"[^\w\s]", "", practice_title)
        if practice_title.lower() in title.lower():
            return True
    return False


def parse_pdf(path: str) -> list[EducationPlanDiscipline]:
    tables = camelot.read_pdf(
        path,
        pages="all",
    )

    table = []
    table_header = None

    for tmp_table in tables:
        table_list = tmp_table.df.values.tolist()
        if table_header is None:
            table_header = table_list[2]
        tmp_table = table_list[3:]
        table += tmp_table

    semester_intervals = []
    for i in range(len(table_header)):
        # получить интервалы от 'з.е.' до 'з.е.'
        if _compare_strings(table_header[i], "з.е."):
            first = i
            for j in range(i + 1, len(table_header)):
                if (
                    _compare_strings(table_header[j], "з.е.")
                    or j == len(table_header) - 1
                ):
                    second = j
                    semester_intervals.append((first, second))
                    break

    result = []

    for i in range(len(table)):
        row = table[i]
        name_index = 1 if _compare_strings("индекс", table_header[0]) else 0

        if _compare_strings(row[name_index], REGULAR_DISCIPLINES_TITLE):
            by_choice = False
            # Парсим основные дисциплины
            for j in range(i + 1, len(table)):
                row = table[j]
                name = row[name_index]
                if _is_blacklisted(name):
                    continue
                if _is_in_practice_titles(name):
                    break
                if OPTIONAL_PART_TITLE.lower() in name.lower():
                    by_choice = True
                elif "элективные дисциплины" in name.lower():
                    by_choice = False
                else:
                    result += _parse_row(
                        name_index,
                        semester_intervals,
                        table_header,
                        row,
                        by_choice,
                        False,
                        False,
                    )

        elif _is_in_practice_titles(row[name_index]):
            # Парсим дисциплины практики
            for j in range(i + 1, len(table)):
                row = table[j]
                name = row[name_index]
                if _is_blacklisted(name):
                    continue
                if _is_in_optional_titles(name) or "блок 3" in name.lower():
                    break

                result += _parse_row(
                    name_index,
                    semester_intervals,
                    table_header,
                    row,
                    False,
                    False,
                    True,
                )

        elif _is_in_optional_titles(row[name_index]):
            # Парсим факультативные дисциплины
            for j in range(i + 1, len(table)):
                row = table[j]
                name = row[name_index]
                if _is_blacklisted(name):
                    continue

                result += _parse_row(
                    name_index,
                    semester_intervals,
                    table_header,
                    row,
                    False,
                    True,
                    False,
                )

    return result
