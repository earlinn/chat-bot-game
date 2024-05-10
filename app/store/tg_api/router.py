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
        if update.message.text == "/start":
            # TODO: проверить, есть ли в текущем чате активная игра,
            # если есть, то предложить дождаться ее окончания либо почитать
            # правила игры; если активных игр нет, то предложить начать игру
            # или почитать правила игры.

            # пока опустим проверку статуса игры, просто выведем приветственное
            # сообщение. Давай пока сделаем все в BotManager, позже можно
            # будет вынести из него хендлеры.
            await self.store.bots_manager.say_hi(update)
        else:
            await self.store.bots_manager.unknown_command(update)
