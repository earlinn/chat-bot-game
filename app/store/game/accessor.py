from collections.abc import Sequence

from aiohttp.web_exceptions import HTTPNotFound
from sqlalchemy import select

from app.base.base_accessor import BaseAccessor
from app.game.models import BalanceModel, GameModel, PlayerModel


class GameAccessor(BaseAccessor):
    async def create_player(self, username: str, tg_id: int) -> PlayerModel:
        async with self.app.database.session() as session:
            player = PlayerModel(username=username, tg_id=tg_id)
            session.add(player)
            await session.commit()
            return player

    async def list_players(self) -> Sequence[PlayerModel]:
        async with self.app.database.session() as session:
            query = select(PlayerModel)
            return await session.scalars(query)

    async def get_player_by_id(self, id_: int) -> PlayerModel | None:
        async with self.app.database.session() as session:
            query = select(PlayerModel).where(PlayerModel.id == id_)
            return await session.scalar(query)

    async def create_player_balance(
        self, chat_id: int, player_id: int
    ) -> BalanceModel:
        async with self.app.database.session() as session:
            balance = BalanceModel(chat_id=chat_id, player_id=player_id)
            session.add(balance)
            await session.commit()
            return balance

    async def list_balances(
        self, player_id: int | None = None
    ) -> Sequence[BalanceModel]:
        if not player_id:
            query = select(BalanceModel)
        elif await self.get_player_by_id(player_id):
            query = select(BalanceModel).where(
                BalanceModel.player_id == player_id
            )
        else:
            raise HTTPNotFound
        async with self.app.database.session() as session:
            return await session.scalars(query)

    async def create_game(
        self, chat_id: int, diller_cards: list[str]
    ) -> GameModel:
        async with self.app.database.session() as session:
            game = GameModel(chat_id=chat_id, diller_cards=diller_cards)
            session.add(game)
            await session.commit()
            return game

    # TODO: добавить подгрузку связанных gameplays (selectinload и т.п.)
    async def list_games(self) -> Sequence[GameModel]:
        async with self.app.database.session() as session:
            query = select(GameModel)
            return await session.scalars(query)
