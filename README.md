# Black Jack Telegram Bot

Телеграм-бот, которого можно добавить в телеграм-чат, чтобы играть в этом чате
в игру Блэк Джек.

# Технологии

![Static Badge](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue) 
![Static Badge](https://img.shields.io/badge/aiohttp-%232C5BB4.svg?&style=for-the-badge&logo=aiohttp&logoColor=white)
![Static Badge](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)
![Static Badge](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![Static Badge](https://img.shields.io/badge/Swagger-85EA2D?style=for-the-badge&logo=Swagger&logoColor=white)
![Static Badge](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Static Badge](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white) 
![Static Badge](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white) 
![Static Badge](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Python 3.12, Telegram Bot API, Aiohttp, Django, SQLAlchemy, Alembic, PostgreSQL, Docker, Nginx, GitHub Actions

# Особенности игры

Каждому новому игроку в чате дается 1000 очков. Игра разрешается даже при отрицательном счете
на балансе игрока. Баланс можно посмотреть в любой момент, нажав на кнопку "Мой баланс"
(другие участники чата его тоже увидят).
Если пользователь играет с ботом сразу в нескольких чатах, у него в каждом чате отдельный баланс.

Также всегда доступна кнопка "Правила игры".

В игре может участвовать одновременно несколько игроков, но в чате может проходить
одновременно только одна игра.

Когда кто-то из участников чата запускает новую игру, начинается стадия присоединения
игроков, и у остальных участников есть возможность присоединиться к этой игре 
в течение определенного времени, пока работает таймер. 
Игрок, запустивший новую игру, автоматически добавляется в нее, и ему можно не
нажимать на кнопку "Присоединиться к игре", хотя если вдруг нажмет, ничего плохого
не случится.
Если кто-то из участников чата не успел присоединиться к игре в течение отведенного
времени, ему нужно будет подождать завершения текущей игры, чтобы запустить новую игру
в данном чате.

Однако бота можно добавить в другой чат и играть с ним в нескольких чатах одновременно.

После стадии присоединения игроков наступает стадия ставок. Она тоже ограничена по времени,
и если все игроки не успеют сделать ставку в течение этого времени, игра будет отменена.

После стадии ставок наступает стадия ходов игроков.
Каждому игроку раздается две карты, а диллеру - одна карта.
Все карты раздаются в открытую, т.к. игроки играют не друг против друга, а все против
диллера.
Если у кого-то из игроков 2 начальные карты составляют БлэкДжек (т.е. туз и карта-картинка),
он не берет себе больше карт.
Если у игрока на начало игры нет на руках БлэкДжека, он может взять еще карту или
отказаться брать. Если игрок отказался брать карты или у него перебор (более 21 очка
суммарно), он больше не может брать новые карты.

После того, как не осталось игроков, берущих новые карты, наступает стадия ходов диллера.
Диллер берет себе по одной карте, пока сумма его очков не достигнет 17.

Затем наступает стадия подведения итогов и выводится сообщение с результатами игры.
Если у игрока перебор очков или нет перебора, но меньше очков, чем у диллера
(и у диллера при этом нет перебора очков), игрок теряет свою ставку.
Если у игрока больше очков, чем у диллера, игрок получает на баланс очки, равные его ставке.
Если у игрока и диллера равное количество очков, значит, он сыграл с диллером вничью,
и все остаются при своих (игрок не теряет и не приобретает очки на балансе).

# Локальный запуск в Docker Compose

Предварительные условия:
- на компьютере должен быть установлен [Docker Compose](https://docs.docker.com/compose/);
- у вас должен быть свой телеграм-бот (можно создать его в BotFather), т.к. его токен
нужно будет скопировать в файл .env

## Клонирование репозитория, создание контейнеров и первоначальная сборка

_Важно: при работе в Linux или через терминал WSL2 все команды docker и docker compose нужно выполнять от имени суперпользователя — начинайте их с sudo._

Склонировать репозиторий на свой компьютер и перейти в него:
```
git clone git@github.com:earlinn/chat-bot-game.git (для клонирования по ssh)
или
git clone https://github.com/earlinn/chat-bot-game.git (для клонирования по https)

cd chat-bot-game
```

Создать в корневой папке файл .env с необходимыми переменными окружения.

Пример содержимого файла:
```
BOT_TOKEN=<токен вашего бота>
POSTGRES_HOST=postgres
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5432
RABBIT_HOST=rabbitmq
RABBIT_USER=guest
RABBIT_PASSWORD=guest
```

Запустить сборку контейнеров с помощью docker compose: 
```
docker compose -f docker-compose.local.yml up -d --build
```

После этого будут созданы и запущены в фоновом режиме контейнеры:
- postgres
- app (телеграм-бот и aiohttp-админка)
- djangoadmin (Django-админка)
- nginx (раздает статику для работы админок)

## Остановка и повторный запуск контейнеров

Для остановки работы приложения можно набрать в терминале команду Ctrl+C или открыть
второй терминал и выполнить команду:
```
docker compose -f docker-compose.local.yml stop 
```

Снова запустить контейнеры без их пересборки можно командой:
```
docker compose -f docker-compose.local.yml start 
```

# Админка

## Админка в Swagger

При запуске в Docker Compose Админка открывается в Swagger по адресу http://localhost/docs

Все эндпойнты Админки, кроме /admin.login, требуют авторизации.
Чтобы авторизоваться, нужно отправить POST-запрос на эндпойнт /admin.login, 
указав email admin@admin.com и password: admin (как в файле etc/config.yml).

После этого в Админке можно будет просматривать и создавать игроков, их балансы и игры.

## Админка Django

Также есть вторая админка - встроенная админка Django.
Она находится по адресу http://localhost/admin/

Перед первым входом создайте Django-админа командой:
```
docker compose -f docker-compose.local.yml exec -it djangoadmin python manage.py createsuperuser
```
