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

from geoalchemy2 import Geometry
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
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import (  # , declarative_base  # , declarative_base
    backref,
    object_session,
    relationship,
)

from app.models.enums import (
    BackgroundTaskStatus,
    MappingLevel,
    MappingPermission,
    OrganisationType,
    ProjectPriority,
    ProjectStatus,
    TaskAction,
    TaskCreationMode,
    TaskSplitType,
    TaskStatus,
    TeamVisibility,
    UserRole,
    ValidationPermission,
)

from .database import Base, FmtmMetadata
from .postgis_utils import timestamp


class DbUser(Base):
    """Describes the history associated with a task."""

    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String, unique=True)
    role = Column(Enum(UserRole), default=UserRole.MAPPER)

    name = Column(String)
    city = Column(String)
    country = Column(String)
    email_address = Column(String)
    is_email_verified = Column(Boolean, default=False)
    is_expert = Column(Boolean, default=False)

    mapping_level = Column(
        Enum(MappingLevel),
        default=MappingLevel.BEGINNER,
    )
    tasks_mapped = Column(Integer, default=0)
    tasks_validated = Column(Integer, default=0)
    tasks_invalidated = Column(Integer, default=0)
    projects_mapped = Column(ARRAY(Integer))

    # mentions_notifications = Column(Boolean, default=True, nullable=False)
    # projects_comments_notifications = Column(
    #     Boolean, default=False, nullable=False
    # )
    # projects_notifications = Column(Boolean, default=True, nullable=False)
    # tasks_notifications = Column(Boolean, default=True, nullable=False)
    # tasks_comments_notifications = Column(Boolean, default=False, nullable=False)
    # teams_announcement_notifications = Column(
    #     Boolean, default=True, nullable=False
    # )

    date_registered = Column(DateTime, default=timestamp)
    # Represents the date the user last had one of their tasks validated
    last_validation_date = Column(DateTime, default=timestamp)


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
    id = Column(Integer, primary_key=True)
    name = Column(String(512), nullable=False, unique=True)
    slug = Column(String(255), nullable=False, unique=True)
    logo = Column(String)  # URL of a logo
    description = Column(String)
    url = Column(String)
    type = Column(Enum(OrganisationType), default=OrganisationType.FREE, nullable=False)
    # subscription_tier = Column(Integer)

    managers = relationship(
        DbUser,
        secondary=organisation_managers,
        backref=backref("organisations", lazy="joined"),
    )


class DbTeam(Base):
    """Describes a team."""

    __tablename__ = "teams"

    # Columns
    id = Column(Integer, primary_key=True)
    organisation_id = Column(
        Integer,
        ForeignKey("organisations.id", name="fk_organisations"),
        nullable=False,
    )
    name = Column(String(512), nullable=False)
    logo = Column(String)  # URL of a logo
    description = Column(String)
    invite_only = Column(Boolean, default=False, nullable=False)
    visibility = Column(
        Enum(TeamVisibility), default=TeamVisibility.PUBLIC, nullable=False
    )
    organisation = relationship(DbOrganisation, backref="teams")


# Secondary table defining many-to-many join for
# private projects that only defined users can map on
project_allowed_users = Table(
    "project_allowed_users",
    FmtmMetadata,
    Column("project_id", Integer, ForeignKey("projects.id")),
    Column("user_id", BigInteger, ForeignKey("users.id")),
)


