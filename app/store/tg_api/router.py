from app.game.models import GameModel
from app.store import Store
from app.store.tg_api.dataclasses import CallbackQuery, Chat, Message, Update


class Router:
    """Принимает список updates и распределяет их по нужным хендлерам."""

    def __init__(self, store: Store) -> None:
        self.store = store

    async def get_updates(self, updates: list[Update]) -> None:
        for update in updates:
            await self._process_update(update)

    async def _process_update(self, update: Update):
        message: Message | None = update.message
        callback_query: CallbackQuery | None = update.callback_query

        # TODO: а если у callback_query отсутствует поле message?
        # Поле chat_instance тоже не подходит, т.к. chat_instance != chat.id
        chat: Chat = message.chat if message else callback_query.message.chat

        current_chat_game: (
            GameModel | None
        ) = await self.store.games.get_active_game_by_chat_id(chat.id)

        if message and message.text == "/start" and not current_chat_game:
            await self.store.bots_manager.say_hi_and_play(update)
        elif message and message.text == "/start" and current_chat_game:
            await self.store.bots_manager.say_hi_and_wait(update)
        elif callback_query and callback_query.data == "some_func":
            await self.store.bots_manager.start_timer(chat.id)
        else:
            await self.store.bots_manager.unknown_command(chat.id)
