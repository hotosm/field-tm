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
"""Pydantic schemas for Projects for usage in endpoints."""

from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal, Optional, Self, Union
from uuid import UUID

from geojson_pydantic import (
    Feature,
    FeatureCollection,
    MultiPolygon,
    Point,
    Polygon,
)
from pydantic import (
    BaseModel,
    Field,
    ValidationInfo,
    computed_field,
)
from pydantic.functional_serializers import field_serializer
from pydantic.functional_validators import field_validator, model_validator

from app.central.central_schemas import ODKCentralDecrypted, ODKCentralIn
from app.config import decrypt_value, encrypt_value
from app.db.enums import (
    BackgroundTaskStatus,
    FieldMappingApp,
    ProjectPriority,
    ProjectStatus,
    ProjectVisibility,
)
from app.db.models import (
    DbBackgroundTask,
    DbBasemap,
    DbProject,
    DbProjectTeam,
    slugify,
)
from app.db.postgis_utils import geojson_to_featcol, merge_polygons


class StubProjectIn(BaseModel):
    """Stub project insert."""

    name: str
    field_mapping_app: FieldMappingApp
    short_description: str
    description: Optional[str] = None
    organisation_id: int
    merge: bool = True
    outline: MultiPolygon | Polygon = None
    location_str: Optional[str] = None
    status: Optional[ProjectStatus] = None
    author_sub: Optional[str] = None
    hashtags: Optional[list[str]] = []
    slug: Optional[str] = None
    use_odk_collect: bool = False

    @field_validator("hashtags", mode="before")
    @classmethod
    def validate_hashtags(
        cls,
        hashtags: Optional[str | list[str]],
    ) -> Optional[list[str]]:
        """Validate hashtags.

        - Receives a string and parsed as a list of tags.
        - Commas or semicolons are replaced with spaces before splitting.
        - Add '#' to hashtag if missing.
        """
        if hashtags is None:
            return None

        if isinstance(hashtags, str):
            hashtags = hashtags.replace(",", " ").replace(";", " ")
            hashtags_list = hashtags.split()
        else:
            hashtags_list = hashtags

        # Add '#' to hashtag strings if missing
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
        """Parse any format geojson into a single Polygon or MultiPolygon.

        NOTE we run this in mode='before' to allow parsing as Feature first.
        """
        if value is None:
            return None
        # FIXME also handle geometry collection type here
        # geojson_pydantic.GeometryCollection
        # FIXME update this to remove the Featcol parsing at some point
        featcol = geojson_to_featcol(value)
        merge = info.data.get("merge", True)
        merged_geojson = merge_polygons(
            featcol=featcol, merge=merge, dissolve_polygon=True
        )

        if merge:
            return merged_geojson.get("features")[0].get("geometry")
        else:
            geometries = [
                feature.get("geometry").get("coordinates")
                for feature in merged_geojson.get("features", [])
            ]
            return {"type": "MultiPolygon", "coordinates": geometries}

    @model_validator(mode="after")
    def append_fmtm_hashtag_and_slug(self) -> Self:
        """Append the #Field-TM hashtag and add URL slug."""
        # NOTE the slug is set here as the field_validator above
        # does not seem to work?
        self.slug = slugify(self.name)

        if not self.hashtags:
            self.hashtags = ["#Field-TM"]
        elif "#Field-TM" not in self.hashtags:
            self.hashtags.append("#Field-TM")
        return self


class ProjectInBase(DbProject, StubProjectIn):
    """Base model for project insert / update (validators)."""

    # Override hashtag input to allow a single string input
    hashtags: Annotated[
        Optional[list[str] | str],
        Field(validate_default=True),
    ] = None
    name: Optional[str] = None

    # Exclude (do not allow update)
    id: Annotated[Optional[int], Field(exclude=True)] = None
    outline: Annotated[Optional[dict], Field(exclude=True)] = None
    # Exclude (calculated fields)
    centroid: Annotated[Optional[dict], Field(exclude=True)] = None
    tasks: Annotated[Optional[list], Field(exclude=True)] = None
    organisation_name: Annotated[Optional[str], Field(exclude=True)] = None
    organisation_logo: Annotated[Optional[str], Field(exclude=True)] = None
    bbox: Annotated[Optional[list[float]], Field(exclude=True)] = None
    last_active: Annotated[Optional[datetime], Field(exclude=True)] = None

    # @field_validator("slug", mode="after")
    # @classmethod
    # def set_project_slug(
    #     cls,
    #     value: Optional[str],
    #     info: ValidationInfo,
    # ) -> str:
    #     """Set the slug attribute from the name.

    #     NOTE this is a bit of a hack.
    #     """
    #     if (name := info.data.get("name")) is None:
    #         return None
    #     return name.replace(" ", "_").lower()

    @field_validator("odk_token", mode="after")
    @classmethod
    def encrypt_token(cls, value: str) -> Optional[str]:
        """Encrypt the ODK Token for insertion into the db."""
        if not value:
            return None
        return encrypt_value(value)


class ProjectIn(ProjectInBase, ODKCentralIn):
    """Upload new project."""

    # Ensure geojson_pydantic.Polygon
    outline: Optional[Polygon] = None


class ProjectUpdate(ProjectInBase, ODKCentralIn):
    """Update a project, where all fields are optional."""

    # Allow updating the name field
    name: Optional[str] = None
    # Override dict type to parse as Polygon
    outline: Optional[Polygon] = None


