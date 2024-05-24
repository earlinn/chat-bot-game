import os
import typing
from dataclasses import dataclass

import yaml

if typing.TYPE_CHECKING:
    from app.web.app import Application


@dataclass
class SessionConfig:
    key: str


@dataclass
class AdminConfig:
    email: str
    password: str


@dataclass
class BotConfig:
    token: str


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "project"


@dataclass
class RabbitConfig:
    host: str
    user: str
    password: str


@dataclass
class Config:
    admin: AdminConfig
    session: SessionConfig | None = None
    bot: BotConfig | None = None
    database: DatabaseConfig | None = None
    rabbit: RabbitConfig | None = None


def setup_config(app: "Application", config_path: str):
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    app.config = Config(
        session=SessionConfig(
            key=raw_config["session"]["key"],
        ),
        admin=AdminConfig(
            email=raw_config["admin"]["email"],
            password=raw_config["admin"]["password"],
        ),
        bot=BotConfig(
            token=os.environ.get("BOT_TOKEN", "token"),
        ),
        database=DatabaseConfig(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=os.environ.get("POSTGRES_PORT", 5432),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
            database=os.environ.get("POSTGRES_DB", "postgres"),
        ),
        rabbit=RabbitConfig(
            host=os.environ.get("RABBIT_HOST", "localhost"),
            user=os.environ.get("RABBIT_USER", "guest"),
            password=os.environ.get("RABBIT_PASSWORD", "guest"),
        ),
    )
