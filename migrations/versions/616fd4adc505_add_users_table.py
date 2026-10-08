"""Duplicate users migration - kept for migration history.

Revision ID: 616fd4adc505
Revises: 8bcd20f3d2dc
Create Date: 2026-08-29 13:24:25.429619
"""

from typing import Sequence, Union


revision: str = "616fd4adc505"
down_revision: Union[str, Sequence[str], None] = "8bcd20f3d2dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass