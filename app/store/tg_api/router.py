import random
from logging import getLogger

from app.game.const import CARDS, GameStage, GameStatus
from app.game.models import BalanceModel, GameModel, GamePlayModel, PlayerModel
from app.store import Store
from app.store.bot.const import ADD_PLAYER_CALLBACK, JOIN_GAME_CALLBACK
from app.store.tg_api.dataclasses import CallbackQuery, Chat, Message, Update

from .dataclasses import BotManagerContext


class Router:
    """Распределяет обновления (updates) по нужным хендлерам."""

    def __init__(self, store: Store) -> None:
        """Подключается к store и к логгеру."""
        self.store = store
        self.logger = getLogger("bot router")

    async def get_updates(self, updates: list[Update]) -> None:
        """Принимает список updates и по одному отправляет их на обработку."""
        for update in updates:
            await self._route_update(update)

    async def _route_update(self, update: Update) -> None:
        """Перенаправляет update в нужный обработчик в зависимости от типа."""
        message: Message | None = update.message
        callback_query: CallbackQuery | None = update.callback_query
        if message:
            await self._process_message_update(message)
        elif callback_query:
            await self._process_callback_query_update(callback_query)
        else:
            self.logger.error("Another type of update: %s", update)

    async def _process_message_update(self, message: Message) -> None:
        """Обрабатывает update типа message: ходит в базу данных и
        в зависимости от результата вызывает различные методы BotManager.
        """
        chat: Chat = message.chat
        bot_context: BotManagerContext = await self._get_bot_context(chat.id)
        current_game: (
            GameModel | None
        ) = await self.store.games.get_active_game_by_chat_id(chat.id)

        if message.text == "/start" and not current_game:
            await self.store.bots_manager.say_hi_and_play(bot_context)
        elif message.text == "/start" and current_game:
            await self.store.bots_manager.say_hi_and_wait(bot_context)

    async def _process_callback_query_update(
        self, callback_query: CallbackQuery
    ) -> None:
        """Обрабатывает update типа callback_query: ходит в базу данных и
        в зависимости от результата вызывает различные методы BotManager.
        """
        query: str = callback_query.data
        chat: Chat = callback_query.message.chat
        bot_context: BotManagerContext = await self._get_bot_context(chat.id)
        current_game: (
            GameModel | None
        ) = await self.store.games.get_active_game_by_chat_id(chat.id)

        # Для случаев:
        # 1) в чате ведется активная игра, но кто-то нажимает на "Начать игру";
        # 2) в чате ведется активная игра не на стадии ожидания игроков,
        # но кто-то нажимает на кнопку "Присоединиться к игре".
        # Что делаем: отвечаем, что надо подождать окончания текущей игры
        if current_game and (
            query == JOIN_GAME_CALLBACK
            or (
                query == ADD_PLAYER_CALLBACK
                and current_game.stage != GameStage.WAITING
            )
        ):
            await self.store.bots_manager.wait_next_game(bot_context)

        # Игры пока нет и нажата кнопка "Начать новую игру".
        # Что делаем: создаем игру и закидываем в нее юзера, нажавшего
        # на кнопку, запускаем таймер для присоединения других игроков и
        # выводим сообщение, что первый игрок уже в игре
        elif query == JOIN_GAME_CALLBACK:
            player: PlayerModel = await self._get_player_with_balance(
                callback_query, chat.id
            )
            game: GameModel = await self._get_game(chat.id)
            await self._get_gameplay(game.id, player.id)
            await self.store.bots_manager.join_new_game(bot_context)
            bot_context.username = player.username
            await self.store.bots_manager.player_joined(bot_context)

        # Игры в чате нет, но кто-то нажал на "Присоединиться к игре".
        # Что делаем: отвечаем, что сначала надо начать новую игру
        elif query == ADD_PLAYER_CALLBACK and not current_game:
            await self.store.bots_manager.join_non_existent_game_fail(
                bot_context
            )

        # Игра на стадии WAITING, запущен таймер для присоединения игроков,
        # кто-то нажимает на "Присоединиться к игре"
        # Что делаем: добавляем еще одного игрока в эту игру, т.е. получаем
        # игрока, создаем для него геймплей и выводим сообщение, что он в игре
        elif (
            query == ADD_PLAYER_CALLBACK
            and current_game
            and current_game.stage == GameStage.WAITING
        ):
            player: PlayerModel = await self._get_player_with_balance(
                callback_query, chat.id
            )
            await self._get_gameplay(current_game.id, player.id)
            bot_context.username = player.username
            await self.store.bots_manager.player_joined(bot_context)

    async def _get_bot_context(
        self, chat_id: int, username: str | None = None
    ) -> BotManagerContext:
        """Собирает контекст в экземпляр класса BotManagerContext."""
        return BotManagerContext(chat_id, username)

    async def _get_player_with_balance(
        self, callback_query: CallbackQuery, chat_id: int
    ) -> PlayerModel:
        """Получает или создает нового игрока. Если создан новый игрок,
        создает ему баланс для текущего чата. Если новый игрок не создан,
        проверяет, есть ли у игрока баланс в данном чате, и создает ему
        баланс, если у него не было баланса в данном чате.
        """
        player_created, player = await self.store.players.get_or_create(
            model=PlayerModel,
            get_params=[PlayerModel.tg_id == callback_query.from_.id],
            create_params={
                "username": callback_query.from_.username,
                "tg_id": callback_query.from_.id,
            },
        )
        self.logger.info("Player: %s, created: %s", player, player_created)
        if (
            player_created
            or not await self.store.players.get_balance_by_player_and_chat(
                player.id, chat_id
            )
        ):
            balance: BalanceModel = (
                await self.store.players.create_player_balance(
                    chat_id, player.id
                )
            )
            self.logger.info("Balance created: %s", balance)
        return player

    async def _get_game(self, chat_id: int) -> GameModel:
        """Получает или создает новую игру."""
        game_created, game = await self.store.players.get_or_create(
            model=GameModel,
            get_params=[
                GameModel.chat_id == chat_id,
                GameModel.status == GameStatus.ACTIVE,
                GameModel.stage == GameStage.WAITING,
            ],
            create_params={
                "chat_id": chat_id,
                "diller_cards": [random.choice(list(CARDS))],
            },
        )
        self.logger.info("Game: %s, created: %s", game, game_created)
        return game

    async def _get_gameplay(
        self, game_id: int, player_id: int
    ) -> GamePlayModel:
        """Получает или создает геймплей, связанный с определенными
        игрой и игроком.
        """
        gameplay_created, gameplay = await self.store.players.get_or_create(
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
        self.logger.info(
            "Gameplay: %s, created: %s", gameplay, gameplay_created
        )
        return gameplay
