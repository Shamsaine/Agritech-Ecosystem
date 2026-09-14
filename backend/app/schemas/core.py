"""Pydantic schemas for core agritech entities."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LocationCreateRequest(BaseModel):
    """Schema for creating a Location."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    location_type: str = Field(..., min_length=1, max_length=50)
    country_code: str = Field(..., min_length=2, max_length=2)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    parent_id: Optional[str] = None
    is_active: bool = Field(default=True)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Ensure slug is lowercase with hyphens only."""
        if not v.islower() or not all(c.isalnum() or c == "-" for c in v):
            raise ValueError("Slug must be lowercase with only alphanumeric characters and hyphens")
        return v


class LocationUpdateRequest(BaseModel):
    """Schema for updating a Location."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    location_type: Optional[str] = Field(None, min_length=1, max_length=50)
    country_code: Optional[str] = Field(None, min_length=2, max_length=2)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    parent_id: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        """Ensure slug is lowercase with hyphens only."""
        if v is None:
            return v
        if not v.islower() or not all(c.isalnum() or c == "-" for c in v):
            raise ValueError("Slug must be lowercase with only alphanumeric characters and hyphens")
        return v


class LocationResponse(LocationCreateRequest):
    """Schema for reading a Location."""

    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganisationCreateRequest(BaseModel):
    """Schema for creating an Organisation."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    organisation_type: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=5000)
    website_url: Optional[str] = Field(None, max_length=500)
    email: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    year_founded: Optional[int] = Field(None, ge=1900)
    headquarters_location_id: Optional[str] = None
    verification_status: str = Field(default="unverified", max_length=50)
    is_active: bool = Field(default=True)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Ensure slug is lowercase with hyphens only."""
        if not v.islower() or not all(c.isalnum() or c == "-" for c in v):
            raise ValueError("Slug must be lowercase with only alphanumeric characters and hyphens")
        return v


class OrganisationUpdateRequest(BaseModel):
    """Schema for updating an Organisation."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    organisation_type: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=5000)
    website_url: Optional[str] = Field(None, max_length=500)
    email: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    year_founded: Optional[int] = Field(None, ge=1900)
    headquarters_location_id: Optional[str] = None
    verification_status: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        """Ensure slug is lowercase with hyphens only."""
        if v is None:
            return v
        if not v.islower() or not all(c.isalnum() or c == "-" for c in v):
            raise ValueError("Slug must be lowercase with only alphanumeric characters and hyphens")
        return v


class OrganisationResponse(OrganisationCreateRequest):
    """Schema for reading an Organisation."""

    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeveloperCreateRequest(BaseModel):
    """Schema for creating a Developer."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    developer_type: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=5000)
    website_url: Optional[str] = Field(None, max_length=500)
    email: Optional[str] = Field(None, max_length=255)
    organisation_id: Optional[str] = None
    verification_status: str = Field(default="unverified", max_length=50)
    is_active: bool = Field(default=True)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Ensure slug is lowercase with hyphens only."""
        if not v.islower() or not all(c.isalnum() or c == "-" for c in v):
            raise ValueError("Slug must be lowercase with only alphanumeric characters and hyphens")
        return v


class DeveloperUpdateRequest(BaseModel):
    """Schema for updating a Developer."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    developer_type: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=5000)
    website_url: Optional[str] = Field(None, max_length=500)
    email: Optional[str] = Field(None, max_length=255)
    organisation_id: Optional[str] = None
    verification_status: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        """Ensure slug is lowercase with hyphens only."""
        if v is None:
            return v
        if not v.islower() or not all(c.isalnum() or c == "-" for c in v):
            raise ValueError("Slug must be lowercase with only alphanumeric characters and hyphens")
        return v


class DeveloperResponse(DeveloperCreateRequest):
    """Schema for reading a Developer."""

    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationCreateRequest(BaseModel):
    """Schema for creating an Application."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    summary: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    website_url: Optional[str] = Field(None, max_length=500)
    launch_year: Optional[int] = Field(None, ge=1900)
    owning_organisation_id: Optional[str] = None
    access_type_id: Optional[str] = None
    availability_status_id: Optional[str] = None
    verification_status: str = Field(default="unverified", max_length=50)
    is_active: bool = Field(default=True)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Ensure slug is lowercase with hyphens only."""
        if not v.islower() or not all(c.isalnum() or c == "-" for c in v):
            raise ValueError("Slug must be lowercase with only alphanumeric characters and hyphens")
        return v


class ApplicationUpdateRequest(BaseModel):
    """Schema for updating an Application."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    summary: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    website_url: Optional[str] = Field(None, max_length=500)
    launch_year: Optional[int] = Field(None, ge=1900)
    owning_organisation_id: Optional[str] = None
    access_type_id: Optional[str] = None
    availability_status_id: Optional[str] = None
    verification_status: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        """Ensure slug is lowercase with hyphens only."""
        if v is None:
            return v
        if not v.islower() or not all(c.isalnum() or c == "-" for c in v):
            raise ValueError("Slug must be lowercase with only alphanumeric characters and hyphens")
        return v


class ApplicationResponse(ApplicationCreateRequest):
    """Schema for reading an Application."""

    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
