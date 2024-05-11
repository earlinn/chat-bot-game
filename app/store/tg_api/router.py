import random
from logging import getLogger

from app.game.const import CARDS, GameStage
from app.game.models import GameModel, GamePlayModel, PlayerModel
from app.store import Store
from app.store.tg_api.dataclasses import CallbackQuery, Chat, Message, Update


class Router:
    """Распределяет обновления (updates) по нужным хендлерам."""

    def __init__(self, store: Store) -> None:
        """Подключается к store и к логгеру."""
        self.store = store
        self.logger = getLogger("bot router")

    async def get_updates(self, updates: list[Update]) -> None:
        """Принимает список updates и по одному отправляет их на обработку."""
        for update in updates:
            await self._process_update(update)

    # TODO: можно выделить из этого метода метод обработки message
    # и метод обработки callback_query (в зависимости от того, какое из этих
    # полей присутствует в update)
    async def _process_update(self, update: Update):
        """Ходит в базу данных и в зависимости от результата вызывает
        различные методы BotManager.
        """
        message: Message | None = update.message
        callback_query: CallbackQuery | None = update.callback_query
        # TODO: а если у callback_query отсутствует поле message?
        # Поле chat_instance тоже не подходит, т.к. chat_instance != chat.id
        chat: Chat = message.chat if message else callback_query.message.chat

        # пытаюсь соблюсти ограничение, что в БД ходим только из слоя Router
        current_chat_game: (
            GameModel | None
        ) = await self.store.games.get_active_game_by_chat_id(chat.id)

        if message and message.text == "/start" and not current_chat_game:
            await self.store.bots_manager.say_hi_and_play(update)
        elif message and message.text == "/start" and current_chat_game:
            await self.store.bots_manager.say_hi_and_wait(chat.id)
        elif (
            callback_query
            and callback_query.data == "start_timer"
            and current_chat_game
        ):
            await self.store.bots_manager.wait_next_game(chat.id)
        elif callback_query and callback_query.data == "start_timer":
            await self.store.bots_manager.start_timer(chat.id)
        elif callback_query and callback_query.data == "add_player":
            # проверка на случай, если присоединение новых игроков уже
            # закончилось, но кто-то нажимает на кнопку "Присоединиться к игре"
            if (
                current_chat_game
                and current_chat_game.stage != GameStage.WAITING
            ):
                await self.store.bots_manager.wait_next_game(chat.id)
            else:
                player: PlayerModel = (  # получаем игрока
                    await self.store.players.get_player_by_tg_id(
                        callback_query.from_.id
                    )
                    or await self.store.players.create_player(
                        username=callback_query.from_.username,
                        tg_id=callback_query.from_.id,
                    )
                )
                self.logger.info("Player: %s", player)
                game: GameModel = (  # получаем игру
                    await self.store.games.get_active_waiting_game_by_chat_id(
                        chat.id
                    )
                    or await self.store.games.create_game(
                        chat_id=chat.id,
                        diller_cards=[random.choice(list(CARDS))],
                    )
                )
                self.logger.info("Game: %s", game)
                # проверка get_gameplay_by_game_and_player на случай, если
                # присоединение новых игроков еще идет, но один и тот же игрок
                # несколько раз нажимает на кнопку "Присоединиться к игре"
                gameplay: GamePlayModel = (  # получаем геймплей этого игрока
                    await self.store.gameplays.get_gameplay_by_game_and_player(
                        game.id, player.id
                    )
                    or await self.store.gameplays.create_gameplay(
                        game_id=game.id, player_id=player.id
                    )
                )
                await self.store.bots_manager.player_joined(
                    chat.id, player.username
                )
                self.logger.info("Gameplay: %s", gameplay)

        else:
            await self.store.bots_manager.unknown_command(chat.id)
