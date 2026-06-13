"""Add location_name and is_restricted_access to AEDs

Revision ID: 005
Revises: 004
Create Date: 2026-06-13

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("aeds", sa.Column("location_name", sa.String(length=255), nullable=True))
    op.add_column(
        "aeds",
        sa.Column(
            "is_restricted_access",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.alter_column("aeds", "is_restricted_access", server_default=None)


def downgrade() -> None:
    op.drop_column("aeds", "is_restricted_access")
    op.drop_column("aeds", "location_name")
