from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_roles, AuthedUser, guard_site_scope
from app.schemas import EventOut, EventActionIn
from app.realtime import broadcaster
from db.models import Event, Camera

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventOut])
def list_events(
    status: str | None = None,
    camera_id: int | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    au: AuthedUser = Depends(require_roles("ADMIN", "SUPERVISOR", "GUARD")),
):
    q = db.query(Event).join(Camera, Event.camera_id == Camera.id)

    if au.user.role == "GUARD":
        if au.site_id is None:
            return []
        q = q.filter(Camera.site_id == au.site_id)
    # else admins can filter by camera_id/status as before

    if status:
        q = q.filter(Event.status == status)
    if camera_id:
        q = q.filter(Event.camera_id == camera_id)

    return q.order_by(Event.ts.desc()).limit(min(limit, 500)).all()


@router.get("/{event_id}", response_model=EventOut)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    au: AuthedUser = Depends(require_roles("ADMIN", "SUPERVISOR", "GUARD")),
):
    ev = db.get(Event, event_id)
    if not ev:
        raise HTTPException(404, "Event not found")
    cam = db.get(Camera, ev.camera_id)
    if not cam:
        raise HTTPException(404, "Camera not found for event")

    guard_site_scope(au, cam.site_id)
    return ev


@router.post("/{event_id}/action", response_model=EventOut)
async def act_on_event(
    event_id: int,
    payload: EventActionIn,
    db: Session = Depends(get_db),
    au: AuthedUser = Depends(require_roles("ADMIN", "SUPERVISOR", "GUARD")),
):
    ev = db.get(Event, event_id)
    if not ev:
        raise HTTPException(404, "Event not found")
    
    cam = db.get(Camera, ev.camera_id)
    if not cam:
        raise HTTPException(404, "Camera not found for event")

    guard_site_scope(au, cam.site_id)

    # Basic validation
    if payload.status == "dealt" and payload.decision not in ("entry_granted", "entry_denied"):
        raise HTTPException(400, "decision required when status=dealt")
    if payload.status != "dealt" and payload.decision is not None:
        raise HTTPException(400, "decision only allowed when status=dealt")

    ev.status = payload.status
    ev.decision = payload.decision
    ev.notes = payload.notes
    ev.handled_by_user_id = au.user.id
    ev.handled_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(ev)

    # Realtime broadcast
    await broadcaster.broadcast(
        {
            "type": "event_updated",
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
            },
        }
    )

    return ev