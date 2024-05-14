import typing
from logging import getLogger

from sqlalchemy import and_, select
from sqlalchemy.sql.elements import BinaryExpression

from app.store.database.sqlalchemy_base import BaseModel

if typing.TYPE_CHECKING:
    from app.web.app import Application

BM = typing.TypeVar("BM", bound=BaseModel)


class BaseAccessor:
    def __init__(self, app: "Application", *args, **kwargs):
        self.app = app
        self.logger = getLogger("accessor")

        app.on_startup.append(self.connect)
        app.on_cleanup.append(self.disconnect)

    async def connect(self, app: "Application"):
        return

    async def disconnect(self, app: "Application"):
        return

    async def get_or_create(
        self,
        model: BM,
        get_params: list[BinaryExpression],
        create_params: dict[str, typing.Any],
    ) -> tuple[bool, BM]:
        """Базовый метод для поиска экземпляра модели и его создания, если
        он не обнаружен при поиске.
        Возвращает кортеж, состоящий из created (тип bool) и экземпляра модели.
        """
        created = False
        get_query = select(model).where(and_(*get_params))

        async with self.app.database.session() as session:
            instance = await session.scalar(get_query)
            if not instance:
                instance = model(**create_params)
                session.add(instance)
                await session.commit()
                created = True
            return created, instance
