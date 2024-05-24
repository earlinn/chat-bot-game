from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone

TG_USERNAME_REGEX: str = r"^[a-zA-Z0-9_]{5,32}$"


class Player(models.Model):
    """Модель игрока - пользователя Telegram."""

    username = models.CharField(
        max_length=32,
        unique=True,
        validators=[RegexValidator(TG_USERNAME_REGEX)],
        null=True,
    )
    first_name = models.CharField(max_length=256)
    tg_id = models.BigIntegerField(unique=True)

    class Meta:
        managed = False
        db_table = "players"

    def __str__(self) -> str:
        return self.first_name or self.username


class Balance(models.Model):
    """Модель баланса игрока в конкретном чате."""

    chat_id = models.BigIntegerField()
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="balances"
    )
    current_value = models.IntegerField(default=1000)

    class Meta:
        managed = False
        db_table = "balances"
        constraints = [
            models.UniqueConstraint(
                fields=["chat_id", "player"], name="chat_player_unique"
            )
        ]

    def __str__(self) -> str:
        return f"{self.player} in chat {self.chat_id}"


class Game(models.Model):
    """Модель игры."""

    STATUS_ACTIVE: str = "ACTIVE"
    STATUS_FINISHED: str = "FINISHED"
    STATUS_INTERRUPTED: str = "INTERRUPTED"
    STATUS_CANCELED: str = "CANCELED"

    STATUS_CHOISES: list[tuple[str]] = [
        (STATUS_ACTIVE, "ACTIVE"),
        (STATUS_FINISHED, "FINISHED"),
        (STATUS_INTERRUPTED, "INTERRUPTED"),
        (STATUS_CANCELED, "CANCELED"),
    ]

    STAGE_WAITING_FOR_PLAYERS_TO_JOIN: str = "WAITING_FOR_PLAYERS_TO_JOIN"
    STAGE_BETTING: str = "BETTING"
    STAGE_PLAYERHIT: str = "PLAYERHIT"
    STAGE_DILLERHIT: str = "DILLERHIT"
    STAGE_SUMMARIZING: str = "SUMMARIZING"

    STAGE_CHOISES: list[tuple[str]] = [
        (STAGE_WAITING_FOR_PLAYERS_TO_JOIN, "WAITING_FOR_PLAYERS_TO_JOIN"),
        (STAGE_BETTING, "BETTING"),
        (STAGE_PLAYERHIT, "PLAYERHIT"),
        (STAGE_DILLERHIT, "DILLERHIT"),
        (STAGE_SUMMARIZING, "SUMMARIZING"),
    ]

    chat_id = models.BigIntegerField()
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=11, choices=STATUS_CHOISES, default=STATUS_ACTIVE
    )
    stage = models.CharField(
        max_length=27,
        choices=STAGE_CHOISES,
        default=STAGE_WAITING_FOR_PLAYERS_TO_JOIN,
    )
    diller_cards = ArrayField(models.CharField(max_length=5))

    class Meta:
        managed = False
        db_table = "games"

    def __str__(self) -> str:
        return f"Game in chat {self.chat_id} created at {self.created_at}"


class GamePlay(models.Model):
    """Модель геймплея (сессии конкретного игрока в конкретной игре)."""

    STATUS_BETTING: str = "BETTING"
    STATUS_TAKING: str = "TAKING"
    STATUS_STANDING: str = "STANDING"
    STATUS_EXCEEDED: str = "EXCEEDED"
    STATUS_LOST: str = "LOST"
    STATUS_WON: str = "WON"
    STATUS_TIE: str = "TIE"

    STATUS_CHOISES: list[tuple[str]] = [
        (STATUS_BETTING, "BETTING"),
        (STATUS_TAKING, "TAKING"),
        (STATUS_STANDING, "STANDING"),
        (STATUS_EXCEEDED, "EXCEEDED"),
        (STATUS_LOST, "LOST"),
        (STATUS_WON, "WON"),
        (STATUS_TIE, "TIE"),
    ]

    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="gameplays"
    )
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="gameplays"
    )
    player_bet = models.IntegerField(validators=[MinValueValidator(1)])
    player_status = models.CharField(
        max_length=8, choices=STATUS_CHOISES, default=STATUS_BETTING
    )
    player_cards = ArrayField(models.CharField(max_length=5), null=True)

    class Meta:
        managed = False
        db_table = "gameplays"
        constraints = [
            models.UniqueConstraint(
                fields=["game", "player"], name="game_player_unique"
            )
        ]
        verbose_name = "Gameplay"
        verbose_name_plural = "Gameplays"

    def __str__(self) -> str:
        return f"Gameplay of {self.player} in {self.game}"
