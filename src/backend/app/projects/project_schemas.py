# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
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
"""Pydantic schemas for Projects for usage in endpoints."""

from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional, Self
from uuid import UUID

from geojson_pydantic import Feature, FeatureCollection, MultiPolygon, Point, Polygon
from pydantic import (
    BaseModel,
    Field,
    computed_field,
)
from pydantic.functional_serializers import field_serializer
from pydantic.functional_validators import field_validator, model_validator

from app.central.central_schemas import ODKCentralDecrypted, ODKCentralIn
from app.config import decrypt_value, encrypt_value, settings
from app.db.enums import (
    BackgroundTaskStatus,
    ProjectPriority,
)
from app.db.models import DbBackgroundTask, DbBasemap, DbProject, slugify
from app.db.postgis_utils import (
    geojson_to_featcol,
    get_address_from_lat_lon,
    merge_polygons,
    polygon_to_centroid,
    timestamp,
)


class ProjectInBase(DbProject):
    """Base model for project insert / update (validators)."""

    # Override hashtag input to allow a single string input
    hashtags: Annotated[
        Optional[list[str] | str],
        Field(validate_default=True),
    ] = None

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
    odk_credentials: Annotated[
        Optional[ODKCentralDecrypted],
        Field(exclude=True, validate_default=True),
    ] = None

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

    @field_validator("odk_token", mode="after")
    @classmethod
    def encrypt_token(cls, value: str) -> Optional[str]:
        """Encrypt the ODK Token for insertion into the db."""
        if not value:
            return None
        return encrypt_value(value)

    @field_validator("outline", mode="before")
    @classmethod
    def parse_input_geojson(
        cls,
        value: FeatureCollection | Feature | MultiPolygon | Polygon,
    ) -> Optional[Polygon]:
        """Parse any format geojson into a single Polygon.

        NOTE we run this in mode='before' to allow parsing as Feature first.
        """
        if value is None:
            return None
        # FIXME also handle geometry collection type here
        # geojson_pydantic.GeometryCollection
        # FIXME update this to remove the Featcol parsing at some point
        featcol = geojson_to_featcol(value)
        merged = merge_polygons(featcol)
        return merged.get("features")[0].get("geometry")

    @model_validator(mode="after")
    def append_fmtm_hashtag_and_slug(self) -> Self:
        """Append the #FMTM hashtag and add URL slug."""
        # NOTE the slug is set here as the field_validator above
        # does not seem to work?
        self.slug = slugify(self.name)

        if not self.hashtags:
            self.hashtags = ["#FMTM"]
        elif "#FMTM" not in self.hashtags:
            self.hashtags.append("#FMTM")
        return self


class ProjectIn(ProjectInBase, ODKCentralIn):
    """Upload new project."""

    # Mandatory
    xform_category: str
    # Ensure geojson_pydantic.Polygon
    outline: Polygon

    @model_validator(mode="after")
    def generate_location_str(self) -> Self:
        """Generate location string after centroid is generated.

        NOTE we use a model_validator as it's guaranteed to only run once.
        NOTE if we use computed then nominatim is called multiple times,
        NOTE as computed fields cannot wait for a http call async.
        """
        if settings.DEBUG:
            # NOTE we add this to avoid spamming Nominatim during tests
            # Required until https://github.com/hotosm/fmtm/issues/1827
            return self

        centroid = polygon_to_centroid(self.outline.model_dump())
        latitude, longitude = centroid.y, centroid.x
        address = get_address_from_lat_lon(latitude, longitude)
        self.location_str = address if address is not None else ""
        return self


class ProjectUpdate(ProjectInBase, ODKCentralIn):
    """Update a project, where all fields are optional."""

    # Allow updating the name field
    name: Optional[str] = None
    # Override dict type to parse as Polygon
    outline: Optional[Polygon] = None


class ProjectOut(DbProject):
    """Converters for DbProject serialisation & display."""

    # Parse as geojson_pydantic.Polygon
    outline: Polygon
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


class ProjectSummary(BaseModel):
    """Project summaries."""

    id: int
    name: str
    organisation_id: int
    priority: ProjectPriority

    hashtags: Optional[list[str]]
    location_str: Optional[str] = None
    description: Optional[str] = None

    # Calculated
    outline: Optional[Polygon]
    centroid: Optional[Point]
    total_tasks: Optional[int] = None
    num_contributors: Optional[int] = None
    tasks_mapped: Optional[int] = None
    tasks_validated: Optional[int] = None
    tasks_bad: Optional[int] = None


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


class ProjectDashboard(BaseModel):
    """Project details dashboard."""

    slug: str
    organisation_name: str
    total_tasks: int
    created_at: datetime
    organisation_logo: Optional[str] = None
    total_submissions: Optional[int] = None
    total_contributors: Optional[int] = None
    last_active: Optional[str | datetime] = None

    @field_serializer("last_active")
    def get_last_active(self, last_active: Optional[str | datetime]):
        """Date of last activity on project."""
        if last_active is None:
            return None

        current_date = timestamp()
        time_difference = current_date - last_active
        days_difference = time_difference.days

        if days_difference == 0:
            return "today"
        elif days_difference == 1:
            return "yesterday"
        elif days_difference < 7:
            return f'{days_difference} day{"s" if days_difference > 1 else ""} ago'
        else:
            return last_active.strftime("%d %b %Y")


class ProjectUserContributions(BaseModel):
    """Users for a project, plus contribution count."""

    user: str
    contributions: int


class BasemapIn(DbBasemap):
    """Basemap tile creation."""

    # Exclude, as the uuid is generated in the database
    id: Annotated[Optional[UUID], Field(exclude=True)] = None
    project_id: int
    tile_source: str
    url: str
    background_task_id: UUID
    status: BackgroundTaskStatus


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
