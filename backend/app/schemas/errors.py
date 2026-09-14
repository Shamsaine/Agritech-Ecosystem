from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class ValidationErrorItem(BaseModel):
    field: str
    message: str
    error_type: str


class ValidationErrorResponse(BaseModel):
    error: ErrorDetail
    validation_errors: list[ValidationErrorItem] = Field(default_factory=list)
