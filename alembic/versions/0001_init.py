"""init schema

Revision ID: 0001_init
Revises:
Create Date: 2026-02-24

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "sites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("org_id", "name", name="uq_sites_org_name"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="GUARD"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("org_id", "email", name="uq_users_org_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("api_key_hash", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False, server_default="edge-agent"),
        sa.Column("version", sa.String(length=50), nullable=True),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_agents_site_id", "agents", ["site_id"])

    op.create_table(
        "cameras",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("stream_url", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("site_id", "name", name="uq_cameras_site_name"),
    )
    op.create_index("ix_cameras_site_id", "cameras", ["site_id"])
    op.create_index("ix_cameras_enabled", "cameras", ["enabled"])

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("camera_id", sa.Integer(), sa.ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ts", sa.DateTime(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("person_name", sa.String(length=200), nullable=True),
        sa.Column("similarity", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
        sa.Column("decision", sa.String(length=32), nullable=True),
        sa.Column("handled_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("handled_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_events_ts", "events", ["ts"])
    op.create_index("ix_events_camera_ts", "events", ["camera_id", "ts"])
    op.create_index("ix_events_status", "events", ["status"])

    op.create_table(
        "evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("image_key", sa.Text(), nullable=False),
        sa.Column("thumb_key", sa.Text(), nullable=True),
        sa.Column("annotations_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_evidence_event_id", "evidence", ["event_id"])

    op.create_table(
        "guests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("contact", sa.String(length=100), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("folder_key", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_guests_site_id", "guests", ["site_id"])
    op.create_index("ix_guests_expires_at", "guests", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_guests_expires_at", table_name="guests")
    op.drop_index("ix_guests_site_id", table_name="guests")
    op.drop_table("guests")

    op.drop_index("ix_evidence_event_id", table_name="evidence")
    op.drop_table("evidence")

    op.drop_index("ix_events_status", table_name="events")
    op.drop_index("ix_events_camera_ts", table_name="events")
    op.drop_index("ix_events_ts", table_name="events")
    op.drop_table("events")

    op.drop_index("ix_cameras_enabled", table_name="cameras")
    op.drop_index("ix_cameras_site_id", table_name="cameras")
    op.drop_table("cameras")

    op.drop_index("ix_agents_site_id", table_name="agents")
    op.drop_table("agents")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.drop_table("sites")
    op.drop_table("organizations")