import random
import re
import typing
from logging import getLogger

from app.game.const import (
    BLACK_JACK,
    CARDS,
    DILLER_STOP_SCORE,
    GameStage,
    GameStatus,
    PlayerStatus,
)
from app.game.models import BalanceModel, GameModel, GamePlayModel, PlayerModel
from app.store.tg_api.dataclasses import CallbackQuery

if typing.TYPE_CHECKING:
    from app.web.app import Application

ACES_REGEX: str = r"A[♦️♠️♥️♣️]"  # regex for "A♦️", "A♠️", "A♥️", "A♣️"


class PlayerManager:
    """Класс с бизнес-логикой для игроков и их балансов."""

    def __init__(self, app: "Application"):
        """Подключается к app и к логгеру."""
        self.app = app
        self.logger = getLogger("player manager")

    async def get_player(
        self, user_id: int, username: str, chat_id: int
    ) -> PlayerModel:
        """Получает или создает нового игрока. Если создан новый игрок,
        создает ему баланс для текущего чата. Если новый игрок не создан,
        проверяет, есть ли у игрока баланс в данном чате, и создает ему
        баланс, если у него не было баланса в данном чате.
        """
        created, player = await self.app.store.players.get_or_create(
            model=PlayerModel,
            get_params=[PlayerModel.tg_id == user_id],
            create_params={"username": username, "tg_id": user_id},
        )
        self.logger.info("Player: %s, created: %s", player, created)
        if (
            created
            or not await self.app.store.players.get_balance_by_player_and_chat(
                player.id, chat_id
            )
        ):
            balance: BalanceModel = (
                await self.app.store.players.create_player_balance(
                    chat_id, player.id
                )
            )
            self.logger.info("Balance created: %s", balance)
        return player

    async def change_player_balance(
        self, player_id: int, chat_id: int, value_change: int
    ):
        """Запрашивает баланс игрока в чате, определяет новую сумму, которая
        должна быть на балансе, и обновляет сумму на балансе.
        """
        balance: BalanceModel = (
            await self.app.store.players.get_balance_by_player_and_chat(
                player_id=player_id, chat_id=chat_id
            )
        )
        new_value: int = balance.current_value + value_change
        await self.app.store.players.change_balance_current_value(
            player_id, chat_id, new_value
        )


