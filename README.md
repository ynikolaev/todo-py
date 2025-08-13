# ToDo List — Django API + Celery + Telegram Bot

Этот проект предоставляет **бэкенд ToDo-листа** на Django/DRF с **тегированием категорий**, **пользовательскими задачами**, **кастомными детерминированными идентификаторами** и **уведомлениями о сроках выполнения** через Celery. **Telegram-бот** (Aiogram + aiogram-dialog) позволяет пользователям просматривать и добавлять задачи через чат. Все сервисы запускаются через **Docker Compose** (Django, PostgreSQL, Redis, Celery worker/beat, бот).

---

## Возможности

- **Django + DRF API** для задач и категорий (CRUD, изоляция по пользователям)
- **Отображение даты создания задачи** (видно в боте)
- **Категории/теги** и флаг **выполнения задачи**
- **Уведомления о сроках** через Telegram-бота
- **Админка** для управления задачами и категориями
- **Часовой пояс по умолчанию:** `America/Adak`
- **Кастомные первичные ключи** (Snowflake-стиль, строки, сортируемые по времени; без UUID, случайных значений и автоинкремента БД)

---

## Требования

- **Docker** ≥ 20.10
- **Docker Compose** ≥ 1.29
- **Make** (опционально, если используете Makefile)
- **Токен Telegram-бота** от @BotFather

---

## Запуск (разработка)

1. Создайте и заполните `.env` (пример):

```env
# Django
SECRET_KEY=change-me
DEBUG=1
ALLOWED_HOSTS=*

# Database
POSTGRES_DB=todo
POSTGRES_USER=todo
POSTGRES_PASSWORD=todo

# Celery/Redis
CELERY_BROKER_URL=redis:redis:6379/0
CELERY_RESULT_BACKEND=redis:redis:6379/1

# Bot
BOT_TOKEN=123456:ABC-DEF
BOT_SHARED_SECRET=supersecret
BOT_INTERNAL_URL=http:bot:8080/internal/notify

# Timezone
TZ=America/Adak
```

2. (Если используете Poetry) экспортируйте зависимости для сборки Docker:

```bash
poetry self add poetry-plugin-export
poetry export -f requirements.txt -o backend/requirements.txt --without-hashes
```

3. Соберите и запустите:

```bash
docker compose build
docker compose up -d
```

4. Инициализация базы:

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

---

## Доступ

- **API (DRF):** http:localhost:8000/api/
- **Админка:** http:localhost:8000/admin
- **Telegram:** отправьте `/start`, `/list`, `/add` своему боту

---

## Обзор API (бэкенд)

- `GET /api/tasks/` — список задач пользователя (с `created_at`, категориями)
- `POST /api/tasks/` — создание задачи (`title`, опционально `description`, `due_at`, `category_ids`)
- `PATCH /api/tasks/{id}/` — обновление задачи
- `DELETE /api/tasks/{id}/` — удаление задачи
- `GET/POST /api/categories/` — управление категориями
- `POST /api/auth/telegram/` — авторизация бота (получение токена DRF по данным пользователя Telegram)

**Аутентификация:** токен (`Authorization: Token <token>`). Бот получает и хранит токен автоматически при `/start`.

---

## Уведомления

- Если у задачи установлено `due_at`, бэкенд планирует выполнение задачи в Celery с `eta=due_at`.
- В указанное время Celery вызывает внутренний эндпоинт бота, который отправляет пользователю сообщение **«Задача к выполнению»**.

---

## Заметки по окружению

- **Часовой пояс** установлен в `America/Adak` на уровне приложения и контейнера.
- При передаче `due_at` предпочтительно использовать **ISO 8601 с временной зоной** (например, `2025-08-20T12:00:00-09:00`).

---

## Заметки по разработке

- Django запускается через **Gunicorn** в контейнере; команды `manage.py` выполняются через `docker compose exec backend …`.
- Бот использует **Aiogram + aiogram-dialog** и взаимодействует с API через сеть Docker.
- Для масштабирования бота или воркера можно поднять дополнительные реплики и хранить сессии бота в Redis.

---

## Следующие шаги

- Добавить диалоги для создания категорий и завершения задач в боте.
- Реализовать пагинацию и ограничение запросов в API.
- Перевести бота на webhook-режим за reverse-proxy.
- Хранить токены пользователей бота в Redis для горизонтального масштабирования.
