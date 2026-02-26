from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_roles, AuthedUser
from app.schemas import SiteCreate, SiteOut
from db.models import Site

router = APIRouter(prefix="/sites", tags=["sites"])


@router.post("", response_model=SiteOut)
def create_site(
    payload: SiteCreate,
    db: Session = Depends(get_db),
    au: AuthedUser = Depends(require_roles("ADMIN", "SUPERVISOR")),
):
    site = Site(org_id=payload.org_id, name=payload.name)
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


@router.get("", response_model=list[SiteOut])
def list_sites(
    db: Session = Depends(get_db),
    au: AuthedUser = Depends(require_roles("ADMIN", "SUPERVISOR", "GUARD")),
):
    if au.user.role == "GUARD":
        if au.site_id is None:
            return []
        return db.query(Site).filter(Site.id == au.site_id).order_by(Site.id.asc()).all()
    return db.query(Site).order_by(Site.id.asc()).all()


@router.get("/{site_id}", response_model=SiteOut)
def get_site(
    site_id: int,
    db: Session = Depends(get_db),
    au: AuthedUser = Depends(require_roles("ADMIN", "SUPERVISOR", "GUARD")),
):
    if au.user.role == "GUARD":
        if au.site_id is None:
            return []
        return db.query(Site).filter(Site.id == au.site_id).order_by(Site.id.asc()).all()
    return db.query(Site).order_by(Site.id.asc()).all()