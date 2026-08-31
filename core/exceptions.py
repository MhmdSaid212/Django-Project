"""
Application exceptions.

Keep this list small. Feature apps may add their own errors that inherit
from TourOpsError so views can map them to JSON consistently.
"""


class TourOpsError(Exception):
    """Base error for TourOps business and infrastructure failures."""

    code = "TOUROPS_ERROR"
    http_status = 400

    def __init__(self, message: str, *, code: str | None = None, http_status: int | None = None):
        super().__init__(message)
        if code:
            self.code = code
        if http_status:
            self.http_status = http_status
        self.message = message


class DatabaseUnavailableError(TourOpsError):
    code = "DATABASE_UNAVAILABLE"
    http_status = 503


class NotFoundError(TourOpsError):
    code = "NOT_FOUND"
    http_status = 404


class ValidationError(TourOpsError):
    code = "VALIDATION_ERROR"
    http_status = 400


class PermissionDeniedError(TourOpsError):
    code = "PERMISSION_DENIED"
    http_status = 403


class NotImplementedFeatureError(TourOpsError):
    code = "NOT_IMPLEMENTED"
    http_status = 501
