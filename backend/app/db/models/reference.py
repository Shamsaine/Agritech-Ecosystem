from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.associations import (
    application_categories,
    application_focus_areas,
    application_languages,
    application_physical_components,
    application_platforms,
    application_technologies,
)
from app.db.models.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from app.db.models.core import Application


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

    applications: Mapped[list["Application"]] = relationship(
        "Application",
        secondary=application_technologies,
        back_populates="technologies",
        passive_deletes=True,
    )


class Category(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    ReferenceTableMixin,
    Base,
):
    __tablename__ = "categories"

    applications: Mapped[list["Application"]] = relationship(
        "Application",
        secondary=application_categories,
        back_populates="categories",
        passive_deletes=True,
    )


class FocusArea(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    ReferenceTableMixin,
    Base,
):
    __tablename__ = "focus_areas"

    applications: Mapped[list["Application"]] = relationship(
        "Application",
        secondary=application_focus_areas,
        back_populates="focus_areas",
        passive_deletes=True,
    )


class Platform(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    ReferenceTableMixin,
    Base,
):
    __tablename__ = "platforms"

    applications: Mapped[list["Application"]] = relationship(
        "Application",
        secondary=application_platforms,
        back_populates="platforms",
        passive_deletes=True,
    )


class Language(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    ReferenceTableMixin,
    Base,
):
    __tablename__ = "languages"

    applications: Mapped[list["Application"]] = relationship(
        "Application",
        secondary=application_languages,
        back_populates="languages",
        passive_deletes=True,
    )


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

    applications: Mapped[list["Application"]] = relationship(
        "Application",
        secondary=application_physical_components,
        back_populates="physical_components",
        passive_deletes=True,
    )