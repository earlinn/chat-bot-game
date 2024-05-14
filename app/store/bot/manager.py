import asyncio
import typing
from logging import getLogger

from app.game.const import GameStage
from app.game.models import GameModel
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

    async def start_betting_stage(self, context: BotManagerContext):
        """Печатает сообщение о старте игры, её участниках,
        а также выводит кнопки для ставок.
        """
        current_game: GameModel = (
            await self.app.store.games.change_active_game_stage(
                chat_id=context.chat_id, stage=GameStage.BETTING
            )
        )
        players: str = ", ".join(
            ["@" + player.username for player in current_game.players]
        )
        button_message = SendMessage(
            chat_id=context.chat_id,
            text=END_TIMER_MESSAGE.format(players=players),
            # TODO:
            # - добавить к каждой кнопке перехват в роутере, чтобы в геймплее
            # игрока обновлялся размер ставки (изначально там 1);
            # - из роутера вызвать метод бот менеджера, который напечатает,
            # сколько поставил данный игрок, и поменяет ему в его геймплее
            # статус с BETTING на TAKING, а также проверит, есть ли игроки,
            # не сделавшие ставку, если есть, то ничего не делаем, просто ждем;
            # - если все игроки сделали ставку, выводим сообщение, что ставки
            # сделаны, и кнопки "Взять карту" и "Достаточно карт", также меняем
            # стадию игры на PLAYERHIT;
            # - добавить к каждой кнопке перехват в роутере;
            # - если нажата кнопка "Взять карту", то в бот менеджере
            # подсчитываем сумму его очков, если он превысил 21, то выводим ему
            # сообщение о переборе очков и меняем в его геймплее статус на
            # EXCEEDED, также проверяем, остались ли другие игроки,
            # в зависимости от этого обновляем стадию игры (если все игроки
            # EXCEEDED, то пропускаем стадию DILLERHIT и сразу переходим
            # к стадии SUMMARIZING и выводим итоговое сообщение, кто с какими
            # очками закончил игру);
            # - если нажата кнопка "Достаточно карт", меняем в геймплее игрока
            # его статус на STANDING и проверяем, есть ли еще игроки в статусе
            # TAKING, если таких нет, то меняем стадию игры на DILLERHIT, и бот
            # берет новые карты, пока не достигнет 17 очков, после этого
            # переходим к стадии игры SUMMARIZING, обновляем статусы игроков
            # (LOST или WON) и выводим итоговое сообщение, кто с какими
            # очками закончил игру)
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
