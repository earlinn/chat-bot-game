from aiohttp.web_exceptions import HTTPNotFound
from aiohttp_apispec import (
    docs,
    querystring_schema,
    request_schema,
    response_schema,
)

from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response

from .models import GamePlayModel
from .schemes import (
    BalanceListSchema,
    BalanceSchema,
    GameListSchema,
    GameSchema,
    PlayerIdSchema,
    PlayerListSchema,
    PlayerSchema,
)


class PlayerAddView(AuthRequiredMixin, View):
    @docs(tags=["players"], summary="Add new player")
    @request_schema(PlayerSchema)
    @response_schema(PlayerSchema, 201)
    async def post(self):
        username, tg_id = self.data["username"], self.data["tg_id"]
        player = await self.store.players.create_player(
            username=username, tg_id=tg_id
        )
        return json_response(data=PlayerSchema().dump(player))


class PlayerListView(AuthRequiredMixin, View):
    @docs(tags=["players"], summary="Get list of players")
    @response_schema(PlayerListSchema, 200)
    async def get(self):
        players = await self.store.players.list_players()
        return json_response(data=PlayerListSchema().dump({"players": players}))


class BalanceAddView(AuthRequiredMixin, View):
    @docs(tags=["players"], summary="Add new player balance")
    @request_schema(BalanceSchema)
    @response_schema(BalanceSchema, 201)
    async def post(self):
        chat_id, player_id = self.data["chat_id"], self.data["player_id"]

        if not await self.store.players.get_player_by_id(id_=player_id):
            raise HTTPNotFound(reason="no such player id")

        balance = await self.store.players.create_player_balance(
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
        balances = await self.store.players.list_balances(player_id)
        return json_response(
            data=BalanceListSchema().dump({"balances": balances})
        )


class GameAddView(AuthRequiredMixin, View):
    @docs(tags=["games"], summary="Add new game")
    @request_schema(GameSchema)
    @response_schema(GameSchema, 201)
    async def post(self):
        chat_id: int = self.data["chat_id"]
        diller_cards: list[str] = self.data["diller_cards"]
        gameplays: list[GamePlayModel] = self.data["gameplays"]
        game = await self.store.games.create_game(
            chat_id=chat_id,
            diller_cards=diller_cards,
            gameplays=[
                GamePlayModel(
                    player_id=gameplay["player_id"],
                    player_bet=gameplay["player_bet"],
                )
                for gameplay in gameplays
            ],
        )
        return json_response(data=GameSchema().dump(game))


class GameListView(AuthRequiredMixin, View):
    @docs(tags=["games"], summary="Get list of games")
    @response_schema(GameListSchema, 200)
    async def get(self):
        games = await self.store.games.list_games()
        return json_response(data=GameListSchema().dump({"games": games}))
