import pytest

from app.game.models import PlayerModel
from app.store import Store
from app.web.exceptions import TG_USERNAME_ERROR, TgUsernameError
from tests.const import *


# TODO: можно протестировать связи с моделями баланса, игры, геймплея
class TestPlayerModel:
    # TODO: у PlayerModel нет дефолтных значений в полях, этот тест можно
    # перенести в тестирование акцессоров
    async def test_player_defaults(self, store: Store) -> None:
        player = await store.players.create_player(
            username=TEST_PLAYER_VALID_USERNAME, tg_id=TEST_PLAYER_TG_ID
        )

        assert isinstance(player, PlayerModel)
        assert player.username == TEST_PLAYER_VALID_USERNAME
        assert player.tg_id == TEST_PLAYER_TG_ID

    def test_player_valid_username(self) -> None:
        validated_username = PlayerModel().validate_username(
            "username", TEST_PLAYER_VALID_USERNAME
        )
        assert validated_username == TEST_PLAYER_VALID_USERNAME

    def test_username_invalid(self):
        for username in TEST_PLAYER_INVALID_USERNAMES:
            with pytest.raises(TgUsernameError) as exc_info:
                PlayerModel().validate_username("username", username)
            assert exc_info.value.message == TG_USERNAME_ERROR
