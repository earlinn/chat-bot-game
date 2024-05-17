from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.game.const import GameStage, GameStatus
from app.game.models import GameModel
from tests.const import *


# TODO: Тестируем
# - relationship gameplays (когда будет фикстура геймплея)
class TestGameModel:
    async def test_default_created_at(
        self,
        db_sessionmaker: async_sessionmaker[AsyncSession],
    ):
        game = GameModel(chat_id=TEST_CHAT_ID, diller_cards=[TEST_DILLER_CARD])
        current_date = datetime.now().date()

        async with db_sessionmaker() as session:
            session.add(game)
            await session.commit()

        assert isinstance(game.created_at, datetime)
        # может падать в определенные часы из-за разницы часовых поясов
        assert game.created_at.date() == current_date

    async def test_default_status(
        self,
        db_sessionmaker: async_sessionmaker[AsyncSession],
    ):
        game = GameModel(chat_id=TEST_CHAT_ID, diller_cards=[TEST_DILLER_CARD])

        async with db_sessionmaker() as session:
            session.add(game)
            await session.commit()

        assert game.status == GameStatus.ACTIVE

    async def test_default_stage(
        self,
        db_sessionmaker: async_sessionmaker[AsyncSession],
    ):
        game = GameModel(chat_id=TEST_CHAT_ID, diller_cards=[TEST_DILLER_CARD])

        async with db_sessionmaker() as session:
            session.add(game)
            await session.commit()

        assert game.stage == GameStage.WAITING_FOR_PLAYERS_TO_JOIN