class DbProjectTeams(Base):
    """Link table between teams and projects."""

    __tablename__ = "project_teams"
    team_id = Column(Integer, ForeignKey("teams.id"), primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    role = Column(Integer, nullable=False)

    project = relationship(
        "DbProject", backref=backref("teams", cascade="all, delete-orphan")
    )
    team = relationship(
        DbTeam, backref=backref("projects", cascade="all, delete-orphan")
    )


class DbProjectInfo(Base):
    """Contains all project info localized into supported languages."""

    __tablename__ = "project_info"

    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    project_id_str = Column(String)
    name = Column(String(512))
    short_description = Column(String)
    description = Column(String)
    text_searchable = Column(
        TSVECTOR
    )  # This contains searchable text and is populated by a DB Trigger
    per_task_instructions = Column(String)

    __table_args__ = (
        Index("textsearch_idx", "text_searchable"),
        {},
    )


class DbProjectChat(Base):
    """Contains all project info localized into supported languages."""

    __tablename__ = "project_chat"
    id = Column(BigInteger, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    time_stamp = Column(DateTime, nullable=False, default=timestamp)
    message = Column(String, nullable=False)

    # Relationships
    posted_by = relationship(DbUser, foreign_keys=[user_id])


class DbXForm(Base):
    """Xform templates and custom uploads."""

    __tablename__ = "xlsforms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    # The XLSForm name is the only unique thing we can use for a key
    # so on conflict update works. Otherwise we get multiple entries.
    title = Column(String, unique=True)
    category = Column(String)
    description = Column(String)
    xml = Column(String)  # Internal form representation
    xls = Column(LargeBinary)  # Human readable representation


class DbTaskInvalidationHistory(Base):
    """Information on task invalidation.

    Describes the most recent history of task invalidation and subsequent validation.
    """

    __tablename__ = "task_invalidation_history"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    task_id = Column(Integer, nullable=False)
    is_closed = Column(Boolean, default=False)
    mapper_id = Column(BigInteger, ForeignKey("users.id", name="fk_mappers"))
    mapped_date = Column(DateTime)
    invalidator_id = Column(BigInteger, ForeignKey("users.id", name="fk_invalidators"))
    invalidated_date = Column(DateTime)
    invalidation_history_id = Column(
        Integer, ForeignKey("task_history.id", name="fk_invalidation_history")
    )
    validator_id = Column(BigInteger, ForeignKey("users.id", name="fk_validators"))
    validated_date = Column(DateTime)
    updated_date = Column(DateTime, default=timestamp)

    __table_args__ = (
        ForeignKeyConstraint(
            [task_id, project_id], ["tasks.id", "tasks.project_id"], name="fk_tasks"
        ),
        Index("idx_task_validation_history_composite", "task_id", "project_id"),
        Index(
            "idx_task_validation_validator_status_composite",
            "invalidator_id",
            "is_closed",
        ),
        Index("idx_task_validation_mapper_status_composite", "mapper_id", "is_closed"),
        {},
    )


class DbTaskMappingIssue(Base):
    """Describes mapping issues.

    An issue (along with an occurrence count) with a
    task mapping that contributed to invalidation of the task.
    """

    __tablename__ = "task_mapping_issues"
    id = Column(Integer, primary_key=True)
    task_history_id = Column(
        Integer, ForeignKey("task_history.id"), nullable=False, index=True
    )
    issue = Column(String, nullable=False)
    mapping_issue_category_id = Column(
        Integer,
        ForeignKey("mapping_issue_categories.id", name="fk_issue_category"),
        nullable=False,
    )
    count = Column(Integer, nullable=False)


class DbMappingIssueCategory(Base):
    """Represents a category of task mapping issues identified during validaton."""

    __tablename__ = "mapping_issue_categories"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    archived = Column(Boolean, default=False, nullable=False)


class DbTaskHistory(Base):
    """Describes the history associated with a task."""

    __tablename__ = "task_history"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    task_id = Column(Integer, nullable=False)
    action = Column(Enum(TaskAction), nullable=False)
    action_text = Column(String)
    action_date = Column(DateTime, nullable=False, default=timestamp)
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_users"),
        index=True,
        nullable=False,
    )
    invalidation_history = relationship(
        DbTaskInvalidationHistory, lazy="dynamic", cascade="all"
    )

    actioned_by = relationship(DbUser)
    task_mapping_issues = relationship(DbTaskMappingIssue, cascade="all")

    __table_args__ = (
        ForeignKeyConstraint(
            [task_id, project_id], ["tasks.id", "tasks.project_id"], name="fk_tasks"
        ),
        Index("idx_task_history_composite", "task_id", "project_id"),
        Index("idx_task_history_project_id_user_id", "user_id", "project_id"),
        {},
    )


class DbQrCode(Base):
    """QR Code."""

    __tablename__ = "qr_code"

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    image = Column(LargeBinary)


class DbTask(Base):
    """Describes an individual mapping Task."""

    __tablename__ = "tasks"

    # Table has composite PK on (id and project_id)
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), index=True, primary_key=True
    )
    project_task_index = Column(Integer)
    project_task_name = Column(String)
    outline = Column(Geometry("POLYGON", srid=4326))
    geometry_geojson = Column(String)
    initial_feature_count = Column(Integer)
    task_status = Column(Enum(TaskStatus), default=TaskStatus.READY)
    locked_by = Column(
        BigInteger, ForeignKey("users.id", name="fk_users_locked"), index=True
    )
    mapped_by = Column(
        BigInteger, ForeignKey("users.id", name="fk_users_mapper"), index=True
    )
    validated_by = Column(
        BigInteger, ForeignKey("users.id", name="fk_users_validator"), index=True
    )

    # Mapped objects
    qr_code_id = Column(Integer, ForeignKey("qr_code.id"), index=True)
    qr_code = relationship(
        DbQrCode, cascade="all, delete, delete-orphan", single_parent=True
    )

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
    id = Column(Integer, primary_key=True)
    odkid = Column(Integer)

    # PROJECT CREATION
    author_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_users"),
        nullable=False,
        server_default="20386219",
    )
    author = relationship(DbUser)
    created = Column(DateTime, default=timestamp, nullable=False)
    task_creation_mode = Column(
        Enum(TaskCreationMode), default=TaskCreationMode.UPLOAD, nullable=False
    )
    # split_strategy = Column(Integer)
    # grid_meters = Column(Integer)
    # task_type = Column(Integer)
    # target_number_of_features = Column(Integer)

    # PROJECT DETAILS
    project_name_prefix = Column(String)
    task_type_prefix = Column(String)
    project_info = relationship(
        DbProjectInfo, cascade="all, delete, delete-orphan", backref="project"
    )
    location_str = Column(String)

    # GEOMETRY
    outline = Column(Geometry("POLYGON", srid=4326))
    # geometry = Column(Geometry("POLYGON", srid=4326, from_text='ST_GeomFromWkt'))

    # PROJECT STATUS
    last_updated = Column(DateTime, default=timestamp)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False)
    total_tasks = Column(Integer)
    # tasks_mapped = Column(Integer, default=0, nullable=False)
    # tasks_validated = Column(Integer, default=0, nullable=False)
    # tasks_bad_imagery = Column(Integer, default=0, nullable=False)

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

    # XFORM DETAILS
    odk_central_src = Column(String, default="")  # TODO Add HOTs as default
    xform_title = Column(String, ForeignKey("xlsforms.title", name="fk_xform"))
    xform = relationship(DbXForm)

    __table_args__ = (
        Index("idx_geometry", outline, postgresql_using="gist"),
        {},
    )

    ## ---------------------------------------------- ##
    # FOR REFERENCE: OTHER ATTRIBUTES IN TASKING MANAGER
    # PROJECT ACCESS
    private = Column(Boolean, default=False)  # Only allowed users can validate
    mapper_level = Column(
        Enum(MappingLevel),
        default=MappingLevel.INTERMEDIATE,
        nullable=False,
        index=True,
    )  # Mapper level project is suitable for
    priority = Column(Enum(ProjectPriority), default=ProjectPriority.MEDIUM)
    featured = Column(
        Boolean, default=False
    )  # Only admins can set a project as featured
    mapping_permission = Column(Enum(MappingPermission), default=MappingPermission.ANY)
    validation_permission = Column(
        Enum(ValidationPermission), default=ValidationPermission.LEVEL
    )  # Means only users with validator role can validate
    allowed_users = relationship(DbUser, secondary=project_allowed_users)
    organisation_id = Column(
        Integer,
        ForeignKey("organisations.id", name="fk_organisations"),
        index=True,
    )
    organisation = relationship(DbOrganisation, backref="projects")
    # PROJECT DETAILS
    due_date = Column(DateTime)
    changeset_comment = Column(String)
    osmcha_filter_id = Column(
        String
    )  # Optional custom filter id for filtering on OSMCha
    imagery = Column(String)
    osm_preset = Column(String)
    odk_preset = Column(String)
    josm_preset = Column(String)
    id_presets = Column(ARRAY(String))
    extra_id_params = Column(String)
    license_id = Column(Integer, ForeignKey("licenses.id", name="fk_licenses"))
    # GEOMETRY
    centroid = Column(Geometry("POINT", srid=4326))
    # country = Column(ARRAY(String), default=[])
    # FEEDBACK
    project_chat = relationship(DbProjectChat, lazy="dynamic", cascade="all")

    ## Odk central server
    odk_central_url = Column(String)
    odk_central_user = Column(String)
    odk_central_password = Column(String)

    # Count of tasks where osm extracts is completed, used for progress bar.
    extract_completed_count = Column(Integer, default=0)

    form_xls = Column(LargeBinary)  # XLSForm file if custom xls is uploaded
    form_config_file = Column(LargeBinary)  # Yaml config file if custom xls is uploaded

    data_extract_type = Column(String)  # Type of data extract (Polygon or Centroid)
    # Options: divide on square, manual upload, task splitting algo
    task_split_type = Column(Enum(TaskSplitType), nullable=True)
    task_split_dimension = Column(SmallInteger, nullable=True)
    task_num_buildings = Column(SmallInteger, nullable=True)

    hashtags = Column(ARRAY(String))  # Project hashtag


