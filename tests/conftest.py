import os

import pytest

from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import app
from database import Base, get_db

# Важно: импортируем модели,
# чтобы SQLAlchemy знал обо всех таблицах
from models import Task, User


load_dotenv()


TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL"
)

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


if not TEST_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL не найден в .env"
    )


# Защита от случайного запуска тестов
# на основной базе
if TEST_DATABASE_URL == DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL не должен совпадать "
        "с DATABASE_URL"
    )


test_engine = create_engine(
    TEST_DATABASE_URL
)


TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db

    finally:
        db.close()


app.dependency_overrides[
    get_db
] = override_get_db


@pytest.fixture(autouse=True)
def prepare_database():
    """
    Перед каждым тестом создаём чистые таблицы.
    После теста удаляем их.
    """

    Base.metadata.drop_all(
        bind=test_engine
    )

    Base.metadata.create_all(
        bind=test_engine
    )

    yield

    Base.metadata.drop_all(
        bind=test_engine
    )


@pytest.fixture
def client():
    """
    Тестовый клиент FastAPI.
    """

    with TestClient(app) as test_client:
        yield test_client