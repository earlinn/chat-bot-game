import asyncio
import typing
from logging import getLogger

from app.store.tg_api.accessor import TgApiAccessor
from app.store.tg_api.dataclasses import (
    BotManagerContext,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    SendMessage,
)

# TODO: может сделать from .const import * ?
from .const import (
    ADD_PLAYER_CALLBACK,
    BET_10_BUTTON,
    BET_25_BUTTON,
    BET_50_BUTTON,
    BET_100_BUTTON,
    END_TIMER_MESSAGE,
    GAME_JOIN_BUTTON,
    GAME_RULES_BUTTON,
    GAME_RULES_URL,
    GAME_START_BUTTON,
    JOIN_GAME_CALLBACK,
    JOIN_NON_EXISTENT_GAME_ERROR,
    JOINED_GAME_MESSAGE,
    START_TIMER_MESSAGE,
    TIMER_DELAY_IN_SECONDS,
    UNKNOWN_COMMAND_MESSAGE,
    WAITING_MESSAGE,
    WELCOME_MESSAGE,
    WELCOME_WAITING_MESSAGE,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application


# TODO: after MVP make Worker class with asyncio.Queue
class BotManager:
    def __init__(self, app: "Application"):
        """Подключается к app и к логгеру."""
        self.app = app
        self.logger = getLogger("bot manager")
        self.background_tasks = set()

    @property
    def tg_api(self) -> TgApiAccessor:
        return self.app.store.tg_api

    async def _start_timer(
        self, coro: typing.Coroutine, seconds: int = TIMER_DELAY_IN_SECONDS
    ):
        """Запускает таймер на время, указанное в аргументе seconds,
        по прошествии этого времени вызывает корутину coro.
        """
        await asyncio.sleep(seconds)
        await coro

    async def say_hi_and_play(self, context: BotManagerContext):
        """Печатает приветствие, а также кнопки 'Начать игру' и
        'Посмотреть правила игры'.
        """
        button_message = SendMessage(
            chat_id=context.chat_id,
            text=WELCOME_MESSAGE,
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        text=GAME_START_BUTTON,
                        callback_data=JOIN_GAME_CALLBACK,
                    ),
                    InlineKeyboardButton(
                        text=GAME_RULES_BUTTON, url=GAME_RULES_URL
                    ),
                ]
            ),
        )
        await self.tg_api.send_message(button_message, any_buttons_present=True)

    async def say_hi_and_wait(self, context: BotManagerContext):
        """Печатает приветствие и кнопку 'Посмотреть правила игры',
        предлагает дождаться окончания текущей игры.
        """
        button_message = SendMessage(
            chat_id=context.chat_id,
            text=WELCOME_WAITING_MESSAGE,
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        text=GAME_RULES_BUTTON, url=GAME_RULES_URL
                    ),
                ]
            ),
        )
        await self.tg_api.send_message(button_message, any_buttons_present=True)

    async def wait_next_game(self, context: BotManagerContext):
        """Предлагает дождаться окончания текущей игры."""
        button_message = SendMessage(
            chat_id=context.chat_id, text=WAITING_MESSAGE
        )
        await self.tg_api.send_message(button_message)

    async def join_new_game(self, context: BotManagerContext):
        """Печатает сообщение о возможности присоединиться к новой игре
        в течение определенного времени и кнопку 'Присоединиться к игре',
        затем запускает таймер.
        """
        button_message = SendMessage(
            chat_id=context.chat_id,
            text=START_TIMER_MESSAGE,
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        text=GAME_JOIN_BUTTON,
                        callback_data=ADD_PLAYER_CALLBACK,
                    ),
                ]
            ),
        )
        await self.tg_api.send_message(button_message, any_buttons_present=True)

        # More info: https://docs.astral.sh/ruff/rules/asyncio-dangling-task/
        timer_task = asyncio.create_task(
            self._start_timer(self.start_betting_stage(context))
        )
        self.logger.info(timer_task)
        self.background_tasks.add(timer_task)
        timer_task.add_done_callback(self.background_tasks.discard)

    async def player_joined(self, context: BotManagerContext):
        """Печатает сообщение о том, что игрок присоединился к игре."""
        await self.tg_api.send_message(
            SendMessage(
                chat_id=context.chat_id,
                text=JOINED_GAME_MESSAGE.format(username=context.username),
            )
        )

    async def join_non_existent_game_fail(self, context: BotManagerContext):
        """Печатает сообщение о том, что нельзя присоединиться
        к несуществующей игре.
        """
        await self.tg_api.send_message(
            SendMessage(
                chat_id=context.chat_id,
                text=JOIN_NON_EXISTENT_GAME_ERROR,
            )
        )

    # TODO:
    # Хочется вывести в этом сообщении список username игроков в текущей
    # игре, но чтобы их узнать, нужно прямо из этого метода сделать запрос в БД
    # для получения активной игры в данном чате и ее игроков.
    # Однако это нарушит ограничение, что запросы к БД делаются только
    # из роутера.
    async def start_betting_stage(self, context: BotManagerContext):
        """Печатает сообщение о старте игры и кнопки для ставок."""
        # TODO: перед ставками чекнуть, что в игре хотя бы один игрок
        button_message = SendMessage(
            chat_id=context.chat_id,
            text=END_TIMER_MESSAGE,
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        text=BET_10_BUTTON,
                        callback_data="make_bet_10",
                    ),
                    InlineKeyboardButton(
                        text=BET_25_BUTTON,
                        callback_data="make_bet_25",
                    ),
                    InlineKeyboardButton(
                        text=BET_50_BUTTON,
                        callback_data="make_bet_50",
                    ),
                    InlineKeyboardButton(
                        text=BET_100_BUTTON,
                        callback_data="make_bet_100",
                    ),
                ]
            ),
        )
        await self.tg_api.send_message(button_message, any_buttons_present=True)

    # TODO: пока не используется, но возможно пригодится в будущем
    async def unknown_command(self, context: BotManagerContext):
        """Печатает сообщение о том, что команда неизвестна."""
        await self.tg_api.send_message(
            SendMessage(chat_id=context.chat_id, text=UNKNOWN_COMMAND_MESSAGE)
        )