# TODO: Add index on project geometry, tried to add in __table args__
# Index("idx_geometry", DbProject.geometry, postgresql_using="gist")

# Secondary table defining the many-to-many join
user_licenses_table = Table(
    "user_licenses",
    FmtmMetadata,
    Column("user", BigInteger, ForeignKey("users.id")),
    Column("license", Integer, ForeignKey("licenses.id")),
)


class DbLicense(Base):
    """Describes an individual license."""

    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    plain_text = Column(String)

    projects = relationship(DbProject, backref="license")
    users = relationship(
        DbUser, secondary=user_licenses_table
    )  # Many to Many relationship


class DbFeatures(Base):
    """Features extracted from osm data."""

    __tablename__ = "features"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    project = relationship(DbProject, backref="features")

    category_title = Column(String, ForeignKey("xlsforms.title", name="fk_xform"))
    category = relationship(DbXForm)
    task_id = Column(Integer, nullable=True)
    properties = Column(JSONB)
    geometry = Column(Geometry(geometry_type="GEOMETRY", srid=4326))

    __table_args__ = (
        ForeignKeyConstraint(
            [task_id, project_id], ["tasks.id", "tasks.project_id"], name="fk_tasks"
        ),
        Index("idx_features_composite", "task_id", "project_id"),
        {},
    )


