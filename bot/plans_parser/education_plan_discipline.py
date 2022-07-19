from typing import Optional

from pydantic import BaseModel

from .constants import ControlFormType


class EducationPlanDiscipline(BaseModel):
    name: str
    semester: int
    by_choice: bool  # По выбору
    is_optional: bool  # Факультативные
    is_practice: bool  # Практика
    lek: Optional[float] = None
    lab: Optional[float] = None
    pr: Optional[float] = None
    sr: Optional[float] = None
    control_forms: list[ControlFormType] = []
