"""Initial schema

Revision ID: f03e73babe24
Revises: 
Create Date: 2026-08-23 12:59:21.908339

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f03e73babe24'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Создание первоначальной таблицы tasks."""

    op.create_table(
        "tasks",

    # Уникальный ID задачи
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False
        ),

    # Название задачи
        sa.Column(
            "title",
            sa.String(length=200),
            nullable=False
        ),

    # Описание задачи
        sa.Column(
            "description",
            sa.Text(),
            nullable=False
        ),

        # Приоритет задачи
        sa.Column(
            "priority",
            sa.String(length=20),
            nullable=False
        ),

    # Выполнена задача или нет
        sa.Column(
            "completed",
            sa.Boolean(),
            nullable=False
        ),

# Указываем id как PRIMARY KEY
        sa.PrimaryKeyConstraint("id")
    )

def downgrade() -> None:
    """Удаление первоначальной таблицы tasks."""
    op.drop_table("tasks")