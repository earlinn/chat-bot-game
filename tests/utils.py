from collections.abc import Iterable

from app.game.models import BalanceModel, PlayerModel


def player_to_dict(player: PlayerModel) -> dict:
    return {"id": player.id, "username": player.username, "tg_id": player.tg_id}


def players_to_list(players: Iterable[PlayerModel]) -> list[dict]:
    return [player_to_dict(player) for player in players]


def balance_to_dict(balance: BalanceModel) -> dict:
    return {
        "id": balance.id,
        "chat_id": balance.chat_id,
        "player_id": balance.player_id,
        "current_value": balance.current_value,
    }


def balances_to_list(balances: Iterable[BalanceModel]) -> list[dict]:
    return [balance_to_dict(balance) for balance in balances]
