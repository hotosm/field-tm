# Copyright (c) Humanitarian OpenStreetMap Team
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
"""Pydantic models for parsing database rows.

Most fields are defined as Optional to allow for flexibility in the returned data
from SQL statements. Sometimes we only need a subset of the fields.
"""

import json
from datetime import timedelta
from io import BytesIO
from re import sub
from typing import TYPE_CHECKING, Annotated, Optional, Self
from uuid import UUID

import geojson
from fastapi import HTTPException, UploadFile
from loguru import logger as log
from psycopg import Connection
from psycopg.rows import class_row
from pydantic import AwareDatetime, BaseModel, Field, ValidationInfo
from pydantic.functional_validators import field_validator

from app.central.central_schemas import ODKCentralDecrypted
from app.config import settings
from app.db.enums import (
    BackgroundTaskStatus,
    CommunityType,
    HTTPStatus,
    MappingLevel,
    MappingState,
    OrganisationType,
    ProjectPriority,
    ProjectRole,
    ProjectStatus,
    ProjectVisibility,
    TaskEvent,
    TaskSplitType,
    UserRole,
    XLSFormType,
)
from app.db.postgis_utils import timestamp
from app.s3 import add_obj_to_bucket, delete_all_objs_under_prefix

# Avoid cyclical dependencies when only type checking
if TYPE_CHECKING:
    from app.organisations.organisation_schemas import (
        OrganisationIn,
        OrganisationUpdate,
    )
    from app.projects.project_schemas import (
        BackgroundTaskIn,
        BackgroundTaskUpdate,
        BasemapIn,
        BasemapUpdate,
        ProjectIn,
        ProjectUpdate,
    )
    from app.tasks.task_schemas import TaskEventIn
    from app.users.user_schemas import UserIn


def dump_and_check_model(db_model: BaseModel):
    """Dump the Pydantic model, removing None and default values.

    Also validates to check the model is not empty for insert / update.
    """
    model_dump = db_model.model_dump(exclude_none=True, exclude_unset=True)

    if not model_dump:
        log.error("Attempted create or update with no data.")
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="No data provided."
        )

    return model_dump


class DbUserRole(BaseModel):
    """Table user_roles."""

    user_id: int
    project_id: int
    role: ProjectRole

    @classmethod
    async def create(
        cls,
        db: Connection,
        project_id: int,
        user_id: int,
        role: ProjectRole,
    ) -> Self:
        """Create a new user role."""
        async with db.cursor() as cur:
            params = {
                "project_id": project_id,
                "user_id": user_id,
                "role": role.name,
            }
            await cur.execute(
                """
                INSERT INTO user_roles
                    (user_id, project_id, role)
                VALUES
                    (%(user_id)s, %(project_id)s, %(role)s)
                RETURNING *;
            """,
                params,
            )
            new_role = await cur.fetchone()

        if new_role is None:
            msg = f"Unknown SQL error for data: {params}"
            log.error(f"Failed user role creation: {params}")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
            )

        return new_role


class DbUser(BaseModel):
    """Table users."""

    id: int  # NOTE normally the OSM ID
    username: str
    role: Optional[UserRole] = None
    profile_img: Optional[str] = None
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    email_address: Optional[str] = None
    is_email_verified: Optional[bool] = False
    is_expert: Optional[bool] = False
    mapping_level: Optional[MappingLevel] = None
    tasks_mapped: Optional[int] = None
    tasks_validated: Optional[int] = None
    tasks_invalidated: Optional[int] = None
    projects_mapped: Optional[list[int]] = None
    registered_at: Optional[AwareDatetime] = None

    # Relationships
    project_roles: Optional[list[DbUserRole]] = None
    orgs_managed: Optional[list[int]] = None

    @classmethod
    async def one(cls, db: Connection, user_identifier: int | str) -> Self:
        """Get a user either by ID or username, including roles and orgs managed."""
        async with db.cursor(row_factory=class_row(cls)) as cur:
            sql = """
                SELECT
                    u.*,
                    array_agg(
                        DISTINCT om.organisation_id
                    ) FILTER (WHERE om.organisation_id IS NOT NULL) AS orgs_managed,
                    jsonb_object_agg(
                        ur.project_id,
                        COALESCE(ur.role, 'MAPPER')
                    ) FILTER (WHERE ur.project_id IS NOT NULL) AS project_roles
                FROM users u
                LEFT JOIN user_roles ur ON u.id = ur.user_id
                LEFT JOIN organisation_managers om ON u.id = om.user_id
            """

            if isinstance(user_identifier, int):
                # Is ID
                sql += """
                    WHERE u.id = %(user_identifier)s
                    GROUP BY u.id;
                """
            else:
                # Is username (basic flexible matching)
                sql += """
                    WHERE u.username ILIKE %(user_identifier)s
                    GROUP BY u.id;
                """
                user_identifier = f"{user_identifier}%"

            await cur.execute(
                sql,
                {"user_identifier": user_identifier},
            )
            db_project = await cur.fetchone()

        if db_project is None:
            raise KeyError(f"User ({user_identifier}) not found.")

        return db_project

    @classmethod
    async def all(
        cls, db: Connection, skip: int = 0, limit: int = 100
    ) -> Optional[list[Self]]:
        """Fetch all users."""
        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                """
                SELECT * FROM users
                ORDER BY registered_at DESC
                OFFSET %(offset)s
                LIMIT %(limit)s;
                """,
                {"offset": skip, "limit": limit},
            )
            return await cur.fetchall()

    @classmethod
    async def create(
        cls,
        db: Connection,
        user_in: "UserIn",
        ignore_conflict: bool = False,
    ) -> Self:
        """Create a new user."""
        if not ignore_conflict and cls.one(db, user_in.username):
            msg = f"Username ({user_in.username}) already exists!"
            log.warning(f"Failed to create new user: {msg}")
            raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=msg)

        model_dump = dump_and_check_model(user_in)
        columns = ", ".join(model_dump.keys())
        value_placeholders = ", ".join(f"%({key})s" for key in model_dump.keys())
        conflict_statement = """
            ON CONFLICT ("username") DO UPDATE
            SET
                role = EXCLUDED.role,
                mapping_level = EXCLUDED.mapping_level,
                name = EXCLUDED.name
        """

        sql = f"""
            INSERT INTO users
                ({columns})
            VALUES
                ({value_placeholders})
            {conflict_statement if ignore_conflict else ''}
            RETURNING *;
        """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql, model_dump)
            new_user = await cur.fetchone()

        if new_user is None:
            msg = f"Unknown SQL error for data: {model_dump}"
            log.error(f"Failed user creation: {model_dump}")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
            )

        return new_user


