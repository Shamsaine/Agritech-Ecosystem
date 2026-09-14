import asyncio
import sys
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AccessType, AvailabilityStatus
from app.db.session import AsyncSessionFactory


@dataclass(frozen=True)
class SeedValue:
    name: str
    slug: str
    description: str | None = None


ACCESS_TYPES = (
    SeedValue("Commercial", "commercial", "Requires paid access."),
    SeedValue("Free", "free", "Available without payment."),
    SeedValue("Freemium", "freemium", "Free core access with paid features."),
    SeedValue("Open Source", "open-source", "Source code is publicly available."),
    SeedValue("Unknown", "unknown", "Access model has not been verified."),
)

AVAILABILITY_STATUSES = (
    SeedValue("Active", "active", "Currently available."),
    SeedValue("Inactive", "inactive", "No longer active."),
    SeedValue("Unknown", "unknown", "Availability has not been verified."),
)


async def seed_values(
    session: AsyncSession,
    model: type,
    values: tuple[SeedValue, ...],
) -> None:
    for value in values:
        result = await session.execute(select(model).where(model.slug == value.slug))
        existing = result.scalar_one_or_none()
        if existing is None:
            session.add(
                model(
                    name=value.name,
                    slug=value.slug,
                    description=value.description,
                    is_active=True,
                )
            )


async def seed_database() -> None:
    async with AsyncSessionFactory() as session:
        try:
            await seed_values(session, AccessType, ACCESS_TYPES)
            await seed_values(session, AvailabilityStatus, AVAILABILITY_STATUSES)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


if __name__ == "__main__":
    loop_factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
    asyncio.run(seed_database(), loop_factory=loop_factory)
