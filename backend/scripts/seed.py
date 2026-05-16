"""Seed sample verified AEDs for local development."""

import asyncio

from geoalchemy2.elements import WKTElement
from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.session import async_session_factory
from app.models.aed import AED, VerificationStatus
from app.models.user import User, UserRole

SAMPLE_AEDS = [
    (-33.8688, 151.2093, "Sydney CBD Station", "Main concourse near information desk"),
    (-33.8523, 151.2108, "Circular Quay", "Near ferry wharf entrance"),
    (-33.8915, 151.2767, "Bondi Beach Pavilion", "Lifeguard station area"),
    (-37.8136, 144.9631, "Melbourne Federation Square", "West plaza kiosk"),
    (-37.8183, 144.9671, "Flinders Street Station", "Underground passage level"),
]


async def seed() -> None:
    async with async_session_factory() as session:
        existing = await session.execute(select(User).where(User.email == "admin@aedlocator.local"))
        if existing.scalar_one_or_none() is None:
            admin = User(
                email="admin@aedlocator.local",
                hashed_password=get_password_hash("adminchange1"),
                full_name="Local Admin",
                role=UserRole.admin,
            )
            session.add(admin)

        count = await session.execute(select(AED).limit(1))
        if count.scalar_one_or_none() is not None:
            print("AEDs already seeded, skipping.")
            await session.commit()
            return

        for lat, lon, address, description in SAMPLE_AEDS:
            point = WKTElement(f"POINT({lon} {lat})", srid=4326)
            session.add(
                AED(
                    location=point,
                    latitude=lat,
                    longitude=lon,
                    address=address,
                    description=description,
                    verification_status=VerificationStatus.verified,
                )
            )
        await session.commit()
        print(f"Seeded {len(SAMPLE_AEDS)} AEDs and admin user.")


if __name__ == "__main__":
    asyncio.run(seed())
