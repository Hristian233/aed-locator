import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings


async def main() -> None:
    engine = create_async_engine(get_settings().database_url)
    async with engine.begin() as conn:
        version = await conn.scalar(text("SELECT version_num FROM alembic_version"))
        print("alembic_version:", version)
        owner = await conn.scalar(
            text("SELECT tableowner FROM pg_tables WHERE tablename = 'reports'")
        )
        print("reports owner:", owner)
        row = (
            await conn.execute(
                text(
                    "SELECT has_table_privilege(current_user, 'reports', 'INSERT'), "
                    "current_user, "
                    "(SELECT rolsuper FROM pg_roles WHERE rolname = current_user)"
                )
            )
        ).one()
        print("can_insert:", row[0], "as:", row[1], "superuser:", row[2])
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
