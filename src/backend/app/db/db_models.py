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
"""SQLAlchemy database models for interacting with Postgresql."""

from datetime import datetime
from typing import cast

from geoalchemy2 import Geometry, WKBElement
from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    LargeBinary,
    SmallInteger,
    String,
    Table,
    UniqueConstraint,
    desc,
)
from sqlalchemy.dialects.postgresql import ARRAY as PostgreSQLArray  # noqa: N811
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import (
    # declarative_base,
    backref,
    object_session,
    relationship,
)

from app.db.database import Base, FmtmMetadata
from app.db.postgis_utils import timestamp
from app.models.enums import (
    BackgroundTaskStatus,
    CommunityType,
    MappingLevel,
    OrganisationType,
    ProjectPriority,
    ProjectRole,
    ProjectStatus,
    ProjectVisibility,
    TaskAction,
    TaskSplitType,
    TaskStatus,
    UserRole,
)


class DbUserRoles(Base):
    """Fine grained user access for projects, described by roles."""

    __tablename__ = "user_roles"

    # Table has composite PK on (user_id and project_id)
    user_id = cast(int, Column(BigInteger, ForeignKey("users.id"), primary_key=True))
    project_id = cast(
        int,
        Column(
            Integer,
            ForeignKey("projects.id"),
            index=True,
            primary_key=True,
        ),
    )
    role = cast(ProjectRole, Column(Enum(ProjectRole), default=ProjectRole.MAPPER))


class DbUser(Base):
    """Describes the history associated with a task."""

    __tablename__ = "users"

    id = cast(int, Column(BigInteger, primary_key=True))
    username = cast(str, Column(String, unique=True))
    profile_img = cast(str, Column(String))
    role = cast(UserRole, Column(Enum(UserRole), default=UserRole.MAPPER))
    project_roles = relationship(
        DbUserRoles, backref="user_roles_link", cascade="all, delete, delete-orphan"
    )

    name = cast(str, Column(String))
    city = cast(str, Column(String))
    country = cast(str, Column(String))
    email_address = cast(str, Column(String))
    is_email_verified = cast(bool, Column(Boolean, default=False))
    is_expert = cast(bool, Column(Boolean, default=False))

    mapping_level = cast(
        MappingLevel,
        Column(
            Enum(MappingLevel),
            default=MappingLevel.BEGINNER,
        ),
    )
    tasks_mapped = cast(int, Column(Integer, default=0))
    tasks_validated = cast(int, Column(Integer, default=0))
    tasks_invalidated = cast(int, Column(Integer, default=0))
    projects_mapped = cast(PostgreSQLArray, Column(ARRAY(Integer)))

    # mentions_notifications = Column(Boolean, default=True, nullable=False)
    # projects_comments_notifications = Column(
    #     Boolean, default=False, nullable=False
    # )
    # projects_notifications = Column(Boolean, default=True, nullable=False)
    # tasks_notifications = Column(Boolean, default=True, nullable=False)
    # tasks_comments_notifications = Column(Boolean, default=False, nullable=False)

    date_registered = cast(datetime, Column(DateTime, default=timestamp))
    # Represents the date the user last had one of their tasks validated
    last_validation_date = cast(datetime, Column(DateTime, default=timestamp))


# Secondary table defining many-to-many relationship between organisations and managers
organisation_managers = Table(
    "organisation_managers",
    FmtmMetadata,
    Column("organisation_id", Integer, ForeignKey("organisations.id"), nullable=False),
    Column("user_id", BigInteger, ForeignKey("users.id"), nullable=False),
    UniqueConstraint("organisation_id", "user_id", name="organisation_user_key"),
)


class DbOrganisation(Base):
    """Describes an Organisation."""

    __tablename__ = "organisations"

    # Columns
    id = cast(int, Column(Integer, primary_key=True))
    name = cast(str, Column(String(512), nullable=False, unique=True))
    slug = cast(str, Column(String(255), nullable=False, unique=True))
    logo = cast(str, Column(String))  # URL of a logo
    description = cast(str, Column(String))
    url = cast(str, Column(String))
    type = cast(
        OrganisationType,
        Column(Enum(OrganisationType), default=OrganisationType.FREE, nullable=False),
    )
    approved = cast(bool, Column(Boolean, default=False))
    created_by = Column(Integer)

    ## Odk central server
    odk_central_url = cast(str, Column(String))
    odk_central_user = cast(str, Column(String))
    odk_central_password = cast(str, Column(String))

    community_type = cast(
        CommunityType,
        Column(
            Enum(CommunityType), default=CommunityType.OSM_COMMUNITY, nullable=False
        ),
    )

    managers = relationship(
        DbUser,
        secondary=organisation_managers,
        backref=backref("organisations", lazy="joined"),
    )


