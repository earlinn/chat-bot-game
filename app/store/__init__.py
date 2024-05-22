import typing
from logging import getLogger

from app.store.database.database import Database
from app.store.rabbit.rabbit import Rabbit

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from app.store.admin.accessor import AdminAccessor
        from app.store.bot.handler import BotHandler
        from app.store.bot.manager import BotManager
        from app.store.game.accessor import (
            GameAccessor,
            GamePlayAccessor,
            PlayerAccessor,
        )
        from app.store.game.manager import GameManager, PlayerManager
        from app.store.tg_api.accessor import TgApiAccessor

        self.admins = AdminAccessor(app)
        self.players = PlayerAccessor(app)
        self.games = GameAccessor(app)
        self.gameplays = GamePlayAccessor(app)
        self.bot_handler = BotHandler(app)
        self.bot_manager = BotManager(app)
        self.player_manager = PlayerManager(app)
        self.game_manager = GameManager(app)
        self.tg_api = TgApiAccessor(app)
        self.logger = getLogger("store")


def setup_store(app: "Application"):
    app.database = Database(app)
    app.rabbit = Rabbit(app)
    app.on_startup.append(app.database.connect)
    app.on_startup.append(app.rabbit.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.on_cleanup.append(app.rabbit.disconnect)
    app.store = Store(app)
