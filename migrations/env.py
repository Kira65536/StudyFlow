from logging.config import fileConfig
from alembic import context
from database import engine, Base
import models

# Получаем конфигурацию Alembic
config = context.config
#Подключаем настройки логирования из alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Передаём Alembic информацию о моделях SQLAlchemy
target_metadata = Base.metadata

def run_migrations_offline():
    # Получаем адрес PostgreSQL
    url = str(engine.url)
    #В offline-режиме Alembic не подключается
    # напрямую к БД, а генерирует SQL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
    )

    #Запускаем миграцию
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    #Создаём реальное подключение к PostgreSQL
    with engine.connect() as connection:
        #Здесь literal_binds НЕ нужен
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        #Запускаем миграцию
        with context.begin_transaction():
            context.run_migrations()

#Проверяем, в каком режиме работает Alembic
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()