class BackgroundTasks(Base):
    """Table managing long running background tasks."""

    __tablename__ = "background_tasks"

    id = Column(String, primary_key=True)
    name = Column(String)
    project_id = Column(Integer, nullable=True)
    status = Column(Enum(BackgroundTaskStatus), nullable=False)
    message = Column(String)


class DbUserRoles(Base):
    """Fine grained user control for projects, described by roles."""

    __tablename__ = "user_roles"

    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    user = relationship(DbUser, backref="user_roles")
    organization_id = Column(Integer, ForeignKey("organisations.id"))
    organization = relationship(DbOrganisation, backref="user_roles")
    project_id = Column(Integer, ForeignKey("projects.id"))
    project = relationship(DbProject, backref="user_roles")
    role = Column(Enum(UserRole), nullable=False)


class DbProjectAOI(Base):
    """The AOI geometry for a project."""

    __tablename__ = "project_aoi"

    id = Column(Integer, primary_key=True)
    project_id = Column(String)
    geom = Column(Geometry(geometry_type="GEOMETRY", srid=4326))
    tags = Column(JSONB)


class DbOsmLines(Base):
    """Associated OSM ways for a project."""

    __tablename__ = "ways_line"

    id = Column(Integer, primary_key=True)
    project_id = Column(String)
    geom = Column(Geometry(geometry_type="GEOMETRY", srid=4326))
    tags = Column(JSONB)


class DbBuildings(Base):
    """Associated OSM buildings for a project."""

    __tablename__ = "ways_poly"

    id = Column(Integer, primary_key=True)
    project_id = Column(String)
    osm_id = Column(String)
    geom = Column(Geometry(geometry_type="GEOMETRY", srid=4326))
    tags = Column(JSONB)


class DbTilesPath(Base):
    """Keeping track of mbtile basemaps for a project."""

    __tablename__ = "mbtiles_path"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer)
    status = Column(Enum(BackgroundTaskStatus), nullable=False)
    path = Column(String)
    tile_source = Column(String)
    background_task_id = Column(String)
    created_at = Column(DateTime, default=timestamp)
