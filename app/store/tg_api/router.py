from logging import getLogger

from app.game.models import GameModel
from app.store import Store
from app.store.bot import const
from app.store.tg_api.dataclasses import CallbackQuery, Chat, Message, Update

from .dataclasses import BotContext


class Router:
    """Класс для распределения обновлений, полученных поллером бота,
    по нужным хендлерам.
    """

    def __init__(self, store: Store) -> None:
        """Подключается к store и к логгеру."""
        self.store = store
        self.logger = getLogger("bot router")

    async def route_updates(self, updates: list[Update]) -> None:
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
        """Обрабатывает update типа message."""
        # TODO: надо сразу добавлять в BotContext поле username
        bot_context: BotContext = await self._get_bot_context(message.chat)
        current_game: (
            GameModel | None
        ) = await self.store.games.get_active_game_by_chat_id(
            bot_context.chat_id
        )

        if message.text == "/start" and not current_game:
            await self.store.bot_manager.say_hi_and_play(bot_context)
        elif message.text == "/start" and current_game:
            await self.store.bot_manager.say_hi_and_wait(bot_context)
        else:
            await self.store.bot_manager.say_unknown_command(bot_context)

    async def _process_callback_query_update(
        self, callback_query: CallbackQuery
    ) -> None:
        """Обрабатывает update типа callback_query: получает контекст для бота,
        информацию об игре и отправляет запрос в BotManager.
        """
        # TODO: надо сразу добавлять в BotContext поле username
        bot_context: BotContext = await self._get_bot_context(
            callback_query.message.chat
        )
        current_game: (
            GameModel | None
        ) = await self.store.games.get_active_game_by_chat_id(
            bot_context.chat_id
        )

        if callback_query.data == const.MY_BALANCE_CALLBACK:
            bot_context.username = callback_query.from_.username
            await self.store.bot_handler.handle_my_balance_query(
                callback_query, bot_context
            )
        elif current_game:
            bot_context.current_game = current_game
            await self.store.bot_handler.handle_active_game(
                callback_query, bot_context
            )
        else:
            await self.store.bot_handler.handle_no_game_case(
                callback_query, bot_context
            )

    async def _get_bot_context(
        self,
        chat: Chat,
        current_game: GameModel | None = None,
        username: str | None = None,
        bet_value: int | None = None,
        message: str | None = None,
    ) -> BotContext:
        """Собирает контекст в экземпляр класса BotContext."""
        return BotContext(chat.id, current_game, username, bet_value, message)
