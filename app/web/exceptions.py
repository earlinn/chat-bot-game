TG_USERNAME_ERROR = (
    "Username должен иметь длину от 5 до 32 символов, допускаются только "
    "латинские буквы, цифры и нижнее подчеркивание."
)
TG_GET_UPDATES_FAILED_ERROR = (
    "Ошибка получения обновлений Telegram Bot API: "
    "error_code - {error_code}, description - {description}"
)


class BaseTgBotApiError(Exception):
    """Базовое исключение для ошибок Telegram Bot API."""


class TgGetUpdatesError(BaseTgBotApiError):
    """Вызывается, если получение обновлений методом getUpdates завершилось
    ошибкой, и в ответе Telegram Bot API присутствует "ok": false.
    """

    def __init__(self, error_code: int, description: str) -> None:
        self.error_code = error_code
        self.description = description
        self.message = TG_GET_UPDATES_FAILED_ERROR.format(
            error_code=self.error_code, description=self.description
        )
        super().__init__(self.message)


class TgUsernameError(BaseTgBotApiError):
    """Вызывается, если username не соответствует правилам Telegram."""

    def __init__(self, message: str = TG_USERNAME_ERROR) -> None:
        self.message = message
        super().__init__(self.message)
