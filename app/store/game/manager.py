import random
import typing
from logging import getLogger

from app.game.const import CARDS, GameStage, GameStatus
from app.game.models import BalanceModel, GameModel, GamePlayModel, PlayerModel
from app.store.tg_api.dataclasses import CallbackQuery

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameManager:
    def __init__(self, app: "Application"):
        """Подключается к app и к логгеру."""
        self.app = app
        self.logger = getLogger("game manager")

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

    async def update_gameplay_bet_and_status(
        self, game_id: int, query: CallbackQuery, bet_value: int
    ) -> bool:
        """Находит геймплей, обновляет в нем ставку игрока и определяет,
        все ли игроки сделали ставку.
        """
        player: PlayerModel = await self.app.store.players.get_player_by_tg_id(
            query.from_.id
        )
        gameplay: GamePlayModel = (
            await self.app.store.gameplays.get_gameplay_by_game_and_player(
                game_id, player.id
            )
        )
        await self.app.store.gameplays.change_player_bet_and_status(
            gameplay.id, bet_value
        )
        return await self.app.store.games.check_all_players_have_bet(game_id)
