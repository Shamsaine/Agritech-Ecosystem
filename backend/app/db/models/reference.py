from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class ReferenceTableMixin:
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )


class Technology(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    ReferenceTableMixin,
    Base,
):
    __tablename__ = "technologies"


class Category(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    ReferenceTableMixin,
    Base,
):
    __tablename__ = "categories"


class FocusArea(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    ReferenceTableMixin,
    Base,
):
    __tablename__ = "focus_areas"


class Platform(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    ReferenceTableMixin,
    Base,
):
    __tablename__ = "platforms"


class Language(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    ReferenceTableMixin,
    Base,
):
    __tablename__ = "languages"


class AccessType(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    ReferenceTableMixin,
    Base,
):
    __tablename__ = "access_types"


class AvailabilityStatus(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    ReferenceTableMixin,
    Base,
):
    __tablename__ = "availability_statuses"


class PhysicalComponent(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    ReferenceTableMixin,
    Base,
):
    __tablename__ = "physical_components"