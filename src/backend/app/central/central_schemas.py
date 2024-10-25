# Copyright (c) 2023 Humanitarian OpenStreetMap Team
#
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Schemas for returned ODK Central objects."""

from dataclasses import dataclass
from typing import Optional, Self, TypedDict

from geojson_pydantic import Feature, FeatureCollection
from loguru import logger as log
from pydantic import BaseModel, Field, ValidationInfo, computed_field
from pydantic.functional_validators import field_validator, model_validator

from app.config import HttpUrlStr, decrypt_value, encrypt_value
from app.db.enums import EntityStatus


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
]


def entity_fields_to_list() -> list[str]:
    """Converts a list of Field objects to a list of field names."""
    return [field.name for field in ENTITY_FIELDS]


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
        if value in ("", " "):  # Treat empty strings as None
            return None
        try:
            return int(value)  # Convert to integer if possible
        except ValueError:
            return value


class EntityTaskID(BaseModel):
    """Map of Entity UUID to FMTM Task ID."""

    id: str
    task_id: Optional[int] = None

    @field_validator("task_id", mode="before")
    @classmethod
    def convert_task_id(cls, value):
        """Set task_id to None if empty or invalid."""
        if value in ("", " "):  # Treat empty strings as None
            return None
        try:
            return int(value)  # Convert to integer if possible
        except ValueError:
            return value


class EntityMappingStatus(EntityOsmID, EntityTaskID):
    """The status for mapping an Entity/feature."""

    updatedAt: Optional[str] = Field(exclude=True)  # noqa: N815
    status: Optional[EntityStatus] = None

    @computed_field
    @property
    def updated_at(self) -> Optional[str]:
        """Convert updatedAt field to updated_at."""
        return self.updatedAt


class EntityMappingStatusIn(BaseModel):
    """Update the mapping status for an Entity."""

    entity_id: str
    status: EntityStatus
    label: str

    @field_validator("label", mode="before")
    @classmethod
    def append_status_emoji(cls, value: str, info: ValidationInfo) -> str:
        """Add 🔒 (locked), ✅ (complete) or ❌ (invalid) emojis."""
        status = info.data.get("status", EntityStatus.UNLOCKED.value)
        emojis = {
            str(EntityStatus.LOCKED.value): "🔒",
            str(EntityStatus.MAPPED.value): "✅",
            str(EntityStatus.BAD.value): "❌",
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
    def integer_status_to_string(cls, value: EntityStatus) -> str:
        """Convert integer status to string for ODK Entity data."""
        return str(value.value)
