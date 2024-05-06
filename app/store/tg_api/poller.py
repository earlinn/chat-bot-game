import asyncio
from asyncio import Future, Task

from app.store import Store
from app.store.tg_api.dataclasses import Update
from app.web.utils import TgGetUpdatesError


class Poller:
    def __init__(self, store: Store) -> None:
        self.store = store
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
        offset: int = 0
        while self.is_running:
            try:
                res: list[Update] = await self.store.tg_api.get_updates(
                    offset=offset, timeout=30
                )
                if res:
                    offset = res[-1].update_id + 1
            except TgGetUpdatesError:
                self.is_running = False
