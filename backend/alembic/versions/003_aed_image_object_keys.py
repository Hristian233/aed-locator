"""Store multiple image object keys per AED submission

Revision ID: 003
Revises: 002
Create Date: 2026-06-03

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("aeds", sa.Column("image_object_keys", sa.Text(), nullable=True))
    op.execute(
        """
        UPDATE aeds
        SET image_object_keys = json_build_array(image_url)::text
        WHERE image_url IS NOT NULL AND image_url <> ''
        """
    )


def downgrade() -> None:
    op.drop_column("aeds", "image_object_keys")
