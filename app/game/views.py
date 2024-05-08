from aiohttp.web_exceptions import HTTPNotFound
from aiohttp_apispec import (
    docs,
    querystring_schema,
    request_schema,
    response_schema,
)

from app.game.schemes import (
    BalanceListSchema,
    BalanceSchema,
    PlayerIdSchema,
    PlayerListSchema,
    PlayerSchema,
)
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class PlayerAddView(AuthRequiredMixin, View):
    @docs(tags=["players"], summary="Add new player")
    @request_schema(PlayerSchema)
    @response_schema(PlayerSchema, 201)
    async def post(self):
        username, tg_id = self.data["username"], self.data["tg_id"]
        player = await self.store.games.create_player(
            username=username, tg_id=tg_id
        )
        return json_response(data=PlayerSchema().dump(player))


class PlayerListView(AuthRequiredMixin, View):
    @docs(tags=["players"], summary="Get list of players")
    @response_schema(PlayerListSchema, 200)
    async def get(self):
        players = await self.store.games.list_players()
        return json_response(data=PlayerListSchema().dump({"players": players}))


class BalanceAddView(AuthRequiredMixin, View):
    @docs(tags=["players"], summary="Add new player balance")
    @request_schema(BalanceSchema)
    @response_schema(BalanceSchema, 201)
    async def post(self):
        chat_id = self.data["chat_id"]
        player_id = self.data["player_id"]
        if not await self.store.games.get_player_by_id(id_=player_id):
            raise HTTPNotFound(reason="no such player id")
        balance = await self.store.games.create_player_balance(
            chat_id=chat_id, player_id=player_id
        )
        return json_response(data=BalanceSchema().dump(balance))


class BalanceListView(AuthRequiredMixin, View):
    @docs(tags=["players"], summary="Get balances list filtered by player id")
    @querystring_schema(PlayerIdSchema)
    @response_schema(BalanceListSchema, 200)
    async def get(self):
        try:
            player_id = int(self.request.query["player_id"])
        except KeyError:
            player_id = None
        balances = await self.store.games.list_balances(player_id)
        return json_response(
            data=BalanceListSchema().dump({"balances": balances})
        )
