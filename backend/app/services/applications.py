from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.repositories.applications import get_application, list_applications
from app.schemas.application import ApplicationDetail, ApplicationListItem, PaginatedApplications
from app.schemas.common import PaginationMeta


async def get_application_page(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    search: str | None,
    technology: str | None,
    category: str | None,
    location: str | None,
    verification_status: str | None,
) -> PaginatedApplications:
    result = await list_applications(
        session,
        page=page,
        page_size=page_size,
        search=search,
        technology_slug=technology,
        category_slug=category,
        location_slug=location,
        verification_status=verification_status,
    )

    return PaginatedApplications(
        items=[ApplicationListItem.model_validate(application) for application in result.applications],
        pagination=PaginationMeta(
            page=result.page,
            page_size=result.page_size,
            total_items=result.total_items,
            total_pages=result.total_pages,
        ),
    )


async def get_application_detail(session: AsyncSession, identifier: str) -> ApplicationDetail:
    application = await get_application(session, identifier)

    if application is None:
        raise ResourceNotFoundError(
            "Application not found",
            details={"identifier": identifier},
        )

    return ApplicationDetail.model_validate(application)
