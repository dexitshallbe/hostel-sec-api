from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, Field


Role = Literal["ADMIN", "SUPERVISOR", "GUARD"]
CameraRole = Literal["entry", "exit"]
EventStatus = Literal["open", "ignored", "dealt"]
EventDecision = Optional[Literal["entry_granted", "entry_denied"]]


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class MeOut(BaseModel):
    id: int
    org_id: int
    name: str
    email: EmailStr
    role: Role
    site_id: Optional[int] = None  # guards can be site-scoped


class SiteCreate(BaseModel):
    org_id: int
    name: str = Field(min_length=1, max_length=200)


class SiteOut(BaseModel):
    id: int
    org_id: int
    name: str
    created_at: datetime


class CameraCreate(BaseModel):
    site_id: int
    name: str = Field(min_length=1, max_length=200)
    role: CameraRole
    stream_url: Optional[str] = None
    enabled: bool = True


class CameraOut(BaseModel):
    id: int
    site_id: int
    name: str
    role: CameraRole
    stream_url: Optional[str]
    enabled: bool
    created_at: datetime


class EventOut(BaseModel):
    id: int
    camera_id: int
    ts: datetime
    type: str
    person_name: Optional[str]
    similarity: Optional[float]
    status: str
    decision: Optional[str]
    handled_by_user_id: Optional[int]
    handled_at: Optional[datetime]
    notes: Optional[str]


class EventActionIn(BaseModel):
    # ignored | dealt
    status: EventStatus
    # only meaningful if status == dealt
    decision: EventDecision = None
    notes: Optional[str] = None