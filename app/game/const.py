import enum

SUITS: tuple[str, str, str, str] = ("♦️", "♠️", "♥️", "♣️")
RANKS: dict[str, int] = {str(number): number for number in range(2, 11)}
RANKS.update({"J": 10, "Q": 10, "K": 10, "A": 11})
CARDS: dict[str, int] = {
    card + suit: rank for card, rank in RANKS.items() for suit in SUITS
}


class GameStatus(enum.StrEnum):
    ACTIVE = "active"
    FINISHED = "finished"
    INTERRUPTED = "interrupted"


class GameStage(enum.StrEnum):
    WAITING_FOR_PLAYERS_TO_JOIN = "waiting_for_players_to_join"
    BETTING = "betting"
    PLAYERHIT = "playerhit"
    DILLERHIT = "dillerhit"
    SUMMARIZING = "summarizing"


class PlayerStatus(enum.StrEnum):
    BETTING = "betting"
    TAKING = "taking"
    STANDING = "standing"
    EXCEEDED = "exceeded"
    LOST = "lost"
    WON = "won"
