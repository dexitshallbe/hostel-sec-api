import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_roles, AuthedUser
from app.security import hash_password
from app.agent_auth import get_current_agent
from app.realtime import broadcaster
from app.storage import put_evidence_from_b64
from db.models import Agent, Camera, Event, Evidence, Site


router = APIRouter(prefix="/agent", tags=["agent"])


# ---------- Admin creates agents ----------

class AgentCreateIn(BaseModel):
    site_id: int
    name: str = Field(default="edge-agent", max_length=200)
    version: Optional[str] = None


class AgentCreateOut(BaseModel):
    id: int
    site_id: int
    name: str
    version: Optional[str]
    api_key: str  # shown only once


@router.post("/create", response_model=AgentCreateOut)
def admin_create_agent(
    payload: AgentCreateIn,
    db: Session = Depends(get_db),
    au: AuthedUser = Depends(require_roles("ADMIN", "SUPERVISOR")),
):
    site = db.get(Site, payload.site_id)
    if not site:
        raise HTTPException(400, "Invalid site_id")

    api_key_plain = secrets.token_urlsafe(32)
    ag = Agent(
        site_id=payload.site_id,
        name=payload.name,
        version=payload.version,
        api_key_hash=hash_password(api_key_plain),
        created_at=datetime.now(timezone.utc),
    )
    db.add(ag)
    db.commit()
    db.refresh(ag)

    return AgentCreateOut(
        id=ag.id,
        site_id=ag.site_id,
        name=ag.name,
        version=ag.version,
        api_key=api_key_plain,
    )


# ---------- Edge agent operations ----------

class CameraConfigOut(BaseModel):
    id: int
    site_id: int
    name: str
    role: str
    stream_url: Optional[str]
    enabled: bool


@router.get("/config", response_model=list[CameraConfigOut])
def agent_config(
    db: Session = Depends(get_db),
    ag: Agent = Depends(get_current_agent),
):
    cams = (
        db.query(Camera)
        .filter(Camera.site_id == ag.site_id)
        .order_by(Camera.id.asc())
        .all()
    )
    return [
        CameraConfigOut(
            id=c.id,
            site_id=c.site_id,
            name=c.name,
            role=c.role,
            stream_url=c.stream_url,
            enabled=c.enabled,
        )
        for c in cams
    ]


class AgentEventIn(BaseModel):
    camera_id: int
    ts: Optional[datetime] = None
    type: str
    person_name: Optional[str] = None
    similarity: Optional[float] = None

    # optional evidence frame as base64 JPG
    evidence_b64: Optional[str] = None

    # initial status usually "open"
    status: str = "open"


class AgentEventOut(BaseModel):
    id: int
    camera_id: int
    ts: datetime
    type: str
    person_name: Optional[str]
    similarity: Optional[float]
    status: str
    evidence_key: Optional[str] = None


@router.post("/events", response_model=AgentEventOut)
async def agent_push_event(
    payload: AgentEventIn,
    db: Session = Depends(get_db),
    ag: Agent = Depends(get_current_agent),
):
    cam = db.get(Camera, payload.camera_id)
    if not cam or cam.site_id != ag.site_id:
        raise HTTPException(403, "Camera not allowed for this agent")
    if not cam.enabled:
        raise HTTPException(400, "Camera disabled")

    ts = payload.ts or datetime.now(timezone.utc)

    ev = Event(
        camera_id=payload.camera_id,
        ts=ts,
        type=payload.type,
        person_name=payload.person_name,
        similarity=payload.similarity,
        status=payload.status,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    evidence_key = None
    if payload.evidence_b64:
        evidence_key = put_evidence_from_b64(payload.evidence_b64, prefix="evidence")
        if evidence_key:
            evid = Evidence(event_id=ev.id, image_key=evidence_key, thumb_key=None, annotations_json=None)
            db.add(evid)
            db.commit()

    # broadcast full payload so guard dashboard updates instantly
    await broadcaster.broadcast(
        {
            "type": "event_created",
            "event": {
                "id": ev.id,
                "camera_id": ev.camera_id,
                "ts": ev.ts.isoformat(),
                "type": ev.type,
                "person_name": ev.person_name,
                "similarity": ev.similarity,
                "status": ev.status,
                "decision": ev.decision,
                "handled_by_user_id": ev.handled_by_user_id,
                "handled_at": ev.handled_at.isoformat() if ev.handled_at else None,
                "notes": ev.notes,
                "evidence_key": evidence_key,
            },
        }
    )

    return AgentEventOut(
        id=ev.id,
        camera_id=ev.camera_id,
        ts=ev.ts,
        type=ev.type,
        person_name=ev.person_name,
        similarity=ev.similarity,
        status=ev.status,
        evidence_key=evidence_key,
    )