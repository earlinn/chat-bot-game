import typing
from logging import getLogger

from app.game.const import (
    BLACK_JACK,
    CARDS,
    GameStage,
    GameStatus,
    PlayerStatus,
)
from app.game.models import GameModel, PlayerModel
from app.store.bot import const
from app.store.bot.manager import BotManager
from app.store.game.manager import GameManager
from app.store.tg_api.dataclasses import BotContext, CallbackQuery

if typing.TYPE_CHECKING:
    from app.web.app import Application


# TODO: Что если юзер, нажавший кнопку в игре, не является игроком?
# Если да, то вправе ли он ее нажимать (например, он уже перестал брать
# карты, а теперь опять жмет на Взять карту).


# TODO: если игроку в самом начале при раздаче карт достались 2 карты,
# которые в сумме равны 21, то он немедленно выигрывает, если диллеру в самом
# начале игры не досталась карта-картинка, можно сделать это после MVP
class BotHandler:
    """Класс для обработки запросов к боту."""

    def __init__(self, app: "Application"):
        """Подключается к app и к логгеру."""
        self.app = app
        self.logger = getLogger("bot handler")

    @property
    def bot_manager(self) -> BotManager:
        return self.app.store.bot_manager

    @property
    def game_manager(self) -> GameManager:
        return self.app.store.game_manager

    @staticmethod
    def _get_cards_string(card_list: list[str]) -> str:
        """Делает из списка карт строку."""
        return ", ".join(card_list)

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
            await self.bot_manager.say_button_no_match_game_stage(context)

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
        # wrong_button нужен там, где после цикла query_message есть еще что-то,
        # что не должно происходить, если нажата неверная кнопка для этой стадии
        wrong_button = False

        if query_message == const.BET_10_CALLBACK:
            bet_value = 10
        elif query_message == const.BET_25_CALLBACK:
            bet_value = 25
        elif query_message == const.BET_50_CALLBACK:
            bet_value = 50
        elif query_message == const.BET_100_CALLBACK:
            bet_value = 100
        else:
            await self.bot_manager.say_button_no_match_game_stage(context)
            wrong_button = True

        if not wrong_button:
            all_players_have_bet: bool = await self._handle_bet(
                game, query, context, bet_value
            )
            if all_players_have_bet:
                await self._handle_playerhit_initial(context)

    async def _handle_bet(
        self,
        game: GameModel,
        query: CallbackQuery,
        context: BotContext,
        bet_value: int,
    ) -> bool:
        """Обрабатывает ставку отдельного игрока, проверяет, остались ли игроки,
        не сделавшие ставку, и возвращает результат этой проверки.
        """
        context.bet_value = bet_value
        await self.bot_manager.say_player_have_bet(context)
        return await self.game_manager.update_gameplay_bet_status_and_cards(
            game, query, bet_value
        )

    async def _handle_playerhit_initial(self, context: BotContext) -> None:
        """Меняет стадию ставок на стадию, когда игроки берут дополнительные
        карты, формирует строку с информацией о картах игроков и диллера
        и отправляет ее в BotManager, чтобы бот показал ее в чате.
        """
        refreshed_game: GameModel = (
            await self.app.store.games.change_active_game_stage(
                chat_id=context.chat_id, stage=GameStage.PLAYERHIT
            )
        )

        players_cards: list[str] = [
            const.PLAYER_CARDS_STR.format(
                username=gameplay.player.username,
                player_cards=self._get_cards_string(gameplay.player_cards),
            )
            for gameplay in refreshed_game.gameplays
        ]
        diller_card_str = const.DILLER_CARDS_STR.format(
            diller_cards=self._get_cards_string(refreshed_game.diller_cards)
        )
        cards_str: str = "\n".join(players_cards) + diller_card_str
        context.message = cards_str
        await self.bot_manager.say_players_take_cards(context)

    async def _handle_game_playerhit_stage(
        self, game: GameModel, query: CallbackQuery, context: BotContext
    ) -> None:
        """Обрабатывает игру на стадии, когда игроки берут карты."""
        query_message: str = query.data
        context.username = query.from_.username
        wrong_button = False

        if query_message == const.TAKE_CARD_CALLBACK:
            exceeded, cards = await self.game_manager.take_a_card(game, query)
            context.message = self._get_cards_string(cards)
            if exceeded:
                await self.bot_manager.say_player_exceeded(context)
            else:
                await self.bot_manager.say_player_not_exceeded(context)

        elif query_message == const.STOP_TAKING_CALLBACK:
            cards = await self.game_manager.stop_take_cards(game, query)
            context.message = self._get_cards_string(cards)
            await self.bot_manager.say_player_stopped_taking(context)

        else:
            wrong_button = True
            await self.bot_manager.say_button_no_match_game_stage(context)

        if not wrong_button:
            refreshed_game: (
                GameModel | None
            ) = await self.app.store.games.get_active_game_by_chat_id(
                context.chat_id
            )
            no_taking_players: list[bool] = [
                gameplay.player_status != PlayerStatus.TAKING
                for gameplay in refreshed_game.gameplays
            ]

            if all(no_taking_players):
                await self._handle_game_dillerhit_stage(context)

    async def _handle_game_dillerhit_stage(self, context: BotContext) -> None:
        """Обрабатывает игру на стадии, когда диллер берет карты."""
        dillerhit_game: GameModel = (
            await self.app.store.games.change_active_game_stage(
                chat_id=context.chat_id, stage=GameStage.DILLERHIT
            )
        )
        diller_score: int = await self.game_manager.take_cards_by_diller(
            dillerhit_game
        )
        summarizing_game: GameModel = (
            await self.app.store.games.change_active_game_stage(
                chat_id=context.chat_id, stage=GameStage.SUMMARIZING
            )
        )
        await self._handle_game_summarizing_stage(
            summarizing_game, context, diller_score
        )

    async def _handle_game_summarizing_stage(
        self,
        summarizing_game: GameModel,
        context: BotContext,
        diller_score: int,
    ) -> None:
        """Обрабатывает игру на стадии подведения итогов."""
        game_results: list[str] = []

        for gameplay in summarizing_game.gameplays:
            player_score: int = sum(
                CARDS[card] for card in gameplay.player_cards
            )

            if gameplay.player_status == PlayerStatus.EXCEEDED:
                result_str = await self.game_manager.finalize_player_result(
                    chat_id=context.chat_id,
                    gameplay=gameplay,
                    player_score=player_score,
                    message=const.PLAYER_EXCEDDED_RESULTS_MESSAGE,
                    player_balance_change=-gameplay.player_bet,
                )
                game_results.append(result_str)

            elif diller_score > BLACK_JACK or player_score > diller_score:
                result_str = await self.game_manager.finalize_player_result(
                    chat_id=context.chat_id,
                    gameplay=gameplay,
                    player_score=player_score,
                    message=const.PLAYER_WON_RESULTS_MESSAGE,
                    player_balance_change=gameplay.player_bet,
                    gameplay_status_change=PlayerStatus.WON,
                )
                game_results.append(result_str)

            elif player_score < diller_score:
                result_str = await self.game_manager.finalize_player_result(
                    chat_id=context.chat_id,
                    gameplay=gameplay,
                    player_score=player_score,
                    message=const.PLAYER_LOST_RESULTS_MESSAGE,
                    player_balance_change=-gameplay.player_bet,
                    gameplay_status_change=PlayerStatus.LOST,
                )
                game_results.append(result_str)

            else:
                result_str = await self.game_manager.finalize_player_result(
                    chat_id=context.chat_id,
                    gameplay=gameplay,
                    player_score=player_score,
                    message=const.PLAYER_TIE_RESULTS_MESSAGE,
                    gameplay_status_change=PlayerStatus.TIE,
                )
                game_results.append(result_str)

        await self.app.store.games.change_game_fields(
            game_id=summarizing_game.id,
            new_values={"status": GameStatus.FINISHED},
        )
        game_results_str = const.GAME_RESULTS_MESSAGE.format(
            players="".join(game_results),
            diller_cards=self._get_cards_string(summarizing_game.diller_cards),
            score=diller_score,
        )
        context.message = game_results_str
        await self.bot_manager.say_game_results(context)
