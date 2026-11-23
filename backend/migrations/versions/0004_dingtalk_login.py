"""账号增加钉钉身份字段。

Revision ID: 0004_dingtalk_login
Revises: 0003_skill_comment
Create Date: 2026-11-19
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_dingtalk_login"
down_revision = "0003_skill_comment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("app_user", sa.Column("dingtalk_union_id", sa.String(64), nullable=True))
    op.add_column("app_user", sa.Column("dingtalk_user_id", sa.String(64), nullable=True))
    op.create_index("ix_app_user_dingtalk_union_id", "app_user", ["dingtalk_union_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_app_user_dingtalk_union_id", table_name="app_user")
    op.drop_column("app_user", "dingtalk_user_id")
    op.drop_column("app_user", "dingtalk_union_id")
