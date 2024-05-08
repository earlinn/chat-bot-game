from aiohttp.web_exceptions import HTTPNotFound
from aiohttp_apispec import docs, request_schema, response_schema

from app.game.schemes import BalanceSchema, PlayerListSchema, PlayerSchema
from app.web.app import View
from app.web.utils import json_response


class PlayerAddView(View):
    @docs(tags=["games"], summary="Add new player")
    @request_schema(PlayerSchema)
    @response_schema(PlayerSchema, 201)
    async def post(self):
        username, tg_id = self.data["username"], self.data["tg_id"]
        player = await self.store.games.create_player(
            username=username, tg_id=tg_id
        )
        return json_response(data=PlayerSchema().dump(player))


class PlayerListView(View):
    @docs(tags=["games"], summary="Get list of players")
    @response_schema(PlayerListSchema, 200)
    async def get(self):
        players = await self.store.games.list_players()
        return json_response(data=PlayerListSchema().dump({"players": players}))


class BalanceAddView(View):
    @docs(tags=["games"], summary="Add new player balance")
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
