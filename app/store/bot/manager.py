import typing
from logging import getLogger

from app.store.tg_api.dataclasses import SendMessage, Update

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")

    async def run_echo(self, updates: list[Update]):
        for update in updates:
            await self.app.store.tg_api.send_message(
                SendMessage(
                    chat_id=update.message.from_.id,
                    text=update.message.text,
                )
            )
