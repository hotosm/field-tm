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

from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator, model_validator

from app.config import HttpUrlStr, decrypt_value, encrypt_value

log = logging.getLogger(__name__)


# NOTE: These remain as Pydantic models (not DTOs) because they:
# 1. Have complex validation logic (URL normalization, password encryption, etc.)
# 2. Are used as input validation models, not output serialization
# 3. Are used directly as route parameters (Litestar handles Pydantic models natively)


class ODKCentral(BaseModel):
    """ODK Central credentials model.

    Handles both input (with encryption) and output (with decryption).
    Use prepare_for_db() to encrypt password before DB insertion.
    Use from_db() class method to decrypt password when reading from DB.
    """

    external_project_instance_url: Optional[HttpUrlStr] = None
    external_project_username: Optional[str] = None
    external_project_password: Optional[str] = None
    # Internal field for encrypted password (used in DB, excluded from serialization)
    password_encrypted: Optional[str] = Field(default=None, exclude=True)

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
        For updates, allow password to be None if password_encrypted exists.
        """
        has_odk_url = bool(self.external_project_instance_url)
        has_odk_user = bool(self.external_project_username)
        has_odk_password = bool(self.external_project_password)
        has_encrypted = bool(self.password_encrypted)

        # If all three are None, that's fine (not updating ODK credentials)
        if not (has_odk_url or has_odk_user or has_odk_password or has_encrypted):
            return self

        # For updates, allow password to be None if encrypted password exists
        if not has_odk_password and has_encrypted:
            return self

        # If password is explicitly provided, require all three together
        if has_odk_password:
            has_all = all([has_odk_url, has_odk_user, has_odk_password])
            if not has_all:
                err = "All ODK details are required together: url, user, password"
                log.debug(err)
                raise ValueError(err)
            return self

        # If password is None but URL/username are provided, allow it (for updates)
        if not has_odk_password and (has_odk_url or has_odk_user):
            return self

        # If any field is set but not all, that's an error (for new projects)
        has_any = any([has_odk_url, has_odk_user, has_odk_password])
        if has_any and not all([has_odk_url, has_odk_user, has_odk_password]):
            err = "All ODK details are required together: url, user, password"
            log.debug(err)
            raise ValueError(err)

        return self

    def prepare_for_db(self) -> dict:
        """Prepare credentials for database insertion (encrypt password).

        Returns a dict with external_project_password_encrypted instead of
        external_project_password. Password field is excluded.
        """
        data = self.model_dump(
            exclude={"external_project_password", "password_encrypted"}
        )

        # Encrypt password if present
        if self.external_project_password:
            data["external_project_password_encrypted"] = encrypt_value(
                self.external_project_password
            )
        elif self.password_encrypted:
            # Keep existing encrypted password if no new password provided
            data["external_project_password_encrypted"] = self.password_encrypted

        return data

    @classmethod
    def from_db(
        cls,
        url: Optional[str] = None,
        username: Optional[str] = None,
        password_encrypted: Optional[str] = None,
    ) -> Optional["ODKCentral"]:
        """Create ODKCentral instance from database fields (decrypt password).

        Args:
            url: ODK Central URL from database
            username: ODK Central username from database
            password_encrypted: Encrypted password from database

        Returns:
            ODKCentral instance with decrypted password, or None if all fields are None
        """
        if not (url or username or password_encrypted):
            return None

        # Decrypt password
        password = None
        if password_encrypted:
            try:
                password = decrypt_value(password_encrypted)
            except Exception as e:
                log.debug(f"Failed to decrypt password (may already be plaintext): {e}")
                # Assume it's already plaintext
                password = password_encrypted

        return cls(
            external_project_instance_url=url,
            external_project_username=username,
            external_project_password=password,
            password_encrypted=password_encrypted,
        )


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
