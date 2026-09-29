# StudyFlow Bot

StudyFlow — учебный backend-проект для управления задачами через FastAPI и Telegram-бота.

Проект позволяет создавать и редактировать задачи, отслеживать их выполнение, а также использовать локальную AI-модель через Ollama для генерации и перепланирования учебных или рабочих планов.

## Возможности

- регистрация и авторизация пользователей;
- JWT-аутентификация;
- создание задач;
- просмотр списка задач;
- изменение задач;
- удаление задач;
- изменение статуса задачи;
- работа с приоритетами;
- установка дедлайнов;
- Telegram-бот на Aiogram;
- привязка Telegram-аккаунта к пользователю StudyFlow;
- просмотр и управление задачами через Telegram;
- AI-генерация плана;
- сохранение AI-задач в PostgreSQL;
- AI-перепланирование существующих задач;
- локальная работа AI через Ollama;
- миграции базы данных через Alembic;
- автоматические тесты через Pytest.

## Технологии

### Backend

- Python 3.12
- FastAPI
- Uvicorn
- SQLAlchemy 2.0
- PostgreSQL
- Alembic
- Pydantic
- PyJWT
- pwdlib

### Telegram

- Aiogram 3

### AI

- Ollama
- локальная LLM

### Тестирование

- Pytest
- HTTPX

## Структура проекта

```text
studyflow/
│
├── bot/
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── common.py
│   │   ├── auth.py
│   │   ├── tasks.py
│   │   ├── ai.py
│   │   └── profile.py
│   │
│   ├── bot.py
│   ├── keyboards.py
│   └── states.py
│
├── routers/
│   ├── auth.py
│   ├── tasks.py
│   └── ai.py
│
├── services/
│   └── ai_service.py
│
├── tests/
│   ├── conftest.py
│   ├── test_ai.py
│   ├── test_auth.py
│   ├── test_bot.py
│   ├── test_system.py
│   └── test_tasks.py
│
├── migrations/
│
├── app.py
├── database.py
├── dependencies.py
├── models.py
├── schemas.py
├── security.py
├── alembic.ini
├── pytest.ini
├── requirements.txt
├── .env.example
└── README.md
```

## Установка

Клонируйте репозиторий:

```bash
git clone <repository-url>
cd studyflow
```

Создайте виртуальное окружение:

```bash
python -m venv .venv
```

Linux:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

Установите зависимости:

```bash
pip install -r requirements.txt
```

## Настройка окружения

Создайте файл `.env` на основе `.env.example`.

Пример:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/studyflow
JWT_SECRET=your-secret-key
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_PROXY=
```

Настоящие пароли, токены и секретные ключи не должны попадать в GitHub.

## PostgreSQL

Создайте базу данных PostgreSQL для StudyFlow.

После настройки `DATABASE_URL` примените миграции:

```bash
alembic upgrade head
```

## Запуск API

```bash
python -m uvicorn app:app --reload
```

После запуска Swagger-документация будет доступна по адресу:

```text
http://127.0.0.1:8000/docs
```

Проверка состояния API:

```text
http://127.0.0.1:8000/health
```

## Запуск Ollama

Установите Ollama и загрузите совместимую модель.

Например:

```bash
ollama pull qwen2.5:3b
```

Запустите Ollama:

```bash
ollama serve
```

AI-функции StudyFlow используют локальную модель и не требуют передачи пользовательских задач во внешний AI API.

## Запуск Telegram-бота

После настройки `TELEGRAM_BOT_TOKEN`:

```bash
python -m bot.bot
```

При успешном подключении:

```text
🤖 StudyFlow Bot запускается...
✅ Подключение к Telegram успешно
```

Если доступ к Telegram осуществляется через proxy, укажите его в `.env`:

```env
TELEGRAM_PROXY=http://127.0.0.1:10809
```

## AI-план

Пользователь может указать:

- цель;
- количество задач;
- количество дней.

AI создаёт структурированный план с:

- названием задачи;
- описанием;
- приоритетом;
- дедлайном.

После предварительного просмотра пользователь может сохранить задачи в PostgreSQL.

## AI-перепланирование

StudyFlow может получить незавершённые задачи пользователя и создать новый порядок выполнения.

AI может изменить:

- последовательность задач;
- приоритеты.

StudyFlow самостоятельно проверяет идентификаторы задач и назначает новые дедлайны.

AI не должен создавать или удалять существующие задачи во время перепланирования.

## Тестирование

Запуск всех тестов:

```bash
pytest -v
```

Проект содержит тесты для:

- системных эндпоинтов;
- авторизации;
- CRUD задач;
- AI-функций;
- Telegram-клавиатур и callback-данных.

## Безопасность

В Git-репозиторий не должны попадать:

```text
.env
.venv/
__pycache__/
.pytest_cache/
```

Для примера переменных окружения используется `.env.example`.

## Цель проекта

StudyFlow создан как pet-project для практики backend-разработки на Python.

В проекте применяются:

- REST API;
- реляционная база данных;
- миграции;
- авторизация;
- Telegram-интерфейс;
- конечные автоматы состояний;
- локальная LLM;
- тестирование;
- разделение проекта на роутеры и сервисы.

## Дальнейшее развитие

Планируется:

- Docker и Docker Compose;
- развёртывание на сервере;
- работа Telegram-бота 24/7;
- улучшение обработки ошибок;
- расширение AI-функций;
- дополнительные тесты.