from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PaginationMeta


class RelatedEntitySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str


class OrganisationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    organisation_type: str | None = None
    verification_status: str


class ApplicationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_record_id: str | None = None
    name: str
    slug: str
    summary: str | None = None
    website_url: str | None = None
    launch_year: int | None = None
    verification_status: str
    record_status: str
    owning_organisation: OrganisationSummary | None = None


class ApplicationDetail(ApplicationListItem):
    description: str | None = None
    technologies: list[RelatedEntitySummary] = Field(default_factory=list)
    categories: list[RelatedEntitySummary] = Field(default_factory=list)
    focus_areas: list[RelatedEntitySummary] = Field(default_factory=list)
    platforms: list[RelatedEntitySummary] = Field(default_factory=list)
    languages: list[RelatedEntitySummary] = Field(default_factory=list)
    physical_components: list[RelatedEntitySummary] = Field(default_factory=list)
    locations: list[RelatedEntitySummary] = Field(default_factory=list)
    developers: list[RelatedEntitySummary] = Field(default_factory=list)


class PaginatedApplications(BaseModel):
    items: list[ApplicationListItem]
    pagination: PaginationMeta
