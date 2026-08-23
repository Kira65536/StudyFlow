from sqlalchemy import String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class Task(Base):
    __tablename__="tasks"
    id: Mapped[int]=mapped_column(
        primary_key=True,
        autoincrement=True
    )

    title: Mapped[str]=mapped_column(
        String(200),
        nullable=False
    )

    description: Mapped[str]=mapped_column(
        Text,
        default=""
    )

    priority: Mapped[str]=mapped_column(
        String(20),
        default="medium",
    )

    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )