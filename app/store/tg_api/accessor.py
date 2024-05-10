import json
import os
import typing
from urllib.parse import urlencode, urljoin

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.tg_api.dataclasses import SendMessage, Update
from app.store.tg_api.poller import Poller
from app.web.utils import TgGetUpdatesError

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
                Update.from_dict(update)
                for update in data.get("result")
                if update.get("message")
            ]
            return updates

    async def send_message(self, message: SendMessage) -> None:
        async with self.session.get(
            self._build_query(
                API_PATH,
                "sendMessage",
                params={"chat_id": message.chat_id, "text": message.text},
            )
        ) as response:
            data = await response.json()
            self.logger.info(data)

    async def send_message_with_button(self, message: SendMessage) -> None:
        button_text = message.reply_markup.inline_keyboard[0].text
        button_url = message.reply_markup.inline_keyboard[0].url
        async with self.session.get(
            self._build_query(
                API_PATH,
                "sendMessage",
                params={
                    "chat_id": message.chat_id,
                    "text": message.text,
                    # TODO: хочется сделать в этом методе аргумент reply_markup,
                    # в котором уже сразу будет нужная json-строка, и передавать
                    # её в параметр reply_markup так:
                    # "reply_markup": reply_markup
                    "reply_markup": json.dumps(
                        {
                            "inline_keyboard": [
                                [{"text": button_text, "url": button_url}]
                            ]
                        }
                    ),
                },
            )
        ) as response:
            data = await response.json()
            self.logger.info(data)
