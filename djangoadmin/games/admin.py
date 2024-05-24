from django.contrib import admin

from .models import Balance, Game, GamePlay, Player


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ["pk", "username", "first_name", "tg_id"]
    list_display_links = ["first_name"]


@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = ["pk", "chat_id", "player", "current_value"]
    list_display_links = ["chat_id", "player"]


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "chat_id",
        "created_at",
        "status",
        "stage",
        "diller_cards",
    ]
    list_display_links = ["chat_id", "created_at"]


@admin.register(GamePlay)
class GamePlayAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "game",
        "player",
        "player_bet",
        "player_status",
        "player_cards",
    ]
    list_display_links = ["game", "player"]
