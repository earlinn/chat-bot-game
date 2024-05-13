import typing

from .views import (
    BalanceAddView,
    BalanceListView,
    GameAddView,
    GameListView,
    GameUpdateStageView,
    PlayerAddView,
    PlayerListView,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/game.add", GameAddView)
    app.router.add_view("/game.list", GameListView)
    app.router.add_view("/game.update.stage", GameUpdateStageView)
    app.router.add_view("/game.player.add", PlayerAddView)
    app.router.add_view("/game.player.list", PlayerListView)
    app.router.add_view("/game.player.balance.add", BalanceAddView)
    app.router.add_view("/game.player.balance.list", BalanceListView)
