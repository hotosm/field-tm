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
"""Schemas and DTOs for ODK Central integration."""

import logging
import re
from dataclasses import dataclass
from typing import Optional, Self, TypedDict

from pydantic import BaseModel
from pydantic.functional_validators import field_validator, model_validator

from app.config import HttpUrlStr, decrypt_value, encrypt_value

log = logging.getLogger(__name__)


# NOTE: These remain as Pydantic models (not DTOs) because they:
# 1. Have complex validation logic (URL normalization, password encryption, etc.)
# 2. Are used as input validation models, not output serialization
# 3. Are used directly as route parameters (Litestar handles Pydantic models natively)


class ODKCentral(BaseModel):
    """ODK Central credentials for API input validation."""

    external_project_instance_url: Optional[HttpUrlStr] = None
    external_project_username: Optional[str] = None
    external_project_password: Optional[str] = None

    @field_validator("external_project_instance_url", mode="after")
    @classmethod
    def remove_trailing_slash(cls, value: HttpUrlStr) -> Optional[HttpUrlStr]:
        """Remove trailing slash from ODK Central URL."""
        if not value:
            return None
        if value.endswith("/"):
            return value[:-1]
        return value

    @model_validator(mode="after")
    def all_odk_vars_together(self) -> Self:
        """Ensure if one ODK variable is set, then all are.

        If all are None/empty, that's allowed (will use default env credentials).
        """
        # Only validate if at least one field is set
        has_any = any(
            [
                self.external_project_instance_url,
                self.external_project_username,
                self.external_project_password,
            ]
        )
        has_all = all(
            [
                self.external_project_instance_url,
                self.external_project_username,
                self.external_project_password,
            ]
        )

        # If any field is set but not all, that's an error
        if has_any and not has_all:
            err = "All ODK details are required together: url, user, password"
            log.debug(err)
            raise ValueError(err)
        return self


class ODKCentralIn(ODKCentral):
    """ODK Central credentials inserted to database."""

    # Map plaintext password input to encrypted field for database
    external_project_password_encrypted: Optional[str] = None

    @field_validator("external_project_password", mode="after")
    @classmethod
    def encrypt_odk_password(cls, value: str) -> Optional[str]:
        """Encrypt the ODK Central password before db insertion."""
        if not value:
            return None
        return encrypt_value(value)

    @model_validator(mode="after")
    def map_password_to_encrypted(self) -> Self:
        """Map encrypted password to the database field name.

        The field_validator already encrypted external_project_password,
        so we copy it to external_project_password_encrypted for the database.
        We set external_project_password to None so it's excluded from DB serialization
        (dump_and_check_model uses exclude_none=True).
        """
        if self.external_project_password:
            # external_project_password is already encrypted by field_validator
            self.external_project_password_encrypted = self.external_project_password
            # Set to None to exclude from DB serialization
            # (only external_project_password_encrypted goes to DB)
            self.external_project_password = None
        return self


class ODKCentralDecrypted(BaseModel):
    """ODK Central credentials extracted from database.

    WARNING never return this as a response model.
    WARNING or log to the terminal.
    """

    external_project_instance_url: Optional[HttpUrlStr] = None
    external_project_username: Optional[str] = None
    external_project_password: Optional[str] = None

    def model_post_init(self, ctx):
        """Run logic after model object instantiated."""
        # Decrypt odk central password from database
        if self.external_project_password:
            if isinstance(self.external_project_password, str):
                encrypted_pass = self.external_project_password
                try:
                    self.external_project_password = decrypt_value(encrypted_pass)
                except Exception as e:
                    # If decryption fails, assume it's already plaintext
                    # This can happen in tests or if password wasn't encrypted
                    # Log the error for debugging but don't fail
                    log.debug(
                        f"Failed to decrypt password (may already be plaintext): {e}"
                    )
                    # Keep the password as-is (assume it's already plaintext)
                    pass

    @field_validator("external_project_instance_url", mode="after")
    @classmethod
    def remove_trailing_slash(cls, value: HttpUrlStr) -> Optional[HttpUrlStr]:
        """Remove trailing slash from ODK Central URL."""
        if not value:
            return None
        if value.endswith("/"):
            return value[:-1]
        return value


@dataclass
class NameTypeMapping:
    """A simple dataclass mapping field name to field type."""

    name: str
    type: str


ENTITY_FIELDS: list[NameTypeMapping] = [
    NameTypeMapping(name="geometry", type="geopoint"),
    NameTypeMapping(name="project_id", type="string"),
    NameTypeMapping(name="task_id", type="string"),
    NameTypeMapping(name="osm_id", type="string"),
    NameTypeMapping(name="tags", type="string"),
    NameTypeMapping(name="version", type="string"),
    NameTypeMapping(name="changeset", type="string"),
    NameTypeMapping(name="timestamp", type="datetime"),
    NameTypeMapping(name="status", type="string"),
    NameTypeMapping(name="created_by", type="string"),
]

RESERVED_KEYS = {
    "name",
    "label",
    "uuid",
}  # Add any other reserved keys of odk central in here as needed
ALLOWED_PROPERTY_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def is_valid_property_name(name: str) -> bool:
    """Check if a property name is valid according to allowed characters pattern."""
    return bool(ALLOWED_PROPERTY_PATTERN.match(name))


def sanitize_key(key: str) -> str:
    """Rename reserved keys to avoid conflicts with ODK Central's schema."""
    if key in RESERVED_KEYS:
        return f"custom_{key}"
    return key


def entity_fields_to_list(properties: list[str]) -> list[str]:
    """Converts a list of Field objects to a list of field names."""
    sanitized_properties = []
    for property in properties:
        if not is_valid_property_name(property):
            log.warning(f"Invalid property name: {property},Excluding from properties.")
            continue
        sanitized_properties.append(sanitize_key(property))
    default_properties = [field.name for field in ENTITY_FIELDS]
    for item in default_properties:
        if item not in sanitized_properties:
            sanitized_properties.append(item)
    return sanitized_properties


# Dynamically generate EntityPropertyDict using ENTITY_FIELDS
def create_entity_property_dict() -> dict[str, type]:
    """Dynamically create a TypedDict using the defined fields."""
    return {field.name: str for field in ENTITY_FIELDS}


EntityPropertyDict = TypedDict("EntityPropertyDict", create_entity_property_dict())


class EntityDict(TypedDict):
    """Dict of Entity label and data."""

    label: str
    data: EntityPropertyDict
