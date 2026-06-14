"""Grant app user privileges on reports table

Revision ID: 007
Revises: 006
Create Date: 2026-06-14

"""

import re
from typing import Sequence, Union

from alembic import op
from sqlalchemy.engine import make_url

from app.core.config import get_settings

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _app_db_user() -> str | None:
    username = make_url(get_settings().database_url).username
    if not username or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", username):
        return None
    return username


def upgrade() -> None:
    app_user = _app_db_user()
    if not app_user:
        return

    op.execute(
        f"""
        DO $$
        DECLARE
            target_user text := '{app_user}';
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_tables
                WHERE tablename = 'reports'
                  AND schemaname = 'public'
                  AND tableowner = current_user
            ) THEN
                EXECUTE format(
                    'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE reports TO %I',
                    target_user
                );
                EXECUTE format(
                    'GRANT USAGE, SELECT ON SEQUENCE reports_id_seq TO %I',
                    target_user
                );
                EXECUTE format(
                    'GRANT USAGE ON TYPE reportstatus TO %I',
                    target_user
                );
            ELSIF EXISTS (
                SELECT 1 FROM pg_roles
                WHERE rolname = current_user AND rolsuper
            ) THEN
                EXECUTE format('ALTER TABLE reports OWNER TO %I', target_user);
                EXECUTE format(
                    'ALTER SEQUENCE reports_id_seq OWNER TO %I',
                    target_user
                );
                EXECUTE format(
                    'GRANT USAGE ON TYPE reportstatus TO %I',
                    target_user
                );
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    app_user = _app_db_user()
    if not app_user:
        return

    op.execute(
        f"""
        DO $$
        DECLARE
            target_user text := '{app_user}';
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_roles
                WHERE rolname = current_user AND rolsuper
            ) THEN
                EXECUTE format(
                    'REVOKE USAGE ON TYPE reportstatus FROM %I',
                    target_user
                );
                EXECUTE format(
                    'REVOKE USAGE, SELECT ON SEQUENCE reports_id_seq FROM %I',
                    target_user
                );
                EXECUTE format(
                    'REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE reports FROM %I',
                    target_user
                );
            END IF;
        END $$;
        """
    )
