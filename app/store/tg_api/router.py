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
            # TODO: проверить, есть ли в текущем чате активная игра,
            # если есть, то предложить дождаться ее окончания либо почитать
            # правила игры; если активных игр нет, то предложить начать игру
            # или почитать правила игры.

            # пока опустим проверку статуса игры, просто выведем приветственное
            # сообщение. Давай пока сделаем все в BotManager, позже можно
            # будет вынести из него хендлеры.
            await self.store.bots_manager.say_hi(update)
        if update.message.text == "/start" and current_chat_game:
            pass
        else:
            await self.store.bots_manager.unknown_command(update)
