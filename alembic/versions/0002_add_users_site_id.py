"""add users.site_id

Revision ID: 0002_add_users_site_id
Revises: 0001_init
Create Date: 2026-02-24
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = "0002_add_users_site_id"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("site_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_users_site_id",
        "users",
        "sites",
        ["site_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_users_site_id", "users", ["site_id"])


def downgrade() -> None:
    op.drop_index("ix_users_site_id", table_name="users")
    op.drop_constraint("fk_users_site_id", "users", type_="foreignkey")
    op.drop_column("users", "site_id")