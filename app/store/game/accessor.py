from collections.abc import Sequence

from sqlalchemy import and_, select

from app.base.base_accessor import BaseAccessor
from app.game.const import GameStage, GameStatus
from app.game.models import BalanceModel, GameModel, GamePlayModel, PlayerModel


class PlayerAccessor(BaseAccessor):
    async def create_player(self, username: str, tg_id: int) -> PlayerModel:
        player = PlayerModel(username=username, tg_id=tg_id)
        async with self.app.database.session() as session:
            session.add(player)
            await session.commit()
        return player

    async def list_players(self) -> Sequence[PlayerModel]:
        query = select(PlayerModel)
        async with self.app.database.session() as session:
            return await session.scalars(query)

    async def get_player_by_id(self, id_: int) -> PlayerModel | None:
        query = select(PlayerModel).where(PlayerModel.id == id_)
        async with self.app.database.session() as session:
            return await session.scalar(query)

    # TODO: больше не используется из-за появления get_or_create в BaseAccessor
    async def get_player_by_tg_id(self, tg_id: int) -> PlayerModel | None:
        query = select(PlayerModel).where(PlayerModel.tg_id == tg_id)
        async with self.app.database.session() as session:
            return await session.scalar(query)

    async def create_player_balance(
        self, chat_id: int, player_id: int
    ) -> BalanceModel:
        balance = BalanceModel(chat_id=chat_id, player_id=player_id)
        async with self.app.database.session() as session:
            session.add(balance)
            await session.commit()
        return balance

    async def list_balances(
        self, player_id: int | None = None
    ) -> Sequence[BalanceModel]:
        if not player_id:
            query = select(BalanceModel)
        else:
            query = select(BalanceModel).where(
                BalanceModel.player_id == player_id
            )
        async with self.app.database.session() as session:
            return await session.scalars(query)


class GameAccessor(BaseAccessor):
    async def create_game(
        self, chat_id: int, diller_cards: list[str]
    ) -> GameModel:
        game = GameModel(chat_id=chat_id, diller_cards=diller_cards)
        async with self.app.database.session() as session:
            session.add(game)
            await session.commit()
        return game

    # TODO: добавить подгрузку связанных gameplays (selectinload и т.п.)
    async def list_games(self) -> Sequence[GameModel]:
        query = select(GameModel)
        async with self.app.database.session() as session:
            return await session.scalars(query)

    async def get_active_game_by_chat_id(
        self, chat_id: int
    ) -> GameModel | None:
        query = select(GameModel).where(
            and_(
                GameModel.chat_id == chat_id,
                GameModel.status == GameStatus.ACTIVE,
            )
        )
        async with self.app.database.session() as session:
            return await session.scalar(query)

    # TODO: больше не используется из-за появления get_or_create в BaseAccessor
    async def get_active_waiting_game_by_chat_id(
        self, chat_id: int
    ) -> GameModel | None:
        query = select(GameModel).where(
            and_(
                GameModel.chat_id == chat_id,
                GameModel.status == GameStatus.ACTIVE,
                GameModel.stage == GameStage.WAITING,
            )
        )
        async with self.app.database.session() as session:
            return await session.scalar(query)


class GamePlayAccessor(BaseAccessor):
    # TODO: больше не используется из-за появления get_or_create в BaseAccessor
    async def create_gameplay(
        self, game_id: int, player_id: int
    ) -> GamePlayModel:
        gameplay = GamePlayModel(
            game_id=game_id, player_id=player_id, player_bet=1
        )
        async with self.app.database.session() as session:
            session.add(gameplay)
            await session.commit()
        return gameplay

    # TODO: больше не используется из-за появления get_or_create в BaseAccessor
    async def get_gameplay_by_game_and_player(
        self, game_id: int, player_id: int
    ) -> GamePlayModel | None:
        query = select(GamePlayModel).where(
            and_(
                GamePlayModel.game_id == game_id,
                GamePlayModel.player_id == player_id,
            )
        )
        async with self.app.database.session() as session:
            return await session.scalar(query)
