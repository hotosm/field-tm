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
"""Enum definitions to translate values into human enum strings."""

from enum import Enum, IntEnum, StrEnum

TILES_SOURCE = ["esri", "bing", "google"]
TILES_FORMATS = ["mbtiles", "sqlitedb", "pmtiles"]


class HTTPStatus(IntEnum):
    """All HTTP status codes used in endpoints."""

    # Success
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204

    # Client Error
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422

    # Server Error
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501


class ProjectStatus(StrEnum, Enum):
    """All possible states of a Mapping Project."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


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


class UserRole(StrEnum, Enum):
    """Available roles assigned to a user site-wide in FMTM.

    Can be used for global user permissions:
        - READ_ONLY = write access blocked (i.e. banned)
        - MAPPER = default for all
        - ADMIN = super admin with access to everything
    """

    READ_ONLY = "READ_ONLY"
    MAPPER = "MAPPER"
    ADMIN = "ADMIN"


class ProjectRole(StrEnum, Enum):
    """Available roles assigned to a user for a specific project.

    All roles must be assigned by someone higher in the hierarchy:
        - MAPPER = default for all
        - VALIDATOR = can validate the mappers output
        - FIELD_MANAGER = can invite mappers and organise people
        - ASSOCIATE_PROJECT_MANAGER = helps the project manager, cannot delete project
        - PROJECT_MANAGER = has all permissions to manage a project, including delete
    """

    MAPPER = "MAPPER"
    VALIDATOR = "VALIDATOR"
    FIELD_MANAGER = "FIELD_MANAGER"
    ASSOCIATE_PROJECT_MANAGER = "ASSOCIATE_PROJECT_MANAGER"
    PROJECT_MANAGER = "PROJECT_MANAGER"


class MappingLevel(StrEnum, Enum):
    """The mapping level the mapper has achieved."""

    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class TaskStatus(StrEnum, Enum):
    """Available Task Statuses."""

    READY = "READY"
    LOCKED_FOR_MAPPING = "LOCKED_FOR_MAPPING"
    MAPPED = "MAPPED"
    LOCKED_FOR_VALIDATION = "LOCKED_FOR_VALIDATION"
    VALIDATED = "VALIDATED"
    INVALIDATED = "INVALIDATED"
    BAD = "BAD"  # Task cannot be mapped
    SPLIT = "SPLIT"  # Task has been split
    ARCHIVED = "ARCHIVED"  # When renew replacement task has been uploaded


class TaskAction(StrEnum, Enum):
    """All possible task actions, recorded in task history."""

    RELEASED_FOR_MAPPING = "RELEASED_FOR_MAPPING"
    LOCKED_FOR_MAPPING = "LOCKED_FOR_MAPPING"
    MARKED_MAPPED = "MARKED_MAPPED"
    LOCKED_FOR_VALIDATION = "LOCKED_FOR_VALIDATION"
    VALIDATED = "VALIDATED"
    MARKED_INVALID = "MARKED_INVALID"
    MARKED_BAD = "MARKED_BAD"  # Task cannot be mapped
    SPLIT_NEEDED = "SPLIT_NEEDED"  # Task needs split
    RECREATED = "RECREATED"
    COMMENT = "COMMENT"


class EntityStatus(IntEnum, Enum):
    """Statuses for Entities in ODK.

    NOTE here we started with int enums and it's hard to migrate.
    NOTE we will continue to use int values in the form.
    """

    UNLOCKED = 0
    LOCKED = 1
    MAPPED = 2
    BAD = 6
    # Should we also add extra statuses?
    # LUMPED
    # SPLIT
    # VALIDATED
    # INVALIDATED


class TaskType(StrEnum, Enum):
    """Task type."""

    BUILDINGS = "BUILDINGS"
    AMENITIES = "AMENITIES"
    OTHER = "OTHER"


class ProjectSplitStrategy(StrEnum, Enum):
    """Task splitting type."""

    GRID = "GRID"
    OSM_VECTORS = "OSM_VECTORS"
    OTHER = "OTHER"


class BackgroundTaskStatus(StrEnum, Enum):
    """FastAPI background Task Statuses."""

    PENDING = "PENDING"
    FAILED = "FAILED"
    RECEIVED = "RECEIVED"
    SUCCESS = "SUCCESS"


class TaskSplitType(StrEnum, Enum):
    """Task splitting type for fmtm-splitter."""

    DIVIDE_ON_SQUARE = "DIVIDE_ON_SQUARE"
    CHOOSE_AREA_AS_TASK = "CHOOSE_AREA_AS_TASK"
    TASK_SPLITTING_ALGORITHM = "TASK_SPLITTING_ALGORITHM"


class ProjectVisibility(StrEnum, Enum):
    """Project visibility to end users."""

    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    INVITE_ONLY = "INVITE_ONLY"


class CommunityType(StrEnum, Enum):
    """Community type."""

    OSM_COMMUNITY = "OSM_COMMUNITY"
    COMPANY = "COMPANY"
    NON_PROFIT = "NON_PROFIT"
    UNIVERSITY = "UNIVERSITY"
    OTHER = "OTHER"


class ReviewStateEnum(StrEnum, Enum):
    """Review states of submission."""

    HASISSUES = "HASISSUES"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class GeometryType(StrEnum, Enum):
    """GeoJSON geometry types."""

    Polygon = "Polygon"
    LineString = "LineString"
    Point = "Point"


class XLSFormType(StrEnum, Enum):
    """XLSForm categories bundled by default.

    The key is the name of the XLSForm file for internal use.
    This cannot match an existing OSM tag value, so some words are replaced
    (e.g. OSM=healthcare, XLSForm=health).

    The the value is the user facing form name (e.g. healthcare).
    """

    buildings = "buildings"
    # highways = "highways"
    health = "healthcare"
    # toilets = "toilets"
    # religious = "religious"
    # landusage = "landusage"
    # waterways = "waterways"


def get_action_for_status_change(task_status: TaskStatus) -> TaskAction:
    """Update task action inferred from previous state."""
    match task_status:
        case TaskStatus.READY:
            return TaskAction.RELEASED_FOR_MAPPING
        case TaskStatus.LOCKED_FOR_MAPPING:
            return TaskAction.LOCKED_FOR_MAPPING
        case TaskStatus.MAPPED:
            return TaskAction.MARKED_MAPPED
        case TaskStatus.LOCKED_FOR_VALIDATION:
            return TaskAction.LOCKED_FOR_VALIDATION
        case TaskStatus.VALIDATED:
            return TaskAction.VALIDATED
        case TaskStatus.BAD:
            return TaskAction.MARKED_BAD
        case TaskStatus.SPLIT:
            return TaskAction.SPLIT_NEEDED
        case TaskStatus.INVALIDATED:
            return TaskAction.MARKED_INVALID
        case _:
            return TaskAction.RELEASED_FOR_MAPPING


def get_status_for_action(task_action: TaskAction) -> TaskStatus:
    """Get the task status inferred from the action."""
    match task_action:
        case TaskAction.RELEASED_FOR_MAPPING:
            return TaskStatus.READY
        case TaskAction.LOCKED_FOR_MAPPING:
            return TaskStatus.LOCKED_FOR_MAPPING
        case TaskAction.MARKED_MAPPED:
            return TaskStatus.MAPPED
        case TaskAction.LOCKED_FOR_VALIDATION:
            return TaskStatus.LOCKED_FOR_VALIDATION
        case TaskAction.VALIDATED:
            return TaskStatus.VALIDATED
        case TaskAction.MARKED_BAD:
            return TaskStatus.BAD
        case TaskAction.SPLIT_NEEDED:
            return TaskStatus.SPLIT
        case TaskAction.MARKED_INVALID:
            return TaskStatus.INVALIDATED
        case _:
            return TaskStatus.READY
