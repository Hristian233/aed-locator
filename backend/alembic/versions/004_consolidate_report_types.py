"""Consolidate report types into new_location and aed_issue

Revision ID: 004
Revises: 003
Create Date: 2026-06-13

"""

from typing import Sequence, Union

from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE reporttype_new AS ENUM ('new_location', 'aed_issue')")
    op.execute("ALTER TABLE aeds ALTER COLUMN report_type DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE aeds
        ALTER COLUMN report_type TYPE reporttype_new
        USING (
            CASE
                WHEN report_type::text IN ('incorrect_info', 'unavailable', 'duplicate')
                THEN 'aed_issue'::reporttype_new
                ELSE report_type::text::reporttype_new
            END
        )
        """
    )
    op.execute("ALTER TABLE aeds ALTER COLUMN report_type SET DEFAULT 'new_location'")
    op.execute("DROP TYPE reporttype")
    op.execute("ALTER TYPE reporttype_new RENAME TO reporttype")


def downgrade() -> None:
    op.execute(
        "CREATE TYPE reporttype_old AS ENUM "
        "('new_location', 'incorrect_info', 'unavailable', 'duplicate')"
    )
    op.execute("ALTER TABLE aeds ALTER COLUMN report_type DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE aeds
        ALTER COLUMN report_type TYPE reporttype_old
        USING (
            CASE
                WHEN report_type::text = 'aed_issue' THEN 'incorrect_info'::reporttype_old
                ELSE report_type::text::reporttype_old
            END
        )
        """
    )
    op.execute("ALTER TABLE aeds ALTER COLUMN report_type SET DEFAULT 'new_location'")
    op.execute("DROP TYPE reporttype")
    op.execute("ALTER TYPE reporttype_old RENAME TO reporttype")
