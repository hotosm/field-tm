from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import desc, Enum, Table, Column, Integer, BigInteger, ARRAY, String, DateTime, Boolean, ForeignKey, ForeignKeyConstraint, UniqueConstraint, Index, Unicode
from sqlalchemy.orm import relationship, backref #, declarative_base
from sqlalchemy.dialects.postgresql import TSVECTOR
from geoalchemy2 import Geometry

from src.backend.db.postgis_utils import timestamp
from src.backend.models.enums import TeamVisibility, OrganisationType, ProjectStatus, ProjectPriority, MappingPermission, ValidationPermission, MappingLevel, UserRole, TaskCreationMode, TaskAction, TaskStatus, ProjectSplitStrategy, TaskType

from .database import Base, FmtmMetadata

class DbUser(Base):
    """Describes the history associated with a task"""

    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String, unique=True)
    role = Column(Enum(UserRole), default=UserRole.MAPPER, nullable=False)

    name = Column(String)
    city = Column(String)
    country = Column(String)
    email_address = Column(String)
    is_email_verified = Column(Boolean, default=False)
    is_expert = Column(Boolean, default=False)

    mapping_level = Column(Enum(MappingLevel), default=MappingLevel.BEGINNER, nullable=False)
    tasks_mapped = Column(Integer, default=0, nullable=False)
    tasks_validated = Column(Integer, default=0, nullable=False)
    tasks_invalidated = Column(Integer, default=0, nullable=False)
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

    # TODO: This changes to use Oath
    password = Column(String)


# Secondary table defining many-to-many relationship between organisations and managers
organisation_managers = Table(
    "organisation_managers",
    FmtmMetadata,
    Column(
        "organisation_id", Integer, ForeignKey("organisations.id"), nullable=False
    ),
    Column("user_id", BigInteger, ForeignKey("users.id"), nullable=False),
    UniqueConstraint("organisation_id", "user_id", name="organisation_user_key"),
)

class DbOrganisation(Base):
    """ Describes an Organisation """

    __tablename__ = "organisations"

    # Columns
    id = Column(Integer, primary_key=True)
    name = Column(String(512), nullable=False, unique=True)
    slug = Column(String(255), nullable=False, unique=True)
    logo = Column(String)  # URL of a logo
    description = Column(String)
    url = Column(String)
    type = Column(Enum(OrganisationType), default=OrganisationType.FREE, nullable=False)
    subscription_tier = Column(Integer)

    managers = relationship(
        DbUser,
        secondary=organisation_managers,
        backref=backref("organisations", lazy="joined"),
    )

class DbTeam(Base):
    """ Describes a team """

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

# Secondary table defining many-to-many join for private projects that only defined users can map on
project_allowed_users = Table(
    "project_allowed_users",
    FmtmMetadata,
    Column("project_id", Integer, ForeignKey("projects.id")),
    Column("user_id", BigInteger, ForeignKey("users.id")),
)

class DbProjectTeams(Base):
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
    """ Contains all project info localized into supported languages """

    __tablename__ = "project_info"

    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    locale = Column(String(10), primary_key=True)
    name = Column(String(512))
    short_description = Column(String)
    description = Column(String)
    instructions = Column(String)
    project_id_str = Column(String)
    text_searchable = Column(
        TSVECTOR
    )  # This contains searchable text and is populated by a DB Trigger
    per_task_instructions = Column(String)

    __table_args__ = (
        Index("idx_project_info_composite", "locale", "project_id"),
        Index("textsearch_idx", "text_searchable"),
        {},
    )

class DbProjectChat(Base):
    """ Contains all project info localized into supported languages """

    __tablename__ = "project_chat"
    id = Column(BigInteger, primary_key=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), index=True, nullable=False
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    time_stamp = Column(DateTime, nullable=False, default=timestamp)
    message = Column(String, nullable=False)

    # Relationships
    posted_by = relationship(DbUser, foreign_keys=[user_id])

class DbXForm(Base):
    """Xform templates and custom uploads"""

    __tablename__ = "x_form"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    form_xml = Column(String) #Internal form representation
    form_xlsx = Column(String) #Human readable representation

