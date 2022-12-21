# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
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

from enum import Enum

class TeamVisibility(Enum):
    """ Describes the visibility associated with an Team """

    PUBLIC = 0
    PRIVATE = 1

class OrganisationType(Enum):
    """ Describes an organisation's subscription type """

    FREE = 1
    DISCOUNTED = 2
    FULL_FEE = 3

class ProjectStatus(Enum):
    """ Enum to describes all possible states of a Mapping Project """

    ARCHIVED = 0
    PUBLISHED = 1
    DRAFT = 2

class ProjectPriority(Enum):
    """ Enum to describe all possible project priority levels """

    URGENT = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3

class UserRole(Enum):
    """ Describes the role a user can be assigned, app doesn't support multiple roles """

    READ_ONLY = -1
    MAPPER = 0
    ADMIN = 1

class MappingLevel(Enum):
    """ The mapping level the mapper has achieved """

    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3

class MappingPermission(Enum):
    """ Describes a set of permissions for mapping on a project """

    ANY = 0
    LEVEL = 1
    TEAMS = 2
    TEAMS_LEVEL = 3


class ValidationPermission(Enum):
    """ Describes a set of permissions for validating on a project """

    ANY = 0
    LEVEL = 1
    TEAMS = 2
    TEAMS_LEVEL = 3

class TaskCreationMode(Enum):
    """ Enum to describe task creation mode """

    GRID = 0
    ROADS = 1
    UPLOAD = 2

class TaskAction(Enum):
    """Describes the possible actions that can happen to to a task, that we'll record history for"""

    LOCKED_FOR_MAPPING = 1
    LOCKED_FOR_VALIDATION = 2
    STATE_CHANGE = 3
    COMMENT = 4
    AUTO_UNLOCKED_FOR_MAPPING = 5
    AUTO_UNLOCKED_FOR_VALIDATION = 6

class TaskStatus(Enum):
    """ Enum describing available Task Statuses """

    READY = 0
    LOCKED_FOR_MAPPING = 1
    MAPPED = 2
    LOCKED_FOR_VALIDATION = 3
    VALIDATED = 4
    INVALIDATED = 5
    BAD = 6  # Task cannot be mapped 
    SPLIT = 7  # Task has been split

class TaskType(Enum):
    BUILDINGS = 0
    AMENITIES = 1
    OTHER = 2

class ProjectSplitStrategy(Enum):
    GRID = 0
    OSM_VECTORS = 1
    OTHER = 2