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
WELCOME_WAITING_MESSAGE: str = (
    "Добро пожаловать в бот для игры в Блэк Джек! "
    "В настоящее время в этом чате уже идет игра. "
    "Чтобы сыграть, пожалуйста, дождитесь окончания текущей игры."
)
GAME_START_MESSAGE: str = "Начать новую игру"
GAME_RULES_MESSAGE: str = "Посмотреть правила игры"
GAME_RULES_URL: str = "https://ru.wikihow.com/играть-в-блэкджек"
START_TIMER_MESSAGE: str = (
    "Начинаем новую игру. Чтобы присоединиться к игре, нажмите на кнопку ниже "
    "в течение 30 секунд."
)
UNKNOWN_COMMAND_MESSAGE: str = "Неизвестная команда"


# TODO: after MVP make Worker class with asyncio.Queue
class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")

    async def say_hi_and_play(self, update: Update):
        button_message: SendMessage = SendMessage(
            chat_id=update.message.chat.id,
            text=WELCOME_MESSAGE,
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        text=GAME_START_MESSAGE,
                        # url=GAME_RULES_URL,  # TODO: remove this parameter
                        callback_data="some_func",  # TODO: add
                    ),
                    InlineKeyboardButton(
                        text=GAME_RULES_MESSAGE, url=GAME_RULES_URL
                    ),
                ]
            ),
        )
        reply_markup = button_message.reply_markup.json_reply_markup_keyboard()
        await self.app.store.tg_api.send_message(button_message, reply_markup)

    async def say_hi_and_wait(self, update: Update):
        button_message: SendMessage = SendMessage(
            chat_id=update.message.chat.id,
            text=WELCOME_WAITING_MESSAGE,
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        text=GAME_RULES_MESSAGE, url=GAME_RULES_URL
                    ),
                ]
            ),
        )
        reply_markup = button_message.reply_markup.json_reply_markup_keyboard()
        await self.app.store.tg_api.send_message(button_message, reply_markup)

    async def start_timer(self, chat_id: int):
        # TODO: добавить кнопку присоединения к игре и запустить
        # асинхронный обратный отсчет времени
        await self.app.store.tg_api.send_message(
            SendMessage(chat_id=chat_id, text=START_TIMER_MESSAGE)
        )

    async def unknown_command(self, chat_id: int):
        await self.app.store.tg_api.send_message(
            SendMessage(chat_id=chat_id, text=UNKNOWN_COMMAND_MESSAGE)
        )