class DbOrganisation(BaseModel):
    """Table organisations."""

    # NOTE this kind of approach is possible for extra metadata in the openapi spec
    # description: Annotated[
    #     Optional[str],
    #     Field(description="Organisation description"),
    # ] = None

    id: int
    name: Optional[str] = None
    slug: Optional[str] = None
    logo: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    type: Optional[OrganisationType] = None
    approved: Optional[bool] = None
    created_by: Optional[int] = None
    odk_central_url: Optional[str] = None
    odk_central_user: Optional[str] = None
    odk_central_password: Optional[str] = None
    community_type: Optional[CommunityType] = None

    # Relationships
    managers: Optional[list[DbUser]] = None

    @classmethod
    async def one(cls, db: Connection, org_identifier: int | str) -> Self:
        """Fetch a single organisation by name or ID."""
        async with db.cursor(row_factory=class_row(cls)) as cur:
            if isinstance(org_identifier, str):
                await cur.execute(
                    """
                    SELECT * FROM organisations
                    WHERE LOWER(name) = %(org_identifier)s;
                    """,
                    {"org_identifier": org_identifier.lower()},
                )
                db_org = await cur.fetchone()
            else:
                await cur.execute(
                    """
                    SELECT * FROM organisations
                    WHERE id = %(org_identifier)s;
                    """,
                    {"org_identifier": org_identifier},
                )
                db_org = await cur.fetchone()

        if db_org is None:
            raise KeyError(f"Organisation ({org_identifier}) not found.")

        return db_org

    @classmethod
    async def all(
        cls, db: Connection, current_user_id: int = 0
    ) -> Optional[list[Self]]:
        """Fetch all organisations.

        Returns all orgs if user is admin, else only approved orgs.
        """
        sql = """
            SELECT *
            FROM organisations
            WHERE
                CASE
                    WHEN (
                        SELECT role
                        FROM users
                        WHERE id = %(user_id)s) = 'ADMIN'
                        THEN TRUE
                    ELSE approved
                END = TRUE
            ORDER BY created_at DESC;
        """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql, {"user_id": current_user_id})
            return await cur.fetchall()

    @classmethod
    async def create(
        cls,
        db: Connection,
        org_in: "OrganisationIn",
        user_id: int,
        new_logo: UploadFile,
        ignore_conflict: bool = False,
    ) -> Optional[Self]:
        """Create a new organisation."""
        # Set requesting user to the org owner
        org_in.created_by = user_id

        if not ignore_conflict and cls.one(db, org_in.name):
            msg = f"Organisation named ({org_in.name}) already exists!"
            log.warning(f"User ({user_id}) failed organisation creation: {msg}")
            raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=msg)

        model_dump = dump_and_check_model(org_in)
        columns = ", ".join(model_dump.keys())
        value_placeholders = ", ".join(f"%({key})s" for key in model_dump.keys())

        sql = f"""
            INSERT INTO organisations
                ({columns})
            VALUES
                ({value_placeholders})
            {'ON CONFLICT ("name") DO NOTHING' if ignore_conflict else ''}
            RETURNING *;
        """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql, model_dump)
            new_org = await cur.fetchone()

        if new_org is None and not ignore_conflict:
            msg = f"Unknown SQL error for data: {model_dump}"
            log.error(f"User ({user_id}) failed organisation creation: {msg}")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
            )

        if new_org and new_org.logo is None and new_logo:
            from app.organisations.organisation_schemas import OrganisationUpdate

            logo_url = await cls.upload_logo(new_org.id, new_logo)
            await cls.update(db, new_org.id, OrganisationUpdate(logo=logo_url))

        return new_org

    @classmethod
    async def upload_logo(
        cls,
        org_id: int,
        logo_file: UploadFile,
    ) -> str:
        """Upload logo using standardised /{org_id}/logo.png format.

        Browsers treat image mimetypes the same, regardless of extension,
        so it should not matter if a .jpg is renamed .png.

        Args:
            org_id (int): The organisation id in the database.
            logo_file (UploadFile): The logo bytes from FastAPI UploadFile.

        Returns:
            logo_url (str): The S3 URL for the logo file.
        """
        logo_path = f"/{org_id}/logo.png"
        logo_bytes = await logo_file.read()
        file_obj = BytesIO(logo_bytes)

        add_obj_to_bucket(
            settings.S3_BUCKET_NAME,
            file_obj,
            logo_path,
            content_type=logo_file.content_type,
        )

        return f"{settings.S3_DOWNLOAD_ROOT}/{settings.S3_BUCKET_NAME}{logo_path}"

    @classmethod
    async def update(
        cls,
        db: Connection,
        org_id: int,
        org_update: "OrganisationUpdate",
        new_logo: Optional[UploadFile] = None,
    ) -> Self:
        """Update values for organisation."""
        if new_logo:
            org_update.logo = await cls.upload_logo(org_id, new_logo)

        model_dump = dump_and_check_model(org_update)
        placeholders = [f"{key} = %({key})s" for key in model_dump.keys()]
        sql = f"""
            UPDATE organisations
            SET {', '.join(placeholders)}
            WHERE id = %(org_id)s
            RETURNING *;
        """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql, {"org_id": org_id, **model_dump})
            updated_org = await cur.fetchone()

        if updated_org is None:
            msg = f"Failed to update org with ID: {org_id}"
            log.error(msg)
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
            )

        return updated_org

    @classmethod
    async def delete(cls, db: Connection, org_id: int) -> bool:
        """Delete an organisation and its related data."""
        sql = """
            WITH deleted_task_events AS (
                DELETE FROM task_events
                WHERE project_id IN (
                    SELECT id FROM projects WHERE organisation_id = %(org_id)s
                )
                RETURNING project_id
            ), deleted_tasks AS (
                DELETE FROM tasks
                WHERE project_id IN (
                    SELECT id FROM projects WHERE organisation_id = %(org_id)s
                )
                RETURNING project_id
            ), deleted_projects AS (
                DELETE FROM projects
                WHERE organisation_id = %(org_id)s
                RETURNING organisation_id
            ), deleted_org AS (
                DELETE FROM organisations
                WHERE id = %(org_id)s
                RETURNING id
            )
            SELECT id FROM deleted_org;
        """

        async with db.cursor() as cur:
            await cur.execute(sql, {"org_id": org_id})
            success = await cur.fetchone()

        if success:
            await delete_all_objs_under_prefix(
                settings.S3_BUCKET_NAME,
                f"/{org_id}/",
            )

    @classmethod
    async def unapproved(cls, db: Connection) -> Optional[list[Self]]:
        """Get all organisations not approved yet."""
        sql = """
            SELECT *
            FROM organisations
            WHERE approved != TRUE;
        """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql)
            return await cur.fetchall()


