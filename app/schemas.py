from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    department: str
    location: str
    employment_type: str
    short_intro: str
    description: str
    requirements: str
    experience_badge: str
    ask_experience: bool
    is_open: bool
    created_at: Optional[datetime] = None


class JobWrite(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    slug: Optional[str] = None
    department: str = ""
    location: str = ""
    employment_type: str = "Full-time"
    short_intro: str = ""
    description: str = ""
    requirements: str = ""
    experience_badge: str = ""
    ask_experience: bool = False
    is_open: bool = True


class JobPatch(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    short_intro: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    experience_badge: Optional[str] = None
    ask_experience: Optional[bool] = None
    is_open: Optional[bool] = None


class LoginIn(BaseModel):
    password: str


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    job_title: str
    job_slug: str
    name: str
    email: str
    phone: str
    message: str
    experience_years: str
    cv_filename: str
    created_at: Optional[datetime] = None
