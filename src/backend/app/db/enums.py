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
"""Enum definitions to translate values into human enum strings."""

from enum import Enum, IntEnum, StrEnum


class ProjectStatus(StrEnum, Enum):
    """All possible states of a Mapping Project."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"
    COMPLETED = "COMPLETED"


class OrganisationType(StrEnum, Enum):
    """An organisation's subscription type."""

    FREE = "FREE"
    DISCOUNTED = "DISCOUNTED"
    FULL_FEE = "FULL_FEE"


class ProjectPriority(StrEnum, Enum):
    """All possible project priority levels."""

    MEDIUM = "MEDIUM"
    LOW = "LOW"
    HIGH = "HIGH"
    URGENT = "URGENT"


class ProjectRole(StrEnum, Enum):
    """Available roles assigned to a user for a specific project.

    Simplified to:
        - MAPPER = default for all contributors
        - PROJECT_ADMIN = per-project admin with full control over that project
    """

    MAPPER = "MAPPER"
    PROJECT_ADMIN = "PROJECT_ADMIN"


class MappingLevel(StrEnum, Enum):
    """The mapping level the mapper has achieved."""

    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class TaskEvent(StrEnum, Enum):
    """Task events via API.

    `MAP` -- Set to *locked for mapping*, i.e. mapping in progress.
    `FINISH` -- Set to *unlocked to validate*, i.e. is mapped.
    `VALIDATE` -- Set to *locked for validation*, i.e. validation in progress.
    `GOOD` -- Set the state to *unlocked done*.
    `BAD` -- Set the state *unlocked to map* again, to be mapped once again.
    `SPLIT` -- Set the state *unlocked done* then generate additional
        subdivided task areas.
    `MERGE` -- Set the state *unlocked done* then generate additional
        merged task area.
    `ASSIGN` -- For a requester user to assign a task to another user.
        Set the state *locked for mapping* passing in the required user id.
        Also notify the user they should map the area.
    `COMMENT` -- Keep the state the same, but simply add a comment.
    """

    MAP = "MAP"
    FINISH = "FINISH"
    VALIDATE = "VALIDATE"
    GOOD = "GOOD"
    BAD = "BAD"
    SPLIT = "SPLIT"
    MERGE = "MERGE"
    ASSIGN = "ASSIGN"
    COMMENT = "COMMENT"
    RESET = "RESET"


class EntityState(IntEnum, Enum):
    """State options for Entities in ODK.

    NOTE here we started with int enums and it's hard to migrate.
    NOTE we will continue to use int values in the form.
    NOTE we keep BAD=6 for legacy reasons too.
    """

    READY = 0
    OPENED_IN_ODK = 1
    SURVEY_SUBMITTED = 2
    VALIDATED = 5
    MARKED_BAD = 6


class TaskSplitType(StrEnum, Enum):
    """Task splitting type for area-splitter."""

    DIVIDE_ON_SQUARE = "DIVIDE_ON_SQUARE"
    CHOOSE_AREA_AS_TASK = "CHOOSE_AREA_AS_TASK"
    TASK_SPLITTING_ALGORITHM = "TASK_SPLITTING_ALGORITHM"


class ProjectVisibility(StrEnum, Enum):
    """Project visibility to end users.

    PUBLIC: All data is publicly available to all authenticated users from UI.

    PRIVATE: The project is not visible to any users until they are invited to the
    project and submissions are only accessible to authenticated users who are
    contributors to the project.
    """

    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class CommunityType(StrEnum, Enum):
    """Community type."""

    OSM_COMMUNITY = "OSM_COMMUNITY"
    COMPANY = "COMPANY"
    NON_PROFIT = "NON_PROFIT"
    UNIVERSITY = "UNIVERSITY"
    OTHER = "OTHER"


class ReviewStateEnum(StrEnum, Enum):
    """Review states of submission.

    NOTE that these values must be camelCase to match what ODK Central requires.
    """

    HASISSUES = "hasIssues"
    APPROVED = "approved"
    REJECTED = "rejected"


class DbGeomType(StrEnum, Enum):
    """Enum in the database, all geom types are in caps."""

    POINT = "POINT"
    POLYGON = "POLYGON"
    POLYLINE = "POLYLINE"


class XLSFormType(StrEnum, Enum):
    """XLSForm categories bundled by default.

    The key is the name of the XLSForm file for internal use.
    This cannot match an existing OSM tag value, so some words are replaced
    (e.g. OSM=healthcare, XLSForm=health).

    The the value is the user facing form name (e.g. healthcare).
    """

    buildings = "OSM Buildings"
    highways = "OSM Highways"
    health = "OSM Healthcare"
    toilets = "OSM Toilets"
    religious = "OSM Religious"
    landusage = "OSM Landuse"
    waterways = "OSM Waterways"
    waterpoints = "OSM Water Points"
    wastedisposal = "OSM Waste Disposal"
    education = "OSM Education"
    cemeteries = "OSM Cemeteries"
    amenities = "OSM Amenities"


class SubmissionDownloadType(StrEnum, Enum):
    """File type to download for ODK submission data."""

    GEOJSON = "geojson"
    JSON = "json"
    CSV = "csv"


class FieldMappingApp(StrEnum, Enum):
    """Downstream field mapping application type."""

    QFIELD = "QField"
    ODK = "ODK"
