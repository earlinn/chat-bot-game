TG_USERNAME_ERROR: str = (
    "Username должен иметь длину от 5 до 32 символов, допускаются только "
    "латинские буквы, цифры и нижнее подчеркивание."
)


class TgGetUpdatesError(Exception):
    """Вызывается, если получение обновлений методом getUpdates завершилось
    ошибкой, и в ответе Telegram Bot API присутствует "ok": false.
    """


class TgUsernameError(ValueError):
    """Вызывается, если username не соответствует правилам Telegram."""

    def __init__(self, message: str = TG_USERNAME_ERROR) -> None:
        self.message = message
        super().__init__(self.message)
