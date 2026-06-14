"""Transfer reports table ownership to the app DB user.

Run when report submission fails with "permission denied for table reports".
Uses DATABASE_MIGRATION_URL when set, otherwise tries postgres superuser URLs.
"""

from __future__ import annotations

import asyncio
import os
import re
import sys

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings


def _candidate_urls() -> list[str]:
    settings = get_settings()
    app_user = make_url(settings.database_url).username or "aed"
    base = make_url(settings.database_url)
    host = base.host or "localhost"
    port = base.port or 5432
    database = base.database or "aed_locator"

    candidates: list[str] = []
    migration_url = os.environ.get("DATABASE_MIGRATION_URL", "").strip()
    if migration_url:
        candidates.append(migration_url)

    for password in ("", "postgres", "aed"):
        auth = "postgres" if password == "" else f"postgres:{password}"
        candidates.append(
            f"postgresql+asyncpg://{auth}@{host}:{port}/{database}"
        )

    # De-duplicate while preserving order.
    seen: set[str] = set()
    unique: list[str] = []
    for url in candidates:
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique, app_user


async def _try_fix(url: str, app_user: str) -> bool:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", app_user):
        print(f"unsupported app user name: {app_user}")
        return False

    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            owner = await conn.scalar(
                text(
                    "SELECT tableowner FROM pg_tables "
                    "WHERE tablename = 'reports' AND schemaname = 'public'"
                )
            )
            if owner is None:
                print("reports table not found")
                return False
            if owner == app_user:
                print(f"reports already owned by {app_user}")
                return True

            is_super = await conn.scalar(
                text(
                    "SELECT rolsuper FROM pg_roles WHERE rolname = current_user"
                )
            )
            if not is_super:
                print(f"connected as non-superuser via {make_url(url).username}")
                return False

            await conn.execute(text(f"ALTER TABLE reports OWNER TO {app_user}"))
            await conn.execute(text(f"ALTER SEQUENCE reports_id_seq OWNER TO {app_user}"))
            await conn.execute(text(f"GRANT USAGE ON TYPE reportstatus TO {app_user}"))
            print(f"transferred reports ownership to {app_user}")
            return True
    except Exception as exc:
        print(f"failed via {make_url(url).username}: {exc}")
        return False
    finally:
        await engine.dispose()


async def main() -> int:
    candidates, app_user = _candidate_urls()
    for url in candidates:
        if await _try_fix(url, app_user):
            return 0
    print(
        "Could not fix privileges automatically. Run as postgres superuser:\n"
        "  psql -U postgres -d aed_locator -f scripts/grant_reports_privileges.sql"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
