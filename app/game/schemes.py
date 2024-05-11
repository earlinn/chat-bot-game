from marshmallow import Schema, fields
from marshmallow.validate import Regexp

from app.web.exceptions import TG_USERNAME_ERROR

from .models import TG_USERNAME_REGEX


class PlayerSchema(Schema):
    id = fields.Int(required=False)
    username = fields.Str(
        required=True,
        validate=Regexp(regex=TG_USERNAME_REGEX, error=TG_USERNAME_ERROR),
    )
    tg_id = fields.Int(required=True)


class PlayerListSchema(Schema):
    players = fields.Nested(PlayerSchema, many=True)


class PlayerIdSchema(Schema):
    player_id = fields.Int()


class BalanceSchema(Schema):
    id = fields.Int(required=False)
    chat_id = fields.Int(required=True)
    player_id = fields.Int(required=True)
    current_value = fields.Int(required=False)
    # TODO: add max_value, min_value after MVP
    # max_value = fields.Int(required=False)
    # min_value = fields.Int(required=False)


class BalanceListSchema(Schema):
    balances = fields.Nested(BalanceSchema, many=True)


class GameSchema(Schema):
    id = fields.Int(required=False)
    chat_id = fields.Int(required=True)
    created_at = fields.DateTime(required=False)
    status = fields.Str(required=False)
    stage = fields.Str(required=False)
    turn_player_id = fields.Int(required=False, allow_none=True)
    diller_cards = fields.List(fields.Str, required=True)


class GameListSchema(Schema):
    games = fields.Nested(GameSchema, many=True)
