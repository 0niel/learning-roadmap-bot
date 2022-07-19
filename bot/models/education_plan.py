import sqlalchemy as db
from sqlalchemy.orm import relationship

from bot.db import base, db_session
from bot.models.base import BaseModel
from bot.models.discipline import Discipline

discipline_education_plans = db.Table(
    "discipline_education_plans",
    base.metadata,
    db.Column("discipline_id", db.Integer, db.ForeignKey(Discipline.id)),
    db.Column("education_plan_id", db.Integer, db.ForeignKey("education_plans.id")),
)


class EducationPlan(BaseModel):
    __tablename__ = "education_plans"

    id = db.Column(db.Integer, primary_key=True)
    profile = db.Column(db.UnicodeText, nullable=True, index=True)
    education_direction_id = db.Column(
        db.Integer, db.ForeignKey("education_directions.id")
    )
    education_direction = relationship(
        "EducationDirection", back_populates="education_plans"
    )
    year = db.Column(db.Integer, nullable=False)
    education_level = db.Column(db.Integer, nullable=False)
    disciplines = relationship(
        "Discipline",
        secondary=discipline_education_plans,
        back_populates="education_plans",
        lazy="joined",
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
                session.query(EducationPlan)
                .filter(
                    EducationPlan.id == id,
                )
                .first()
            )

    @staticmethod
    def get_or_create(
        profile, education_direction_id, year, education_level, disciplines
    ):
        with db_session() as session:
            education_plan = (
                session.query(EducationPlan)
                .filter(
                    EducationPlan.profile == profile,
                    EducationPlan.education_direction_id == education_direction_id,
                    EducationPlan.year == year,
                    EducationPlan.education_level == education_level,
                )
                .first()
            )
            if education_plan is None:
                education_plan = EducationPlan(
                    profile=profile,
                    education_direction_id=education_direction_id,
                    year=year,
                    education_level=education_level,
                    disciplines=disciplines,
                )

                session.add(education_plan)
                session.commit()
                session.refresh(education_plan)

            return education_plan

    @staticmethod
    def get_by_name(name):
        with db_session() as session:
            return (
                session.query(EducationPlan).filter(EducationPlan.name == name).first()
            )

    @staticmethod
    def search_by_profile(profile):
        with db_session() as session:
            return (
                session.query(EducationPlan)
                .filter(EducationPlan.profile.contains(profile))
                .all()
            )


EducationPlan.__table__.create(checkfirst=True)
discipline_education_plans.create(checkfirst=True)
