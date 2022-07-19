from enum import IntEnum


class ControlFormType(IntEnum):
    # Экзамен, Зачет, Зачет с оценкой, Курсовой Проект, Курсовая Работа
    EXAM = 1
    TEST = 2
    TEST_WITH_MARK = 3
    COURSEPROJECT = 4
    COURSEWORK = 5


class EducationLevel(IntEnum):

    # Уровень образования:
    # 1) высшее образование - бакалавриат;
    # 2) высшее образование - специалитет;
    # 3) высшее образование - магистратура;
    # 4) высшее образование - аспирантура;
    # 5) среднее профессиональное образование.
    BACHELOR = 1
    SPECIALIST = 2
    MASTER = 3
    POSTGRADUATE = 4
    SECONDARY = 5


EDUCATION_LEVELS_NAMES = {
    EducationLevel.BACHELOR: "бакалавриат",
    EducationLevel.SPECIALIST: "специалитет",
    EducationLevel.MASTER: "магистратура",
    EducationLevel.POSTGRADUATE: "аспирантура",
    EducationLevel.SECONDARY: "среднее профессиональное образование",
}
