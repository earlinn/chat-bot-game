import re
from datetime import datetime
from typing import Annotated

from sqlalchemy import (
    ARRAY,
    BigInteger,
    CheckConstraint,
    ForeignKey,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.store.database.sqlalchemy_base import BaseModel
from app.web.exceptions import TgUsernameError

from .const import GameStage, GameStatus, PlayerStatus

TG_USERNAME_REGEX: str = r"^[a-zA-Z0-9_]{5,32}$"
DEFAULT_NEW_BALANCE = 1000
intpk = Annotated[int, mapped_column(primary_key=True)]
int_default_1000 = Annotated[int, mapped_column(default=DEFAULT_NEW_BALANCE)]
created_at = Annotated[
    datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))
]


class PlayerModel(BaseModel):
    __tablename__ = "players"

    id: Mapped[intpk]
    username: Mapped[str] = mapped_column(String(32), unique=True)
    tg_id: Mapped[int] = mapped_column(BigInteger(), unique=True)

    balances: Mapped[list["BalanceModel"]] = relationship(
        back_populates="player"
    )
    gameplays: Mapped[list["GamePlayModel"]] = relationship(
        back_populates="player"
    )

    @validates("username")
    def validate_username(self, key: str, value: str):
        if not re.match(TG_USERNAME_REGEX, value):
            raise TgUsernameError
        return value


class BalanceModel(BaseModel):
    __tablename__ = "balances"

    id: Mapped[intpk]
    chat_id: Mapped[int] = mapped_column(BigInteger())
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE")
    )
    current_value: Mapped[int_default_1000]
    # TODO: add max_value, min_value after MVP
    # max_value: Mapped[int_default_1000]
    # min_value: Mapped[int_default_1000]

    player: Mapped["PlayerModel"] = relationship(back_populates="balances")

    __table_args__ = (
        UniqueConstraint("chat_id", "player_id", name="chat_player_unique"),
    )


# TODO: добавить поле для таймера, чтобы хранить его не в константе
# WAITING_STAGE_TIMER_IN_SECONDS, а иметь возможность редактировать через
# Админку, а константа станет временем по дефолту.
# Можно сделать одно поле для таймера на стадии присоединения игроков
# (константа WAITING_STAGE_TIMER_IN_SECONDS) и второе поле для таймера на стадии
# ставок (константа BETTING_STAGE_TIMER_IN_SECONDS).
# TODO: добавить поле для минимальных очков диллера, чтобы хранить его не в
# константе DILLER_STOP_SCORE, а иметь возможность редактировать через Админку,
# а константа станет количеством очков по дефолту
# TODO: можно управлять размером минимальной ставки (константа MINIMAL_BET) или
# даже всеми предлагаемыми ставками (их количеством и значениями) через Админку
class GameModel(BaseModel):
    __tablename__ = "games"

    id: Mapped[intpk]
    chat_id: Mapped[int] = mapped_column(BigInteger())
    created_at: Mapped[created_at]
    status: Mapped[GameStatus] = mapped_column(default=GameStatus.ACTIVE)
    stage: Mapped[GameStage] = mapped_column(
        default=GameStage.WAITING_FOR_PLAYERS_TO_JOIN
    )
    diller_cards: Mapped[list[str]] = mapped_column(ARRAY(String))

    gameplays: Mapped[list["GamePlayModel"]] = relationship(
        back_populates="game"
    )


class GamePlayModel(BaseModel):
    __tablename__ = "gameplays"

    id: Mapped[intpk]
    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE")
    )
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE")
    )
    player_bet: Mapped[int]
    player_status: Mapped[PlayerStatus] = mapped_column(
        default=PlayerStatus.BETTING
    )
    player_cards: Mapped[list[str] | None] = mapped_column(ARRAY(String))

    game: Mapped["GameModel"] = relationship(back_populates="gameplays")
    player: Mapped["PlayerModel"] = relationship(back_populates="gameplays")

    __table_args__ = (
        UniqueConstraint("game_id", "player_id", name="game_player_unique"),
        CheckConstraint(
            "player_bet > 0", name="positive_player_bet_constraint"
        ),
    )