class DbTaskInvalidationHistory(Base):
    """Describes the most recent history of task invalidation and subsequent validation"""

    __tablename__ = "task_invalidation_history"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    task_id = Column(Integer, nullable=False)
    is_closed = Column(Boolean, default=False)
    mapper_id = Column(BigInteger, ForeignKey("users.id", name="fk_mappers"))
    mapped_date = Column(DateTime)
    invalidator_id = Column(
        BigInteger, ForeignKey("users.id", name="fk_invalidators")
    )
    invalidated_date = Column(DateTime)
    invalidation_history_id = Column(
        Integer,ForeignKey("task_history.id", name="fk_invalidation_history")
    )
    validator_id = Column(
        BigInteger, ForeignKey("users.id", name="fk_validators")
    )
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
        Index(
            "idx_task_validation_mapper_status_composite", "mapper_id", "is_closed"
        ),
        {},
    )

class DbTaskMappingIssue(Base):
    """Describes an issue (along with an occurrence count) with a
    task mapping that contributed to invalidation of the task"""

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
    """ Represents a category of task mapping issues identified during validaton """

    __tablename__ = "mapping_issue_categories"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    archived = Column(Boolean, default=False, nullable=False)

class DbTaskHistory(Base):
    """Describes the history associated with a task"""

    __tablename__ = "task_history"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    task_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
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

class DbTask(Base):
    """Describes an individual mapping Task"""

    __tablename__ = "tasks"

    # Table has composite PK on (id and project_id)
    id = Column(Integer, primary_key=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), index=True, primary_key=True
    )
    project_task_index = Column(Integer)
    x = Column(Integer)
    y = Column(Integer)
    zoom = Column(Integer)
    extra_properties = Column(Unicode)
    # Tasks need to be split differently if created from an arbitrary grid or were clipped to the edge of the AOI
    is_square = Column(Boolean, default=True)
    geometry = Column(Geometry("MULTIPOLYGON", srid=4326))
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
    task_history = relationship(
        DbTaskHistory, cascade="all", order_by=desc(DbTaskHistory.action_date)
    )
    lock_holder = relationship(DbUser, foreign_keys=[locked_by])
    mapper = relationship(DbUser, foreign_keys=[mapped_by])

class DbProject(Base):
    """Describes a HOT Mapping Project"""

    __tablename__ = "projects"

    # Columns
    id = Column(Integer, primary_key=True)
    
    # PROJECT CREATION
    author_id = Column(
        BigInteger, ForeignKey("users.id", name="fk_users"), nullable=False
    )
    author = relationship(DbUser)
    created = Column(DateTime, default=timestamp, nullable=False)
    task_creation_mode = Column(
        Enum(TaskCreationMode), default=TaskCreationMode.UPLOAD, nullable=False
    )
    split_strategy = Column(Integer)
    grid_meters = Column(Integer)
    task_type = Column(Integer)
    target_number_of_features = Column(Integer)

    # PROJECT ACCESS
    private = Column(Boolean, default=False)  # Only allowed users can validate
    default_locale = Column(
        String(10), default="en"
    )  # The locale that is returned if requested locale not available
    mapper_level = Column(
        Enum(MappingLevel), default=MappingLevel.INTERMEDIATE, nullable=False, index=True
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
    project_info = relationship(DbProjectInfo, lazy="dynamic", cascade="all")

    # XFORM DETAILS
    odk_central_src = Column(String, default="") #TODO Add HOTs as default
    xform_id = Column(Integer, ForeignKey("x_form.id", name="fk_xform"))
    xform = relationship(DbXForm)

    # GEOMETRY
    geometry = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=False)
    centroid = Column(Geometry("POINT", srid=4326), nullable=False)
    country = Column(ARRAY(String), default=[])
    
    # PROJECT STATUS
    last_updated = Column(DateTime, default=timestamp)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False)
    total_tasks = Column(Integer, nullable=False)
    tasks_mapped = Column(Integer, default=0, nullable=False)
    tasks_validated = Column(Integer, default=0, nullable=False)
    tasks_bad_imagery = Column(Integer, default=0, nullable=False)

    # TASKS
    tasks = relationship(
        DbTask, backref="projects", cascade="all, delete, delete-orphan", lazy="dynamic"
    )

    # FEEDBACK
    project_chat = relationship(DbProjectChat, lazy="dynamic", cascade="all")

    __table_args__ = (
       Index(
            "idx_geometry", geometry, postgresql_using="gist"
        ),
        {}, 
    )

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
    """ Describes an individual license"""

    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    plain_text = Column(String)

    projects = relationship(DbProject, backref="license")
    users = relationship(
        DbUser, secondary=user_licenses_table
    )  # Many to Many relationship