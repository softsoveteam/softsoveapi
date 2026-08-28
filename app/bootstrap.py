"""Create tables and seed the admin login. Safe to run more than once."""

from .database import Base, SessionLocal, engine
from .models import AdminUser
from .seed import seed_admin, seed_jobs


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_jobs(db)
        seed_admin(db)
        print(f"database ready, admins={db.query(AdminUser).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
