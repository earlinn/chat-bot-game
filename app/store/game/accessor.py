from collections.abc import Sequence

from sqlalchemy import select

from app.base.base_accessor import BaseAccessor
from app.game.models import BalanceModel, PlayerModel


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
