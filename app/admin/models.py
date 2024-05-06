from hashlib import sha256
from typing import Self

from aiohttp_session import Session
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.store.database.sqlalchemy_base import BaseModel


class AdminModel(BaseModel):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True)
    password: Mapped[str] = mapped_column(String(128))

    @classmethod
    def from_session(cls, session: Session) -> Self:
        return cls(id=session["admin"]["id"], email=session["admin"]["email"])

    @staticmethod
    def hashed_password(password: str) -> str:
        return sha256(password.encode()).hexdigest()

    def is_password_valid(self, password: str) -> bool:
        return self.password == self.hashed_password(password)
