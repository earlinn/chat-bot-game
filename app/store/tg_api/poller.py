import asyncio
from asyncio import Future, Task

from app.store import Store
from app.web.exceptions import TgGetUpdatesError

from .dataclasses import Update
from .router import Router


class Poller:
    def __init__(self, store: Store, queue: asyncio.Queue) -> None:
        self.store = store
        self.queue = queue
        self.router: Router = Router(self.store, self.queue)
        self.is_running = False
        self.poll_task: Task | None = None

    def _done_callback(self, result: Future) -> None:
        if result.exception():
            self.store.logger.exception(
                "poller stopped with exception", exc_info=result.exception()
            )
        if self.is_running:
            self.start()

    def start(self) -> None:
        self.is_running = True
        self.poll_task = asyncio.create_task(self.poll())
        self.poll_task.add_done_callback(self._done_callback)

    async def stop(self) -> None:
        self.is_running = False
        if self.poll_task:
            self.poll_task.cancel()
            try:
                await self.poll_task
            except asyncio.CancelledError:
                self.store.logger.exception("Polling was cancelled")

    async def poll(self) -> None:
        """Получает список updates из TgApiAccessor и по одному складывает их
        в очередь, увеличивая параметр offset на единицу по сравнению с
        update_id (чтобы не обрабатывать неактуальные updates).
        """
        offset: int = 0
        while self.is_running:
            try:
                updates: list[Update] = await self.store.tg_api.get_updates(
                    offset=offset, timeout=30
                )
                if updates:
                    for update in updates:
                        self.queue.put_nowait(update)
                        offset = update.update_id + 1
            except TgGetUpdatesError:
                self.is_running = False
