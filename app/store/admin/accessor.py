from typing import TYPE_CHECKING

from sqlalchemy import select

from app.admin.models import AdminModel
from app.base.base_accessor import BaseAccessor

if TYPE_CHECKING:
    from app.web.app import Application


class AdminAccessor(BaseAccessor):
    async def connect(self, app: "Application") -> None:
        admin = await self.get_by_email(email=app.config.admin.email)
        if not admin:
            await self.create_admin(
                email=app.config.admin.email, password=app.config.admin.password
            )

    async def get_by_email(self, email: str) -> AdminModel | None:
        async with self.app.database.session() as session:
            query = select(AdminModel).where(AdminModel.email == email)
            return await session.scalar(query)

    async def create_admin(self, email: str, password: str) -> AdminModel:
        async with self.app.database.session() as session:
            admin = AdminModel(
                email=email, password=AdminModel.hashed_password(password)
            )
            session.add(admin)
            await session.commit()
            return admin
