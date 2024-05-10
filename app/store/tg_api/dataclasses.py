from dataclasses import dataclass


@dataclass
class InlineKeyboardButton:
    text: str
    url: str | None = None
    callback_data: str | None = None


@dataclass
class InlineKeyboardMarkup:
    inline_keyboard: list[InlineKeyboardButton]


@dataclass
class SendMessage:
    chat_id: int
    text: str
    reply_markup: InlineKeyboardMarkup | None = None


@dataclass
class Chat:
    id: int
    type: str
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    title: str | None = None


@dataclass
class User:
    id: int
    is_bot: bool
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None


@dataclass
class Message:
    message_id: int
    from_: User
    chat: Chat
    date: int
    text: str | None = None


@dataclass
class Update:
    update_id: int
    message: Message

    @classmethod
    def from_dict(cls, update: dict) -> "Update":
        return cls(
            update_id=update["update_id"],
            message=Message(
                message_id=update["message"]["message_id"],
                from_=User(
                    id=update["message"]["from"]["id"],
                    is_bot=update["message"]["from"]["is_bot"],
                    first_name=update["message"]["from"]["first_name"],
                    last_name=update["message"]["from"]["last_name"],
                    username=update["message"]["from"]["username"],
                    language_code=update["message"]["from"]["language_code"],
                ),
                chat=Chat(
                    id=update["message"]["chat"]["id"],
                    first_name=update["message"]["chat"].get("first_name"),
                    last_name=update["message"]["chat"].get("last_name"),
                    username=update["message"]["chat"].get("username"),
                    type=update["message"]["chat"]["type"],
                    title=update["message"]["chat"].get("title"),
                ),
                date=update["message"]["date"],
                text=update["message"].get("text"),
            ),
        )
