import enum


class GameStatus(enum.StrEnum):
    ACTIVE = "active"
    FINISHED = "finished"
    INTERRUPTED = "interrupted"


class GameStage(enum.StrEnum):
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
