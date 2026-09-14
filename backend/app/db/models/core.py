"""Core agritech entity models: locations, organisations, developers, applications."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.associations import (
    application_categories,
    application_developers,
    application_focus_areas,
    application_languages,
    application_locations,
    application_physical_components,
    application_platforms,
    application_technologies,
)
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.reference import (
        Category,
        FocusArea,
        Language,
        PhysicalComponent,
        Platform,
        Technology,
    )
    from app.db.models.governance import (
        ApplicationEvidence,
        DataQualityIssue,
        ImportRow,
        VerificationReview,
    )


class Location(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represents a geographic location: country, state, city, etc."""

    __tablename__ = "locations"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    location_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="country, state, region, city, etc.",
    )

    country_code: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
        index=True,
        comment="ISO 3166-1 alpha-2 code",
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("locations.id", ondelete="RESTRICT"),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        server_default="true",
    )

    # Relationships
    parent: Mapped["Location | None"] = relationship(
        "Location",
        remote_side="Location.id",
        backref="children",
        foreign_keys=[parent_id],
    )

    organisations: Mapped[list["Organisation"]] = relationship(
        "Organisation",
        back_populates="headquarters_location",
        foreign_keys="Organisation.headquarters_location_id",
    )

    applications: Mapped[list["Application"]] = relationship(
        "Application",
        secondary=application_locations,
        back_populates="locations",
        passive_deletes=True,
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "latitude >= -90 AND latitude <= 90",
            name="ck_location_latitude_range",
        ),
        CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name="ck_location_longitude_range",
        ),
    )


class Organisation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represents an organisation: startup, company, government, NGO, research institution, etc."""

    __tablename__ = "organisations"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    organisation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="startup, company, government, ngo, research, development, etc.",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    website_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    phone_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    year_founded: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    headquarters_location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
    )

    verification_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="unverified",
        server_default="unverified",
        comment="unverified, verified, rejected, etc.",
    )

    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        server_default="true",
    )

    # Relationships
    headquarters_location: Mapped["Location | None"] = relationship(
        "Location",
        back_populates="organisations",
        foreign_keys=[headquarters_location_id],
    )

    developers: Mapped[list["Developer"]] = relationship(
        "Developer",
        back_populates="organisation",
        foreign_keys="Developer.organisation_id",
    )

    applications: Mapped[list["Application"]] = relationship(
        "Application",
        back_populates="owning_organisation",
        foreign_keys="Application.owning_organisation_id",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "year_founded IS NULL OR (year_founded >= 1900 AND year_founded <= EXTRACT(YEAR FROM NOW()))",
            name="ck_organisation_year_founded_range",
        ),
    )


class Developer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represents an individual developer or development team."""

    __tablename__ = "developers"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    developer_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="individual, team, company, etc.",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    website_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    organisation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organisations.id", ondelete="SET NULL"),
        nullable=True,
    )

    verification_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="unverified",
        server_default="unverified",
        comment="unverified, verified, rejected, etc.",
    )

    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        server_default="true",
    )

    # Relationships
    organisation: Mapped["Organisation | None"] = relationship(
        "Organisation",
        back_populates="developers",
        foreign_keys=[organisation_id],
    )

    applications: Mapped[list["Application"]] = relationship(
        "Application",
        secondary=application_developers,
        back_populates="developers",
        passive_deletes=True,
    )


class Application(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represents an agritech application/solution/product."""

    __tablename__ = "applications"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    summary: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    website_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    launch_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    source_record_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        unique=True,
        index=True,
    )

    record_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="draft",
        server_default="draft",
        index=True,
    )

    owning_organisation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organisations.id", ondelete="SET NULL"),
        nullable=True,
    )

    access_type_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("access_types.id", ondelete="RESTRICT"),
        nullable=True,
    )

    availability_status_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("availability_statuses.id", ondelete="RESTRICT"),
        nullable=True,
    )

    verification_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="unverified",
        server_default="unverified",
        index=True,
        comment="unverified, verified, rejected, etc.",
    )

    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )

    # Relationships
    owning_organisation: Mapped["Organisation | None"] = relationship(
        "Organisation",
        back_populates="applications",
        foreign_keys=[owning_organisation_id],
    )

    developers: Mapped[list["Developer"]] = relationship(
        "Developer",
        secondary=application_developers,
        back_populates="applications",
        passive_deletes=True,
    )

    locations: Mapped[list["Location"]] = relationship(
        "Location",
        secondary=application_locations,
        back_populates="applications",
        passive_deletes=True,
    )

    technologies: Mapped[list["Technology"]] = relationship(
        "Technology",
        secondary=application_technologies,
        back_populates="applications",
        passive_deletes=True,
    )

    platforms: Mapped[list["Platform"]] = relationship(
        "Platform",
        secondary=application_platforms,
        back_populates="applications",
        passive_deletes=True,
    )

    languages: Mapped[list["Language"]] = relationship(
        "Language",
        secondary=application_languages,
        back_populates="applications",
        passive_deletes=True,
    )

    categories: Mapped[list["Category"]] = relationship(
        "Category",
        secondary=application_categories,
        back_populates="applications",
        passive_deletes=True,
    )

    focus_areas: Mapped[list["FocusArea"]] = relationship(
        "FocusArea",
        secondary=application_focus_areas,
        back_populates="applications",
        passive_deletes=True,
    )

    physical_components: Mapped[list["PhysicalComponent"]] = relationship(
        "PhysicalComponent",
        secondary=application_physical_components,
        back_populates="applications",
        passive_deletes=True,
    )

    evidence: Mapped[list["ApplicationEvidence"]] = relationship(
        "ApplicationEvidence",
        back_populates="application",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    verification_reviews: Mapped[list["VerificationReview"]] = relationship(
        "VerificationReview",
        back_populates="application",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    import_rows: Mapped[list["ImportRow"]] = relationship(
        "ImportRow",
        back_populates="application",
        passive_deletes=True,
    )

    quality_issues: Mapped[list["DataQualityIssue"]] = relationship(
        "DataQualityIssue",
        back_populates="application",
        passive_deletes=True,
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "launch_year IS NULL OR (launch_year >= 1900 AND launch_year <= EXTRACT(YEAR FROM NOW()))",
            name="ck_application_launch_year_range",
        ),
    )
