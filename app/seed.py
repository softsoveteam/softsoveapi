from sqlalchemy.orm import Session

from .auth import hash_password
from .models import AdminUser, Job

SEED_ADMIN_EMAIL = "care@softsove.com"
SEED_ADMIN_PASSWORD = "Softsove@2026@@$"

SEED_JOBS = [
    {
        "title": "Product Designer",
        "slug": "product-designer",
        "department": "Design",
        "location": "Anand / Hybrid",
        "employment_type": "Full-time",
        "short_intro": "Make screens that refuse to look like everyone else's.",
        "description": "You will shape brand, product, and mischief across websites and campaigns. Boring templates are illegal here.",
        "requirements": "A sharp eye, a messy Figma, and work you are proud to show.",
        "experience_badge": "2+ years",
        "ask_experience": True,
        "is_open": True,
    },
    {
        "title": "Frontend Developer",
        "slug": "frontend-developer",
        "department": "Engineering",
        "location": "Anand / Remote",
        "employment_type": "Full-time",
        "short_intro": "Ship interfaces that move, click, and stay weird on purpose.",
        "description": "Build the Softsove site and client work with Next.js, care, and zero beige energy.",
        "requirements": "React/Next chops, CSS that holds up, and taste.",
        "experience_badge": "3+ years",
        "ask_experience": True,
        "is_open": True,
    },
    {
        "title": "Studio Intern",
        "slug": "studio-intern",
        "department": "Studio",
        "location": "Anand",
        "employment_type": "Internship",
        "short_intro": "Come learn, break things politely, and leave less boring than you arrived.",
        "description": "Support design and production. Ask questions. Bring curiosity.",
        "requirements": "Hunger to make things. Portfolio or classwork welcome.",
        "experience_badge": "Fresher",
        "ask_experience": False,
        "is_open": True,
    },
]


def seed_jobs(db: Session) -> None:
    if db.query(Job).count():
        return
    for row in SEED_JOBS:
        db.add(Job(**row))
    db.commit()


def seed_admin(db: Session) -> None:
    email = SEED_ADMIN_EMAIL.lower()
    if db.query(AdminUser).filter(AdminUser.email == email).first():
        return
    db.add(
        AdminUser(
            email=email,
            password_hash=hash_password(SEED_ADMIN_PASSWORD),
        )
    )
    db.commit()
