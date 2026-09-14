class ApplicationError(Exception):
    status_code = 400
    code = "application_error"

    def __init__(
        self,
        message: str,
        *,
        details: dict | None = None,
    ) -> None:
        self.message = message
        self.details = details
        super().__init__(message)


class ResourceNotFoundError(ApplicationError):
    status_code = 404
    code = "resource_not_found"


class ConflictError(ApplicationError):
    status_code = 409
    code = "resource_conflict"


class ImportValidationError(ApplicationError):
    status_code = 422
    code = "import_validation_failed"
