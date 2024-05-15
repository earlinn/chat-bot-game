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


# TODO: вынести все обработчики в новый класс, типа BotHandler или GameHandler,
# а в BotManager оставить только прокидывание сообщений и кнопок.
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
        self, query: CallbackQuery, context: BotContext
    ) -> None:
        """Обрабатывает callback_query при отсутствии активной игры в чате."""
        query_message: str = query.data

        if query_message == const.ADD_PLAYER_CALLBACK:
            await self._say_join_non_existent_game_fail(context)

        elif query_message == const.JOIN_GAME_CALLBACK:
            player: PlayerModel = await self.game_manager.get_player(
                query.from_.id, query.from_.username, context.chat_id
            )
            game: GameModel = await self.game_manager.get_game(context.chat_id)
            await self.game_manager.get_gameplay(game.id, player.id)
            await self._say_join_new_game(context)
            context.username = player.username
            await self._say_player_joined(context)

    async def handle_active_game(
        self,
        game: GameModel,
        query: CallbackQuery,
        context: BotContext,
    ) -> None:
        """Обрабатывает callback_query при наличии активной игры в чате."""
        query_message: str = query.data

        if game.stage == GameStage.WAITING_FOR_PLAYERS_TO_JOIN:
            await self._handle_game_waiting_stage(game, query, context)
        elif game.stage == GameStage.BETTING:
            await self._handle_game_betting_stage(game, query, context)
        elif game.stage == GameStage.PLAYERHIT:
            await self._handle_game_playerhit_stage(game, query, context)
        elif (
            query_message == const.JOIN_GAME_CALLBACK
            or query_message == const.ADD_PLAYER_CALLBACK
        ):
            await self._say_wait_next_game(context)

    async def _handle_game_waiting_stage(
        self, game: GameModel, query: CallbackQuery, context: BotContext
    ) -> None:
        """Обрабатывает игру в состоянии ожидания присоединения игроков."""
        query_message: str = query.data

        if query_message == const.ADD_PLAYER_CALLBACK:
            player: PlayerModel = await self.game_manager.get_player(
                query.from_.id, query.from_.username, context.chat_id
            )
            await self.game_manager.get_gameplay(game.id, player.id)
            context.username = player.username
            await self._say_player_joined(context)
        else:
            # TODO: написать, что кнопка не соответствует стадии игры
            pass

    # TODO: А если на эти кнопки кто-то нажмет, когда никакой игры вообще нет?
    # Или она есть, но не на стадии ставок? Или юзер не является игроком?
    # Это любых кнопок касается.
    # Наверно надо эти ситуации обрабатывать в хендлерах стадий игры
    # ( _handle_game_waiting_stage,_handle_game_betting_stage и т.п.).
    # Там можно по query_message понять, относится ли эта кнопка к этой стадии
    # (внутри каждого хендлера стадии есть условный оператор, и если кнопка
    # не относится к этой стадии, то она попадет под else, который выведет
    # сообщение, что кнопка не относится к текущей стадии игры).
    # Если да, то является ли юзер, нажавший кнопку игроком в этой игре.
    # Если да, то вправе ли он ее нажимать (например, он уже перестал брать
    # карты, а теперь опять жмет на Взять карту).
    # TODO: Если не все сделали ставки, то ничего не делаем или, как вариант,
    # запускаем таймер и пишем, что у них 30 секунд на ставки, если они все
    # не успели за это время, то досрочно завершаем игру и выводим сообщение,
    # что игра завершена, т.к. не все игроки сделали ставки
    async def _handle_game_betting_stage(
        self, game: GameModel, query: CallbackQuery, context: BotContext
    ) -> None:
        """Обрабатывает игру в состоянии, когда игроки делают ставки."""
        query_message: str = query.data
        context.username = query.from_.username

        if query_message == const.BET_10_CALLBACK:
            all_players_have_bet: bool = (
                await self.game_manager.update_gameplay_bet_and_status(
                    game.id, query, 10
                )
            )
            context.bet_value = 10
            await self._say_player_have_bet(context)
        elif query_message == const.BET_25_CALLBACK:
            all_players_have_bet: bool = (
                await self.game_manager.update_gameplay_bet_and_status(
                    game.id, query, 25
                )
            )
            context.bet_value = 25
            await self._say_player_have_bet(context)
        elif query_message == const.BET_50_CALLBACK:
            all_players_have_bet: bool = (
                await self.game_manager.update_gameplay_bet_and_status(
                    game.id, query, 50
                )
            )
            context.bet_value = 50
            await self._say_player_have_bet(context)
        elif query_message == const.BET_100_CALLBACK:
            all_players_have_bet: bool = (
                await self.game_manager.update_gameplay_bet_and_status(
                    game.id, query, 100
                )
            )
            context.bet_value = 100
            await self._say_player_have_bet(context)
        else:
            # TODO: написать, что кнопка не соответствует стадии игры
            pass

        if all_players_have_bet:
            await self.app.store.games.change_active_game_stage(
                chat_id=context.chat_id, stage=GameStage.PLAYERHIT
            )
            # TODO: стадия игры поменялась, теперь надо раздать каждому игроку
            # по 2 карты и вывести их в сообщении ниже вместе с кнопками, также
            # вывести на экран единственную карту диллера
            await self._say_players_take_cards(context)

    async def _handle_game_playerhit_stage(
        self, game: GameModel, query: CallbackQuery, context: BotContext
    ) -> None:
        """Обрабатывает игру в состоянии, когда игроки берут карты."""
        query_message: str = query.data

        if query_message == const.TAKE_CARD_CALLBACK:
            # TODO: проверить, не превысил ли игрок 21, если да, то меняем
            # в его геймплее статус на EXCEEDED и бот пишет ему "У {username}
            # более 21 очка, карты на руках: {его карты}"
            pass
        elif query_message == const.STOP_TAKING_CALLBACK:
            # TODO: меняем в геймплее игрока его статус на STANDING и пишем
            # "{username} больше не берет карты, карты на руках: {его карты}"
            pass
        else:
            # TODO: написать, что кнопка не соответствует стадии игры
            pass

        # TODO:
        # - проверить, есть ли геймплеи на стадии TAKING
        # - если есть, просто ждем
        # - если нет, посмотреть, есть ли геймплеи в статусе STANDING
        # -- если есть, то меняем стадию игры на DILLERHIT, и диллер берет
        # карты, пока не достигнет 17 очков
        # - когда диллер достиг 17 очков, выводим его карты на экран, меняем
        # статус игры на SUMMARIZING, подводим итоги игры (игрокам, которые
        # не EXCEEDED, в геймплеях проставляем LOST или WON), меняем статус
        # игры на FINISHED и выводим через бота сообщение с подведением итогов
        # (кто победил/проиграл и с какими очками)
        # -- если нет, то сразу делаем SUMMARIZING
        # - также меняем балансы игроков для этого чата (кто-то в +, кто-то в -)

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

    async def _say_player_have_bet(self, context: BotContext):
        await self.tg_api.send_message(
            SendMessage(
                chat_id=context.chat_id,
                text=const.PLAYER_HAVE_BET_MESSAGE.format(
                    player=context.username, bet=context.bet_value
                ),
            )
        )

    async def _say_players_take_cards(self, context: BotContext):
        button_message = SendMessage(
            chat_id=context.chat_id,
            text=const.GAME_PLAYERHIT_STAGE_MESSAGE,
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
