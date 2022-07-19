import sqlalchemy as db
from sqlalchemy.orm import relationship

from bot.db import db_session
from bot.models.base import BaseModel

# from bot.models.education_plan import EducationPlan


class EducationDirection(BaseModel):
    __tablename__ = "education_directions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, nullable=False, index=True)
    code = db.Column(db.UnicodeText, nullable=False, index=True)
    education_plans = relationship(
        "EducationPlan", back_populates="education_direction", lazy="joined"
    )

    def create(self):
        with db_session() as session:
            session.add(self)
            session.commit()
            session.refresh(self)

    @staticmethod
    def get_by_id(id):
        with db_session() as session:
            return (
                session.query(EducationDirection)
                .filter(
                    EducationDirection.id == id,
                )
                .first()
            )

    @staticmethod
    def get_or_create(name, code):
        with db_session() as session:
            education_direction = (
                session.query(EducationDirection)
                .filter(
                    EducationDirection.name == name,
                    EducationDirection.code == code,
                )
                .first()
            )
            if education_direction is None:
                education_direction = EducationDirection(
                    name=name,
                    code=code,
                )
                session.add(education_direction)
                session.commit()
                session.refresh(education_direction)
            return education_direction

    @staticmethod
    def get_by_code(code):
        with db_session() as session:
            return (
                session.query(EducationDirection)
                .filter(
                    EducationDirection.code == code,
                )
                .first()
            )

    @staticmethod
    def get_by_name(name):
        with db_session() as session:
            return (
                session.query(EducationDirection)
                .filter(
                    EducationDirection.name == name,
                )
                .all()
            )


EducationDirection.__table__.create(checkfirst=True)
