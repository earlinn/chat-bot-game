import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.game.models import BalanceModel, GameModel, PlayerModel
from tests.const import *


@pytest.fixture
async def player(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> PlayerModel:
    player: PlayerModel = PlayerModel(
        username=TEST_PLAYER_VALID_USERNAME, tg_id=TEST_PLAYER_TG_ID
    )

    async with db_sessionmaker() as session:
        session.add(player)
        await session.commit()

    return player


@pytest.fixture
async def balance(
    db_sessionmaker: async_sessionmaker[AsyncSession], player: PlayerModel
) -> BalanceModel:
    balance: BalanceModel = BalanceModel(
        chat_id=TEST_CHAT_ID, player_id=player.id
    )

    async with db_sessionmaker() as session:
        session.add(balance)
        await session.commit()

    return balance


@pytest.fixture
async def game(db_sessionmaker: async_sessionmaker[AsyncSession]) -> GameModel:
    game: GameModel = GameModel(
        chat_id=TEST_CHAT_ID, diller_cards=[TEST_DILLER_CARD]
    )

    async with db_sessionmaker() as session:
        session.add(game)
        await session.commit()

    return game


@pytest.fixture
async def game_with_turn_player_id(
    db_sessionmaker: async_sessionmaker[AsyncSession], player: PlayerModel
) -> GameModel:
    game: GameModel = GameModel(
        chat_id=TEST_CHAT_ID,
        diller_cards=[TEST_DILLER_CARD],
        turn_player_id=player.id,
    )

    async with db_sessionmaker() as session:
        session.add(game)
        await session.commit()

    return game
