# Timer time
TIMER_DELAY_IN_SECONDS = 1  # TODO: change to 30 seconds

# URLs
GAME_RULES_URL = "https://ru.wikihow.com/играть-в-блэкджек"

# Messages
WELCOME_MESSAGE = "Добро пожаловать в бот для игры в Блэк Джек!"
WELCOME_WAITING_MESSAGE = (
    "Добро пожаловать в бот для игры в Блэк Джек!\n"
    "В настоящее время в этом чате уже идет игра. "
    "Чтобы сыграть, пожалуйста, дождитесь окончания текущей игры."
)
WAITING_MESSAGE = (
    "В настоящее время в этом чате уже идет игра. "
    "Чтобы сыграть, пожалуйста, дождитесь окончания текущей игры."
)
START_TIMER_MESSAGE = (
    "Начинаем новую игру. Чтобы присоединиться к игре, нажмите на кнопку ниже "
    f"в течение {TIMER_DELAY_IN_SECONDS} секунд."
)
JOINED_GAME_MESSAGE = "{username} в игре"
JOIN_NON_EXISTENT_GAME_ERROR = (
    "На данный момент ни одна игра не запущена. Чтобы запустить новую игру, "
    "вызовите игрового бота командой 'start', затем нажмите на кнопку "
    "'Начать новую игру'."
)
END_TIMER_MESSAGE = (
    "Игра началась.\nИгроки: {players}\n"
    "Каждый игрок должен сделать ставку, нажав на одну из кнопок ниже. "
    "Ставка делается один раз за игру и не может быть изменена."
)
PLAYER_HAVE_BET_MESSAGE = "{player} ставит {bet} очков."
GAME_PLAYERHIT_STAGE_MESSAGE = (
    "Ставки сделаны. "
    "Теперь вы можете взять себе карту или отказаться брать новые карты.\n\n"
    "Карты на руках:\n\n{cards_str}"
)
PLAYER_EXCEEDED_MESSAGE = "У {player} более 21 очка, на руках: {cards}"
PLAYER_NOT_EXCEEDED_MESSAGE = "{player} берет еще карту, на руках: {cards}"
PLAYER_STOP_TAKING_MESSAGE = "{player} больше не берет карты, на руках: {cards}"
PLAYER_EXCEDDED_RESULTS_MESSAGE = (
    "У {player} перебор, на руках: {cards} (в сумме {score}).\n"
    "-{bet} к балансу в этом чате.\n\n"
)
PLAYER_WON_RESULTS_MESSAGE = (
    "{player} выигрывает у диллера, на руках: {cards} (в сумме {score}).\n"
    "+{bet} к балансу в этом чате.\n\n"
)
PLAYER_LOST_RESULTS_MESSAGE = (
    "{player} проигрывает диллеру, на руках: {cards} (в сумме {score}).\n"
    "-{bet} к балансу в этом чате.\n\n"
)
PLAYER_TIE_RESULTS_MESSAGE = (
    "У {player} ничья с диллером, на руках: {cards} (в сумме {score}).\n"
    "Баланс не меняется.\n\n"
)
GAME_RESULTS_MESSAGE = (
    "Итоги игры:\n\n{players}" "Карты диллера: {diller_cards} (в сумме {score})"
)
UNKNOWN_MESSAGE = "Неизвестная команда"

# Cards strings
PLAYER_CARDS_STR = "{username}:  {player_cards}"
DILLER_CARDS_STR = "\nДиллер:  {diller_cards}"

# Buttons
GAME_START_BUTTON = "Начать новую игру"
GAME_JOIN_BUTTON = "Присоединиться к игре"
GAME_RULES_BUTTON = "Посмотреть правила игры"
GAME_ONE_MORE_TIME_BUTTON = "Сыграть еще раз"
BET_10_BUTTON = "10💰"
BET_25_BUTTON = "25💰"
BET_50_BUTTON = "50💰"
BET_100_BUTTON = "100💰"
TAKE_CARD_BUTTON = "Взять карту"
STOP_TAKING_BUTTON = "Достаточно карт"

# Callback query names
JOIN_GAME_CALLBACK = "join_new_game"
ADD_PLAYER_CALLBACK = "add_player"
BET_10_CALLBACK = "make_bet_10"
BET_25_CALLBACK = "make_bet_25"
BET_50_CALLBACK = "make_bet_50"
BET_100_CALLBACK = "make_bet_100"
TAKE_CARD_CALLBACK = "take_card"
STOP_TAKING_CALLBACK = "stop_taking"
