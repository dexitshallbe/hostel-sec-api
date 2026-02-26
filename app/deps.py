from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.security import decode_token
from db.models import User

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


class AuthedUser:
    def __init__(self, user: User, site_id: Optional[int] = None):
        self.user = user
        self.site_id = site_id  # optional guard scope


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2)) -> AuthedUser:
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    sub = payload.get("sub")
    if not sub or ":" not in sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    user_id_str, scope_site = sub.split(":", 1)
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found/inactive")

    site_id = None
    if scope_site != "none":
        try:
            site_id = int(scope_site)
        except ValueError:
            site_id = None

    return AuthedUser(user=user, site_id=site_id)


def require_roles(*roles: str):
    def _inner(au: AuthedUser = Depends(get_current_user)) -> AuthedUser:
        if au.user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return au
    return _inner


def guard_site_scope(au: AuthedUser, site_id: int) -> None:
    if au.user.role in ("ADMIN", "SUPERVISOR"):
        return

    # For GUARD, we enforce token scope (site_id in token subject)
    if au.user.role == "GUARD":
        if au.site_id is None:
            raise HTTPException(status_code=403, detail="Guard not assigned to a site")
        if au.site_id != site_id:
            raise HTTPException(status_code=403, detail="Guard cannot access this site")
        return

    raise HTTPException(status_code=403, detail="Forbidden")