# 📌 ToDo List Backend (Django + DRF + Celery)

Бэкенд-сервис для управления задачами (ToDo List) с поддержкой категорий, пользователей и уведомлений о сроках выполнения.  
Реализован на **Django**, **Django REST Framework**, с асинхронными задачами на **Celery** и хранением данных в **PostgreSQL**.  
Сервис упакован в Docker и использует **Poetry** для управления зависимостями.

---

## 🚀 Возможности

- CRUD-операции для задач и категорий через REST API
- Привязка задач к конкретным пользователям
- Отображение даты создания задачи
- Уведомления о наступлении срока выполнения через Celery
- Административная панель для управления задачами и категориями
- Часовой пояс сервера по умолчанию: `America/Adak`
- Использование кастомных идентификаторов (без UUID, random, автоинкремента)

---

## 📂 Стек технологий

- Python 3.11
- Django 5 + Django REST Framework
- PostgreSQL
- Celery + Redis
- Poetry
- Docker + Docker Compose
- Gunicorn (продакшн WSGI-сервер)

---

## 📦 Установка и запуск

### 1. Клонирование репозитория

```bash
git clone https:github.com/<ваш_репозиторий>.git
cd <ваш_репозиторий>
```

### 2. Настройка переменных окружения

Скопируйте пример файла окружения и при необходимости измените значения:

```bash
cp .env.example .env
```

Пример `.env`:

```
# Django
SECRET_KEY=change-me
DEBUG=1
ALLOWED_HOSTS=*

# База данных
POSTGRES_DB=todo
POSTGRES_USER=todo
POSTGRES_PASSWORD=todo

# Celery/Redis
CELERY_BROKER_URL=redis:redis:6379/0
CELERY_RESULT_BACKEND=redis:redis:6379/1

# Часовой пояс
TZ=America/Adak
```

### 3. Экспорт зависимостей Poetry в requirements.txt

(Только если собираете образ Docker)

```bash
poetry self add poetry-plugin-export
poetry export -f requirements.txt -o backend/requirements.txt --without-hashes
```

### 4. Сборка и запуск контейнеров

```bash
docker compose build
docker compose up -d
```

### 5. Миграции базы данных

```bash
docker compose exec backend python manage.py migrate
```

### 6. Создание суперпользователя

```bash
docker compose exec backend python manage.py createsuperuser
```

---

## 📜 Доступ к сервису

- API (DRF): http:localhost:8000/api/
- Админ-панель: http:localhost:8000/admin/

---

## 🛠 Разработка

### Локальный запуск (без Docker)

```bash
poetry install
poetry run python manage.py migrate
poetry run python manage.py runserver
```

---

## 🔔 Уведомления о сроках

- При создании или обновлении задачи с полем `due_at` Celery планирует выполнение задачи на указанное время.
- Когда срок наступает, Celery отправляет уведомление (в связанный телеграм-бот или другой канал).

---

## 📌 Структура проекта

```
crud-django-service/
├── src/
│   └── __init__.py
├── Makefile
├── poetry.lock
├── pyproject.toml
├── README.md
└── ruff.toml
```

---

## ⚠ Возможные проблемы

- **invalid HTTP_HOST header** — добавьте хост в `ALLOWED_HOSTS` или установите `*` для разработки
- **Проблемы с миграциями** — убедитесь, что приложение `todo` добавлено в `INSTALLED_APPS`
- **Celery не запускается** — проверьте, что Redis работает и переменные `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` указаны верно

---

## 📄 Лицензия

MIT License
