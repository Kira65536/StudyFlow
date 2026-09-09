"""Rename username column

Revision ID: 9a44096b1420
Revises: 616fd4adc505
Create Date: 2026-08-29 14:08:16.725465

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a44096b1420'
down_revision: Union[str, Sequence[str], None] = '616fd4adc505'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "Username",
        new_column_name="username"
    )

def downgrade() -> None:
    op.alter_column(
        "users",
        "username",
        new_column_name="Username"
    )
