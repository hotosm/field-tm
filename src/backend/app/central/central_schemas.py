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
"""Schemas for returned ODK Central objects."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Self, TypedDict

from geojson_pydantic import Feature, FeatureCollection
from loguru import logger as log
from pydantic import BaseModel, Field, ValidationInfo, computed_field
from pydantic.functional_validators import field_validator, model_validator

from app.config import HttpUrlStr, decrypt_value, encrypt_value
from app.db.enums import EntityState, OdkWebhookEvents


class ODKCentral(BaseModel):
    """ODK Central credentials."""

    odk_central_url: Optional[HttpUrlStr] = None
    odk_central_user: Optional[str] = None
    odk_central_password: Optional[str] = None

    @field_validator("odk_central_url", mode="after")
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
        """Ensure if one ODK variable is set, then all are."""
        if any(
            [
                self.odk_central_url,
                self.odk_central_user,
                self.odk_central_password,
            ]
        ) and not all(
            [
                self.odk_central_url,
                self.odk_central_user,
                self.odk_central_password,
            ]
        ):
            err = "All ODK details are required together: url, user, password"
            log.debug(err)
            raise ValueError(err)
        return self


class ODKCentralIn(ODKCentral):
    """ODK Central credentials inserted to database."""

    @field_validator("odk_central_password", mode="after")
    @classmethod
    def encrypt_odk_password(cls, value: str) -> Optional[str]:
        """Encrypt the ODK Central password before db insertion."""
        if not value:
            return None
        return encrypt_value(value)


class ODKCentralDecrypted(BaseModel):
    """ODK Central credentials extracted from database.

    WARNING never return this as a response model.
    WARNING or log to the terminal.
    """

    odk_central_url: Optional[HttpUrlStr] = None
    odk_central_user: Optional[str] = None
    odk_central_password: Optional[str] = None

    def model_post_init(self, ctx):
        """Run logic after model object instantiated."""
        # Decrypt odk central password from database
        if self.odk_central_password:
            if isinstance(self.odk_central_password, str):
                encrypted_pass = self.odk_central_password
                self.odk_central_password = decrypt_value(encrypted_pass)

    @field_validator("odk_central_url", mode="after")
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
    NameTypeMapping(name="submission_ids", type="string"),
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


class EntityProperties(BaseModel):
    """ODK Entity properties to include in GeoJSON."""

    updatedAt: Optional[str] = Field(exclude=True)  # noqa: N815

    # project_id: Optional[str] = None
    task_id: Optional[str] = None
    osm_id: Optional[str] = None
    tags: Optional[str] = None
    version: Optional[str] = None
    changeset: Optional[str] = None
    timestamp: Optional[str] = None
    status: Optional[str] = None
    created_by: Optional[str] = None

    @computed_field
    @property
    def updated_at(self) -> Optional[str]:
        """Convert updatedAt field to updated_at."""
        return self.updatedAt


class EntityFeature(Feature):
    """ODK Entities as a GeoJSON Feature."""

    properties: EntityProperties


class EntityFeatureCollection(FeatureCollection):
    """ODK Entity Features wrapped in a FeatureCollection."""

    features: list[EntityFeature]


class EntityOsmID(BaseModel):
    """Map of Entity UUID to OSM Feature ID."""

    id: str
    osm_id: Optional[int] = None

    @field_validator("osm_id", mode="before")
    @classmethod
    def convert_osm_id(cls, value):
        """Set osm_id to None if empty or invalid."""
        if value in ("", " ", None, "None"):  # Treat empty strings as None
            return None
        try:
            return int(value)  # Convert to integer if possible
        except ValueError:
            return value


class EntityTaskID(BaseModel):
    """Map of Entity UUID to Field-TM Task ID."""

    id: str
    # Parse as integer
    task_id: Optional[int] = None

    @field_validator("task_id", mode="before")
    @classmethod
    def convert_task_id_to_int(cls, value: str | None):
        """Set task_id to None if empty or invalid."""
        if value in ("", " ", None, "None"):  # Treat empty strings as None
            return None
        try:
            return int(value)  # Convert to integer if possible
        except ValueError:
            return value


class EntityMappingStatus(EntityOsmID, EntityTaskID):
    """The status for mapping an Entity/feature."""

    updatedAt: Optional[str | datetime] = Field(exclude=True)  # noqa: N815
    status: Optional[EntityState] = None
    submission_ids: Optional[str] = None
    geometry: Optional[str] = None
    created_by: Optional[str] = None

    @computed_field
    @property
    def updated_at(self) -> Optional[str | datetime]:
        """Convert updatedAt field to updated_at."""
        if isinstance(self.updatedAt, datetime):
            # In format 2022-01-31T23:59:59.999Z
            return self.updatedAt.isoformat(timespec="milliseconds").replace(
                "+00:00", "Z"
            )
        return self.updatedAt


class EntityMappingStatusIn(BaseModel):
    """Update the mapping status for an Entity."""

    entity_id: str
    status: EntityState
    label: str
    submission_ids: Optional[str] = None

    @field_validator("label", mode="before")
    @classmethod
    def append_status_emoji(cls, value: str, info: ValidationInfo) -> str:
        """Add 🔒 (locked), ✅ (complete) or ❌ (invalid) emojis."""
        status = info.data.get("status", EntityState.READY.value)
        emojis = {
            str(EntityState.OPENED_IN_ODK.value): "🔒",
            str(EntityState.SURVEY_SUBMITTED.value): "✅",
            str(EntityState.MARKED_BAD.value): "❌",
        }

        # Remove any existing emoji at the start of the label
        for emoji in emojis.values():
            if value.startswith(emoji):
                value = value[len(emoji) :].lstrip()
                break

        if status in emojis.keys():
            value = f"{emojis[status]} {value}"

        return value

    @field_validator("status", mode="after")
    @classmethod
    def integer_status_to_string(cls, value: EntityState) -> str:
        """Convert integer status to string for ODK Entity data."""
        return str(value.value)


class OdkCentralWebhookRequest(BaseModel):
    """The POST data from the central webhook service."""

    type: OdkWebhookEvents
    # NOTE we cannot use UUID validation, as Central often passes uuid as 'uuid:xxx-xxx'
    id: str
    # NOTE do not use EntityPropertyDict or similar to allow more flexible parsing
    # submission.create provides an XML string as the 'data'
    data: dict


class OdkEntitiesUpdate(BaseModel):
    """A small base model to update the OdkEntity status field only."""

    status: str  # this must be the str representation of the db enum
    submission_ids: Optional[str] = None
