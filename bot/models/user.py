import sqlalchemy as db

from bot.db import db_session
from bot.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    id = db.Column(db.BigInteger, primary_key=True, unique=True)

    @staticmethod
    def create_if_not_exists(id):
        with db_session() as session:
            user = session.query(User).filter(User.id == id).first()
            if user is None:
                user = User(id=id)
                session.add(user)
                session.commit()
                session.refresh(user)
            return user


User.__table__.create(checkfirst=True)
