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
"""Schemas for QFieldCloud integration."""

import logging
from typing import Optional, Self

from pydantic import BaseModel
from pydantic.functional_validators import field_validator, model_validator

from app.config import HttpUrlStr

log = logging.getLogger(__name__)


# NOTE: This remains as a Pydantic model (not a DTO) because it:
# 1. Has complex validation logic (URL normalization, credential validation)
# 2. Is used as an input validation model, not output serialization
# 3. Is used directly as a route parameter (Litestar handles Pydantic models natively)


class QFieldCloud(BaseModel):
    """QField Cloud credentials for API input validation."""

    qfield_cloud_url: Optional[HttpUrlStr] = None
    qfield_cloud_user: Optional[str] = None
    qfield_cloud_password: Optional[str] = None

    @field_validator("qfield_cloud_url", mode="after")
    @classmethod
    def validate_qfc_url(cls, value: HttpUrlStr) -> Optional[HttpUrlStr]:
        """Add trailing slash & ensure API suffix in place.

        Unlike ODK Central, the QFC CLI / SDK requires a trailing slash.
        """
        if not value:
            return None
        # Remove trailing slash
        if value.endswith("/"):
            return value[:-1]
        # Standardise and append /api/v1
        if not value.endswith("/api/v1"):
            value = f"{value}/api/v1"
        # Add trailing slash back on
        return f"{value}/"

    @model_validator(mode="after")
    def all_qfc_vars_together(self) -> Self:
        """Ensure if one QFieldCloud variable is set, then all are."""
        if any(
            [
                self.qfield_cloud_url,
                self.qfield_cloud_user,
                self.qfield_cloud_password,
            ]
        ) and not all(
            [
                self.qfield_cloud_url,
                self.qfield_cloud_user,
                self.qfield_cloud_password,
            ]
        ):
            err = "All QFieldCloud details are required together: url, user, password"
            log.debug(err)
            raise ValueError(err)
        return self
