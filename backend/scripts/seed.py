"""Seed sample verified AEDs for local development (Sofia, Bulgaria)."""

import asyncio
import sys
from pathlib import Path

# Allow `python scripts/seed.py` from the backend directory without PYTHONPATH.
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from geoalchemy2.elements import WKTElement
from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.session import async_session_factory
from app.models.aed import AED, AccessibilityType, VerificationStatus
from app.models.user import User, UserRole

# (latitude, longitude, address, description)
SAMPLE_AEDS = [
    (42.6853, 23.3189, "NDK — National Palace of Culture", "Main entrance foyer, left of the information desk"),
    (42.6977, 23.3219, "Serdika Metro Station", "Concourse level near exit to Vitosha Boulevard"),
    (42.6934, 23.3342, "Sofia University Rectorate", "Ground floor lobby, security desk area"),
    (42.7114, 23.3213, "Sofia Central Railway Station", "Main hall, near the western ticket counters"),
    (42.6950, 23.4142, "Sofia Airport — Terminal 2", "Departures hall, landside near information desk"),
    (42.6885, 23.3448, "Borisova Gradina Park", "Park entrance near Ariana Lake, kiosk building"),
    (42.6980, 23.3095, "Mall of Sofia", "Ground floor near the central atrium escalators"),
    (42.6869, 23.3144, "Medical University Sofia", "Faculty building A, main corridor ground floor"),
    (42.6910, 23.3190, "Vitosha Boulevard — Patriarch Evtimiy", "Pharmacy entrance, staff can direct to AED cabinet"),
    (42.6570, 23.3765, "Paradise Center", "Cinema level, next to first-aid room signage"),
    (42.6690, 23.3420, "Arena Armeec Sofia", "Event hall concourse, staff entrance B"),
    (42.6780, 23.3525, "National Stadium Vasil Levski", "West stand concourse, level 1"),
]

PENDING_AEDS = [
    (42.6720, 23.3580, "Lozenets District Municipality", "Reception area — awaiting photo review"),
    (42.6480, 23.3670, "Studentski grad — Block 8", "Ground floor entrance, near security booth"),
    (42.7100, 23.2930, "Lyulin Metro Station", "Platform level — needs verifier site visit"),
]


async def seed() -> None:
    async with async_session_factory() as session:
        existing = await session.execute(select(User).where(User.email == "admin@aedlocator.local"))
        if existing.scalar_one_or_none() is None:
            session.add(
                User(
                    email="admin@aedlocator.local",
                    hashed_password=get_password_hash("adminchange1"),
                    full_name="Sofia Admin",
                    role=UserRole.admin,
                )
            )
            session.add(
                User(
                    email="reporter@example.com",
                    hashed_password=get_password_hash("reporter123"),
                    full_name="Demo Reporter",
                    role=UserRole.user,
                )
            )

        count = await session.execute(select(AED).limit(1))
        if count.scalar_one_or_none() is not None:
            print("AEDs already seeded, skipping.")
            await session.commit()
            return

        reporter = await session.execute(select(User).where(User.email == "reporter@example.com"))
        reporter_id = reporter.scalar_one_or_none()
        submitter_id = reporter_id.id if reporter_id else None

        accessibility_cycle = [
            AccessibilityType.always_open,
            AccessibilityType.business_hours,
            AccessibilityType.restricted_access,
        ]
        business_hours_json = (
            '{"mon":{"open":"08:00","close":"20:00"},'
            '"tue":{"open":"08:00","close":"20:00"},'
            '"wed":{"open":"08:00","close":"20:00"},'
            '"thu":{"open":"08:00","close":"20:00"},'
            '"fri":{"open":"08:00","close":"20:00"},'
            '"sat":{"open":"10:00","close":"16:00"}}'
        )

        for index, (lat, lon, address, description) in enumerate(SAMPLE_AEDS):
            point = WKTElement(f"POINT({lon} {lat})", srid=4326)
            access = accessibility_cycle[index % len(accessibility_cycle)]
            session.add(
                AED(
                    location=point,
                    latitude=lat,
                    longitude=lon,
                    address=address,
                    description=description,
                    verification_status=VerificationStatus.verified,
                    accessibility_type=access,
                    opening_hours=business_hours_json if access == AccessibilityType.business_hours else None,
                    submitter_id=submitter_id,
                    ai_confidence=0.9,
                    spam_score=0.05,
                )
            )

        for lat, lon, address, description in PENDING_AEDS:
            point = WKTElement(f"POINT({lon} {lat})", srid=4326)
            session.add(
                AED(
                    location=point,
                    latitude=lat,
                    longitude=lon,
                    address=address,
                    description=description,
                    verification_status=VerificationStatus.pending,
                    submitter_id=submitter_id,
                    ai_confidence=0.6,
                    spam_score=0.2,
                )
            )

        await session.commit()
        total = len(SAMPLE_AEDS) + len(PENDING_AEDS)
        print(f"Seeded {total} AEDs ({len(SAMPLE_AEDS)} verified, {len(PENDING_AEDS)} pending) and users.")


if __name__ == "__main__":
    asyncio.run(seed())
