import re
from datetime import datetime
from typing import Annotated

from sqlalchemy import ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.store.database.sqlalchemy_base import BaseModel

TG_USERNAME_ERROR: str = (
    "Username должен иметь длину от 5 до 32 символов, допускаются только "
    "латинские буквы, цифры и нижнее подчеркивание."
)
TG_USERNAME_REGEX: str = r"^[a-zA-Z0-9_]{5,32}$"
intpk = Annotated[int, mapped_column(primary_key=True)]
int_unique = Annotated[int, mapped_column(unique=True)]
int_default_1000 = Annotated[int, mapped_column(default=1000)]
created_at = Annotated[datetime, mapped_column(server_default=func.now())]


class PlayerModel(BaseModel):
    __tablename__ = "players"

    id: Mapped[intpk]
    username: Mapped[str] = mapped_column(String(32), unique=True)
    tg_id: Mapped[int_unique]

    balances: Mapped[list["BalanceModel"]] = relationship(
        back_populates="player"
    )

    @validates("username")
    def validate_username(self, key, value):
        if not re.match(TG_USERNAME_REGEX, value):
            raise ValueError(TG_USERNAME_ERROR)
        return value


class BalanceModel(BaseModel):
    __tablename__ = "balances"

    id: Mapped[intpk]
    chat_id: Mapped[int]
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE")
    )
    current_value: Mapped[int_default_1000]
    max_value: Mapped[int_default_1000]
    min_value: Mapped[int_default_1000]

    player: Mapped["PlayerModel"] = relationship(back_populates="balances")

    __table_args__ = (
        UniqueConstraint("chat_id", "player_id", name="chat_player_unique"),
    )
