from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import LoginIn, RefreshIn, TokenPair, MeOut
from app.security import verify_password, create_access_token, create_refresh_token, decode_token, is_refresh
from app.deps import get_current_user, AuthedUser
from db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


def _sub_for_user(user: User) -> str:
    # Admins/supervisors are unscoped
    if user.role in ("ADMIN", "SUPERVISOR"):
        return f"{user.id}:none"
    # Guards are scoped to their assigned site
    if user.site_id is None:
        return f"{user.id}:none"
    return f"{user.id}:{user.site_id}"


@router.post("/login", response_model=TokenPair)
def login(
    db: Session = Depends(get_db),
    form: OAuth2PasswordRequestForm = Depends(),
):
    # Swagger sends: username + password (form-encoded)
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    sub = _sub_for_user(user)
    return TokenPair(
        access_token=create_access_token(sub),
        refresh_token=create_refresh_token(sub),
    )


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshIn):
    try:
        tok = decode_token(payload.refresh_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if not is_refresh(tok):
        raise HTTPException(status_code=401, detail="Not a refresh token")

    sub = tok.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token")
    return TokenPair(
        access_token=create_access_token(sub),
        refresh_token=create_refresh_token(sub),
    )


@router.get("/me", response_model=MeOut)
def me(au: AuthedUser = Depends(get_current_user)):
    u = au.user
    return MeOut(
        id=u.id,
        org_id=u.org_id,
        name=u.name,
        email=u.email,
        role=u.role,  # type: ignore
        site_id=au.site_id,
    )