"""新增技能评论表。

Revision ID: 0003_skill_comment
Revises: 0002_username_email
Create Date: 2026-11-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_skill_comment"
down_revision = "0002_username_email"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skill_comment",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "skill_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("skill.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("app_user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("author_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_skill_comment_skill_id", "skill_comment", ["skill_id"])
    op.create_index("ix_skill_comment_created_at", "skill_comment", ["created_at"])


def downgrade() -> None:
    op.drop_table("skill_comment")
