from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_roles, AuthedUser
from app.schemas import CameraCreate, CameraOut
from db.models import Camera

router = APIRouter(prefix="/cameras", tags=["cameras"])


@router.post("", response_model=CameraOut)
def create_camera(
    payload: CameraCreate,
    db: Session = Depends(get_db),
    au: AuthedUser = Depends(require_roles("ADMIN", "SUPERVISOR")),
):
    from app.deps import guard_site_scope
    # admin/supervisor only already; but still validate for consistency:
    # (no guard create)
    cam = Camera(
        site_id=payload.site_id,
        name=payload.name,
        role=payload.role,
        stream_url=payload.stream_url,
        enabled=payload.enabled,
    )
    db.add(cam)
    db.commit()
    db.refresh(cam)
    return cam


@router.get("", response_model=list[CameraOut])
def list_cameras(
    site_id: int | None = None,
    db: Session = Depends(get_db),
    au: AuthedUser = Depends(require_roles("ADMIN", "SUPERVISOR", "GUARD")),
):
    q = db.query(Camera)

    if au.user.role == "GUARD":
        if au.site_id is None:
            return []
        q = q.filter(Camera.site_id == au.site_id)
    elif site_id is not None:
        q = q.filter(Camera.site_id == site_id)

    return q.order_by(Camera.id.asc()).all()


@router.get("/{camera_id}", response_model=CameraOut)
def get_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    au: AuthedUser = Depends(require_roles("ADMIN", "SUPERVISOR", "GUARD")),
):
    cam = db.get(Camera, camera_id)
    if not cam:
        raise HTTPException(404, "Camera not found")
    from app.deps import guard_site_scope
    guard_site_scope(au, cam.site_id)
    return cam