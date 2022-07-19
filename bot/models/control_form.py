import sqlalchemy as db
from sqlalchemy.orm import relationship

from bot.db import db_session
from bot.models.base import BaseModel


class ControlForm(BaseModel):
    __tablename__ = "control_forms"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Integer, nullable=False, index=True, unique=True)
    disciplines = relationship(
        "Discipline",
        secondary="discipline_control_forms",
        back_populates="control_forms",
    )

    def create(self):
        with db_session() as session:
            session.add(self)
            session.commit()
            session.refresh(self)

    @staticmethod
    def get_or_create(type):
        with db_session() as session:
            control_form = (
                session.query(ControlForm)
                .filter(
                    ControlForm.type == type,
                )
                .first()
            )
            if control_form is None:
                control_form = ControlForm(
                    type=type,
                )
                session.add(control_form)
                session.commit()
                session.refresh(control_form)
            return control_form

    @staticmethod
    def get_by_type(type):
        with db_session() as session:
            return (
                session.query(ControlForm)
                .filter(
                    ControlForm.type == type,
                )
                .first()
            )


ControlForm.__table__.create(checkfirst=True)
