import asyncio
import typing
from logging import getLogger

from app.game.const import GameStage
from app.game.models import GameModel, PlayerModel
from app.store.bot import const
from app.store.tg_api.accessor import TgApiAccessor
from app.store.tg_api.dataclasses import (
    BotContext,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    SendMessage,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    """Класс для отправки сообщений от имени бота и запуска таймеров."""

    def __init__(self, app: "Application"):
        """Подключается к app и к логгеру."""
        self.app = app
        self.logger = getLogger("bot manager")
        self.background_tasks = set()

    @property
    def tg_api(self) -> TgApiAccessor:
        return self.app.store.tg_api

    async def _start_timer(self, coro: typing.Coroutine, seconds: int):
        """Запускает таймер на время, указанное в аргументе seconds,
        по прошествии этого времени вызывает корутину coro.
        """
        try:
            await asyncio.sleep(seconds)
            await coro
        except asyncio.CancelledError:
            pass

    async def say_hi_and_play(self, context: BotContext):
        """Печатает приветствие и кнопки 'Новая игра', 'Мой баланс' и
        'Правила игры'.
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
                        text=const.MY_BALANCE_BUTTON,
                        callback_data=const.MY_BALANCE_CALLBACK,
                    ),
                    InlineKeyboardButton(
                        text=const.GAME_RULES_BUTTON, url=const.GAME_RULES_URL
                    ),
                ]
            ),
        )
        await self.tg_api.send_message(button_message, any_buttons_present=True)

    async def say_hi_and_wait(self, context: BotContext):
        """Печатает приветствие и кнопки 'Правила игры' и 'Мой баланс',
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
                    InlineKeyboardButton(
                        text=const.MY_BALANCE_BUTTON,
                        callback_data=const.MY_BALANCE_CALLBACK,
                    ),
                ]
            ),
        )
        await self.tg_api.send_message(button_message, any_buttons_present=True)

    async def say_unknown_command(self, context: BotContext):
        """Печатает сообщение, что команда неизвестна."""
        await self.tg_api.send_message(
            SendMessage(chat_id=context.chat_id, text=const.UNKNOWN_MESSAGE)
        )

    async def say_wait_next_game(self, context: BotContext):
        """Предлагает дождаться окончания текущей игры."""
        button_message = SendMessage(
            chat_id=context.chat_id, text=const.WAITING_MESSAGE
        )
        await self.tg_api.send_message(button_message)

    async def say_join_new_game(self, context: BotContext):
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
        timer_task: asyncio.Task = asyncio.create_task(
            self._start_timer(
                self.say_start_betting_stage(context),
                const.WAITING_STAGE_TIMER_IN_SECONDS,
            )
        )
        self.logger.info(timer_task)
        self.background_tasks.add(timer_task)
        timer_task.add_done_callback(self.background_tasks.discard)

    async def say_player_joined(self, context: BotContext):
        """Печатает сообщение, что игрок присоединился к игре."""
        await self.tg_api.send_message(
            SendMessage(
                chat_id=context.chat_id,
                text=const.JOINED_GAME_MESSAGE.format(player=context.username),
            )
        )

    async def say_join_non_existent_game_fail(self, context: BotContext):
        """Печатает сообщение о том, что нельзя присоединиться
        к несуществующей игре.
        """
        await self.tg_api.send_message(
            SendMessage(
                chat_id=context.chat_id,
                text=const.JOIN_NON_EXISTENT_GAME_ERROR,
            )
        )

    async def say_start_betting_stage(self, context: BotContext):
        """Печатает сообщение о старте игры, её участниках и кнопки для ставок.
        Затем запускает таймер, чтобы игроки сделали ставки в течение
        определенного времени, либо игра отменится.
        """
        current_game: GameModel = (
            await self.app.store.games.change_active_game_stage(
                chat_id=context.chat_id, stage=GameStage.BETTING
            )
        )
        context.current_game = current_game
        players: list[PlayerModel] = [
            gameplay.player for gameplay in current_game.gameplays
        ]
        players_str: str = ", ".join(
            [
                player.first_name if player.first_name else player.username
                for player in players
            ]
        )
        button_message = SendMessage(
            chat_id=context.chat_id,
            text=const.END_WAITING_STAGE_TIMER_MESSAGE.format(
                players=players_str
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        text=const.BET_10_BUTTON,
                        callback_data=const.BET_10_CALLBACK,
                    ),
                    InlineKeyboardButton(
                        text=const.BET_25_BUTTON,
                        callback_data=const.BET_25_CALLBACK,
                    ),
                    InlineKeyboardButton(
                        text=const.BET_50_BUTTON,
                        callback_data=const.BET_50_CALLBACK,
                    ),
                    InlineKeyboardButton(
                        text=const.BET_100_BUTTON,
                        callback_data=const.BET_100_CALLBACK,
                    ),
                ]
            ),
        )
        await self.tg_api.send_message(button_message, any_buttons_present=True)
        timer_task: asyncio.Task = asyncio.create_task(
            self._start_timer(
                self.say_game_was_cancelled_due_to_timer(context),
                const.BETTING_STAGE_TIMER_IN_SECONDS,
            )
        )
        self.logger.info(timer_task)
        self.background_tasks.add(timer_task)
        timer_task.add_done_callback(self.background_tasks.discard)

    async def say_player_has_bet(self, context: BotContext):
        """Печатает сообщение, что игрок такой-то сделал ставку такую-то."""
        await self.tg_api.send_message(
            SendMessage(
                chat_id=context.chat_id,
                text=const.PLAYER_HAVE_BET_MESSAGE.format(
                    player=context.username, bet=context.bet_value
                ),
            )
        )

    async def say_player_has_blackjack(self, context: BotContext):
        """Печатает сообщение, что у игрока блэкджек."""
        await self.tg_api.send_message(
            SendMessage(
                chat_id=context.chat_id,
                text=const.PLAYER_BLACK_JACK_MESSAGE.format(
                    player=context.username
                ),
            )
        )

    async def say_players_take_cards(self, context: BotContext):
        """Печатает сообщение, что ставки сделаны, показывает карты всех игроков
        и диллера, выводит кнопки 'Взять карту' и 'Достаточно карт'.
        """
        button_message = SendMessage(
            chat_id=context.chat_id,
            text=const.GAME_PLAYERHIT_STAGE_MESSAGE.format(
                cards_str=context.message
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        text=const.TAKE_CARD_BUTTON,
                        callback_data=const.TAKE_CARD_CALLBACK,
                    ),
                    InlineKeyboardButton(
                        text=const.STOP_TAKING_BUTTON,
                        callback_data=const.STOP_TAKING_CALLBACK,
                    ),
                ]
            ),
        )
        await self.tg_api.send_message(button_message, any_buttons_present=True)

    async def say_player_exceeded(self, context: BotContext):
        """Печатает сообщение, что игрок превысил 21 очко, и показывает
        его карты.
        """
        await self.tg_api.send_message(
            SendMessage(
                chat_id=context.chat_id,
                text=const.PLAYER_EXCEEDED_MESSAGE.format(
                    player=context.username, cards=context.message
                ),
            )
        )

    async def say_player_not_exceeded(self, context: BotContext):
        """Печатает сообщение, что игрок взял карту, и показывает его карты
        вместе с кнопками 'Взять карту' и 'Достаточно карт'.
        """
        button_message = SendMessage(
            chat_id=context.chat_id,
            text=const.PLAYER_NOT_EXCEEDED_MESSAGE.format(
                player=context.username, cards=context.message
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        text=const.TAKE_CARD_BUTTON,
                        callback_data=const.TAKE_CARD_CALLBACK,
                    ),
                    InlineKeyboardButton(
                        text=const.STOP_TAKING_BUTTON,
                        callback_data=const.STOP_TAKING_CALLBACK,
                    ),
                ]
            ),
        )
        await self.tg_api.send_message(button_message, any_buttons_present=True)

    async def say_player_stopped_taking(self, context: BotContext):
        """Печатает сообщение, что игрок закончил брать карты,
        и показывает его карты.
        """
        await self.tg_api.send_message(
            SendMessage(
                chat_id=context.chat_id,
                text=const.PLAYER_STOP_TAKING_MESSAGE.format(
                    player=context.username, cards=context.message
                ),
            )
        )

    async def say_game_results(self, context: BotContext):
        """Печатает итоги игры и кнопки 'Новая игра', 'Мой баланс' и
        'Правила игры'.
        """
        button_message = SendMessage(
            chat_id=context.chat_id,
            text=context.message,
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        text=const.GAME_ONE_MORE_TIME_BUTTON,
                        callback_data=const.JOIN_GAME_CALLBACK,
                    ),
                    InlineKeyboardButton(
                        text=const.MY_BALANCE_BUTTON,
                        callback_data=const.MY_BALANCE_CALLBACK,
                    ),
                    InlineKeyboardButton(
                        text=const.GAME_RULES_BUTTON,
                        url=const.GAME_RULES_URL,
                    ),
                ]
            ),
        )
        await self.tg_api.send_message(button_message, any_buttons_present=True)

    async def say_button_no_match_game_stage(self, context: BotContext):
        """Печатает сообщение, что кнопка не соответствует стадии игры."""
        await self.tg_api.send_message(
            SendMessage(
                chat_id=context.chat_id,
                text=const.BUTTON_NO_MATCH_STAGE_MESSAGE,
            )
        )

    async def say_wrong_status_to_take_cards(self, context: BotContext):
        """Печатает сообщение, что данный игрок уже не может брать карты
        (для случаев, когда игрок нажал на 'Достаточно карт', но затем пытается
        взять еще карты).
        """
        await self.tg_api.send_message(
            SendMessage(
                chat_id=context.chat_id,
                text=const.WRONG_STATUS_TO_TAKE_CARD_MESSAGE.format(
                    player=context.username
                ),
            )
        )

    async def say_no_game_user(self, context: BotContext):
        """Печатает сообщение, что данный пользователь не является игроком
        в текущей игре, в случаях, если пользователи-неигроки нажимают на
        игровые кнопки не на стадии присоединения игроков.
        """
        await self.tg_api.send_message(
            SendMessage(
                chat_id=context.chat_id,
                text=const.NOT_GAME_USER_MESSAGE.format(
                    player=context.username
                ),
            )
        )

    async def say_my_balance(self, context: BotContext):
        """Печатает баланс игрока в данном чате."""
        await self.tg_api.send_message(
            SendMessage(
                chat_id=context.chat_id,
                text=const.MY_BALANCE_MESSAGE.format(
                    player=context.username,
                    value=context.message,
                ),
            )
        )

    async def say_no_balance(self, context: BotContext):
        """Печатает сообщение, что у пользователя нет баланса в данном чате."""
        await self.tg_api.send_message(
            SendMessage(
                chat_id=context.chat_id,
                text=const.NO_BALANCE_MESSAGE.format(username=context.username),
            )
        )

    async def say_game_was_cancelled_due_to_timer(self, context: BotContext):
        """Инициирует отмену игры.
        Если игра была отменена, печатает сообщение об этом и кнопки
        'Новая игра', 'Мой баланс' и 'Правила игры'.
        Возможен случай, что игра не отменяется, поскольку она уже не
        на стадии ставок, т.е. игроки успели сделать ставки вовремя.
        """
        canceled_game: (
            GameModel | None
        ) = await self.app.store.games.cancel_active_game_due_to_timer(
            context.current_game.id
        )
        if canceled_game:
            button_message = SendMessage(
                chat_id=context.chat_id,
                text=const.GAME_CANCELED_MESSAGE,
                reply_markup=InlineKeyboardMarkup(
                    [
                        InlineKeyboardButton(
                            text=const.GAME_START_BUTTON,
                            callback_data=const.JOIN_GAME_CALLBACK,
                        ),
                        InlineKeyboardButton(
                            text=const.MY_BALANCE_BUTTON,
                            callback_data=const.MY_BALANCE_CALLBACK,
                        ),
                        InlineKeyboardButton(
                            text=const.GAME_RULES_BUTTON,
                            url=const.GAME_RULES_URL,
                        ),
                    ]
                ),
            )
            await self.tg_api.send_message(
                button_message, any_buttons_present=True
            )