class DbOrganisationManagers(BaseModel):
    """Table organisation_managers."""

    organisation_id: int
    user_id: int

    @classmethod
    async def create(
        cls,
        db: Connection,
        org_id: int,
        user_id: int,
    ) -> Self:
        """Add a new organisation manager.

        Args:
            db (Connection): The database connection.
            org_id (int): The organisation ID.
            user_id (int): The user ID to add as manager.

        Returns:
            Self: An instance of DbOrganisationManagers.
        """
        log.info(f"Adding user ({user_id}) as org ({org_id}) admin")
        sql = """
            INSERT INTO public.organisation_managers
                (organisation_id, user_id)
            VALUES
                (%(org_id)s, %(user_id)s)
            ON CONFLICT (organisation_id, user_id) DO NOTHING;
        """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            data = {
                "org_id": org_id,
                "user_id": user_id,
            }
            await cur.execute(sql, data)


class DbXLSForm(BaseModel):
    """Table xlsforms.

    XLSForm templates and custom uploads.

    TODO SQL migrate and rename this to 'template_xlsforms'.
    """

    id: int
    title: str
    xls: Optional[bytes] = None

    @classmethod
    async def all(
        cls,
        db: Connection,
    ) -> Optional[list[Self]]:
        """Fetch all XLSForms."""
        include_categories = [category.value for category in XLSFormType]

        sql = """
            SELECT
                id, title
            FROM xlsforms
            WHERE title IN (
                SELECT UNNEST(%(categories)s::text[])
            );
            """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql, {"categories": include_categories})
            forms = await cur.fetchall()

        # Don't include 'xls' field in the response
        return [{"id": form.id, "title": form.title} for form in forms]


