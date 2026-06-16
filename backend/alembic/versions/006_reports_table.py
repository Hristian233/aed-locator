"""Add reports table for problem reports

Revision ID: 006
Revises: 005
Create Date: 2026-06-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    reports_exists = bind.execute(
        sa.text("SELECT to_regclass('public.reports') IS NOT NULL")
    ).scalar()
    if reports_exists:
        return

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("aed_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("reporter_latitude", sa.Float(), nullable=True),
        sa.Column("reporter_longitude", sa.Float(), nullable=True),
        sa.Column(
            "reporter_location",
            Geography(geometry_type="POINT", srid=4326),
            nullable=True,
        ),
        sa.Column("image_url", sa.String(length=1024), nullable=True),
        sa.Column("image_object_keys", sa.Text(), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("submitter_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "reviewed",
                "dismissed",
                "resolved",
                name="reportstatus",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("spam_score", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["aed_id"], ["aeds.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["submitter_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reports_status"), "reports", ["status"], unique=False)
    op.create_index(op.f("ix_reports_aed_id"), "reports", ["aed_id"], unique=False)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_reports_reporter_location "
        "ON reports USING GIST (reporter_location)"
    )


def downgrade() -> None:
    op.drop_index("idx_reports_reporter_location", table_name="reports")
    op.drop_index(op.f("ix_reports_aed_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_status"), table_name="reports")
    op.drop_table("reports")
    op.execute("DROP TYPE reportstatus")
