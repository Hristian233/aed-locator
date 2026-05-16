from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aed import AED, VerificationStatus


class AEDRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, aed_id: int) -> AED | None:
        result = await self.session.execute(select(AED).where(AED.id == aed_id))
        return result.scalar_one_or_none()

    async def create(self, aed: AED) -> AED:
        self.session.add(aed)
        await self.session.flush()
        await self.session.refresh(aed)
        return aed

    async def update(self, aed: AED) -> AED:
        await self.session.flush()
        await self.session.refresh(aed)
        return aed

    async def list_aeds(
        self,
        *,
        page: int,
        page_size: int,
        status: VerificationStatus | None = None,
        verified_only: bool = True,
    ) -> tuple[list[tuple[AED, float | None]], int]:
        offset = (page - 1) * page_size
        query = select(AED)
        count_query = select(func.count()).select_from(AED)

        if status:
            query = query.where(AED.verification_status == status)
            count_query = count_query.where(AED.verification_status == status)
        elif verified_only:
            query = query.where(AED.verification_status == VerificationStatus.verified)
            count_query = count_query.where(
                AED.verification_status == VerificationStatus.verified
            )

        total = (await self.session.execute(count_query)).scalar_one()
        result = await self.session.execute(
            query.order_by(AED.created_at.desc()).offset(offset).limit(page_size)
        )
        rows = [(row, None) for row in result.scalars().all()]
        return rows, total

    async def find_nearest(
        self,
        latitude: float,
        longitude: float,
        *,
        limit: int,
        max_distance_meters: float | None,
        verified_only: bool = True,
    ) -> list[tuple[AED, float]]:
        status_filter = ""
        if verified_only:
            status_filter = "AND verification_status = 'verified'"

        max_filter = ""
        params: dict = {
            "lat": latitude,
            "lon": longitude,
            "limit": limit,
        }
        if max_distance_meters is not None:
            max_filter = "AND ST_DWithin(location, user_point, :max_dist)"
            params["max_dist"] = max_distance_meters

        sql = text(
            f"""
            SELECT id, latitude, longitude, address, description, image_url,
                   verification_status, submitter_id, ai_confidence, spam_score,
                   created_at, updated_at,
                   ST_Distance(location::geography, user_point) AS distance_meters
            FROM aeds,
                 LATERAL (SELECT ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography AS user_point) AS pt
            WHERE location IS NOT NULL
            {status_filter}
            {max_filter}
            ORDER BY location <-> ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
            LIMIT :limit
            """
        )
        result = await self.session.execute(sql, params)
        rows = result.mappings().all()
        aeds: list[tuple[AED, float]] = []
        for row in rows:
            aed = await self.get_by_id(row["id"])
            if aed:
                aeds.append((aed, float(row["distance_meters"])))
        return aeds

    async def find_duplicate_nearby(
        self, latitude: float, longitude: float, radius_meters: float
    ) -> AED | None:
        sql = text(
            """
            SELECT id FROM aeds
            WHERE ST_DWithin(
                location::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                :radius
            )
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        result = await self.session.execute(
            sql, {"lat": latitude, "lon": longitude, "radius": radius_meters}
        )
        row = result.first()
        if not row:
            return None
        return await self.get_by_id(row[0])
