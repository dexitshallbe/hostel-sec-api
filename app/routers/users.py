from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_roles, AuthedUser
from app.security import hash_password
from db.models import User, Site

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    org_id: int
    site_id: int | None = None
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=4, max_length=128)
    role: str = "GUARD"  # ADMIN/SUPERVISOR/GUARD


class UserOut(BaseModel):
    id: int
    org_id: int
    site_id: int | None
    name: str
    email: EmailStr
    role: str
    is_active: bool


@router.post("", response_model=UserOut)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    au: AuthedUser = Depends(require_roles("ADMIN")),
):
    # if site_id given, ensure site exists
    if payload.site_id is not None:
        site = db.get(Site, payload.site_id)
        if not site:
            raise HTTPException(400, "Invalid site_id")

    existing = db.query(User).filter(User.org_id == payload.org_id, User.email == payload.email).first()
    if existing:
        raise HTTPException(409, "User already exists")

    u = User(
        org_id=payload.org_id,
        site_id=payload.site_id,
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return UserOut(
        id=u.id,
        org_id=u.org_id,
        site_id=u.site_id,
        name=u.name,
        email=u.email,
        role=u.role,
        is_active=u.is_active,
    )


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    au: AuthedUser = Depends(require_roles("ADMIN", "SUPERVISOR")),
):
    rows = db.query(User).order_by(User.id.asc()).all()
    return [
        UserOut(
            id=u.id,
            org_id=u.org_id,
            site_id=u.site_id,
            name=u.name,
            email=u.email,
            role=u.role,
            is_active=u.is_active,
        )
        for u in rows
    ]