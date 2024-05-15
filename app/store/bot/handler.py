import typing
from logging import getLogger

from app.game.const import GameStage
from app.game.models import GameModel, PlayerModel
from app.store.bot import const
from app.store.bot.manager import BotManager
from app.store.game.manager import GameManager
from app.store.tg_api.dataclasses import BotContext, CallbackQuery

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotHandler:
    """Класс для обработки запросов к боту."""

    def __init__(self, app: "Application"):
        """Подключается к app и к логгеру."""
        self.app = app
        self.logger = getLogger("bot handler")

    @property
    def bot_manager(self) -> BotManager:
        return self.app.store.bots_manager

    @property
    def game_manager(self) -> GameManager:
        return self.app.store.game_manager

    async def handle_no_game_case(
        self, query: CallbackQuery, context: BotContext
    ) -> None:
        """Обрабатывает callback_query при отсутствии активной игры в чате."""
        query_message: str = query.data

        if query_message == const.ADD_PLAYER_CALLBACK:
            await self.bot_manager.say_join_non_existent_game_fail(context)

        elif query_message == const.JOIN_GAME_CALLBACK:
            player: PlayerModel = await self.game_manager.get_player(
                query.from_.id, query.from_.username, context.chat_id
            )
            game: GameModel = await self.game_manager.get_game(context.chat_id)
            await self.game_manager.get_gameplay(game.id, player.id)
            await self.bot_manager.say_join_new_game(context)
            context.username = player.username
            await self.bot_manager.say_player_joined(context)

    async def handle_active_game(
        self,
        query: CallbackQuery,
        context: BotContext,
    ) -> None:
        """Обрабатывает callback_query при наличии активной игры в чате."""
        query_message: str = query.data
        game = context.current_game

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
            await self.bot_manager.say_wait_next_game(context)

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
            await self.bot_manager.say_player_joined(context)
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
                await self.game_manager.update_gameplay_bet_status_and_cards(
                    game.id, query, 10
                )
            )
            context.bet_value = 10
            await self.bot_manager.say_player_have_bet(context)
        elif query_message == const.BET_25_CALLBACK:
            all_players_have_bet: bool = (
                await self.game_manager.update_gameplay_bet_status_and_cards(
                    game.id, query, 25
                )
            )
            context.bet_value = 25
            await self.bot_manager.say_player_have_bet(context)
        elif query_message == const.BET_50_CALLBACK:
            all_players_have_bet: bool = (
                await self.game_manager.update_gameplay_bet_status_and_cards(
                    game.id, query, 50
                )
            )
            context.bet_value = 50
            await self.bot_manager.say_player_have_bet(context)
        elif query_message == const.BET_100_CALLBACK:
            all_players_have_bet: bool = (
                await self.game_manager.update_gameplay_bet_status_and_cards(
                    game.id, query, 100
                )
            )
            context.bet_value = 100
            await self.bot_manager.say_player_have_bet(context)
        else:
            # TODO: написать, что кнопка не соответствует стадии игры
            pass

        if all_players_have_bet:
            refreshed_game = (
                await self.app.store.games.change_active_game_stage(
                    chat_id=context.chat_id, stage=GameStage.PLAYERHIT
                )
            )

            players_cards: list[str] = [
                const.PLAYER_CARDS_STR.format(
                    username=gameplay.player.username,
                    player_cards=", ".join(gameplay.player_cards),
                )
                for gameplay in refreshed_game.gameplays
            ]
            diller_card_str = const.DILLER_CARDS_STR.format(
                diller_cards=", ".join(refreshed_game.diller_cards)
            )
            cards_str: str = "\n".join(players_cards) + diller_card_str
            context.message = cards_str
            await self.bot_manager.say_players_take_cards(context)

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
