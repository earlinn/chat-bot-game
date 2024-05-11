import asyncio
import typing
from logging import getLogger

from app.store.tg_api.dataclasses import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    SendMessage,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application

WELCOME_MESSAGE: str = "Добро пожаловать в бот для игры в Блэк Джек!"
WELCOME_WAITING_MESSAGE: str = (
    "Добро пожаловать в бот для игры в Блэк Джек!\n"
    "В настоящее время в этом чате уже идет игра. "
    "Чтобы сыграть, пожалуйста, дождитесь окончания текущей игры."
)
WAITING_MESSAGE: str = (
    "В настоящее время в этом чате уже идет игра. "
    "Чтобы сыграть, пожалуйста, дождитесь окончания текущей игры."
)
GAME_START_MESSAGE: str = "Начать новую игру"
GAME_JOIN_BUTTON: str = "Присоединиться к игре"
GAME_RULES_BUTTON: str = "Посмотреть правила игры"
MAKE_BET_BUTTON: str = "Сделать ставку"
GAME_RULES_URL: str = "https://ru.wikihow.com/играть-в-блэкджек"
TIMER_DELAY_IN_SECONDS: int = 30
START_TIMER_MESSAGE: str = (
    "Начинаем новую игру. Чтобы присоединиться к игре, нажмите на кнопку ниже "
    f"в течение {TIMER_DELAY_IN_SECONDS} секунд."
)
END_TIMER_MESSAGE: str = "Игра началась. Игроки делают ставки."
UNKNOWN_COMMAND_MESSAGE: str = "Неизвестная команда"


# TODO: after MVP make Worker class with asyncio.Queue
class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("bot manager")

    async def say_hi_and_play(self, chat_id: int):
        button_message: SendMessage = SendMessage(
            chat_id=chat_id,
            text=WELCOME_MESSAGE,
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        text=GAME_START_MESSAGE,
                        callback_data="join_new_game",
                    ),
                    InlineKeyboardButton(
                        text=GAME_RULES_BUTTON, url=GAME_RULES_URL
                    ),
                ]
            ),
        )
        reply_markup = button_message.reply_markup.json_reply_markup_keyboard()
        await self.app.store.tg_api.send_message(button_message, reply_markup)

    async def say_hi_and_wait(self, chat_id: int):
        button_message: SendMessage = SendMessage(
            chat_id=chat_id,
            text=WELCOME_WAITING_MESSAGE,
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        text=GAME_RULES_BUTTON, url=GAME_RULES_URL
                    ),
                ]
            ),
        )
        reply_markup = button_message.reply_markup.json_reply_markup_keyboard()
        await self.app.store.tg_api.send_message(button_message, reply_markup)

    async def wait_next_game(self, chat_id: int):
        button_message: SendMessage = SendMessage(
            chat_id=chat_id, text=WAITING_MESSAGE
        )
        await self.app.store.tg_api.send_message(button_message)

    # TODO:
    # Хочется вывести в этом сообщении список username игроков в текущей
    # игре, но чтобы их узнать, нужно прямо из этого метода сделать запрос в БД
    # для получения активной игры в данном чате и ее игроков.
    # Однако это нарушит ограничение, что запросы к БД делаются только
    # из роутера.
    async def start_betting_stage(self, chat_id: int):
        await asyncio.sleep(TIMER_DELAY_IN_SECONDS)
        button_message = SendMessage(
            chat_id=chat_id,
            text=END_TIMER_MESSAGE,
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        text=MAKE_BET_BUTTON,
                        callback_data="make_bet",
                    ),
                ]
            ),
        )
        reply_markup = button_message.reply_markup.json_reply_markup_keyboard()
        await self.app.store.tg_api.send_message(button_message, reply_markup)
        # Пока к callback_query "make_bet" не подключены никакие действия,
        # но в дальнейшем он будет обработан в роутере - стадия (поле stage
        # в GameModel) игры поменяется с WAITING на BETTING, а в gameplay
        # игрока, нажавшего на кнопку "Сделать ставку" поменяется размер ставки
        # (поле player_bet в GamePlayModel).

        # Но сейчас игроку негде указать размер своей ставки.
        # 1 вариант - сделать ставку фиксированной, например, по нажатию на
        # кнопку "Сделать ставку 10" делается ставка 10, тогда у всех
        # игроков будет одинаковый размер ставки. Хотя можно сделать несколько
        # кнопок с разными фиксированными размерами ставок.
        # 2 вариант - сделать не кнопку, а команду типа /bet<размер ставки>,
        # например, /bet10, /bet50. Но как игрок узнает список всех возможных
        # команд /bet<размер ставки> ? Поэтому 1 вариант кажется лучше.

        # После каждой сделанной ставки нужно из роутера дергать БД - проверять,
        # есть ли игроки, не сделавшие ставку. И если все сделали ставки, то
        # менять стадию игры с BETTING на PLAYERHIT, раздавать игрокам
        # по 2 карты и выводить на печать их карты и единственную карту диллера,
        # предлагая взять еще карту или остановиться (2 кнопки).

    async def join_new_game(self, chat_id: int):
        button_message = SendMessage(
            chat_id=chat_id,
            text=START_TIMER_MESSAGE,
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        text=GAME_JOIN_BUTTON,
                        callback_data="add_player",
                    ),
                ]
            ),
        )
        reply_markup = button_message.reply_markup.json_reply_markup_keyboard()
        await self.app.store.tg_api.send_message(button_message, reply_markup)

        # Приходится создавать переменную timer_task, иначе ruff выдает ошибку:
        # RUF006 Store a reference to the return value of `asyncio.create_task`

        # Чтобы переменная timer_task была использована, передаю ее в логгер,
        # иначе ruff выдаст ошибку: F841 Local variable `timer_task` is assigned
        # to but never used
        timer_task = asyncio.create_task(self.start_betting_stage(chat_id))
        self.logger.info(timer_task)

        # вариант с loop.call_later не получился, т.к. метод
        # self.start_betting_stage(chat_id) (в нем тогда не было строки
        # await asyncio.sleep(TIMER_DELAY_IN_SECONDS)) вызывался
        # не через 30 секунд, а сразу. Поэтому сделала asyncio.create_task

        # loop = asyncio.get_event_loop()
        # loop.call_later(
        #     TIMER_DELAY_IN_SECONDS, await self.start_betting_stage(chat_id)
        # )

    async def player_joined(self, chat_id: int, username: str):
        await self.app.store.tg_api.send_message(
            SendMessage(chat_id=chat_id, text=f"{username} в игре")
        )

    # TODO: пока не используется, но возможно пригодится в будущем
    async def unknown_command(self, chat_id: int):
        await self.app.store.tg_api.send_message(
            SendMessage(chat_id=chat_id, text=UNKNOWN_COMMAND_MESSAGE)
        )
