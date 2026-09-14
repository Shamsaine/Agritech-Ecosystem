from __future__ import annotations

import uuid
from dataclasses import dataclass
from math import ceil

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Application, Category, Location, Technology


@dataclass(frozen=True)
class ApplicationPage:
    applications: list[Application]
    page: int
    page_size: int
    total_items: int

    @property
    def total_pages(self) -> int:
        if self.total_items == 0:
            return 0
        return ceil(self.total_items / self.page_size)


def visible_applications_query():
    return select(Application).where(
        Application.is_active.is_(True),
        Application.record_status == "pilot",
    )


async def list_applications(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    technology_slug: str | None = None,
    category_slug: str | None = None,
    location_slug: str | None = None,
    verification_status: str | None = None,
) -> ApplicationPage:
    query = visible_applications_query()

    if search:
        search_term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Application.name.ilike(search_term),
                Application.summary.ilike(search_term),
                Application.description.ilike(search_term),
            )
        )

    if technology_slug:
        query = query.join(Application.technologies).where(Technology.slug == technology_slug)

    if category_slug:
        query = query.join(Application.categories).where(Category.slug == category_slug)

    if location_slug:
        query = query.join(Application.locations).where(Location.slug == location_slug)

    if verification_status:
        query = query.where(Application.verification_status == verification_status)

    query = query.distinct()

    count_query = select(func.count()).select_from(query.order_by(None).subquery())
    total_items = (await session.execute(count_query)).scalar_one()

    offset = (page - 1) * page_size
    query = (
        query.options(selectinload(Application.owning_organisation))
        .order_by(Application.name)
        .offset(offset)
        .limit(page_size)
    )
    result = await session.execute(query)
    applications = list(result.scalars().unique().all())

    return ApplicationPage(
        applications=applications,
        page=page,
        page_size=page_size,
        total_items=total_items,
    )


async def get_application(session: AsyncSession, identifier: str) -> Application | None:
    conditions = [
        Application.slug == identifier,
        Application.source_record_id == identifier,
    ]

    try:
        parsed_id = uuid.UUID(identifier)
    except ValueError:
        parsed_id = None

    if parsed_id is not None:
        conditions.append(Application.id == parsed_id)

    query = (
        visible_applications_query()
        .where(or_(*conditions))
        .options(
            selectinload(Application.owning_organisation),
            selectinload(Application.technologies),
            selectinload(Application.categories),
            selectinload(Application.focus_areas),
            selectinload(Application.platforms),
            selectinload(Application.languages),
            selectinload(Application.physical_components),
            selectinload(Application.locations),
            selectinload(Application.developers),
        )
    )

    result = await session.execute(query)
    return result.scalars().unique().one_or_none()
