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
"""DTOs and schemas for project workflows."""

from typing import Annotated, Optional, Self, Union

from area_splitter import SplittingAlgorithm
from geojson_aoi import parse_aoi
from geojson_pydantic import (
    Feature,
    FeatureCollection,
    MultiPolygon,
    Polygon,
)
from pydantic import (
    AliasChoices,
    AwareDatetime,
    BaseModel,
    Field,
    ValidationError,
    ValidationInfo,
)
from pydantic.functional_validators import field_validator, model_validator

from app.central.central_schemas import ODKCentral
from app.config import encrypt_value, settings
from app.db.enums import (
    FieldMappingApp,
    ProjectPriority,
    ProjectStatus,
)
from app.db.models import slugify


class StubProjectIn(BaseModel):
    """Input model for creating a project stub (with validators)."""

    location_str: Optional[str] = None
    slug: Optional[str] = None
    created_by_sub: Optional[str] = None

    project_name: str = Field(validation_alias=AliasChoices("project_name", "name"))
    field_mapping_app: FieldMappingApp
    description: Optional[str] = None
    outline: MultiPolygon | Polygon = None
    status: Optional[ProjectStatus] = None
    hashtags: Optional[list[str]] = []

    @field_validator("hashtags", mode="before")
    @classmethod
    def validate_hashtags(
        cls,
        hashtags: Optional[str | list[str]],
    ) -> Optional[list[str]]:
        """Split tags on spaces, commas, or semicolons and add missing # prefixes."""
        if hashtags is None:
            return None

        if isinstance(hashtags, str):
            hashtags = hashtags.replace(",", " ").replace(";", " ")
            hashtags_list = hashtags.split()
        else:
            hashtags_list = hashtags

        return [
            f"#{hashtag}" if hashtag and not hashtag.startswith("#") else hashtag
            for hashtag in hashtags_list
        ]

    @field_validator("outline", mode="before")
    @classmethod
    def parse_input_geojson(
        cls,
        value: FeatureCollection | Feature | MultiPolygon | Polygon,
        info: ValidationInfo,
    ) -> Optional[Union[Polygon, MultiPolygon]]:
        """Parse GeoJSON into a Polygon or MultiPolygon before field validation."""
        if value is None:
            return None

        geom_type = None
        if isinstance(value, dict):
            geom_type = value.get("type")
            if geom_type == "Feature":
                geom_type = value.get("geometry", {}).get("type")
            elif geom_type == "FeatureCollection":
                features = value.get("features", [])
                if features:
                    geom_type = features[0].get("geometry", {}).get("type")
        elif hasattr(value, "type"):
            geom_type = getattr(value, "type", None)

        if geom_type in ["Point", "MultiPoint", "LineString", "MultiLineString"]:
            raise ValidationError.from_exception_data(
                "ValueError",
                [
                    {
                        "type": "value_error",
                        "loc": ("outline",),
                        "msg": (
                            f"Invalid geometry type: {geom_type}. "
                            "Only Polygon and MultiPolygon are supported."
                        ),
                        "input": value,
                    }
                ],
            )

        input_geojson = value.model_dump() if hasattr(value, "model_dump") else value
        features = parse_aoi(settings.FTM_DB_URL, input_geojson)["features"]

        if len(features) == 1:
            return features[0]["geometry"]
        geometries = [feature["geometry"]["coordinates"] for feature in features]
        return {"type": "MultiPolygon", "coordinates": geometries}

    @model_validator(mode="after")
    def append_ftm_hashtag_and_slug(self) -> Self:
        """Append the #Field-TM hashtag and add URL slug."""
        self.slug = slugify(self.project_name)

        if not self.hashtags:
            self.hashtags = ["#Field-TM"]
        elif "#Field-TM" not in self.hashtags:
            self.hashtags.append("#Field-TM")
        return self


class ProjectInBase(StubProjectIn):
    """Base model for project insert / update (validators)."""

    hashtags: Annotated[
        Optional[list[str] | str],
        Field(validate_default=True),
    ] = None
    project_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("project_name", "name"),
    )
    field_mapping_app: Optional[FieldMappingApp] = None

    # Token used for ODK appuser; encrypted at rest
    odk_token: Optional[str] = None

    external_project_instance_url: Optional[str] = None
    external_project_id: Optional[str | int] = None
    external_project_username: Optional[str] = None
    external_project_password_encrypted: Optional[str] = None

    # Exclude (do not allow update)
    id: Annotated[Optional[int], Field(exclude=True)] = None
    outline: Annotated[Optional[dict], Field(exclude=True)] = None

    @field_validator("odk_token", mode="after")
    @classmethod
    def encrypt_token(cls, value: str) -> Optional[str]:
        """Encrypt the ODK Token for insertion into the db."""
        if not value:
            return None
        return encrypt_value(value)


class ProjectIn(ProjectInBase, ODKCentral):
    """Input model for creating a project in ODK Central."""

    outline: Optional[Polygon] = None

    task_split_type: Optional[SplittingAlgorithm] = None
    priority: Optional[ProjectPriority] = None

    @property
    def odk_credentials(self) -> Optional[ODKCentral]:
        """Return project ODK credentials, or None to use deployment defaults."""
        if (
            not self.external_project_instance_url
            and not self.external_project_username
            and not self.external_project_password
        ):
            return None

        return ODKCentral(
            external_project_instance_url=self.external_project_instance_url,
            external_project_username=self.external_project_username,
            external_project_password=self.external_project_password,
        )


class ProjectUpdate(ProjectInBase, ODKCentral):
    """Input model for updating a project (all fields optional)."""

    # The field mapping app should not be updatable
    field_mapping_app: Annotated[Optional[FieldMappingApp], Field(exclude=True)] = None

    project_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("project_name", "name"),
    )
    outline: Optional[Polygon] = None

    task_split_type: Optional[SplittingAlgorithm] = None
    priority: Optional[ProjectPriority] = None

    xlsform_content: Optional[bytes] = None
    data_extract_geojson: Optional[dict] = None
    task_areas_geojson: Optional[dict] = None
    tasks_synced_hash: Optional[str] = None

    # Offline basemap workflow state
    basemap_stac_item_id: Optional[str] = None
    basemap_url: Optional[str] = None
    basemap_status: Optional[str] = None
    basemap_minzoom: Optional[int] = None
    basemap_maxzoom: Optional[int] = None
    basemap_attach_status: Optional[str] = None
    basemap_attach_error: Optional[str] = None
    basemap_attach_updated_at: Optional[AwareDatetime] = None

    # Async creation workflow state
    creation_status: Optional[str] = None
    creation_error: Optional[str] = None
    creation_updated_at: Optional[AwareDatetime] = None
