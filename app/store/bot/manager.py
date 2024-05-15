import asyncio
import typing
from logging import getLogger

from app.game.const import GameStage
from app.game.models import GameModel, PlayerModel
from app.store.bot import const
from app.store.game.manager import GameManager
from app.store.tg_api.accessor import TgApiAccessor
from app.store.tg_api.dataclasses import (
    BotContext,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    SendMessage,
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

    @property
    def game_manager(self) -> GameManager:
        return self.app.store.game_manager

    async def handle_no_game_case(
        self, query: CallbackQuery, bot_context: BotContext
    ) -> None:
        """Обрабатывает callback_query при отсутствии активной игры в чате."""
        query_message: str = query.data

        if query_message == const.ADD_PLAYER_CALLBACK:
            await self._say_join_non_existent_game_fail(bot_context)

        elif query_message == const.JOIN_GAME_CALLBACK:
            player: PlayerModel = await self.game_manager.get_player(
                query.from_.id, query.from_.username, bot_context.chat_id
            )
            game: GameModel = await self.game_manager.get_game(
                bot_context.chat_id
            )
            await self.game_manager.get_gameplay(game.id, player.id)
            await self._say_join_new_game(bot_context)
            bot_context.username = player.username
            await self._say_player_joined(bot_context)

    async def handle_active_game(
        self,
        game: GameModel,
        query: CallbackQuery,
        bot_context: BotContext,
    ) -> None:
        """Обрабатывает callback_query при наличии активной игры в чате."""
        query_message: str = query.data

        if game.stage == GameStage.WAITING_FOR_PLAYERS_TO_JOIN:
            await self._handle_game_waiting_stage(game, query, bot_context)
        elif (
            query_message == const.JOIN_GAME_CALLBACK
            or query_message == const.ADD_PLAYER_CALLBACK
        ):
            await self._say_wait_next_game(bot_context)

    async def _handle_game_waiting_stage(
        self, game: GameModel, query: CallbackQuery, bot_context: BotContext
    ) -> None:
        """Обрабатывает игру в состоянии ожидания присоединения игроков."""
        query_message: str = query.data

        if query_message == const.ADD_PLAYER_CALLBACK:
            player: PlayerModel = await self.game_manager.get_player(
                query.from_.id, query.from_.username, bot_context.chat_id
            )
            await self.game_manager.get_gameplay(game.id, player.id)
            bot_context.username = player.username
            await self._say_player_joined(bot_context)

    async def say_hi_and_play(self, context: BotContext):
        """Печатает приветствие, а также кнопки 'Начать игру' и
        'Посмотреть правила игры'.
        """
        button_message = SendMessage(
            chat_id=context.chat_id,
            text=const.WELCOME_MESSAGE,
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        text=const.GAME_START_BUTTON,
                        callback_data=const.JOIN_GAME_CALLBACK,
                    ),
                    InlineKeyboardButton(
                        text=const.GAME_RULES_BUTTON, url=const.GAME_RULES_URL
                    ),
                ]
            ),
        )
        await self.tg_api.send_message(button_message, any_buttons_present=True)

    async def say_hi_and_wait(self, context: BotContext):
        """Печатает приветствие и кнопку 'Посмотреть правила игры',
        предлагает дождаться окончания текущей игры.
        """
        button_message = SendMessage(
            chat_id=context.chat_id,
            text=const.WELCOME_WAITING_MESSAGE,
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        text=const.GAME_RULES_BUTTON, url=const.GAME_RULES_URL
                    ),
                ]
            ),
        )
        await self.tg_api.send_message(button_message, any_buttons_present=True)

    async def unknown_command(self, context: BotContext):
        """Печатает сообщение, что команда неизвестна."""
        await self.tg_api.send_message(
            SendMessage(chat_id=context.chat_id, text=const.UNKNOWN_MESSAGE)
        )

    async def _start_timer(
        self,
        coro: typing.Coroutine,
        seconds: int = const.TIMER_DELAY_IN_SECONDS,
    ):
        """Запускает таймер на время, указанное в аргументе seconds,
        по прошествии этого времени вызывает корутину coro.
        """
        await asyncio.sleep(seconds)
        await coro

    async def _say_wait_next_game(self, context: BotContext):
        """Предлагает дождаться окончания текущей игры."""
        button_message = SendMessage(
            chat_id=context.chat_id, text=const.WAITING_MESSAGE
        )
        await self.tg_api.send_message(button_message)

    async def _say_join_new_game(self, context: BotContext):
        """Печатает сообщение, что можно присоединиться к новой игре
        в течение определенного времени, и кнопку 'Присоединиться к игре',
        затем запускает таймер.
        """
        button_message = SendMessage(
            chat_id=context.chat_id,
            text=const.START_TIMER_MESSAGE,
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        text=const.GAME_JOIN_BUTTON,
                        callback_data=const.ADD_PLAYER_CALLBACK,
                    ),
                ]
            ),
        )
        await self.tg_api.send_message(button_message, any_buttons_present=True)

        # More info: https://docs.astral.sh/ruff/rules/asyncio-dangling-task/
        timer_task = asyncio.create_task(
            self._start_timer(self._say_start_betting_stage(context))
        )
        self.logger.info(timer_task)
        self.background_tasks.add(timer_task)
        timer_task.add_done_callback(self.background_tasks.discard)

    async def _say_player_joined(self, context: BotContext):
        """Печатает сообщение, что игрок присоединился к игре."""
        await self.tg_api.send_message(
            SendMessage(
                chat_id=context.chat_id,
                text=const.JOINED_GAME_MESSAGE.format(
                    username=context.username
                ),
            )
        )

    async def _say_join_non_existent_game_fail(self, context: BotContext):
        """Печатает сообщение о том, что нельзя присоединиться
        к несуществующей игре.
        """
        await self.tg_api.send_message(
            SendMessage(
                chat_id=context.chat_id,
                text=const.JOIN_NON_EXISTENT_GAME_ERROR,
            )
        )

    async def _say_start_betting_stage(self, context: BotContext):
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
            text=const.END_TIMER_MESSAGE.format(players=players),
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
                        text=const.BET_10_BUTTON,
                        callback_data="make_bet_10",
                    ),
                    InlineKeyboardButton(
                        text=const.BET_25_BUTTON,
                        callback_data="make_bet_25",
                    ),
                    InlineKeyboardButton(
                        text=const.BET_50_BUTTON,
                        callback_data="make_bet_50",
                    ),
                    InlineKeyboardButton(
                        text=const.BET_100_BUTTON,
                        callback_data="make_bet_100",
                    ),
                ]
            ),
        )
        await self.tg_api.send_message(button_message, any_buttons_present=True)
