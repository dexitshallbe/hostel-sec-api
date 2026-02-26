from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    String, Text, DateTime, Boolean, ForeignKey,
    Integer, Float, UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    sites: Mapped[list["Site"]] = relationship(back_populates="org", cascade="all, delete-orphan")
    users: Mapped[list["User"]] = relationship(back_populates="org", cascade="all, delete-orphan")


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    org: Mapped["Organization"] = relationship(back_populates="sites")
    cameras: Mapped[list["Camera"]] = relationship(back_populates="site", cascade="all, delete-orphan")
    agents: Mapped[list["Agent"]] = relationship(back_populates="site", cascade="all, delete-orphan")
    guests: Mapped[list["Guest"]] = relationship(back_populates="site", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("org_id", "name", name="uq_sites_org_name"),
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    # ✅ add this: guards can be scoped to a site
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id", ondelete="SET NULL"), nullable=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[str] = mapped_column(String(32), nullable=False, default="GUARD")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    org: Mapped["Organization"] = relationship(back_populates="users")

    __table_args__ = (
        UniqueConstraint("org_id", "email", name="uq_users_org_email"),
        Index("ix_users_email", "email"),
        Index("ix_users_site_id", "site_id"),  # ✅ add index
    )


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)

    # You’ll store only a hash of the agent API key later.
    api_key_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False, default="edge-agent")
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    site: Mapped["Site"] = relationship(back_populates="agents")

    __table_args__ = (
        Index("ix_agents_site_id", "site_id"),
    )


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # entry / exit
    role: Mapped[str] = mapped_column(String(16), nullable=False)

    # stream URL should be encrypted later; MVP keeps plain text but nullable
    stream_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    site: Mapped["Site"] = relationship(back_populates="cameras")
    events: Mapped[list["Event"]] = relationship(back_populates="camera", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("site_id", "name", name="uq_cameras_site_name"),
        Index("ix_cameras_site_id", "site_id"),
        Index("ix_cameras_enabled", "enabled"),
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False)

    ts: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    # entry / exit / unknown / etc (keep flexible)
    type: Mapped[str] = mapped_column(String(32), nullable=False)

    # recognized person name (optional)
    person_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    similarity: Mapped[float | None] = mapped_column(Float, nullable=True)

    # open / ignored / dealt
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")

    # entry_granted / entry_denied (only meaningful after dealt)
    decision: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # for later: which user handled it
    handled_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    camera: Mapped["Camera"] = relationship(back_populates="events")
    evidence_items: Mapped[list["Evidence"]] = relationship(back_populates="event", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_events_ts", "ts"),
        Index("ix_events_camera_ts", "camera_id", "ts"),
        Index("ix_events_status", "status"),
    )


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False)

    # object storage keys (S3/MinIO)
    image_key: Mapped[str] = mapped_column(Text, nullable=False)
    thumb_key: Mapped[str | None] = mapped_column(Text, nullable=True)

    # bbox + face boxes + extra metadata
    annotations_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    event: Mapped["Event"] = relationship(back_populates="evidence_items")

    __table_args__ = (
        Index("ix_evidence_event_id", "event_id"),
    )


class Guest(Base):
    __tablename__ = "guests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact: Mapped[str | None] = mapped_column(String(100), nullable=True)

    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # later: where their embeddings/images live
    folder_key: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    site: Mapped["Site"] = relationship(back_populates="guests")

    __table_args__ = (
        Index("ix_guests_site_id", "site_id"),
        Index("ix_guests_expires_at", "expires_at"),
    )