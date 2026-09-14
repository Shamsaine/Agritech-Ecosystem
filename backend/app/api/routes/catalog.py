from __future__ import annotations

import uuid
from math import ceil
from typing import Any

from fastapi import APIRouter, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import DatabaseSession
from app.core.exceptions import ResourceNotFoundError
from app.db.models import (
    Application,
    Category,
    Developer,
    Location,
    Organisation,
    Platform,
    Technology,
)
from app.db.models.associations import application_developers


router = APIRouter(tags=["Catalogue"])


def page_payload(items: list[Any], page: int, page_size: int, total: int) -> dict[str, Any]:
    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": ceil(total / page_size) if total else 0,
        },
    }


def visible_application_ids():
    return select(Application.id).where(
        Application.is_active.is_(True),
        Application.record_status == "pilot",
    )


async def directory_page(
    session: AsyncSession,
    model: Any,
    *,
    page: int,
    page_size: int,
    search: str | None,
    sort_by: str,
    sort_order: str,
    filters: list[Any] | None = None,
    joins: list[Any] | None = None,
) -> dict[str, Any]:
    filters = filters or []
    joins = joins or []
    query = select(model)
    for join in joins:
        query = query.join(join)
    query = query.where(model.is_active.is_(True), *filters).distinct()
    if search:
        query = query.where(model.name.ilike(f"%{search.strip()}%"))

    sort_fields = {"name": model.name, "created_at": model.created_at}
    sort_column = sort_fields.get(sort_by, model.name)
    query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())
    total = (await session.execute(select(func.count()).select_from(query.order_by(None).subquery()))).scalar_one()
    result = await session.execute(query.offset((page - 1) * page_size).limit(page_size))
    items = [{"id": item.id, "name": item.name, "slug": item.slug} for item in result.scalars().all()]
    return page_payload(items, page, page_size, total)


@router.get("/organisations")
async def organisations_list(
    session: DatabaseSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, min_length=2, max_length=100),
    sort_by: str = "name",
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    verification_status: str | None = None,
) -> dict[str, Any]:
    filters = [Organisation.verification_status == verification_status] if verification_status else []
    filters.append(Organisation.id.in_(select(Application.owning_organisation_id).where(
        Application.id.in_(visible_application_ids()),
        Application.owning_organisation_id.is_not(None),
    )))
    return await directory_page(session, Organisation, page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order, filters=filters)


@router.get("/developers")
async def developers_list(
    session: DatabaseSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, min_length=2, max_length=100),
    sort_by: str = "name",
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
) -> dict[str, Any]:
    filters = [Developer.id.in_(select(application_developers.c.developer_id).where(application_developers.c.application_id.in_(visible_application_ids())))]
    return await directory_page(session, Developer, page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order, filters=filters)


@router.get("/categories")
async def categories_list(
    session: DatabaseSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, min_length=2, max_length=100),
    sort_by: str = "name",
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
) -> dict[str, Any]:
    return await directory_page(session, Category, page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order, filters=[Category.applications.any(Application.id.in_(visible_application_ids()))])


@router.get("/countries")
async def countries_list(
    session: DatabaseSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, min_length=2, max_length=100),
    sort_by: str = "name",
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
) -> dict[str, Any]:
    filters = [Location.applications.any(Application.id.in_(visible_application_ids())), Location.location_type == "country"]
    return await directory_page(session, Location, page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order, filters=filters)


@router.get("/platforms")
async def platforms_list(
    session: DatabaseSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, min_length=2, max_length=100),
    sort_by: str = "name",
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
) -> dict[str, Any]:
    return await directory_page(session, Platform, page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order, filters=[Platform.applications.any(Application.id.in_(visible_application_ids()))])


async def profile_query(session: AsyncSession, model: Any, identifier: str, relationships: list[Any]):
    conditions = [model.slug == identifier]
    try:
        conditions.append(model.id == uuid.UUID(identifier))
    except ValueError:
        pass
    result = await session.execute(select(model).where(or_(*conditions), model.is_active.is_(True)).options(*relationships))
    return result.scalars().unique().one_or_none()


