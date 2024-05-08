from marshmallow import Schema, fields
from marshmallow.validate import Regexp

from app.game.models import TG_USERNAME_ERROR, TG_USERNAME_REGEX


class PlayerSchema(Schema):
    id = fields.Int(required=False)
    username = fields.Str(
        required=True,
        validate=Regexp(regex=TG_USERNAME_REGEX, error=TG_USERNAME_ERROR),
    )
    tg_id = fields.Int(required=True)


class PlayerListSchema(Schema):
    players = fields.Nested(PlayerSchema, many=True)


class BalanceSchema(Schema):
    id = fields.Int(required=False)
    chat_id = fields.Int(required=True)
    player_id = fields.Int(required=True)
    current_value = fields.Int(required=False)
    max_value = fields.Int(required=False)
    min_value = fields.Int(required=False)
