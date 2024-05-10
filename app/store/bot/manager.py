import typing
from logging import getLogger

from app.store.tg_api.dataclasses import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    SendMessage,
    Update,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application

WELCOME_MESSAGE: str = "Добро пожаловать в бот для игры в Блэк Джек!"
GAME_RULES_MESSAGE: str = "Посмотреть правила игры"
GAME_RULES_URL: str = "https://ru.wikihow.com/играть-в-блэкджек"
UNKNOWN_COMMAND_MESSAGE: str = "Неизвестная команда"


# TODO: after MVP make Worker class with asyncio.Queue
class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")

    async def say_hi(self, update: Update):
        await self.app.store.tg_api.send_message_with_button(
            SendMessage(
                chat_id=update.message.chat.id,
                text=WELCOME_MESSAGE,
                reply_markup=InlineKeyboardMarkup(
                    [
                        InlineKeyboardButton(
                            text=GAME_RULES_MESSAGE, url=GAME_RULES_URL
                        )
                    ]
                ),
            )
        )

    async def unknown_command(self, update: Update):
        await self.app.store.tg_api.send_message(
            SendMessage(
                chat_id=update.message.chat.id,
                text=UNKNOWN_COMMAND_MESSAGE,
            )
        )
