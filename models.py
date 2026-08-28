from datetime import datetime
from sqlalchemy import String, Boolean, Text, DateTime
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


# Модель таблицы tasks
class Task(Base):

    # Название таблицы в PostgreSQL
    __tablename__ = "tasks"


    # Уникальный ID задачи
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )


    # Название задачи
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    #Описание задачи
    description: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    #Приоритет задачи
    priority: Mapped[str] = mapped_column(
        String(20),
        default="medium"
    )

    # Старое поле выполнения пока оставляем
    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

#Статус задачи
    status: Mapped[str] = mapped_column(
        String(20),
        default="todo",
        server_default="todo",
        nullable=False
    )

    #Дедлайн задачи может отсутствовать, поэтому Optional

    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    #Дата создания задачи
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    #Дата последнего изменения
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )