from collections.abc import Sequence
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.orm import selectinload

from app.base.base_accessor import BaseAccessor
from app.game.const import MINIMAL_BET, GameStage, GameStatus
from app.game.models import BalanceModel, GameModel, GamePlayModel, PlayerModel


class PlayerAccessor(BaseAccessor):
    async def create_player(
        self, username: str | None, tg_id: int, first_name: str
    ) -> PlayerModel:
        """Создает и отдает игрока."""
        player = PlayerModel(
            username=username, tg_id=tg_id, first_name=first_name
        )
        async with self.app.database.session() as session:
            session.add(player)
            await session.commit()
        return player

    async def change_player_fields(
        self, player_id: int, new_values: dict[str, Any]
    ) -> PlayerModel:
        """Меняет значения полей игрока и возвращает обновленного игрока."""
        query = (
            update(PlayerModel)
            .where(PlayerModel.id == player_id)
            .values(**new_values)
            .returning(PlayerModel)
        )
        async with self.app.database.session() as session:
            player: PlayerModel = await session.scalar(query)
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

    async def change_balance_current_value(
        self, player_id: int, chat_id: int, new_value: int
    ) -> BalanceModel:
        """Меняет сумму на балансе игрока в определенном чате и возвращает
        обновленный баланс.
        """
        query = (
            update(BalanceModel)
            .where(
                and_(
                    BalanceModel.chat_id == chat_id,
                    BalanceModel.player_id == player_id,
                )
            )
            .values(current_value=new_value)
        ).returning(BalanceModel)
        async with self.app.database.session() as session:
            balance = await session.scalar(query)
            await session.commit()
        return balance


class GameAccessor(BaseAccessor):
    async def create_game(
        self,
        chat_id: int,
        diller_cards: list[str],
        gameplays: list[GamePlayModel],
    ) -> GameModel:
        """Создает и отдает игру."""
        game = GameModel(
            chat_id=chat_id, diller_cards=diller_cards, gameplays=gameplays
        )
        async with self.app.database.session() as session:
            session.add(game)
            await session.commit()
        return game

    async def list_games(self) -> Sequence[GameModel]:
        """Отдает список всех игр с подгруженными геймплеями."""
        query = select(GameModel).options(selectinload(GameModel.gameplays))
        async with self.app.database.session() as session:
            return await session.scalars(query)

    async def get_active_game_by_chat_id(
        self, chat_id: int
    ) -> GameModel | None:
        """Ищет в определенном чате активную игру с подгруженными геймплеями
        и игроками.
        """
        query = (
            select(GameModel)
            .where(
                and_(
                    GameModel.chat_id == chat_id,
                    GameModel.status == GameStatus.ACTIVE,
                )
            )
            .options(
                selectinload(GameModel.gameplays).subqueryload(
                    GamePlayModel.player
                )
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

    async def change_game_fields(
        self, game_id: int, new_values: dict[str, Any]
    ) -> GameModel:
        """Меняет значения полей игры и возвращает обновленную игру."""
        query = (
            update(GameModel)
            .where(GameModel.id == game_id)
            .values(**new_values)
            .returning(GameModel)
        )
        async with self.app.database.session() as session:
            game: GameModel = await session.scalar(query)
            await session.commit()
        return game

    async def change_active_game_stage(
        self, chat_id: int, stage: GameStage
    ) -> GameModel:
        """Находит активную игру (с подгруженными геймплеями и игроками)
        по chat_id, переводит ее на новую стадию и возвращает эту игру.
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
        ).options(
            selectinload(GameModel.gameplays).subqueryload(GamePlayModel.player)
        )

        async with self.app.database.session() as session:
            game: GameModel = await session.scalar(query)
            await session.commit()
        return game

    async def check_all_players_have_bet(self, game_id: int) -> bool:
        """Проверяет, что все игроки сделали ставки:
        - получает игру с подгруженными геймплеями,
        - перебирает все геймплеи, проверяя, что ставка не меньше минимально
        допустимой (при создании геймплея ставка равна 1, что означает, что
        игрок еще не делал ставку),
        - возвращает результат проверки.
        """
        query = (
            select(GameModel)
            .where(GameModel.id == game_id)
            .options(selectinload(GameModel.gameplays))
        )

        async with self.app.database.session() as session:
            game_with_gameplays: GameModel = await session.scalar(query)

        players_have_bet: list[bool] = [
            play.player_bet >= MINIMAL_BET
            for play in game_with_gameplays.gameplays
        ]
        return all(players_have_bet)

    async def cancel_active_game_due_to_timer(
        self, game_id: int
    ) -> GameModel | None:
        """Находит активную игру на стадии ставок по id и меняет
        ее статус на canceled. Возвращает отмененную игру или None
        (если активной игры на стадии ставок в данном чате нет).
        """
        query = (
            update(GameModel)
            .where(
                and_(
                    GameModel.id == game_id,
                    GameModel.status == GameStatus.ACTIVE,
                    GameModel.stage == GameStage.BETTING,
                )
            )
            .values(status=GameStatus.CANCELED)
            .returning(GameModel)
        )
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

    async def change_gameplay_fields(
        self, gameplay_id: int, new_values: dict[str, Any]
    ) -> GamePlayModel:
        """Меняет значения полей геймплея и возвращает геймплей."""
        query = (
            update(GamePlayModel)
            .where(GamePlayModel.id == gameplay_id)
            .values(**new_values)
            .returning(GamePlayModel)
        )
        async with self.app.database.session() as session:
            gameplay: GamePlayModel = await session.scalar(query)
            await session.commit()
        return gameplay