class DbTaskEvent(BaseModel):
    """Table task_events.

    Task events such as locking, marking mapped, and comments.
    """

    event_id: UUID
    task_id: Annotated[Optional[int], Field(gt=0)] = None
    event: TaskEvent

    project_id: Annotated[Optional[int], Field(gt=0)] = None
    user_id: Annotated[Optional[int], Field(gt=0)] = None
    comment: Optional[str] = None
    created_at: Optional[AwareDatetime] = None

    # Computed
    username: Optional[str] = None
    profile_img: Optional[str] = None
    # Computed via database trigger
    state: Optional[MappingState] = None

    @classmethod
    async def all(
        cls,
        db: Connection,
        project_id: Optional[int] = None,
        task_id: Optional[int] = None,
        days: Optional[int] = None,
        comments: Optional[bool] = None,
    ) -> Optional[list[Self]]:
        """Fetch all task event entries for a project.

        Args:
            db (Connection): the database connection.
            project_id (int): return all events for a project.
            task_id (Connection): return all events for a task.
            days (int): filter to only include events since X days ago.
            comments (bool): show comments rather than events.

        Returns:
            list[DbTaskEvent]: list of task event objects.
        """
        if project_id and task_id:
            raise ValueError("Specify either project_id or task_id, not both.")
        if not project_id and not task_id:
            raise ValueError("Either project_id or task_id must be provided.")

        filters = []
        params = {}

        if project_id:
            filters.append("project_id = %(project_id)s")
            params["project_id"] = project_id
        if task_id:
            filters.append("task_id = %(task_id)s")
            params["task_id"] = task_id
        if days is not None:
            end_date = timestamp() - timedelta(days=days)
            filters.append("created_at >= %(end_date)s")
            params["end_date"] = end_date
        if comments:
            filters.append("event = 'COMMENT'")
        else:
            filters.append("event != 'COMMENT'")

        filters_joined = " AND ".join(filters)

        sql = f"""
            SELECT
                *,
                u.username,
                u.profile_img
            FROM
                public.task_events
            JOIN
                users u ON u.id = task_events.user_id
            WHERE {filters_joined}
            ORDER BY created_at DESC;
        """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()

    @classmethod
    async def create(
        cls,
        db: Connection,
        event_in: "TaskEventIn",
    ) -> Self:
        """Create a new task event."""
        model_dump = dump_and_check_model(event_in)
        columns = ", ".join(model_dump.keys())
        value_placeholders = ", ".join(f"%({key})s" for key in model_dump.keys())

        # NOTE the project_id need not be passed, as it's extracted from the task
        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                f"""
                    WITH inserted AS (
                        INSERT INTO public.task_events (
                            event_id,
                            project_id,
                            {columns}
                        )
                        VALUES (
                            gen_random_uuid(),
                            (SELECT project_id FROM tasks WHERE id = %(task_id)s),
                            {value_placeholders}
                        )
                        RETURNING *
                    )
                    SELECT
                        inserted.*,
                        u.username,
                        u.profile_img
                    FROM inserted
                    JOIN users u ON u.id = inserted.user_id;
            """,
                model_dump,
            )
            new_task_event = await cur.fetchone()

        if new_task_event is None:
            msg = f"Unknown SQL error for data: {model_dump}"
            log.error(f"Failed task event creation: {model_dump}")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
            )

        return new_task_event


class DbTask(BaseModel):
    """Table tasks."""

    id: int
    outline: Optional[dict] = None
    project_id: Optional[int] = None
    project_task_index: Optional[int] = None
    feature_count: Optional[int] = None

    # Calculated
    task_state: Optional[MappingState] = None
    actioned_by_uid: Optional[int] = None
    actioned_by_username: Optional[str] = None

    @classmethod
    async def one(cls, db: Connection, task_id: int) -> Self:
        """Fetch a single task by it's ID.

        Also returns the current task status, and user that actioned the task.
        """
        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                """
                    SELECT
                        tasks.*,
                        ST_AsGeoJSON(tasks.outline)::jsonb AS outline,
                        COALESCE(
                            latest_event.state, 'UNLOCKED_TO_MAP'
                        ) AS task_state,
                        COALESCE(latest_event.user_id, NULL) AS actioned_by_uid,
                        COALESCE(latest_event.username, NULL) AS actioned_by_username
                    FROM
                        tasks
                    LEFT JOIN LATERAL (
                        SELECT
                            th.event,
                            th.state,
                            th.user_id,
                            u.username
                        FROM
                            task_events th
                        LEFT JOIN
                            users u ON u.id = th.user_id
                        WHERE
                            th.task_id = tasks.id
                            AND th.event != 'COMMENT'
                        ORDER BY
                            th.created_at DESC
                        LIMIT 1
                    ) latest_event ON true
                    WHERE
                        tasks.id = %(task_id)s;
                """,
                {"task_id": task_id},
            )
            db_task = await cur.fetchone()

        if db_task is None:
            raise KeyError(f"Task ({task_id}) not found.")

        return db_task

    @classmethod
    async def all(
        cls,
        db: Connection,
        project_id: int,
    ) -> Optional[list[Self]]:
        """Fetch all tasks for a project.

        Also returns the current task status, and user that actioned the task.
        """
        sql = """
            SELECT
                tasks.*,
                ST_AsGeoJSON(tasks.outline)::jsonb AS outline,
                COALESCE(latest_event.state, 'UNLOCKED_TO_MAP') AS task_state,
                COALESCE(latest_event.user_id, NULL) AS actioned_by_uid,
                COALESCE(latest_event.username, NULL) AS actioned_by_username
            FROM
                tasks
            LEFT JOIN LATERAL (
                SELECT
                    th.event,
                    th.state,
                    th.user_id,
                    u.username
                FROM
                    task_events th
                LEFT JOIN
                    users u ON u.id = th.user_id
                WHERE
                    th.task_id = tasks.id
                    AND th.event != 'COMMENT'
                ORDER BY
                    th.created_at DESC
                LIMIT 1
            ) latest_event ON true
            WHERE
                tasks.project_id = %(project_id)s;
        """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql, {"project_id": project_id})
            return await cur.fetchall()

    @classmethod
    async def create(
        cls,
        db: Connection,
        project_id: int,
        tasks: geojson.FeatureCollection,
    ) -> bool:
        """Create a set of new tasks for a project.

        Args:
            db (Connection): The database connection.
            project_id (int): The organisation ID.
            tasks (geojson.FeatureCollection): FeatureCollection of task areas.

        Returns:
            bool: Success or failure.
        """
        features = tasks.get("features")
        log.info(f"Adding ({len(features)}) tasks to project ({project_id})")

        sql = """
            INSERT INTO public.tasks
                (project_id, project_task_index, outline)
            VALUES
        """

        # Prepare data for bulk insert
        values = []
        data = {}
        for index, feature in enumerate(features):
            feature_index = f"geom_{index}"
            values.append(
                "(%(project_id)s,"
                f"{index + 1},"
                f"ST_GeomFromGeoJSON(%({feature_index})s))"
            )
            # Must be string json for db input
            data[feature_index] = json.dumps(feature["geometry"])
        data["project_id"] = project_id

        # Join the values list into the SQL statement
        sql += ", ".join(values) + " RETURNING True;"

        async with db.cursor() as cur:
            await cur.execute(sql, data)
            result = await cur.fetchall()

        return bool(result)