class DbProjectInfo(Base):
    """Contains all project info localized into supported languages."""

    __tablename__ = "project_info"

    project_id = cast(int, Column(Integer, ForeignKey("projects.id"), primary_key=True))
    project_id_str = cast(str, Column(String))
    name = cast(str, Column(String(512)))
    short_description = cast(str, Column(String))
    description = cast(str, Column(String))
    text_searchable = cast(
        TSVECTOR, Column(TSVECTOR)
    )  # This contains searchable text and is populated by a DB Trigger
    per_task_instructions = cast(str, Column(String))

    __table_args__ = (
        Index("textsearch_idx", "text_searchable"),
        {},
    )


class DbXLSForm(Base):
    """XLSForm templates and custom uploads."""

    __tablename__ = "xlsforms"
    id = cast(int, Column(Integer, primary_key=True, autoincrement=True))
    # The XLSForm name is the only unique thing we can use for a key
    # so on conflict update works. Otherwise we get multiple entries.
    title = cast(str, Column(String, unique=True))
    xls = cast(bytes, Column(LargeBinary))


class DbXForm(Base):
    """XForms linked per project.

    TODO eventually we will support multiple forms per project.
    TODO So the category field a stub until then.
    TODO currently it's maintained under projects.xform_category.
    """

    __tablename__ = "xforms"
    id = cast(int, Column(Integer, primary_key=True, autoincrement=True))
    project_id = cast(
        int, Column(Integer, ForeignKey("projects.id"), name="project_id", index=True)
    )
    odk_form_id = cast(str, Column(String))
    category = cast(str, Column(String))


class DbTaskHistory(Base):
    """Describes the history associated with a task."""

    __tablename__ = "task_history"

    id = cast(int, Column(Integer, primary_key=True))
    project_id = cast(int, Column(Integer, ForeignKey("projects.id"), index=True))
    task_id = cast(int, Column(Integer, nullable=False))
    action = cast(TaskAction, Column(Enum(TaskAction), nullable=False))
    action_text = cast(str, Column(String))
    action_date = cast(datetime, Column(DateTime, nullable=False, default=timestamp))
    user_id = cast(
        int,
        Column(
            BigInteger,
            ForeignKey("users.id", name="fk_users"),
            index=True,
            nullable=False,
        ),
    )

    # Define relationships
    user = relationship(DbUser, uselist=False, backref="task_history_user")
    actioned_by = relationship(DbUser, overlaps="task_history_user,user")

    __table_args__ = (
        ForeignKeyConstraint(
            [task_id, project_id], ["tasks.id", "tasks.project_id"], name="fk_tasks"
        ),
        Index("idx_task_history_composite", "task_id", "project_id"),
        Index("idx_task_history_project_id_user_id", "user_id", "project_id"),
        {},
    )


class TaskComment(Base):
    """Represents a comment associated with a task."""

    __tablename__ = "task_comment"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    comment_text = Column(String)
    commented_by = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_users"),
        index=True,
        nullable=False,
    )
    created_at = Column(DateTime, nullable=False, default=timestamp)

    __table_args__ = (
        ForeignKeyConstraint(
            [task_id, project_id], ["tasks.id", "tasks.project_id"], name="fk_tasks"
        ),
        Index("idx_task_comment_composite", "task_id", "project_id"),
        {},
    )


