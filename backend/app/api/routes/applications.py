from typing import Annotated

from fastapi import APIRouter, Query

from app.api.dependencies import DatabaseSession
from app.schemas.application import ApplicationDetail, PaginatedApplications
from app.services.applications import get_application_detail, get_application_page


router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


@router.get(
    "",
    response_model=PaginatedApplications,
    summary="Browse agritech applications",
    description="Returns approved pilot applications with pagination, search and filters. Quarantined records are excluded.",
)
async def applications_list(
    session: DatabaseSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(min_length=2, max_length=100)] = None,
    technology: str | None = None,
    category: str | None = None,
    location: str | None = None,
    verification_status: str | None = None,
) -> PaginatedApplications:
    return await get_application_page(
        session,
        page=page,
        page_size=page_size,
        search=search,
        technology=technology,
        category=category,
        location=location,
        verification_status=verification_status,
    )


@router.get(
    "/{identifier}",
    response_model=ApplicationDetail,
    summary="Get an application profile",
    description="Find an approved application using its UUID, slug or source record ID.",
)
async def application_detail(
    identifier: str,
    session: DatabaseSession,
) -> ApplicationDetail:
    return await get_application_detail(session, identifier)
