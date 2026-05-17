"""Add accessibility and report fields to AEDs

Revision ID: 002
Revises: 001
Create Date: 2026-05-17

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE accessibilitytype AS ENUM ('24_7', 'business_hours', 'restricted_access')"
    )
    op.execute(
        "CREATE TYPE reporttype AS ENUM ('new_location', 'incorrect_info', 'unavailable', 'duplicate')"
    )
    op.add_column(
        "aeds",
        sa.Column(
            "accessibility_type",
            sa.Enum(
                "24_7",
                "business_hours",
                "restricted_access",
                name="accessibilitytype",
                create_type=False,
            ),
            nullable=False,
            server_default="24_7",
        ),
    )
    op.add_column("aeds", sa.Column("opening_hours", sa.Text(), nullable=True))
    op.add_column(
        "aeds",
        sa.Column(
            "report_type",
            sa.Enum(
                "new_location",
                "incorrect_info",
                "unavailable",
                "duplicate",
                name="reporttype",
                create_type=False,
            ),
            nullable=False,
            server_default="new_location",
        ),
    )
    op.add_column("aeds", sa.Column("contact_email", sa.String(length=255), nullable=True))
    op.add_column("aeds", sa.Column("related_aed_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_aeds_related_aed_id",
        "aeds",
        "aeds",
        ["related_aed_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_aeds_related_aed_id", "aeds", type_="foreignkey")
    op.drop_column("aeds", "related_aed_id")
    op.drop_column("aeds", "contact_email")
    op.drop_column("aeds", "report_type")
    op.drop_column("aeds", "opening_hours")
    op.drop_column("aeds", "accessibility_type")
    op.execute("DROP TYPE IF EXISTS reporttype")
    op.execute("DROP TYPE IF EXISTS accessibilitytype")
