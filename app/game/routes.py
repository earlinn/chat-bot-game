import typing

from app.game.views import BalanceAddView, PlayerAddView, PlayerListView

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/game.player_add", PlayerAddView)
    app.router.add_view("/game.player_list", PlayerListView)
    app.router.add_view("/game.balance_add", BalanceAddView)
