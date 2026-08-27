from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from .auth import create_token, password_ok, require_admin
from .config import settings
from .database import Base, engine, get_db
from .models import Application, Job
from .schemas import ApplicationOut, JobOut, JobPatch, JobWrite, LoginIn
from .seed import seed_jobs

EMAIL_OK = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
CV_EXTS = {".pdf", ".doc", ".docx"}
CV_MAX_BYTES = 5 * 1024 * 1024
ROOT = Path(__file__).resolve().parent.parent
UPLOAD_ROOT = (ROOT / settings.upload_dir).resolve()

app = FastAPI(title="Softsove API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        seed_jobs(db)
    finally:
        db.close()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "role"


def unique_slug(db: Session, base: str, ignore_id: Optional[int] = None) -> str:
    slug = slugify(base)
    candidate = slug
    n = 2
    while True:
        q = db.query(Job).filter(Job.slug == candidate)
        if ignore_id is not None:
            q = q.filter(Job.id != ignore_id)
        if not q.first():
            return candidate
        candidate = f"{slug}-{n}"
        n += 1


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "softsove-api"}


@app.get("/jobs", response_model=List[JobOut])
def list_jobs(db: Session = Depends(get_db)) -> List[Job]:
    return db.query(Job).filter(Job.is_open.is_(True)).order_by(Job.id.desc()).all()


@app.get("/jobs/{slug}", response_model=JobOut)
def get_job(slug: str, db: Session = Depends(get_db)) -> Job:
    job = db.query(Job).filter(Job.slug == slug, Job.is_open.is_(True)).first()
    if not job:
        raise HTTPException(status_code=404, detail="This role is not open.")
    return job


@app.post("/jobs/{slug}/apply")
async def apply(
    slug: str,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    message: str = Form(""),
    experience_years: str = Form(""),
    cv: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> JSONResponse:
    job = db.query(Job).filter(Job.slug == slug, Job.is_open.is_(True)).first()
    if not job:
        raise HTTPException(status_code=404, detail="This role is not open.")

    name = name.strip()
    email = email.strip()
    phone = phone.strip()
    message = message.strip()
    experience_years = experience_years.strip()

    if not name or not email:
        raise HTTPException(status_code=400, detail="Please fill in your name and email.")
    if not EMAIL_OK.match(email):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    if job.ask_experience and not experience_years:
        raise HTTPException(status_code=400, detail="Please enter your years of experience.")

    suffix = Path(cv.filename or "").suffix.lower()
    if suffix not in CV_EXTS:
        raise HTTPException(status_code=400, detail="Upload a PDF, DOC, or DOCX CV.")

    raw = await cv.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Your CV file is empty.")
    if len(raw) > CV_MAX_BYTES:
        raise HTTPException(status_code=400, detail="CV must be 5MB or smaller.")

    stored_name = f"{job.slug}-{uuid.uuid4().hex}{suffix}"
    dest = UPLOAD_ROOT / stored_name
    dest.write_bytes(raw)

    application = Application(
        job_id=job.id,
        name=name,
        email=email,
        phone=phone,
        message=message,
        experience_years=experience_years,
        cv_filename=cv.filename or stored_name,
        cv_path=str(dest),
    )
    db.add(application)
    db.commit()

    return JSONResponse(
        {
            "success": True,
            "message": "Thanks for applying. Our team will get back shortly.",
        }
    )


@app.post("/admin/login")
def admin_login(body: LoginIn) -> dict:
    if not password_ok(body.password):
        raise HTTPException(status_code=401, detail="Wrong password.")
    return {"token": create_token()}


@app.get("/admin/jobs", response_model=List[JobOut])
def admin_jobs(_: str = Depends(require_admin), db: Session = Depends(get_db)) -> List[Job]:
    return db.query(Job).order_by(Job.id.desc()).all()


@app.post("/admin/jobs", response_model=JobOut)
def create_job(body: JobWrite, _: str = Depends(require_admin), db: Session = Depends(get_db)) -> Job:
    slug = unique_slug(db, body.slug or body.title)
    job = Job(
        title=body.title.strip(),
        slug=slug,
        department=body.department.strip(),
        location=body.location.strip(),
        employment_type=body.employment_type.strip() or "Full-time",
        short_intro=body.short_intro.strip(),
        description=body.description.strip(),
        requirements=body.requirements.strip(),
        experience_badge=body.experience_badge.strip(),
        ask_experience=body.ask_experience,
        is_open=body.is_open,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@app.patch("/admin/jobs/{job_id}", response_model=JobOut)
def update_job(
    job_id: int,
    body: JobPatch,
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Job:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Role not found.")

    data = body.model_dump(exclude_unset=True)
    if "slug" in data and data["slug"]:
        data["slug"] = unique_slug(db, data["slug"], ignore_id=job.id)
    elif "title" in data and data["title"] and not data.get("slug"):
        data["slug"] = unique_slug(db, data["title"], ignore_id=job.id)

    for key, value in data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(job, key, value)

    db.commit()
    db.refresh(job)
    return job


@app.delete("/admin/jobs/{job_id}")
def delete_job(job_id: int, _: str = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Role not found.")
    db.query(Application).filter(Application.job_id == job.id).delete()
    db.delete(job)
    db.commit()
    return {"success": True}


@app.get("/admin/applications", response_model=List[ApplicationOut])
def admin_applications(_: str = Depends(require_admin), db: Session = Depends(get_db)) -> List[ApplicationOut]:
    rows = db.query(Application).order_by(Application.id.desc()).all()
    out: List[ApplicationOut] = []
    for row in rows:
        out.append(
            ApplicationOut(
                id=row.id,
                job_id=row.job_id,
                job_title=row.job.title if row.job else "",
                job_slug=row.job.slug if row.job else "",
                name=row.name,
                email=row.email,
                phone=row.phone,
                message=row.message,
                experience_years=row.experience_years,
                cv_filename=row.cv_filename,
                created_at=row.created_at,
            )
        )
    return out


@app.get("/admin/applications/{application_id}/cv")
def download_cv(
    application_id: int,
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
) -> FileResponse:
    row = db.query(Application).filter(Application.id == application_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found.")
    path = Path(row.cv_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="CV file is missing.")
    return FileResponse(path, filename=row.cv_filename, media_type="application/octet-stream")
