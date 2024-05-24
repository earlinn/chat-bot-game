from collections.abc import Iterable

from app.game.models import DEFAULT_NEW_BALANCE, BalanceModel, PlayerModel
from app.store import Store
from tests.const import *
from tests.utils import (
    balance_to_dict,
    balances_to_list,
    player_to_dict,
    players_to_list,
)


class TestPlayerAccessor:
    async def test_create_player(self, store: Store):
        new_player: PlayerModel = await store.players.create_player(
            username=TEST_PLAYER_VALID_USERNAME,
            tg_id=TEST_PLAYER_TG_ID,
            first_name=TEST_PLAYER_FIRST_NAME,
        )

        assert isinstance(new_player, PlayerModel)
        assert new_player.username == TEST_PLAYER_VALID_USERNAME
        assert new_player.tg_id == TEST_PLAYER_TG_ID

    async def test_list_players(self, store: Store, player: PlayerModel):
        player_list: Iterable[PlayerModel] = await store.players.list_players()

        assert isinstance(player_list, Iterable)
        assert players_to_list(player_list)[0] == player_to_dict(player)

    async def test_get_player_by_id(self, store: Store, player: PlayerModel):
        player_found: PlayerModel = await store.players.get_player_by_id(
            player.id
        )

        assert isinstance(player, PlayerModel)
        assert player_to_dict(player_found) == player_to_dict(player)

    async def test_get_player_by_tg_id(self, store: Store, player: PlayerModel):
        player_found: PlayerModel = await store.players.get_player_by_tg_id(
            player.tg_id
        )

        assert isinstance(player, PlayerModel)
        assert player_to_dict(player_found) == player_to_dict(player)


class TestBalanceAccessor:
    async def test_create_player_balance(
        self, store: Store, player: PlayerModel
    ):
        new_balance: BalanceModel = await store.players.create_player_balance(
            chat_id=TEST_CHAT_ID, player_id=player.id
        )

        assert isinstance(new_balance, BalanceModel)
        assert new_balance.chat_id == TEST_CHAT_ID
        assert new_balance.player_id == player.id
        assert new_balance.current_value == DEFAULT_NEW_BALANCE

    async def test_list_balances(self, store: Store, balance: BalanceModel):
        balance_list: Iterable[
            BalanceModel
        ] = await store.players.list_balances()

        assert isinstance(balance_list, Iterable)
        assert balances_to_list(balance_list)[0] == balance_to_dict(balance)

    async def test_get_balance_by_player_and_chat(
        self, store: Store, player: PlayerModel, balance: BalanceModel
    ):
        balance_found: BalanceModel = (
            await store.players.get_balance_by_player_and_chat(
                player.id, TEST_CHAT_ID
            )
        )

        assert isinstance(balance_found, BalanceModel)
        assert balance_to_dict(balance_found) == balance_to_dict(balance)
