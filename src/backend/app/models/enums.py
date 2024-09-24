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

from enum import Enum


class StrEnum(str, Enum):
    """Wrapper for string enums, until Python 3.11 upgrade."""

    pass


class IntEnum(int, Enum):
    """Wrapper for string enums, until Python 3.11 upgrade."""

    pass


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


class OrganisationType(IntEnum, Enum):
    """Describes an organisation's subscription type."""

    FREE = 1
    DISCOUNTED = 2
    FULL_FEE = 3


class ProjectStatus(IntEnum, Enum):
    """Enum to describes all possible states of a Mapping Project."""

    ARCHIVED = 0
    PUBLISHED = 1
    DRAFT = 2


class ProjectPriority(IntEnum, Enum):
    """Enum to describe all possible project priority levels."""

    URGENT = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class UserRole(IntEnum, Enum):
    """Available roles assigned to a user site-wide in FMTM.

    Can be used for global user permissions:
        - READ_ONLY = write access blocked (i.e. banned)
        - MAPPER = default for all
        - ADMIN = super admin with access to everything
    """

    READ_ONLY = -1
    MAPPER = 0
    ADMIN = 1


class ProjectRole(IntEnum, Enum):
    """Available roles assigned to a user for a specific project.

    All roles must be assigned by someone higher in the hierarchy:
        - MAPPER = default for all
        - VALIDATOR = can validate the mappers output
        - FIELD_MANAGER = can invite mappers and organise people
        - ASSOCIATE_PROJECT_MANAGER = helps the project manager, cannot delete project
        - PROJECT_MANAGER = has all permissions to manage a project, including delete
    """

    MAPPER = 0
    VALIDATOR = 1
    FIELD_MANAGER = 2
    ASSOCIATE_PROJECT_MANAGER = 3
    PROJECT_MANAGER = 4


class MappingLevel(IntEnum, Enum):
    """The mapping level the mapper has achieved."""

    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3


class TaskStatus(IntEnum, Enum):
    """Enum describing available Task Statuses."""

    READY = 0
    LOCKED_FOR_MAPPING = 1
    MAPPED = 2
    LOCKED_FOR_VALIDATION = 3
    VALIDATED = 4
    INVALIDATED = 5
    BAD = 6  # Task cannot be mapped
    SPLIT = 7  # Task has been split
    ARCHIVED = 8  # When new replacement task has been uploaded


def verify_valid_status_update(old_status: TaskStatus, new_status: TaskStatus):
    """Verify the status update is valid, inferred from previous state."""
    if old_status is TaskStatus.READY:
        return new_status in [
            TaskStatus.LOCKED_FOR_MAPPING,
            TaskStatus.BAD,
            TaskStatus.SPLIT,
        ]
    elif old_status is TaskStatus.LOCKED_FOR_MAPPING:
        return new_status in [
            TaskStatus.READY,
            TaskStatus.MAPPED,
            TaskStatus.BAD,
            TaskStatus.SPLIT,
        ]
    elif old_status is TaskStatus.MAPPED:
        return new_status in [
            TaskStatus.LOCKED_FOR_MAPPING,
            TaskStatus.LOCKED_FOR_VALIDATION,
        ]
    elif old_status is TaskStatus.LOCKED_FOR_VALIDATION:
        return new_status in [TaskStatus.INVALIDATED, TaskStatus.VALIDATED]
    elif old_status is TaskStatus.VALIDATED:
        return new_status == TaskStatus.INVALIDATED
    elif old_status is TaskStatus.INVALIDATED:
        return new_status in [
            TaskStatus.LOCKED_FOR_MAPPING,
            TaskStatus.BAD,
            TaskStatus.SPLIT,
        ]
    elif old_status is TaskStatus.BAD:
        return new_status == TaskStatus.ARCHIVED
    elif old_status is TaskStatus.SPLIT:
        return new_status == TaskStatus.ARCHIVED


class TaskAction(IntEnum, Enum):
    """All possible task actions, recorded in task history."""

    RELEASED_FOR_MAPPING = 0
    LOCKED_FOR_MAPPING = 1
    MARKED_MAPPED = 2
    LOCKED_FOR_VALIDATION = 3
    VALIDATED = 4
    MARKED_INVALID = 5
    MARKED_BAD = 6  # Task cannot be mapped
    SPLIT_NEEDED = 7  # Task needs split
    RECREATED = 8
    COMMENT = 9


def is_status_change_action(task_action):
    """Check if action is a valid status change type."""
    return task_action in [
        TaskAction.RELEASED_FOR_MAPPING,
        TaskAction.LOCKED_FOR_MAPPING,
        TaskAction.MARKED_MAPPED,
        TaskAction.LOCKED_FOR_VALIDATION,
        TaskAction.VALIDATED,
        TaskAction.MARKED_INVALID,
        TaskAction.MARKED_BAD,
        TaskAction.SPLIT_NEEDED,
    ]


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


class TaskType(IntEnum, Enum):
    """Task type."""

    BUILDINGS = 0
    AMENITIES = 1
    OTHER = 2


class ProjectSplitStrategy(IntEnum, Enum):
    """Task splitting type."""

    GRID = 0
    OSM_VECTORS = 1
    OTHER = 2


class BackgroundTaskStatus(IntEnum, Enum):
    """Enum describing fast api background Task Statuses."""

    PENDING = 1
    FAILED = 2
    RECEIVED = 3
    SUCCESS = 4


TILES_SOURCE = ["esri", "bing", "google"]
TILES_FORMATS = ["mbtiles", "sqlitedb", "sqlite3", "sqlite", "pmtiles"]


class TaskSplitType(IntEnum, Enum):
    """Enum describing task splitting type."""

    DIVIDE_ON_SQUARE = 0
    CHOOSE_AREA_AS_TASK = 1
    TASK_SPLITTING_ALGORITHM = 2


class ProjectVisibility(IntEnum, Enum):
    """Enum describing task splitting type."""

    PUBLIC = 0
    PRIVATE = 1
    INVITE_ONLY = 2


class CommunityType(IntEnum, Enum):
    """Enum describing community type."""

    OSM_COMMUNITY = 0
    COMPANY = 1
    NON_PROFIT = 2
    UNIVERSITY = 3
    OTHER = 4


class ReviewStateEnum(StrEnum, Enum):
    """Enum describing review states of submission."""

    hasissues = "hasIssues"
    approved = "approved"
    rejected = "rejected"


class GeometryType(str, Enum):
    """Enum for GeoJSON types."""

    Polygon = "Polygon"
    LineString = "LineString"
    Point = "Point"


class XLSFormType(str, Enum):
    """Enum for XLSForm categories.

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