class DbProject(BaseModel):
    """Table projects."""

    id: int
    name: str
    outline: Optional[dict] = None
    odkid: Optional[int] = None
    author_id: Optional[int] = None
    organisation_id: Optional[int] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    per_task_instructions: Optional[str] = None
    slug: Optional[str] = None
    task_split_type: Optional[TaskSplitType] = None
    location_str: Optional[str] = None
    custom_tms_url: Optional[str] = None
    status: Optional[ProjectStatus] = None
    visibility: Optional[ProjectVisibility] = None
    total_tasks: Optional[int] = None
    xform_category: Optional[str] = None
    odk_form_id: Optional[str] = None
    xlsform_content: Optional[bytes] = None
    mapper_level: Optional[MappingLevel] = None
    priority: Optional[ProjectPriority] = None
    featured: Optional[bool] = None
    odk_central_url: Optional[str] = None
    odk_central_user: Optional[str] = None
    odk_central_password: Optional[str] = None
    odk_token: Optional[str] = None
    data_extract_type: Optional[str] = None
    data_extract_url: Optional[str] = None
    task_split_dimension: Optional[int] = None
    task_num_buildings: Optional[int] = None
    hashtags: Optional[list[str]] = None
    due_date: Optional[AwareDatetime] = None
    updated_at: Optional[AwareDatetime] = None
    created_at: Optional[AwareDatetime] = None

    # Relationships
    tasks: Optional[list[DbTask]] = None

    # Calculated
    organisation_name: Optional[str] = None
    organisation_logo: Optional[str] = None
    centroid: Optional[dict] = None
    bbox: Optional[list[float]] = None
    last_active: Optional[AwareDatetime] = None
    odk_credentials: Annotated[
        Optional["ODKCentralDecrypted"],
        Field(validate_default=True),
    ] = None

    @field_validator("odk_credentials", mode="before")
    @classmethod
    def set_odk_credentials_on_project(
        cls,
        value: None,
        info: ValidationInfo,
    ) -> Optional["ODKCentralDecrypted"]:
        """Set the odk_credentials object on the project.

        Defaults to organisation credentials if none are set.
        """
        return ODKCentralDecrypted(
            odk_central_url=info.data.get("odk_central_url"),
            odk_central_user=info.data.get("odk_central_user"),
            odk_central_password=info.data.get("odk_central_password"),
        )

    @classmethod
    async def one(cls, db: Connection, project_id: int) -> Self:
        """Get project by ID, including all tasks and other details."""
        async with db.cursor(row_factory=class_row(cls)) as cur:
            sql = """
                WITH latest_status_per_task AS (
                    SELECT DISTINCT ON (task_id)
                        th.task_id,
                        th.event,
                        th.state,
                        th.created_at,
                        th.user_id,
                        u.username AS username
                    FROM
                        task_events th
                    LEFT JOIN
                        users u ON u.id = th.user_id
                    WHERE
                        th.event != 'COMMENT'
                    ORDER BY
                        th.task_id, th.created_at DESC
                ),

                project_bbox AS (
                    SELECT ST_Envelope(p.outline) AS bbox
                    FROM projects p
                    WHERE p.id = %(project_id)s
                )

                SELECT
                    p.*,
                    ST_AsGeoJSON(p.outline)::jsonb AS outline,
                    ST_AsGeoJSON(ST_Centroid(p.outline))::jsonb AS centroid,
                    ARRAY[
                        ST_XMin(project_bbox.bbox),
                        ST_YMin(project_bbox.bbox),
                        ST_XMax(project_bbox.bbox),
                        ST_YMax(project_bbox.bbox)
                    ] AS bbox,
                    project_org.name AS organisation_name,
                    project_org.logo AS organisation_logo,
                    MAX(latest_status_per_task.created_at)::timestamptz AS last_active,
                    COALESCE(
                        NULLIF(p.odk_central_url, ''),
                        project_org.odk_central_url
                    ) AS odk_central_url,
                    COALESCE(
                        NULLIF(p.odk_central_user, ''),
                        project_org.odk_central_user
                    ) AS odk_central_user,
                    COALESCE(
                        NULLIF(p.odk_central_password, ''),
                        project_org.odk_central_password
                    ) AS odk_central_password,
                    COALESCE(
                        JSON_AGG(
                            JSON_BUILD_OBJECT(
                                'id', tasks.id,
                                'project_id', tasks.project_id,
                                'project_task_index', tasks.project_task_index,
                                'outline', ST_AsGeoJSON(tasks.outline)::jsonb,
                                'feature_count', tasks.feature_count,
                                'task_state', COALESCE(
                                    latest_status_per_task.state,
                                    'UNLOCKED_TO_MAP'
                                ),
                                'actioned_by_uid', COALESCE(
                                    latest_status_per_task.user_id,
                                    NULL
                                ),
                                'actioned_by_username', COALESCE(
                                    latest_status_per_task.username,
                                    NULL
                                )
                            )
                        -- Required filter if the task array is empty
                        ) FILTER (WHERE tasks.id IS NOT NULL), '[]'::json
                    ) AS tasks
                FROM
                    projects p
                -- For org name, logo, and ODK credentials
                LEFT JOIN
                    organisations project_org ON p.organisation_id = project_org.id
                -- Get tasks for the project
                LEFT JOIN
                    tasks ON tasks.project_id = p.id
                -- Link latest event per task with project tasks
                LEFT JOIN
                    latest_status_per_task ON
                        tasks.id = latest_status_per_task.task_id
                -- Required to get the BBOX object
                JOIN
                    project_bbox ON project_bbox.bbox IS NOT NULL
                WHERE
                    p.id = %(project_id)s
                GROUP BY
                    p.id, project_org.id, project_bbox.bbox;
            """

            # Simpler query without additional metadata
            # sql = """
            #     SELECT
            #         p.*,
            #         ST_AsGeoJSON(p.outline)::jsonb AS outline,
            #         ST_AsGeoJSON(ST_Centroid(p.outline))::jsonb AS centroid,
            #         COALESCE(
            #             JSON_AGG(
            #                 JSON_BUILD_OBJECT(
            #                     'id', t.id,
            #                     'project_id', t.project_id,
            #                     'project_task_index', t.project_task_index,
            #                     'outline', ST_AsGeoJSON(t.outline)::jsonb,
            #                     'feature_count', t.feature_count
            #                 )
            #             ) FILTER (WHERE t.id IS NOT NULL), '[]'::json
            #         ) AS tasks
            #     FROM
            #         projects p
            #     LEFT JOIN
            #         tasks t ON t.project_id = %(project_id)s
            #     WHERE
            #         p.id = %(project_id)s AND (
            #             t.project_id = %(project_id)s
            #                 -- Also required to return a project with if tasks
            #                 OR t.project_id IS NULL
            #         )
            #     GROUP BY p.id;
            # """

            await cur.execute(
                sql,
                {"project_id": project_id},
            )
            db_project = await cur.fetchone()

        if db_project is None:
            raise KeyError(f"Project ({project_id}) not found.")

        if db_project.odk_token is None:
            log.warning(
                f"Project ({db_project.id}) has no 'odk_token' set. "
                "The QRCode will not work!"
            )

        return db_project

    @classmethod
    async def all(
        cls,
        db: Connection,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        hashtags: Optional[list[str]] = None,
        search: Optional[str] = None,
    ) -> Optional[list[Self]]:
        """Fetch all projects with optional filters for user, hashtags, and search."""
        filters = []
        params = {"offset": skip, "limit": limit}

        # Filter by user_id (project author)
        if user_id:
            filters.append("author_id = %(user_id)s")
            params["user_id"] = user_id

        # Filter by hashtags
        if hashtags:
            filters.append("hashtags && %(hashtags)s")
            params["hashtags"] = hashtags

        # Filter by search term (project name using ILIKE for case-insensitive match)
        if search:
            filters.append("slug ILIKE %(search)s")
            params["search"] = f"%{search}%"

        # Base query with optional filtering
        sql = f"""
            SELECT
                p.*,
                ST_AsGeoJSON(p.outline)::jsonb AS outline,
                ST_AsGeoJSON(ST_Centroid(p.outline))::jsonb AS centroid,
                project_org.logo as organisation_logo,
                COUNT(t.id) AS task_count
            FROM
                projects p
            LEFT JOIN
                organisations project_org ON p.organisation_id = project_org.id
            LEFT JOIN
                tasks t ON p.id = t.project_id
            {'WHERE ' + ' AND '.join(filters) if filters else ''}
            GROUP BY
                p.id, project_org.id
            ORDER BY
                p.created_at DESC
            OFFSET %(offset)s
            LIMIT %(limit)s;
        """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()

    @classmethod
    async def create(cls, db: Connection, project_in: "ProjectIn") -> Self:
        """Create a new project in the database."""
        model_dump = dump_and_check_model(project_in)
        columns = []
        value_placeholders = []

        for key in model_dump.keys():
            columns.append(key)
            if key == "outline":
                value_placeholders.append(f"ST_GeomFromGeoJSON(%({key})s)")
                # Must be string json for db input
                model_dump[key] = json.dumps(model_dump[key])
            else:
                value_placeholders.append(f"%({key})s")

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                f"""
                INSERT INTO projects
                    ({", ".join(columns)})
                VALUES
                    ({", ".join(value_placeholders)})
                RETURNING
                    *,
                    ST_AsGeoJSON(outline)::jsonb AS outline;
            """,
                model_dump,
            )
            new_project = await cur.fetchone()

            if new_project is None:
                msg = f"Unknown SQL error for data: {model_dump}"
                log.error(f"Project creation failed: {msg}")
                raise HTTPException(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
                )

            # NOTE we want a trackable hashtag DOMAIN-PROJECT_ID
            new_project.hashtags.append(f"#{settings.FMTM_DOMAIN}-{new_project.id}")

            await cur.execute(
                """
                    UPDATE projects
                    SET hashtags = %(hashtags)s
                    WHERE id = %(project_id)s
                    RETURNING
                        *,
                        ST_AsGeoJSON(outline)::jsonb AS outline;
                """,
                {"hashtags": new_project.hashtags, "project_id": new_project.id},
            )
            updated_project = await cur.fetchone()

        if updated_project is None:
            msg = f"Failed to update hashtags for project ID: {new_project.id}"
            log.error(msg)
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
            )

        return updated_project

    @classmethod
    async def update(
        cls,
        db: Connection,
        project_id: int,
        project_update: "ProjectUpdate",
    ) -> Self:
        """Update values for project."""
        model_dump = dump_and_check_model(project_update)
        placeholders = [f"{key} = %({key})s" for key in model_dump.keys()]

        # NOTE we want a trackable hashtag DOMAIN-PROJECT_ID
        if "hashtags" in model_dump:
            fmtm_hashtag = f"#{settings.FMTM_DOMAIN}-{project_id}"
            if fmtm_hashtag not in model_dump["hashtags"]:
                model_dump["hashtags"].append(fmtm_hashtag)

        sql = f"""
            UPDATE projects
            SET {', '.join(placeholders)}
            WHERE id = %(project_id)s
            RETURNING
                *,
                ST_AsGeoJSON(outline)::jsonb AS outline;
        """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql, {"project_id": project_id, **model_dump})
            updated_project = await cur.fetchone()

        if updated_project is None:
            msg = f"Failed to update project with ID: {project_id}"
            log.error(msg)
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
            )

        return updated_project

    @classmethod
    async def delete(cls, db: Connection, project_id: int) -> bool:
        """Delete a project and its related data."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM background_tasks WHERE project_id = %(project_id)s;
            """,
                {"project_id": project_id},
            )
            await cur.execute(
                """
                DELETE FROM basemaps WHERE project_id = %(project_id)s;
            """,
                {"project_id": project_id},
            )
            await cur.execute(
                """
                DELETE FROM user_roles WHERE project_id = %(project_id)s;
            """,
                {"project_id": project_id},
            )
            await cur.execute(
                """
                DELETE FROM task_events WHERE project_id = %(project_id)s;
            """,
                {"project_id": project_id},
            )
            await cur.execute(
                """
                DELETE FROM tasks WHERE project_id = %(project_id)s;
            """,
                {"project_id": project_id},
            )
            await cur.execute(
                """
                DELETE FROM projects WHERE id = %(project_id)s;
            """,
                {"project_id": project_id},
            )


