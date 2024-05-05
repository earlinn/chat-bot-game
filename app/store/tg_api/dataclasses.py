from dataclasses import dataclass


@dataclass
class SendMessage:
    chat_id: int
    text: str


@dataclass
class Chat:
    id: int
    type: str
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None


@dataclass
class MessageFrom:
    id: int
    is_bot: bool
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None


@dataclass
class Message:
    message_id: int
    from_: MessageFrom
    chat: Chat
    date: int
    text: str | None = None


@dataclass
class Update:
    update_id: int
    message: Message