class DbTask(Base):
    """Describes an individual mapping Task."""

    __tablename__ = "tasks"

    # Table has composite PK on (id and project_id)
    id = cast(int, Column(Integer, primary_key=True, autoincrement=True))
    project_id = cast(
        int, Column(Integer, ForeignKey("projects.id"), index=True, primary_key=True)
    )
    project_task_index = cast(int, Column(Integer))
    project_task_name = cast(str, Column(String))
    outline = cast(WKBElement, Column(Geometry("POLYGON", srid=4326)))
    geometry_geojson = cast(str, Column(String))
    feature_count = cast(int, Column(Integer))
    task_status = cast(TaskStatus, Column(Enum(TaskStatus), default=TaskStatus.READY))
    locked_by = cast(
        int,
        Column(BigInteger, ForeignKey("users.id", name="fk_users_locked"), index=True),
    )
    mapped_by = cast(
        int,
        Column(BigInteger, ForeignKey("users.id", name="fk_users_mapper"), index=True),
    )
    validated_by = cast(
        int,
        Column(
            BigInteger, ForeignKey("users.id", name="fk_users_validator"), index=True
        ),
    )

    # Define relationships
    task_history = relationship(
        DbTaskHistory, cascade="all", order_by=desc(DbTaskHistory.action_date)
    )
    lock_holder = relationship(DbUser, foreign_keys=[locked_by])
    mapper = relationship(DbUser, foreign_keys=[mapped_by])

    ## ---------------------------------------------- ##
    # FOR REFERENCE: OTHER ATTRIBUTES IN TASKING MANAGER
    # x = Column(Integer)
    # y = Column(Integer)
    # zoom = Column(Integer)
    # extra_properties = Column(Unicode)
    # # Tasks need to be split differently if created from an arbitrary grid
    # or were clipped to the edge of the AOI
    # is_square = Column(Boolean, default=False)