class ProjectOut(DbProject):
    """Converters for DbProject serialisation & display."""

    # Parse as geojson_pydantic.Polygon
    outline: Polygon | MultiPolygon
    # Parse as geojson_pydantic.Point (sometimes not present, e.g. during create)
    centroid: Optional[Point] = None
    bbox: Optional[list[float]] = None
    # Ensure the ODK password is omitted
    odk_central_password: Annotated[Optional[str], Field(exclude=True)] = None
    # We need validate_default to run the validator and set to None
    odk_credentials: Annotated[
        Optional[ODKCentralDecrypted],
        Field(exclude=True, validate_default=True),
    ] = None
    # We shouldn't attempt to serialise the xlsform_content bytes
    xlsform_content: Annotated[Optional[bytes], Field(exclude=True)] = None

    @field_serializer("odk_token")
    def decrypt_token(self, value: str) -> Optional[str]:
        """Decrypt the ODK Token extracted from the db."""
        if not value:
            return None
        return decrypt_value(value)


# Models for specific endpoints


class ProjectOutNoXml(ProjectOut):
    """For reading all projects, it's overly verbose including XML."""

    odk_form_xml: Annotated[Optional[str], Field(exclude=True)] = None


class ProjectSummary(BaseModel):
    """Project summaries."""

    id: int
    name: str
    organisation_id: Optional[int]
    priority: Optional[ProjectPriority]

    hashtags: Optional[list[str]]
    location_str: Optional[str] = None
    short_description: Optional[str] = None
    project_url: Optional[str] = None
    external_project_id: Optional[int] = None
    external_project_instance_url: Optional[str] = None
    status: Optional[ProjectStatus] = None
    visibility: Optional[ProjectVisibility] = None
    field_mapping_app: Optional[FieldMappingApp] = None

    # Calculated
    organisation_logo: Optional[str] = None
    centroid: Optional[Point]
    total_tasks: Optional[int] = 0
    num_contributors: Optional[int] = 0
    total_submissions: Optional[int] = 0
    tasks_mapped: Optional[int] = 0
    tasks_validated: Optional[int] = 0
    tasks_bad: Optional[int] = 0


class PaginationInfo(BaseModel):
    """Pagination JSON return."""

    has_next: bool
    has_prev: bool
    next_num: Optional[int]
    page: int
    pages: int
    prev_num: Optional[int]
    per_page: int
    total: int


class PaginatedProjectSummaries(BaseModel):
    """Project summaries + Pagination info."""

    results: list[ProjectSummary]
    pagination: PaginationInfo


class ProjectUserContributions(BaseModel):
    """A single project contributor and their submission count."""

    user: str
    submissions: int


class BasemapGenerate(BaseModel):
    """Params to generate a new basemap."""

    tile_source: Annotated[
        Literal["esri", "bing", "google", "custom"], Field(default="esri")
    ]
    file_format: Annotated[
        Literal["mbtiles", "sqlitedb", "pmtiles"],
        Field(default="mbtiles"),
    ]
    tms_url: Optional[str] = None


class BasemapIn(DbBasemap):
    """Basemap tile creation."""

    # Exclude, as the uuid is generated in the database
    id: Annotated[Optional[UUID], Field(exclude=True)] = None
    project_id: int
    tile_source: str
    background_task_id: UUID
    status: BackgroundTaskStatus
    # 'url' not set to mandatory, as it can be updated after upload


class BasemapUpdate(DbBasemap):
    """Update a background task."""

    id: Annotated[Optional[int], Field(exclude=True)] = None


class BasemapOut(DbBasemap):
    """Basemap tile list for a project."""

    # project_id not needed as called for a specific project
    project_id: Annotated[Optional[int], Field(exclude=True)] = None

    @computed_field
    @property
    def format(self) -> Optional[str]:
        """Get the basemap format from file extension."""
        if not self.url:
            return None
        return Path(self.url).suffix[1:]

    @computed_field
    @property
    def mimetype(self) -> Optional[str]:
        """Set the mimetype based on the extension."""
        if not self.url:
            return None

        file_format = Path(self.url).suffix[1:]
        if file_format == "mbtiles":
            return "application/vnd.mapbox-vector-tile"
        elif file_format == "pmtiles":
            return "application/vnd.pmtiles"
        else:
            return "application/vnd.sqlite3"


class BackgroundTaskIn(DbBackgroundTask):
    """Insert a background task."""

    # Exclude, as the uuid is generated in the database
    id: Annotated[Optional[UUID], Field(exclude=True)] = None
    # Make related project_id mandatory
    project_id: int


class BackgroundTaskUpdate(DbBackgroundTask):
    """Update a background task."""

    id: Annotated[Optional[int], Field(exclude=True)] = None
    # Make status update mandatory
    status: BackgroundTaskStatus


class BackgroundTaskStatus(BaseModel):
    """Background task status for project related tasks."""

    status: str
    message: Optional[str] = None


class ProjectTeamUser(BaseModel):
    """Single user with name and image for project team."""

    sub: str
    username: str
    profile_img: Optional[str] = None


class ProjectTeam(DbProjectTeam):
    """Project team."""

    users: list[ProjectTeamUser] = []


class ProjectTeamOne(DbProjectTeam):
    """Project team without users."""

    users: list[ProjectTeamUser] = Field(exclude=True)


class ProjectTeamIn(ProjectTeamOne):
    """Create a new project team."""

    # Exclude, as the uuid is generated in the database
    team_id: Annotated[Optional[UUID], Field(exclude=True)] = None