class DbBackgroundTask(BaseModel):
    """Table background_tasks.

    For managing long-running background tasks.

    NOTE: This may eventually be removed.
    """

    id: UUID
    status: Optional[BackgroundTaskStatus] = None
    name: Optional[str] = None
    project_id: Optional[int] = None
    message: Optional[str] = None

    @classmethod
    async def one(cls, db: Connection, task_id: int) -> Self:
        """Fetch a single background task by its ID."""
        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                """
                    SELECT * FROM background_tasks
                    WHERE id = %(task_id)s;
                """,
                {"task_id": task_id},
            )
            db_task = await cur.fetchone()

        if db_task is None:
            raise KeyError(f"Background task ({task_id}) not found.")

        return db_task

    @classmethod
    async def create(
        cls,
        db: Connection,
        task_in: "BackgroundTaskIn",
    ) -> int:
        """Create a new background task.

        Return the task ID only.
        """
        model_dump = dump_and_check_model(task_in)
        columns = ", ".join(model_dump.keys())
        value_placeholders = ", ".join(f"%({key})s" for key in model_dump.keys())

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                f"""
                INSERT INTO background_tasks
                    (
                        id,
                        {columns}
                    )
                VALUES
                    (
                        gen_random_uuid(),
                        {value_placeholders}
                    )
                RETURNING id;
            """,
                model_dump,
            )
            bg_task = await cur.fetchone()

        if bg_task is None:
            msg = f"Unknown SQL error for data: {model_dump}"
            log.error(f"Failed background task creation: {model_dump}")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
            )

        return bg_task.id

    @classmethod
    async def update(
        cls,
        db: Connection,
        task_id: int,
        task_update: "BackgroundTaskUpdate",
    ) -> Self:
        """Update values for a background task."""
        model_dump = dump_and_check_model(task_update)
        placeholders = [f"{key} = %({key})s" for key in model_dump.keys()]
        sql = f"""
            UPDATE background_tasks
            SET {', '.join(placeholders)}
            WHERE id = %(task_id)s
            RETURNING *;
        """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql, {"task_id": task_id, **model_dump})
            updated_task = await cur.fetchone()

        if updated_task is None:
            msg = f"Failed to update background task with ID: {task_id}"
            log.error(msg)
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
            )

        return updated_task


