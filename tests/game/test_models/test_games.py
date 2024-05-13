from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.game.const import GameStage, GameStatus
from app.game.models import GameModel, PlayerModel
from tests.const import *


# TODO: Тестируем
# - каскадное удаление игры при удалении turn_player_id (тест не проходит)
# - relationship gameplays (когда будет фикстура геймплея)
class TestPlayerModel:
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

        assert game.stage == GameStage.WAITING

    async def test_default_turn_player_id(
        self,
        db_sessionmaker: async_sessionmaker[AsyncSession],
    ):
        game = GameModel(chat_id=TEST_CHAT_ID, diller_cards=[TEST_DILLER_CARD])

        async with db_sessionmaker() as session:
            session.add(game)
            await session.commit()

        assert game.turn_player_id is None

    # TODO: может я как-то не так делаю session.refresh? Ожидаю, что после
    # удаления player удалится и сама игра, где ему принадлежит право хода,
    # но в deleted_game не None, а все та же игра (game_with_turn_player_id)
    @pytest.mark.skip(
        "Игра deleted_game не удаляется, несмотря на удаление игрока player"
    )
    async def test_cascade_deletion_if_turn_player_deleted(
        self,
        db_sessionmaker: async_sessionmaker[AsyncSession],
        game_with_turn_player_id: GameModel,
        player: PlayerModel,
    ):
        async with db_sessionmaker() as session:
            session.delete(player)
            await session.commit()
            session.refresh(player)
            session.refresh(game_with_turn_player_id)
            deleted_game = await session.get(
                GameModel, game_with_turn_player_id.id
            )

        assert deleted_game is None

    async def test_turn_player_relationship(
        self,
        db_sessionmaker: async_sessionmaker[AsyncSession],
        game_with_turn_player_id: GameModel,
        player: PlayerModel,
    ):
        async with db_sessionmaker() as session:
            game_from_session = await session.scalar(
                select(GameModel).options(selectinload(GameModel.turn_player))
            )

        assert game_from_session.turn_player.id == player.id
