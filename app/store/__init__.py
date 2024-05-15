import typing
from logging import getLogger

from app.store.database.database import Database

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
        from app.store.game.manager import GameManager
        from app.store.tg_api.accessor import TgApiAccessor

        self.admins = AdminAccessor(app)
        self.players = PlayerAccessor(app)
        self.games = GameAccessor(app)
        self.gameplays = GamePlayAccessor(app)
        self.bot_handler = BotHandler(app)
        self.bot_manager = BotManager(app)
        self.game_manager = GameManager(app)
        self.tg_api = TgApiAccessor(app)
        self.logger = getLogger("store")


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.store = Store(app)
