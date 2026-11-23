"""加宽账号用户名字段，支持邮箱。

Revision ID: 0002_username_email
Revises: 0001_initial
Create Date: 2026-11-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_username_email"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("app_user", "username", type_=sa.String(255), existing_type=sa.String(64), existing_nullable=False)


def downgrade() -> None:
    op.alter_column("app_user", "username", type_=sa.String(64), existing_type=sa.String(255), existing_nullable=False)