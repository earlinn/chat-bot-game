import json
from dataclasses import asdict, dataclass
from typing import Any, Optional


@dataclass
class BotContext:
    """Контекст для передачи в методы-обработчики класса BotManager."""

    chat_id: int
    username: str | None = None
    bet_value: int | None = None


@dataclass
class InlineKeyboardButton:
    """This object represents one button of an inline keyboard.
    You must use exactly one of the optional fields.
    """

    text: str
    url: str | None = None
    callback_data: str | None = None

    @classmethod
    def from_dict(
        cls, button: dict[str, str] | None
    ) -> Optional["InlineKeyboardButton"]:
        if button is None:
            return None
        return cls(
            text=button["text"],
            url=button.get("url"),
            callback_data=button.get("callback_data"),
        )


@dataclass
class InlineKeyboardMarkup:
    """This object represents an inline keyboard that appears right next
    to the message it belongs to.
    """

    inline_keyboard: list[list[InlineKeyboardButton]]

    @classmethod
    def from_dict(
        cls, reply_markup: dict[str, list[list[dict[str, str]]]] | None
    ) -> "InlineKeyboardMarkup":
        if reply_markup is None:
            return None
        return cls(
            inline_keyboard=[
                [InlineKeyboardButton.from_dict(button) for button in item]
                for item in reply_markup["inline_keyboard"]
            ]
        )

    def json_reply_markup_keyboard(self) -> str:
        res_dict = {
            "inline_keyboard": [
                [
                    {
                        key: value
                        for (key, value) in asdict(button).items()
                        if value
                    }
                    for button in self.inline_keyboard
                ]
            ]
        }
        return json.dumps(res_dict)


@dataclass
class SendMessage:
    """Custom message instance for sendMessage request."""

    chat_id: int
    text: str
    reply_markup: InlineKeyboardMarkup | None = None


@dataclass
class Chat:
    """This object represents a chat."""

    id: str
    type: str
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    title: str | None = None

    @classmethod
    def from_dict(cls, chat: dict) -> "Chat":
        return cls(
            id=chat["id"],
            first_name=chat.get("first_name"),
            last_name=chat.get("last_name"),
            username=chat.get("username"),
            type=chat["type"],
            title=chat.get("title"),
        )


@dataclass
class User:
    """This object represents a Telegram user or bot."""

    id: int
    is_bot: bool
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None

    @classmethod
    def from_dict(
        cls, user: dict[str, int | bool | str | None] | None
    ) -> Optional["User"]:
        if user is None:
            return None
        return cls(
            id=user["id"],
            is_bot=user["is_bot"],
            first_name=user["first_name"],
            last_name=user.get("last_name"),
            username=user.get("username"),
            language_code=user.get("language_code"),
        )


@dataclass
class MessageEntity:
    """This object represents one special entity in a text message.
    For example, hashtags, usernames, URLs, etc.
    """

    type: str
    offset: int
    length: int
    url: str | None = None
    user: User | None = None
    language: str | None = None
    custom_emoji_id: str | None = None

    @classmethod
    def from_dict(
        cls, entities: list[dict[str, int | str]] | None
    ) -> list["MessageEntity"] | None:
        if entities is None:
            return None
        return [
            cls(
                type=entity["type"],
                offset=entity["offset"],
                length=entity["length"],
                user=User.from_dict(entity.get("user")),
                language=entity.get("language"),
                custom_emoji_id=entity.get("custom_emoji_id"),
            )
            for entity in entities
        ]


@dataclass
class Message:
    """This object represents a message."""

    message_id: int
    from_: User
    chat: Chat
    date: int
    text: str | None = None
    reply_markup: InlineKeyboardMarkup | None = None
    entities: list[MessageEntity] | None = None

    @classmethod
    def from_dict(cls, message: dict[str, Any] | None) -> Optional["Message"]:
        if message is None:
            return None
        return cls(
            message_id=message["message_id"],
            from_=User.from_dict(message["from"]),
            chat=Chat.from_dict(message["chat"]),
            date=message["date"],
            text=message.get("text"),
            reply_markup=InlineKeyboardMarkup.from_dict(
                message.get("reply_markup")
            ),
            entities=MessageEntity.from_dict(message.get("entities")),
        )


@dataclass
class InaccessibleMessage:
    """This object describes a message that was deleted or is otherwise
    inaccessible to the bot.
    """

    chat: Chat
    message_id: int
    date: int = 0

    @classmethod
    def from_dict(cls, message: dict[str, Any]) -> "InaccessibleMessage":
        return cls(
            chat=Chat.from_dict(message["chat"]),
            message_id=message["message_id"],
            date=message["date"],
        )


@dataclass
class CallbackQuery:
    """This object represents an incoming callback query from a callback button
    in an inline keyboard.
    If the button that originated the query was attached to a message sent
    by the bot, the field message will be present.
    If the button was attached to a message sent via the bot (in inline mode),
    the field inline_message_id will be present.
    Exactly one of the fields data or game_short_name will be present.

    У меня присутствуют поля id, from, message (Message), chat_instance, data.
    """

    id: int
    from_: User
    chat_instance: str
    message: Message | InaccessibleMessage | None = None
    inline_message_id: str | None = None
    data: str | None = None
    game_short_name: str | None = None

    @classmethod
    def from_dict(
        cls, callback_query: dict[str, Any] | None
    ) -> Optional["CallbackQuery"]:
        if callback_query is None:
            return None

        message = callback_query.get("message")
        if message is not None and message["date"] == 0:
            message = InaccessibleMessage.from_dict(message)
        elif message is not None and message["date"] != 0:
            message = Message.from_dict(message)

        return cls(
            id=callback_query["id"],
            from_=User.from_dict(callback_query["from"]),
            chat_instance=callback_query["chat_instance"],
            message=message,
            inline_message_id=callback_query.get("inline_message_id"),
            data=callback_query.get("data"),
            game_short_name=callback_query.get("game_short_name"),
        )


@dataclass
class Update:
    """This object represents an incoming update.
    At most one of the optional parameters can be present in any given update.
    """

    update_id: int
    message: Message | None = None
    callback_query: CallbackQuery | None = None

    @classmethod
    def from_dict(cls, update: dict) -> "Update":
        return cls(
            update_id=update["update_id"],
            message=Message.from_dict(update.get("message")),
            callback_query=CallbackQuery.from_dict(
                update.get("callback_query")
            ),
        )
