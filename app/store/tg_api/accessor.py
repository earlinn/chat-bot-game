import os
import typing
from urllib.parse import urlencode, urljoin

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.tg_api.dataclasses import SendMessage, Update
from app.store.tg_api.poller import Poller
from app.web.exceptions import TgGetUpdatesError

if typing.TYPE_CHECKING:
    from app.web.app import Application


BOT_TOKEN = os.environ.get("BOT_TOKEN", "token")
API_PATH = f"https://api.telegram.org/bot{BOT_TOKEN}/"


class TgApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: ClientSession | None = None
        self.poller: Poller | None = None

    async def connect(self, app: "Application") -> None:
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))
        self.poller = Poller(app.store)
        self.logger.info("start polling")
        self.poller.start()

    async def disconnect(self, app: "Application") -> None:
        if self.session:
            await self.session.close()

        if self.poller:
            await self.poller.stop()

    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        return f"{urljoin(host, method)}?{urlencode(params)}"

    async def get_updates(
        self,
        offset: int | None = None,
        limit: int = 100,
        timeout: int = 0,
        allowed_updates: list[str] | None = None,
    ) -> list[Update]:
        params = {}
        if offset:
            params["offset"] = offset
        if limit:
            params["limit"] = limit
        if timeout:
            params["timeout"] = timeout
        if allowed_updates:
            params["allowed_updates"] = allowed_updates

        async with self.session.get(
            self._build_query(
                host=API_PATH,
                method="getUpdates",
                params=params,
            )
        ) as response:
            data = await response.json()

            if not data["ok"]:
                self.logger.error(
                    "Ошибка Telegram Bot: %s - %s",
                    data["error_code"],
                    data["description"],
                )
                raise TgGetUpdatesError

            if not data.get("result"):
                return []

            updates: list[Update] = [
                Update.from_dict(update) for update in data.get("result")
            ]
            return updates

    async def send_message(
        self, message: SendMessage, reply_markup: str | None = None
    ) -> None:
        if reply_markup is not None:
            params = {
                "chat_id": message.chat_id,
                "text": message.text,
                "reply_markup": reply_markup,
            }
        else:
            params = {"chat_id": message.chat_id, "text": message.text}

        async with self.session.get(
            self._build_query(
                API_PATH,
                "sendMessage",
                params=params,
            )
        ) as response:
            data = await response.json()
            self.logger.info(data)
