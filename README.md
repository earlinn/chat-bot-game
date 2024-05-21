# Black Jack Telegram Bot

![Static Badge](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue) 
![Static Badge](https://img.shields.io/badge/aiohttp-%232C5BB4.svg?&style=for-the-badge&logo=aiohttp&logoColor=white)
![Static Badge](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![Static Badge](https://img.shields.io/badge/Swagger-85EA2D?style=for-the-badge&logo=Swagger&logoColor=white)
![Static Badge](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Static Badge](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white) 
![Static Badge](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white) 
![Static Badge](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Телеграм-бот, которого можно добавить в телеграм-чат, чтобы играть в этом чате
в игру Блэк Джек.

# Локальный запуск в Docker Compose

Предварительные условия:
- на компьютере должен быть установлен [Docker Compose](https://docs.docker.com/compose/);
- у вас должен быть свой телеграм-бот (можно создать его в BotFather), т.к. его токен
нужно будет скопировать в файл .env

## Клонирование репозитория, создание контейнеров и первоначальная сборка

_Важно: при работе в Linux или через терминал WSL2 все команды docker и docker compose нужно выполнять от имени суперпользователя — начинайте их с sudo._

Склонировать репозиторий на свой компьютер и перейти в него:
```
git git@github.com:earlinn/chat-bot-game.git
cd chat-bot-game
```

Создать в корневой папке файл .env с необходимыми переменными окружения.

Пример содержимого файла:
```
BOT_TOKEN=<токен вашего бота>
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

Запустить сборку контейнеров с помощью docker compose: 
```
docker compose up -d --build
```

После этого будут созданы и запущены в фоновом режиме контейнеры c postgres, app и nginx.

## Остановка и повторный запуск контейнеров

Для остановки работы приложения можно набрать в терминале команду Ctrl+C или открыть
второй терминал и выполнить команду:
```
docker compose stop 
```

Снова запустить контейнеры без их пересборки можно командой:
```
docker compose start 
```

# Админка в Swagger

При запуске в Docker Compose Админка открывается в Swagger по адресу http://localhost/docs

Все эндпойнты Админки, кроме /admin.login, требуют авторизации.
Чтобы авторизоваться, нужно отправить POST-запрос на эндпойнт /admin.login, 
указав email admin@admin.com и password: admin (как в файле etc/config.yml).

После этого в Админке можно будет просматривать и создавать игроков, их балансы и игры.
