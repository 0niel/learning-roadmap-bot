import sqlalchemy as db
from sqlalchemy.orm import relationship

from bot.db import db_session
from bot.models.base import BaseModel


class DisciplineName(BaseModel):
    __tablename__ = "discipline_names"

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.UnicodeText, nullable=False, index=True, unique=True)
    disciplines = relationship("Discipline", back_populates="name")

    def create(self):
        with db_session() as session:
            session.add(self)
            session.commit()
            session.refresh(self)

    @staticmethod
    def get_or_create(text):
        with db_session() as session:
            discipline_name = (
                session.query(DisciplineName)
                .filter(
                    DisciplineName.text == text,
                )
                .first()
            )

            if discipline_name is None:
                discipline_name = DisciplineName(
                    text=text,
                )
                session.add(discipline_name)
                session.commit()
                session.refresh(discipline_name)

            return discipline_name

    @staticmethod
    def get_by_text(text):
        with db_session() as session:
            return (
                session.query(DisciplineName)
                .filter(
                    DisciplineName.text == text,
                )
                .first()
            )


DisciplineName.__table__.create(checkfirst=True)
