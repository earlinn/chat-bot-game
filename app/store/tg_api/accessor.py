import os
import typing
from urllib.parse import urlencode, urljoin

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.tg_api.dataclasses import (
    Chat,
    Message,
    Update,
    User,
)
from app.store.tg_api.poller import Poller

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

    async def _get_updates(
        self,
        offset: int | None = None,
        limit: int = 100,
        timeout: int = 0,
        allowed_updates: list[str] | None = None,
    ) -> list[Update] | None:
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
                    {data["error_code"]},
                    {data["description"]},
                )
                return None
            if data.get("result"):
                updates: list[Update] = [
                    Update(
                        update_id=update["update_id"],
                        message=Message(
                            message_id=update["message"]["message_id"],
                            from_=User(
                                id=update["message"]["from"]["id"],
                                is_bot=update["message"]["from"]["is_bot"],
                                first_name=update["message"]["from"][
                                    "first_name"
                                ],
                                last_name=update["message"]["from"][
                                    "last_name"
                                ],
                                username=update["message"]["from"]["username"],
                                language_code=update["message"]["from"][
                                    "language_code"
                                ],
                            ),
                            chat=Chat(
                                id=update["message"]["chat"]["id"],
                                first_name=update["message"]["chat"].get(
                                    "first_name"
                                ),
                                last_name=update["message"]["chat"].get(
                                    "last_name"
                                ),
                                username=update["message"]["chat"].get(
                                    "username"
                                ),
                                type=update["message"]["chat"]["type"],
                                title=update["message"]["chat"].get("title"),
                            ),
                            date=update["message"]["date"],
                            text=update["message"].get("text"),
                        ),
                    )
                    for update in data.get("result")
                    if update.get("message")
                ]
            else:
                updates = []
            await self.app.store.bots_manager.run_echo(updates)
            return updates

    async def send_message(self, message: Message) -> None:
        async with self.session.get(
            self._build_query(
                API_PATH,
                "sendMessage",
                params={"chat_id": message.chat_id, "text": message.text},
            )
        ) as response:
            data = await response.json()
            self.logger.info(data)
