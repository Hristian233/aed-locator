"""Initial schema with PostGIS

Revision ID: 001
Revises:
Create Date: 2026-05-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("role", sa.Enum("user", "admin", name="userrole"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "aeds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("location", Geography(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("address", sa.String(length=512), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=1024), nullable=True),
        sa.Column(
            "verification_status",
            sa.Enum("pending", "verified", "rejected", name="verificationstatus"),
            nullable=False,
        ),
        sa.Column("submitter_id", sa.Integer(), nullable=True),
        sa.Column("ai_confidence", sa.Float(), nullable=True),
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
        sa.ForeignKeyConstraint(["submitter_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_aeds_verification_status"), "aeds", ["verification_status"], unique=False
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_aeds_location ON aeds USING GIST (location)"
    )


def downgrade() -> None:
    op.drop_index("idx_aeds_location", table_name="aeds")
    op.drop_index(op.f("ix_aeds_verification_status"), table_name="aeds")
    op.drop_table("aeds")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS verificationstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
