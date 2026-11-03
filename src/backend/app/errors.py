# Copyright (c) Humanitarian OpenStreetMap Team
#
# This file is part of Field-TM.
#
#     Field-TM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Field-TM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Field-TM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Domain errors raised by services, crud and db code.

Raise these instead of Litestar's HTTPException below the route layer.
Each class carries the status code the route layer responds with, so
handlers can use ``error.status_code`` without a per-type mapping.
"""

from litestar import status_codes as status


class ServiceError(Exception):
    """Base exception for service layer errors."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message: str, code: str = "error"):
        """Initialize with message and error code."""
        self.message = message
        self.code = code
        super().__init__(message)


class ValidationError(ServiceError):
    """Input validation failed."""

    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str):
        """Initialize with message."""
        super().__init__(message, code="validation_error")


class UnprocessableError(ServiceError):
    """Input is well formed but the project is not in a state to process it."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    def __init__(self, message: str):
        """Initialize with message."""
        super().__init__(message, code="unprocessable")


class NotFoundError(ServiceError):
    """Resource not found."""

    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, message: str):
        """Initialize with message."""
        super().__init__(message, code="not_found")


class ConflictError(ServiceError):
    """Resource conflict (e.g. duplicate name)."""

    status_code = status.HTTP_409_CONFLICT

    def __init__(self, message: str):
        """Initialize with message."""
        super().__init__(message, code="conflict")


class UpstreamError(ServiceError):
    """An external service (ODK, QFieldCloud, OAM, raw-data-api) failed."""

    status_code = status.HTTP_502_BAD_GATEWAY

    def __init__(self, message: str):
        """Initialize with message."""
        super().__init__(message, code="upstream_error")


class UpstreamTimeoutError(ServiceError):
    """An external service did not finish in time."""

    status_code = status.HTTP_504_GATEWAY_TIMEOUT

    def __init__(self, message: str):
        """Initialize with message."""
        super().__init__(message, code="upstream_timeout")


class DownstreamDeleteError(ServiceError):
    """Failed to delete downstream project, so local project must be kept."""

    def __init__(self, message: str):
        """Initialize with message."""
        super().__init__(message, code="downstream_delete_failed")
