import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.game.models import BalanceModel, PlayerModel
from app.web.exceptions import TG_USERNAME_ERROR, TgUsernameError
from tests.const import *


# TODO: протестировать связи (relationship) с моделями игры и геймплея
class TestPlayerModel:
    def test_valid_username(self):
        validated_username = PlayerModel().validate_username(
            "username", TEST_PLAYER_VALID_USERNAME
        )
        assert validated_username == TEST_PLAYER_VALID_USERNAME

    def test_invalid_username(self):
        for username in TEST_PLAYER_INVALID_USERNAMES:
            with pytest.raises(TgUsernameError) as exc_info:
                PlayerModel().validate_username("username", username)
            assert exc_info.value.message == TG_USERNAME_ERROR

    async def test_balances_relationship(
        self,
        db_sessionmaker: async_sessionmaker[AsyncSession],
        balance: BalanceModel,
    ):
        async with db_sessionmaker() as session:
            player_from_session = await session.scalar(
                select(PlayerModel).options(selectinload(PlayerModel.balances))
            )

        # почему-то если делать сравнение самих объектов,
        # (т.е. assert player_from_session.balances[0] == balance),
        # тест падает с ошибкой AssertionError:
        # assert <BalanceModel id=1,chat_id=-4242424242,player_id=1> ==
        # <BalanceModel id=1,chat_id=-4242424242,player_id=1>
        # А если сравнивать только их id, то тест проходит.

        # Если делать запрос без selectinload, то тест падает с ошибкой
        # sqlalchemy.orm.exc.DetachedInstanceError: Parent instance
        # <PlayerModel at 0x752aaa6745c0> is not bound to a Session;
        # lazy load operation of attribute 'balances' cannot proceed
        # (Background on this error at: https://sqlalche.me/e/20/bhk3
        assert player_from_session.balances[0].id == balance.id
