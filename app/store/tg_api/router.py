import random
from logging import getLogger

from app.game.const import CARDS, GameStage, GameStatus
from app.game.models import GameModel, GamePlayModel, PlayerModel
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

    async def _get_bot_context(
        self, chat_id: int, username: str | None = None
    ) -> BotManagerContext:
        """Собирает контекст в экземпляр класса BotManagerContext."""
        return BotManagerContext(chat_id, username)

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

        if current_game and (
            query == JOIN_GAME_CALLBACK
            or (
                query == ADD_PLAYER_CALLBACK
                and current_game.stage != GameStage.WAITING
            )
        ):
            await self.store.bots_manager.wait_next_game(bot_context)

        elif query == JOIN_GAME_CALLBACK:
            await self.store.bots_manager.join_new_game(bot_context)

        # TODO: если игры в чате нет, но кто-то вместо кнопки "Начать новую
        # игру" нажал на кнопку "Присоединиться к игре", то создаются игрок,
        # новая игра и геймплей игрока, при этом бот не пишет, что начата игра,
        # таймер не запускается, бот пишет только "<username> в игре", а для
        # читающих даже не очевидно, что начинается игра. И тогда же можно
        # создать самого первого игрока - того юзера, который нажал на кнопку
        # "Начать новую игру". Тогда нам впоследствии не придется чистить БД
        # от игр, в которых нет ни одного игрока.

        # Наверно экземпляр GameModel надо создавать раньше - при нажатии на
        # кнопку "Начать новую игру", а тут надо проверять, есть ли какая-то
        # игра на стадии WAITING. Если нет, то писать "На данный момент ни одна
        # игра не запущена. Чтобы запустить игру, нажмите на кнопку Начать новую
        # игру". Если есть, то создавать геймплей для этого юзера.
        elif query == ADD_PLAYER_CALLBACK:
            player_created, player = await self.store.players.get_or_create(
                model=PlayerModel,
                get_params=[PlayerModel.tg_id == callback_query.from_.id],
                create_params={
                    "username": callback_query.from_.username,
                    "tg_id": callback_query.from_.id,
                },
            )
            self.logger.info("Player: %s, created: %s", player, player_created)
            if player_created:
                # TODO: если создается новый игрок, то нужно также создать ему
                # баланс в этом чате
                pass

            game_created, game = await self.store.players.get_or_create(
                model=GameModel,
                get_params=[
                    GameModel.chat_id == chat.id,
                    GameModel.status == GameStatus.ACTIVE,
                    GameModel.stage == GameStage.WAITING,
                ],
                create_params={
                    "chat_id": chat.id,
                    "diller_cards": [random.choice(list(CARDS))],
                },
            )
            self.logger.info("Game: %s, created: %s", game, game_created)

            gameplay_created, gameplay = await self.store.players.get_or_create(
                model=GamePlayModel,
                get_params=[
                    GamePlayModel.game_id == game.id,
                    GamePlayModel.player_id == player.id,
                ],
                create_params={
                    "game_id": game.id,
                    "player_id": player.id,
                    "player_bet": 1,
                },
            )
            self.logger.info(
                "Gameplay: %s, created: %s", gameplay, gameplay_created
            )

            bot_context.username = player.username
            await self.store.bots_manager.player_joined(bot_context)
