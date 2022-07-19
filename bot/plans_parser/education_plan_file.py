from typing import Optional

from pydantic import BaseModel

from .constants import EducationLevel


class EducationPlanFile(BaseModel):
    url: str
    code: str
    name: str
    year: int
    education_level: EducationLevel
    profile: Optional[str] = None