class GameManager:
    """Класс с бизнес-логикой для игры и геймплея."""

    def __init__(self, app: "Application"):
        """Подключается к app и к логгеру."""
        self.app = app
        self.logger = getLogger("game manager")

    async def get_game(self, chat_id: int) -> GameModel:
        """Получает или создает новую игру."""
        created, game = await self.app.store.players.get_or_create(
            model=GameModel,
            get_params=[
                GameModel.chat_id == chat_id,
                GameModel.status == GameStatus.ACTIVE,
                GameModel.stage == GameStage.WAITING_FOR_PLAYERS_TO_JOIN,
            ],
            create_params={
                "chat_id": chat_id,
                "diller_cards": [random.choice(list(CARDS))],
            },
        )
        self.logger.info("Game: %s, created: %s", game, created)
        return game

    async def get_gameplay(self, game_id: int, player_id: int) -> GamePlayModel:
        """Получает или создает геймплей."""
        created, gameplay = await self.app.store.players.get_or_create(
            model=GamePlayModel,
            get_params=[
                GamePlayModel.game_id == game_id,
                GamePlayModel.player_id == player_id,
            ],
            create_params={
                "game_id": game_id,
                "player_id": player_id,
                "player_bet": 1,
            },
        )
        self.logger.info("Gameplay: %s, created: %s", gameplay, created)
        return gameplay

    async def update_gameplay_bet_status_and_cards(
        self, game: GameModel, query: CallbackQuery, bet_value: int
    ) -> bool:
        """Находит геймплей, обновляет в нем статус и ставку игрока, проверяет,
        все ли игроки сделали ставку, и возвращает результат проверки.
        """
        player: PlayerModel = await self.app.store.players.get_player_by_tg_id(
            query.from_.id
        )
        gameplay: GamePlayModel = next(
            filter(lambda x: x.player.id == player.id, game.gameplays)
        )
        new_gameplay_values = {
            "player_bet": bet_value,
            "player_status": PlayerStatus.TAKING,
            "player_cards": [random.choice(list(CARDS)) for _ in range(2)],
        }
        await self.app.store.gameplays.change_gameplay_fields(
            gameplay.id, new_gameplay_values
        )
        return await self.app.store.games.check_all_players_have_bet(game.id)

    async def take_a_card(
        self, game: GameModel, query: CallbackQuery
    ) -> tuple[bool, list[str], bool]:
        """Добавляет игроку в геймплей еще одну карту, проверяет превышение
        21 очка и возвращает результат проверки, список карт, а также результат
        проверки правильности статуса игрока (находится ли он в статусе игрока,
        который берет карты).
        """
        exceeded, wrong_player_status = False, False
        player: PlayerModel = await self.app.store.players.get_player_by_tg_id(
            query.from_.id
        )
        gameplay: GamePlayModel = next(
            filter(lambda x: x.player.id == player.id, game.gameplays)
        )

        if gameplay.player_status != PlayerStatus.TAKING:
            wrong_player_status = True
            return exceeded, gameplay.player_cards, wrong_player_status

        gameplay.player_cards.append(random.choice(list(CARDS)))
        updated_cards: list[str] = gameplay.player_cards
        score: int = self.process_score_with_aces(updated_cards)

        if score > BLACK_JACK:
            exceeded = True
            new_gameplay_values = {
                "player_status": PlayerStatus.EXCEEDED,
                "player_cards": updated_cards,
            }
        else:
            new_gameplay_values = {"player_cards": updated_cards}

        await self.app.store.gameplays.change_gameplay_fields(
            gameplay.id, new_gameplay_values
        )
        return exceeded, updated_cards, wrong_player_status

    async def stop_take_cards(
        self, game: GameModel, query: CallbackQuery
    ) -> list[str]:
        """Меняет статус геймплея на STANDING (игрок больше не берет карты)
        и возвращает список его карт.
        """
        player: PlayerModel = await self.app.store.players.get_player_by_tg_id(
            query.from_.id
        )
        gameplay: GamePlayModel = next(
            filter(lambda x: x.player.id == player.id, game.gameplays)
        )
        new_gameplay_values = {"player_status": PlayerStatus.STANDING}
        await self.app.store.gameplays.change_gameplay_fields(
            gameplay.id, new_gameplay_values
        )
        return gameplay.player_cards

    async def take_cards_by_diller(self, game: GameModel) -> int:
        """Добавляет карты диллеру, пока число его очков не достигнет 17,
        возвращает итоговое число очков диллера.
        """
        score: int = sum(CARDS[card] for card in game.diller_cards)
        while score < DILLER_STOP_SCORE:
            game.diller_cards.append(random.choice(list(CARDS)))
            score: int = sum(CARDS[card] for card in game.diller_cards)

        score_with_aces: int = self.process_score_with_aces(game.diller_cards)
        new_game_values = {"diller_cards": game.diller_cards}
        await self.app.store.games.change_game_fields(game.id, new_game_values)
        return score_with_aces

    async def finalize_player_result(
        self,
        chat_id: int,
        gameplay: GamePlayModel,
        player_score: int,
        message: str,
        player_balance_change: int | None = None,
        gameplay_status_change: str | None = None,
    ) -> str:
        """Присваивает игроку в геймплее финальный статус (если у игрока не было
        перебора очков), обновляет его баланс (если игрок не сыграл с диллером
        вничью) и возвращает строку с результатами игрока.
        """
        if gameplay_status_change:
            await self.app.store.gameplays.change_gameplay_fields(
                gameplay_id=gameplay.id,
                new_values={"player_status": gameplay_status_change},
            )
        if player_balance_change:
            await PlayerManager.change_player_balance(
                self, gameplay.player_id, chat_id, player_balance_change
            )
            result_str = message.format(
                player=gameplay.player.username,
                cards=self.app.store.bot_handler._get_cards_string(
                    gameplay.player_cards
                ),
                bet=gameplay.player_bet,
                score=player_score,
            )
        else:
            result_str = message.format(
                player=gameplay.player.username,
                cards=self.app.store.bot_handler._get_cards_string(
                    gameplay.player_cards
                ),
                score=player_score,
            )
        return result_str

    def process_score_with_aces(self, cards: list[str]) -> int:
        """Определяет суммарное число очков по картам, учитывая, что тузы
        могут стоить 1 очко вместо 11, если общая сумма превышает 21.
        """
        aces: int = sum(1 for card in cards if re.match(ACES_REGEX, card))
        score: int = sum(CARDS[card] for card in cards)

        while score > BLACK_JACK and aces:
            score -= 10
            aces -= 1

        return score
