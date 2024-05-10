from app.game.models import GameModel
from app.store import Store
from app.store.tg_api.dataclasses import Update


class Router:
    """Принимает список updates и распределяет их по нужным хендлерам."""

    def __init__(self, store: Store) -> None:
        self.store = store

    async def get_updates(self, updates: list[Update]) -> None:
        for update in updates:
            await self._process_update(update)

    async def _process_update(self, update: Update):
        current_chat_game: (
            GameModel | None
        ) = await self.store.games.get_active_game_by_chat_id(
            update.message.chat.id
        )
        if update.message.text == "/start" and not current_chat_game:
            await self.store.bots_manager.say_hi_and_play(update)
        elif update.message.text == "/start" and current_chat_game:
            await self.store.bots_manager.say_hi_and_wait(update)
        else:
            await self.store.bots_manager.unknown_command(update)
