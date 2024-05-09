from aiohttp.web_exceptions import HTTPForbidden
from aiohttp_apispec import docs, request_schema, response_schema
from aiohttp_session import new_session

from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response

from .schemes import AdminSchema


class AdminLoginView(View):
    @docs(tags=["admin"], summary="Login admin")
    @request_schema(AdminSchema)
    @response_schema(AdminSchema, 200)
    async def post(self):
        email, password = self.data["email"], self.data["password"]
        admin = await self.store.admins.get_by_email(email)

        if not (admin and admin.is_password_valid(password)):
            raise HTTPForbidden(reason="admin not found or invalid password")

        session = await new_session(self.request)
        raw_admin = AdminSchema().dump(admin)
        session["admin"] = raw_admin
        return json_response(data=raw_admin)


class AdminCurrentView(AuthRequiredMixin, View):
    @docs(tags=["admin"], summary="Get current admin")
    @response_schema(AdminSchema, 200)
    async def get(self):
        return json_response(data=AdminSchema().dump(self.request.admin))