class DbProject(Base):
    """Describes a HOT Mapping Project."""

    __tablename__ = "projects"

    # Columns
    id = cast(int, Column(Integer, primary_key=True))
    odkid = cast(int, Column(Integer))
    organisation_id = cast(
        int,
        Column(
            Integer,
            ForeignKey("organisations.id", name="fk_organisations"),
            index=True,
        ),
    )
    organisation = relationship(DbOrganisation, backref="projects")

    # PROJECT CREATION
    author_id = cast(
        int,
        Column(
            BigInteger,
            ForeignKey("users.id", name="fk_users"),
            nullable=False,
            server_default="20386219",
        ),
    )
    author = relationship(DbUser, uselist=False, backref="user")
    created = cast(datetime, Column(DateTime, default=timestamp, nullable=False))

    task_split_type = Column(Enum(TaskSplitType), nullable=True)
    # split_strategy = Column(Integer)
    # grid_meters = Column(Integer)
    # task_type = Column(Integer)
    # target_number_of_features = Column(Integer)

    # PROJECT DETAILS
    project_name_prefix = cast(str, Column(String))
    task_type_prefix = cast(str, Column(String))
    project_info = relationship(
        DbProjectInfo,
        cascade="all, delete, delete-orphan",
        uselist=False,
        backref="project",
    )
    location_str = cast(str, Column(String))
    custom_tms_url = cast(str, Column(String))

    # GEOMETRY
    outline = cast(WKBElement, Column(Geometry("POLYGON", srid=4326)))
    # geometry = Column(Geometry("POLYGON", srid=4326, from_text='ST_GeomFromWkt'))
    centroid = cast(WKBElement, Column(Geometry("POINT", srid=4326)))

    # PROJECT STATUS
    last_updated = cast(datetime, Column(DateTime, default=timestamp))
    status = cast(
        ProjectStatus,
        Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False),
    )
    visibility = cast(
        ProjectVisibility,
        Column(
            Enum(ProjectVisibility), default=ProjectVisibility.PUBLIC, nullable=False
        ),
    )
    total_tasks = cast(int, Column(Integer))
    # tasks_mapped = Column(Integer, default=0, nullable=False)
    # tasks_validated = Column(Integer, default=0, nullable=False)
    # tasks_bad_imagery = Column(Integer, default=0, nullable=False)

    # Roles
    roles = relationship(
        DbUserRoles, backref="project_roles_link", cascade="all, delete, delete-orphan"
    )

    # TASKS
    tasks = relationship(
        DbTask, backref="projects", cascade="all, delete, delete-orphan"
    )

    @property
    def tasks_mapped(self):
        """Get the number of tasks mapped for a project."""
        return (
            object_session(self)
            .query(DbTask)
            .filter(DbTask.task_status == TaskStatus.MAPPED)
            .with_parent(self)
            .count()
        )

    @property
    def tasks_validated(self):
        """Get the number of tasks validated for a project."""
        return (
            object_session(self)
            .query(DbTask)
            .filter(DbTask.task_status == TaskStatus.VALIDATED)
            .with_parent(self)
            .count()
        )

    @property
    def tasks_bad(self):
        """Get the number of tasks marked bad for a project."""
        return (
            object_session(self)
            .query(DbTask)
            .filter(DbTask.task_status == TaskStatus.BAD)
            .with_parent(self)
            .count()
        )

    # XForm category specified
    xform_category = cast(str, Column(String))
    # Linked XForms
    forms = relationship(
        DbXForm, backref="project_xform_link", cascade="all, delete, delete-orphan"
    )

    __table_args__ = (
        Index("idx_geometry", outline, postgresql_using="gist"),
        {},
    )

    mapper_level = cast(
        MappingLevel,
        Column(
            Enum(MappingLevel),
            default=MappingLevel.INTERMEDIATE,
            nullable=False,
            index=True,
        ),
    )
    priority = cast(
        ProjectPriority, Column(Enum(ProjectPriority), default=ProjectPriority.MEDIUM)
    )
    featured = cast(
        bool, Column(Boolean, default=False)
    )  # Only admins can set a project as featured
    changeset_comment = cast(str, Column(String))

    # Odk central server
    odk_central_url = cast(str, Column(String))
    odk_central_user = cast(str, Column(String))
    odk_central_password = cast(str, Column(String))
    odk_token = cast(str, Column(String, nullable=True))

    form_xls = cast(
        bytes, Column(LargeBinary)
    )  # XLSForm file if custom xls is uploaded
    form_config_file = cast(
        bytes, Column(LargeBinary)
    )  # Yaml config file if custom xls is uploaded

    data_extract_type = cast(
        str, Column(String)
    )  # Type of data extract (Polygon or Centroid)
    data_extract_url = cast(str, Column(String))
    task_split_type = cast(
        TaskSplitType, Column(Enum(TaskSplitType), nullable=True)
    )  # Options: divide on square, manual upload, task splitting algo
    task_split_dimension = cast(int, Column(SmallInteger, nullable=True))
    task_num_buildings = cast(int, Column(SmallInteger, nullable=True))

    hashtags = cast(list, Column(ARRAY(String)))  # Project hashtag

    # Other Attributes
    imagery = cast(str, Column(String))
    osm_preset = cast(str, Column(String))
    odk_preset = cast(str, Column(String))
    josm_preset = cast(str, Column(String))
    id_presets = cast(list, Column(ARRAY(String)))
    extra_id_params = cast(str, Column(String))

    # GEOMETRY
    # country = Column(ARRAY(String), default=[])

    # FEEDBACK
    osmcha_filter_id = cast(
        str, Column(String)
    )  # Optional custom filter id for filtering on OSMCha
    due_date = cast(datetime, Column(DateTime))


class BackgroundTasks(Base):
    """Table managing long running background tasks."""

    __tablename__ = "background_tasks"

    id = cast(str, Column(String, primary_key=True))
    name = cast(str, Column(String))
    project_id = cast(int, Column(Integer, nullable=True))
    status = cast(
        BackgroundTaskStatus, Column(Enum(BackgroundTaskStatus), nullable=False)
    )
    message = cast(str, Column(String))


class DbTilesPath(Base):
    """Keeping track of mbtile basemaps for a project."""

    __tablename__ = "mbtiles_path"

    id = cast(int, Column(Integer, primary_key=True))
    project_id = cast(int, Column(Integer))
    status = cast(
        BackgroundTaskStatus, Column(Enum(BackgroundTaskStatus), nullable=False)
    )
    path = cast(str, Column(String))
    tile_source = cast(str, Column(String))
    background_task_id = cast(str, Column(String))
    created_at = cast(datetime, Column(DateTime, default=timestamp))


class DbSubmissionPhotos(Base):
    """Keeping track of submission photos for a project."""

    __tablename__ = "submission_photos"

    id = cast(int, Column(Integer, primary_key=True))
    project_id = cast(int, Column(Integer))
    task_id = cast(int, Column(Integer))
    submission_id = cast(str, Column(String))
    s3_path = cast(str, Column(String))
