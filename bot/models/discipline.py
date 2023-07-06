import sqlalchemy as db
from sqlalchemy.orm import relationship

from bot.db import base, db_session
from bot.models.base import BaseModel
from bot.models.control_form import ControlForm
from bot.models.discipline_name import DisciplineName


class Discipline(BaseModel):
    __tablename__ = "disciplines"

    id = db.Column(db.Integer, primary_key=True)
    name_id = db.Column(
        db.Integer, db.ForeignKey("discipline_names.id"), nullable=False
    )
    name = relationship(DisciplineName, back_populates="disciplines", lazy="joined")
    semester = db.Column(db.Integer, nullable=False)
    by_choice = db.Column(db.Boolean, nullable=False)
    is_optional = db.Column(db.Boolean, nullable=False)
    is_practice = db.Column(db.Boolean, nullable=False)
    lek = db.Column(db.FLOAT, nullable=True)
    lab = db.Column(db.FLOAT, nullable=True)
    pr = db.Column(db.FLOAT, nullable=True)
    sr = db.Column(db.FLOAT, nullable=True)
    control_forms = relationship(
        "ControlForm",
        secondary="discipline_control_forms",
        back_populates="disciplines",
        lazy="joined",
    )
    education_plans = relationship(
        "EducationPlan",
        secondary="discipline_education_plans",
        back_populates="disciplines",
    )

    def create(self):
        with db_session() as session:
            session.add(self)
            session.commit()
            session.refresh(self)

    @staticmethod
    def get_or_create(
        name_id,
        semester,
        by_choice,
        is_optional,
        is_practice,
        lek,
        lab,
        pr,
        sr,
        control_forms,
    ):
        with db_session() as session:
            discipline = (
                session.query(Discipline)
                .filter(
                    Discipline.name_id == name_id,
                    Discipline.semester == semester,
                    Discipline.by_choice == by_choice,
                    Discipline.is_optional == is_optional,
                    Discipline.is_practice == is_practice,
                    Discipline.lek == lek,
                    Discipline.lab == lab,
                    Discipline.pr == pr,
                    Discipline.sr == sr,
                )
                .first()
            )
            if discipline is None:
                discipline = Discipline(
                    name_id=name_id,
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
                try:
                    session.add(discipline)
                    session.commit()
                    session.refresh(discipline)
                except Exception as e:
                    discipline = (
                        session.query(Discipline)
                        .filter(
                            Discipline.name_id == name_id,
                            Discipline.semester == semester,
                            Discipline.by_choice == by_choice,
                            Discipline.is_optional == is_optional,
                            Discipline.is_practice == is_practice,
                            Discipline.lek == lek,
                            Discipline.lab == lab,
                            Discipline.pr == pr,
                            Discipline.sr == sr,
                        )
                        .first()
                    )
            return discipline

    @staticmethod
    def get_by_name(name_id, semester):
        with db_session() as session:
            return (
                session.query(Discipline)
                .filter(
                    Discipline.name_id == name_id,
                    Discipline.semester == semester,
                )
                .first()
            )


discipline_control_forms = db.Table(
    "discipline_control_forms",
    base.metadata,
    db.Column(
        "discipline_id",
        db.Integer,
        db.ForeignKey(Discipline.id),
        nullable=False,
        primary_key=True,
    ),
    db.Column(
        "control_form_id",
        db.Integer,
        db.ForeignKey(ControlForm.id),
        nullable=False,
        primary_key=True,
    ),
)


Discipline.__table__.create(checkfirst=True)
discipline_control_forms.create(checkfirst=True)