def app_card(application: Application) -> dict[str, Any]:
    return {"id": application.id, "name": application.name, "slug": application.slug, "summary": application.summary, "website_url": application.website_url}


@router.get("/organisations/{identifier}")
async def organisation_detail(identifier: str, session: DatabaseSession) -> dict[str, Any]:
    organisation = await profile_query(session, Organisation, identifier, [selectinload(Organisation.headquarters_location), selectinload(Organisation.applications)])
    if organisation is None:
        raise ResourceNotFoundError("Organisation not found", details={"identifier": identifier})
    applications = [app_card(app) for app in organisation.applications if app.is_active and app.record_status == "pilot"]
    return {"id": organisation.id, "name": organisation.name, "slug": organisation.slug, "organisation_type": organisation.organisation_type, "verification_status": organisation.verification_status, "headquarters": organisation.headquarters_location, "applications": applications}


@router.get("/developers/{identifier}")
async def developer_detail(identifier: str, session: DatabaseSession) -> dict[str, Any]:
    developer = await profile_query(session, Developer, identifier, [selectinload(Developer.organisation), selectinload(Developer.applications)])
    if developer is None:
        raise ResourceNotFoundError("Developer not found", details={"identifier": identifier})
    applications = [app_card(app) for app in developer.applications if app.is_active and app.record_status == "pilot"]
    return {"id": developer.id, "name": developer.name, "slug": developer.slug, "developer_type": developer.developer_type, "verification_status": developer.verification_status, "organisation": developer.organisation, "applications": applications}


@router.get("/analytics/summary")
async def analytics_summary(session: DatabaseSession) -> dict[str, int]:
    visible = visible_application_ids()
    values = {
        "applications": await session.scalar(select(func.count()).select_from(Application).where(Application.id.in_(visible))) or 0,
        "organisations": await session.scalar(select(func.count(func.distinct(Application.owning_organisation_id))).where(Application.id.in_(visible), Application.owning_organisation_id.is_not(None)) ) or 0,
        "developers": await session.scalar(select(func.count(func.distinct(application_developers.c.developer_id))).where(application_developers.c.application_id.in_(visible))) or 0,
        "countries": await session.scalar(select(func.count(func.distinct(Location.id))).where(Location.location_type == "country", Location.applications.any(Application.id.in_(visible)))) or 0,
        "technologies": await session.scalar(select(func.count(func.distinct(Technology.id))).where(Technology.applications.any(Application.id.in_(visible)))) or 0,
        "categories": await session.scalar(select(func.count(func.distinct(Category.id))).where(Category.applications.any(Application.id.in_(visible)))) or 0,
    }
    return values


async def distribution(session: AsyncSession, model: Any, relationship: Any, label: str) -> dict[str, list[dict[str, Any]]]:
    result = await session.execute(select(model.name, func.count(func.distinct(Application.id)).label("application_count")).join(relationship).join(Application).where(Application.id.in_(visible_application_ids())).group_by(model.name).order_by(model.name))
    return {"items": [{label: name, "application_count": count} for name, count in result.all()]}


@router.get("/analytics/categories")
async def analytics_categories(session: DatabaseSession) -> dict[str, list[dict[str, Any]]]:
    return await distribution(session, Category, Category.applications, "category")


@router.get("/analytics/technologies")
async def analytics_technologies(session: DatabaseSession) -> dict[str, list[dict[str, Any]]]:
    return await distribution(session, Technology, Technology.applications, "technology")


@router.get("/analytics/platforms")
async def analytics_platforms(session: DatabaseSession) -> dict[str, list[dict[str, Any]]]:
    return await distribution(session, Platform, Platform.applications, "platform")


@router.get("/analytics/geography")
async def analytics_geography(session: DatabaseSession) -> dict[str, list[dict[str, Any]]]:
    result = await session.execute(select(Location.name, Location.country_code, func.count(func.distinct(Application.id)).label("application_count")).join(Location.applications).where(Location.location_type == "country", Application.id.in_(visible_application_ids())).group_by(Location.name, Location.country_code).order_by(Location.name))
    return {"items": [{"country": name, "country_code": code, "application_count": count} for name, code, count in result.all()]}
