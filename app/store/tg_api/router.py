import asyncio
from logging import getLogger

from app.game.models import GameModel
from app.store import Store
from app.store.bot import const
from app.store.tg_api.dataclasses import CallbackQuery, Message

from .dataclasses import BotContext


class Router:
    """Класс для распределения обновлений, полученных поллером бота,
    по нужным хендлерам.
    """

    def __init__(self, store: Store, queue: asyncio.Queue) -> None:
        """Подключается к store и к логгеру."""
        self.store = store
        self.queue = queue
        self.logger = getLogger("bot router")

    async def route_update(self) -> None:
        """Получает по одному update из очереди и перенаправляет в нужный
        обработчик в зависимости от типа update (message или callback_query).
        """
        while True:
            update = await self.queue.get()
            try:
                message: Message | None = update.message
                callback_query: CallbackQuery | None = update.callback_query
                if message:
                    await self._process_message_update(message)
                elif callback_query:
                    await self._process_callback_query_update(callback_query)
                else:
                    self.logger.error("Another type of update: %s", update)
            finally:
                self.queue.task_done()

    async def _process_message_update(self, message: Message) -> None:
        """Обрабатывает update типа message."""
        bot_context = BotContext(
            chat_id=message.chat.id, username=message.from_.first_name
        )
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
            self.logger.error("Another type of message: %s", message)

    async def _process_callback_query_update(
        self, callback_query: CallbackQuery
    ) -> None:
        """Обрабатывает update типа callback_query: получает контекст для бота,
        информацию об игре и отправляет запрос в BotManager.
        """
        bot_context = BotContext(
            chat_id=callback_query.message.chat.id,
            username=callback_query.from_.first_name,
        )
        current_game: (
            GameModel | None
        ) = await self.store.games.get_active_game_by_chat_id(
            bot_context.chat_id
        )

        if callback_query.data == const.MY_BALANCE_CALLBACK:
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
