import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.game.models import BalanceModel, PlayerModel
from tests.const import *


class TestPlayerModel:
    async def test_default_in_current_value(
        self,
        db_sessionmaker: async_sessionmaker[AsyncSession],
        player: PlayerModel,
    ):
        balance = BalanceModel(chat_id=TEST_CHAT_ID, player_id=player.id)

        async with db_sessionmaker() as session:
            session.add(balance)
            await session.commit()

        assert balance.current_value == 1000

    async def test_chat_player_unique_constraint(
        self,
        db_sessionmaker: async_sessionmaker[AsyncSession],
        player: PlayerModel,
        balance: BalanceModel,
    ):
        duplicate_balance = BalanceModel(
            chat_id=TEST_CHAT_ID, player_id=player.id
        )

        async with db_sessionmaker() as session:
            session.add(duplicate_balance)
            with pytest.raises(IntegrityError):
                await session.commit()

    async def test_player_relationship(
        self,
        db_sessionmaker: async_sessionmaker[AsyncSession],
        player: PlayerModel,
        balance: BalanceModel,
    ):
        async with db_sessionmaker() as session:
            balance_from_session = await session.scalar(
                select(BalanceModel).options(selectinload(BalanceModel.player))
            )

        assert balance_from_session.player.id == player.id
