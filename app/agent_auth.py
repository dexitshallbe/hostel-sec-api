from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.security import verify_password
from db.models import Agent


def get_current_agent(
    x_agent_id: int | None = Header(default=None, alias="X-Agent-Id"),
    x_agent_key: str | None = Header(default=None, alias="X-Agent-Key"),
    db: Session = Depends(get_db),
) -> Agent:
    if x_agent_id is None or not x_agent_key:
        raise HTTPException(401, "Missing agent headers")

    ag = db.get(Agent, x_agent_id)
    if not ag or not ag.api_key_hash:
        raise HTTPException(401, "Invalid agent")

    if not verify_password(x_agent_key, ag.api_key_hash):
        raise HTTPException(401, "Invalid agent key")

    return ag