class DbBasemap(BaseModel):
    """Table tiles_path.

    TODO for now we generate the basemap entry in FMTM.
    TODO In future we will use a basemap generator microservice
    TODO that will handle the basemap generation db entries.
    TODO https://github.com/hotosm/basemap-api
    """

    id: UUID
    project_id: Optional[int] = None
    url: Optional[str] = None
    tile_source: Optional[str] = None
    background_task_id: Optional[UUID] = None
    status: Optional[BackgroundTaskStatus] = None
    created_at: Optional[AwareDatetime] = None

    # Calculated
    bbox: Optional[list[float]] = None

    @classmethod
    async def one(cls, db: Connection, basemap_id: UUID) -> Self:
        """Get a tile archive file DB record."""
        # NOTE we must import here to prevent cyclical import
        from app.projects.project_schemas import BasemapOut

        async with db.cursor(row_factory=class_row(BasemapOut)) as cur:
            sql = """
                SELECT *
                FROM basemaps
                WHERE id = %(basemap_id)s;
            """
            await cur.execute(sql, {"basemap_id": basemap_id})
            db_basemap = await cur.fetchone()

        if db_basemap is None:
            raise KeyError(f"Basemap with ID ({db_basemap}) not found.")

        return db_basemap

    @classmethod
    async def all(cls, db: Connection, project_id: int) -> Optional[list[Self]]:
        """Fetch all basemaps for a specific project."""
        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                """
                    SELECT * FROM basemaps
                    WHERE project_id = %(project_id)s
                    ORDER BY created_at DESC;
                """,
                {"project_id": project_id},
            )
            basemaps = await cur.fetchall()
            return basemaps

    @classmethod
    async def create(
        cls,
        db: Connection,
        basemap_in: "BasemapIn",
    ) -> Self:
        """Create a new basemap and return its bounding box."""
        model_dump = dump_and_check_model(basemap_in)
        columns = ", ".join(model_dump.keys())
        value_placeholders = ", ".join(f"%({key})s" for key in model_dump.keys())

        sql = f"""
            WITH inserted_basemap AS (
                INSERT INTO basemaps (
                    id,
                    {columns}
                )
                VALUES (
                    gen_random_uuid(),
                    {value_placeholders}
                )
                RETURNING *
            ),
            project_bbox AS (
                SELECT ST_Envelope(outline) AS bbox
                FROM projects
                WHERE id = (SELECT project_id FROM inserted_basemap)
            )
            SELECT
                inserted_basemap.*,
                ARRAY[
                    ST_XMin(project_bbox.bbox),
                    ST_YMin(project_bbox.bbox),
                    ST_XMax(project_bbox.bbox),
                    ST_YMax(project_bbox.bbox)
                ] AS bbox
            FROM inserted_basemap
            JOIN project_bbox ON project_bbox.bbox IS NOT NULL;
        """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql, model_dump)
            new_basemap = await cur.fetchone()

        if new_basemap is None:
            msg = f"Unknown SQL error for data: {model_dump}"
            log.error(f"Failed basemap creation: {model_dump}")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
            )

        return new_basemap

    @classmethod
    async def update(
        cls,
        db: Connection,
        basemap_id: int,
        basemap_update: "BasemapUpdate",
    ) -> Self:
        """Update values for a basemap."""
        model_dump = dump_and_check_model(basemap_update)
        placeholders = [f"{key} = %({key})s" for key in model_dump.keys()]
        sql = f"""
            UPDATE basemaps
            SET {', '.join(placeholders)}
            WHERE id = %(basemap_id)s
            RETURNING *;
        """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql, {"basemap_id": basemap_id, **model_dump})
            updated_basemap = await cur.fetchone()

        if updated_basemap is None:
            msg = f"Failed to update basemap with ID: {basemap_id}"
            log.error(msg)
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
            )

        return updated_basemap


class DbSubmissionPhoto(BaseModel):
    """Table submission_photo.

    TODO SQL this will be replace by ODK Central direct S3 upload.
    """

    id: int
    project_id: Optional[int] = None
    task_id: Optional[int] = None  # Note this is not a DbTask, but an ODK task_id
    submission_id: Optional[str] = None
    s3_path: Optional[str] = None


def slugify(name: Optional[str]) -> Optional[str]:
    """Return a sanitised URL slug from a name."""
    if name is None:
        return None
    # Remove special characters and replace spaces with hyphens
    slug = sub(r"[^\w\s-]", "", name).strip().lower().replace(" ", "-")
    # Remove consecutive hyphens
    slug = sub(r"[-\s]+", "-", slug)
    return slug
