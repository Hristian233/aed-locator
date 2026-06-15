from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.report import Report, ReportStatus


class ReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, report_id: int) -> Report | None:
        result = await self.session.execute(
            select(Report)
            .options(selectinload(Report.aed))
            .where(Report.id == report_id)
        )
        return result.scalar_one_or_none()

    async def create(self, report: Report) -> Report:
        self.session.add(report)
        await self.session.flush()
        await self.session.refresh(report, attribute_names=["aed"])
        return report

    async def update(self, report: Report) -> Report:
        await self.session.flush()
        await self.session.refresh(report, attribute_names=["aed"])
        return report

    async def list_pending(
        self,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Report], int]:
        offset = (page - 1) * page_size
        query = (
            select(Report)
            .options(selectinload(Report.aed))
            .where(Report.status == ReportStatus.pending)
        )
        count_query = (
            select(func.count())
            .select_from(Report)
            .where(Report.status == ReportStatus.pending)
        )

        total = (await self.session.execute(count_query)).scalar_one()
        result = await self.session.execute(
            query.order_by(Report.created_at.desc()).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total
