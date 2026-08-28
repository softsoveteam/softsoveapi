"""initial jobs, applications, admins

Revision ID: 001_initial
Revises:
Create Date: 2026-08-27
"""

from typing import Sequence, Set, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tables() -> Set[str]:
    return set(inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    existing = _tables()

    if "jobs" not in existing:
        op.create_table(
            "jobs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title", sa.String(length=160), nullable=False),
            sa.Column("slug", sa.String(length=180), nullable=False),
            sa.Column("department", sa.String(length=120), nullable=False, server_default=""),
            sa.Column("location", sa.String(length=160), nullable=False, server_default=""),
            sa.Column("employment_type", sa.String(length=80), nullable=False, server_default="Full-time"),
            sa.Column("short_intro", sa.String(length=280), nullable=False, server_default=""),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("requirements", sa.Text(), nullable=False, server_default=""),
            sa.Column("experience_badge", sa.String(length=80), nullable=False, server_default=""),
            sa.Column("ask_experience", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("is_open", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_jobs_slug", "jobs", ["slug"], unique=True)

    if "applications" not in existing:
        op.create_table(
            "applications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id"), nullable=False),
            sa.Column("name", sa.String(length=160), nullable=False),
            sa.Column("email", sa.String(length=200), nullable=False),
            sa.Column("phone", sa.String(length=80), nullable=False, server_default=""),
            sa.Column("message", sa.Text(), nullable=False, server_default=""),
            sa.Column("experience_years", sa.String(length=40), nullable=False, server_default=""),
            sa.Column("cv_filename", sa.String(length=255), nullable=False),
            sa.Column("cv_path", sa.String(length=500), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_applications_job_id", "applications", ["job_id"])

    if "admins" not in existing:
        op.create_table(
            "admins",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("email", sa.String(length=200), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_admins_email", "admins", ["email"], unique=True)


def downgrade() -> None:
    existing = _tables()
    if "applications" in existing:
        op.drop_index("ix_applications_job_id", table_name="applications")
        op.drop_table("applications")
    if "jobs" in existing:
        op.drop_index("ix_jobs_slug", table_name="jobs")
        op.drop_table("jobs")
    if "admins" in existing:
        op.drop_index("ix_admins_email", table_name="admins")
        op.drop_table("admins")
