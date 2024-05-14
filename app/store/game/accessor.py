from collections.abc import Sequence

from sqlalchemy import and_, select, update
from sqlalchemy.orm import selectinload

from app.base.base_accessor import BaseAccessor
from app.game.const import GameStage, GameStatus
from app.game.models import BalanceModel, GameModel, GamePlayModel, PlayerModel


class PlayerAccessor(BaseAccessor):
    async def create_player(self, username: str, tg_id: int) -> PlayerModel:
        """Создает и отдает игрока."""
        player = PlayerModel(username=username, tg_id=tg_id)
        async with self.app.database.session() as session:
            session.add(player)
            await session.commit()
        return player

    async def list_players(self) -> Sequence[PlayerModel]:
        """Отдает список игроков."""
        query = select(PlayerModel)
        async with self.app.database.session() as session:
            return await session.scalars(query)

    async def get_player_by_id(self, id_: int) -> PlayerModel | None:
        """Ищет игрока по id."""
        query = select(PlayerModel).where(PlayerModel.id == id_)
        async with self.app.database.session() as session:
            return await session.scalar(query)

    # TODO: больше не используется из-за появления get_or_create в BaseAccessor
    async def get_player_by_tg_id(self, tg_id: int) -> PlayerModel | None:
        """Ищет игрока по telegram id."""
        query = select(PlayerModel).where(PlayerModel.tg_id == tg_id)
        async with self.app.database.session() as session:
            return await session.scalar(query)

    async def create_player_balance(
        self, chat_id: int, player_id: int
    ) -> BalanceModel:
        """Создает баланс игрока для определенного чата."""
        balance = BalanceModel(chat_id=chat_id, player_id=player_id)
        async with self.app.database.session() as session:
            session.add(balance)
            await session.commit()
        return balance

    async def list_balances(
        self, player_id: int | None = None
    ) -> Sequence[BalanceModel]:
        """Отдает список балансов всех игроков во всех чатах.
        Можно отфильтровать по определенному игроку.
        """
        if not player_id:
            query = select(BalanceModel)
        else:
            query = select(BalanceModel).where(
                BalanceModel.player_id == player_id
            )
        async with self.app.database.session() as session:
            return await session.scalars(query)

    async def get_balance_by_player_and_chat(
        self, player_id: int, chat_id: int
    ) -> BalanceModel | None:
        """Ищет баланс определенного игрока в определенном чате."""
        query = select(BalanceModel).where(
            and_(
                BalanceModel.player_id == player_id,
                BalanceModel.chat_id == chat_id,
            )
        )
        async with self.app.database.session() as session:
            return await session.scalar(query)


class GameAccessor(BaseAccessor):
    async def create_game(
        self, chat_id: int, diller_cards: list[str]
    ) -> GameModel:
        """Создает и отдает игру."""
        game = GameModel(chat_id=chat_id, diller_cards=diller_cards)
        async with self.app.database.session() as session:
            session.add(game)
            await session.commit()
        return game

    async def list_games(self) -> Sequence[GameModel]:
        """Отдает список всех игр."""
        query = select(GameModel).options(selectinload(GameModel.gameplays))
        async with self.app.database.session() as session:
            return await session.scalars(query)

    async def get_active_game_by_chat_id(
        self, chat_id: int
    ) -> GameModel | None:
        """Ищет в определенном чате активную игру."""
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
        """Ищет в определенном чате активную игру на стадии ожидания игроков."""
        query = select(GameModel).where(
            and_(
                GameModel.chat_id == chat_id,
                GameModel.status == GameStatus.ACTIVE,
                GameModel.stage == GameStage.WAITING_FOR_PLAYERS_TO_JOIN,
            )
        )
        async with self.app.database.session() as session:
            return await session.scalar(query)

    async def change_active_game_stage(
        self, chat_id: int, stage: GameStage
    ) -> GameModel:
        """Находит активную игру по chat_id, переводит ее на новую стадию
        и возвращает эту игру. Если в чате нет активной игры, возвращает None.
        """
        query = (
            update(GameModel)
            .where(
                and_(
                    GameModel.chat_id == chat_id,
                    GameModel.status == GameStatus.ACTIVE,
                )
            )
            .values(stage=stage)
            .returning(GameModel)
        ).options(selectinload(GameModel.players))
        async with self.app.database.session() as session:
            game = await session.scalar(query)
            await session.commit()
        return game


class GamePlayAccessor(BaseAccessor):
    # TODO: больше не используется из-за появления get_or_create в BaseAccessor
    async def create_gameplay(
        self, game_id: int, player_id: int
    ) -> GamePlayModel:
        """Создает и отдает геймплей."""
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
        """Ищет геймплей по игроку и игре."""
        query = select(GamePlayModel).where(
            and_(
                GamePlayModel.game_id == game_id,
                GamePlayModel.player_id == player_id,
            )
        )
        async with self.app.database.session() as session:
            return await session.scalar(query)
