import asyncio
import typing

import aio_pika
from aio_pika.abc import AbstractRobustConnection
from aio_pika.pool import Pool

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Rabbit:
    def __init__(self, app: "Application"):
        self.app = app
        self.queue_name = "tg_updates_queue"
        self.connection_pool: Pool | None = None
        self.channel_pool: Pool | None = None

    async def connect(self, *_: list, **__: dict) -> None:
        self.connection_pool = Pool(self.get_connection, max_size=2)
        self.channel_pool = Pool(self.get_channel, max_size=20)
        async with self.channel_pool.acquire() as channel:
            await channel.declare_queue(
                self.queue_name, durable=False, auto_delete=False
            )

    async def disconnect(self, *_: list, **__: dict):
        if self.channel_pool:
            await self.channel_pool.close()
        if self.connection_pool:
            await self.connection_pool.close()

    async def get_connection(self) -> AbstractRobustConnection:
        loop = asyncio.get_event_loop()
        return await aio_pika.connect_robust(
            host=self.app.config.rabbit.host,
            login=self.app.config.rabbit.user,
            password=self.app.config.rabbit.password,
            loop=loop,
        )

    async def get_channel(self) -> aio_pika.Channel:
        async with self.connection_pool.acquire() as connection:
            return await connection.channel()

    async def publish(self, message: str) -> None:
        async with self.channel_pool.acquire() as channel:
            await channel.default_exchange.publish(
                aio_pika.Message(message.encode()), self.queue_name
            )

    async def consume(self) -> aio_pika.Message | None:
        async with self.channel_pool.acquire() as channel:
            await channel.set_qos(10)
            queue = await channel.declare_queue(
                self.queue_name, durable=False, auto_delete=False
            )
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    return message
        return None
