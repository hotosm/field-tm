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
"""Pydantic models for parsing database rows.

Most fields are defined as Optional to allow for flexibility in the returned data
from SQL statements. Sometimes we only need a subset of the fields.
"""

import json
from datetime import timedelta
from io import BytesIO
from re import sub
from typing import TYPE_CHECKING, Annotated, List, Optional, Self
from uuid import UUID

import geojson
import psycopg
from fastapi import HTTPException, UploadFile
from loguru import logger as log
from psycopg import Connection
from psycopg.errors import UniqueViolation
from psycopg.rows import class_row
from pydantic import AwareDatetime, BaseModel, Field, PositiveInt, ValidationInfo
from pydantic.functional_validators import field_validator

from app.central.central_schemas import ODKCentralDecrypted
from app.config import settings
from app.db import database
from app.db.enums import (
    BackgroundTaskStatus,
    CommunityType,
    DbGeomType,
    EntityState,
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
    from app.central.central_schemas import OdkEntitiesUpdate
    from app.organisations.organisation_schemas import (
        OrganisationIn,
        OrganisationUpdate,
    )
    from app.projects.project_schemas import (
        BackgroundTaskIn,
        BackgroundTaskUpdate,
        BasemapIn,
        BasemapUpdate,
        ProjectTeamIn,
        ProjectUpdate,
        StubProjectIn,
    )
    from app.tasks.task_schemas import TaskEventIn
    from app.users.user_schemas import (
        UserIn,
        UserInviteIn,
        UserInviteUpdate,
        UserUpdate,
    )


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

    user_sub: str
    project_id: int
    role: ProjectRole
    username: Optional[str] = None

    @classmethod
    async def create(
        cls,
        db: Connection,
        project_id: int,
        user_sub: str,
        role: ProjectRole,
    ) -> Self:
        """Create a new user role."""
        async with db.cursor(row_factory=class_row(cls)) as cur:
            params = {
                "project_id": project_id,
                "user_sub": user_sub,
                "role": role.name,
            }
            await cur.execute(
                """
                INSERT INTO user_roles
                    (user_sub, project_id, role)
                VALUES
                    (%(user_sub)s, %(project_id)s, %(role)s)
                    ON CONFLICT (user_sub, project_id) DO UPDATE
                    SET role = EXCLUDED.role
                    WHERE user_roles.role < EXCLUDED.role;
            """,
                params,
            )

            # NOTE this will return the latest role, even if it's not updated
            # to make sure something is always returned
            await cur.execute(
                """
                SELECT * FROM user_roles
                WHERE user_sub = %(user_sub)s AND project_id = %(project_id)s;
            """,
                params,
            )
            latest_role = await cur.fetchone()

        if latest_role is None:
            msg = f"Failed to create user role: {params}"
            log.error(msg)
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
            )

        return latest_role

    @classmethod
    async def all(
        cls,
        db: Connection,
        project_id: Optional[int] = None,
        role: Optional[ProjectRole] = None,
    ) -> Optional[list[Self]]:
        """Fetch all project user roles, along with username."""
        filters = []
        params = {}
        if project_id:
            filters.append("ur.project_id = %(project_id)s")
            params["project_id"] = project_id
        if role:
            filters.append("ur.role = %(role)s")
            params["role"] = role if isinstance(role, str) else role.name

        sql = f"""
                SELECT ur.*, u.username
                FROM user_roles ur
                JOIN users u ON ur.user_sub = u.sub
                {"WHERE " + " AND ".join(filters) if filters else ""}
            """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                sql,
                params if params else None,
            )
            return await cur.fetchall()

    @classmethod
    async def delete(
        cls,
        db: Connection,
        project_id: int,
        user_sub: str,
    ) -> bool:
        """Delete a user's role from a specific project (unassign user from project)."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM user_roles WHERE project_id = %(project_id)s
                AND user_sub = %(user_sub)s;
                """,
                {"project_id": project_id, "user_sub": user_sub},
            )
        return True

    @classmethod
    async def get(
        cls,
        db: Connection,
        project_id: Optional[int] = None,
        user_sub: Optional[str] = None,
    ) -> Optional[Self]:
        """Fetch a user's role for a project.

        filtered by any combination of user_sub and project_id.
        """
        filters = []
        params = {}

        if user_sub:
            filters.append("user_sub = %(user_sub)s")
            params["user_sub"] = str(user_sub)

        if project_id is not None:
            filters.append("project_id = %(project_id)s")
            params["project_id"] = int(project_id)

        sql = f"""
            SELECT * FROM user_roles
            {"WHERE " + " AND ".join(filters) if filters else ""}
            LIMIT 1
        """

        async with db.cursor() as cur:
            await cur.execute(sql, params if params else None)
            return await cur.fetchone()


class DbUser(BaseModel):
    """Table users."""

    sub: str
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
    api_key: Optional[str] = None
    registered_at: Optional[AwareDatetime] = None
    last_login_at: Optional[AwareDatetime] = None

    # Relationships
    project_roles: Optional[dict[int, ProjectRole]] = None  # project:role pairs
    orgs_managed: Optional[list[int]] = None

    @classmethod
    async def one(cls, db: Connection, user_subidentifier: str) -> Self:
        """Get a user either by ID or username, including roles and orgs managed."""
        async with db.cursor(row_factory=class_row(cls)) as cur:
            sql = """
                SELECT
                    u.*,

                -- Aggregate organisation IDs managed by the user
                array_agg(
                    DISTINCT om.organisation_id
                ) FILTER (WHERE om.organisation_id IS NOT NULL) AS orgs_managed,

                -- Aggregate project roles for the user, as project:role pairs
                jsonb_object_agg(
                    ur.project_id,
                    COALESCE(ur.role, 'MAPPER')
                ) FILTER (WHERE ur.project_id IS NOT NULL) AS project_roles

                FROM users u
                LEFT JOIN user_roles ur ON u.sub = ur.user_sub
                LEFT JOIN organisation_managers om ON u.sub = om.user_sub
                WHERE u.sub ILIKE %(user_subidentifier)s
                GROUP BY u.sub;
            """

            await cur.execute(
                sql,
                {"user_subidentifier": user_subidentifier},
            )
            db_user = await cur.fetchone()

        if db_user is None:
            raise KeyError(f"User ({user_subidentifier}) not found.")

        return db_user

    @classmethod
    async def all(
        cls,
        db: Connection,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        search: Optional[str] = None,
        username: Optional[str] = None,
        signin_type: Optional[str] = None,
        role: Optional[UserRole] = None,
    ) -> Optional[list[Self]]:
        """Fetch all users."""
        filters = []
        params = {"offset": skip, "limit": limit} if skip and limit else {}

        if search:
            filters.append("username ILIKE %(search)s")
            params["search"] = f"%{search}%"

        if username:
            filters.append("username = %(username)s")
            params["username"] = username

        if signin_type:
            filters.append("sub LIKE %(signin_type)s")
            params["signin_type"] = f"{signin_type}|%"

        if role:
            filters.append("role = %(role)s")
            params["role"] = role

        sql = f"""
            SELECT * FROM users
            {"WHERE " + " AND ".join(filters) if filters else ""}
            ORDER BY registered_at DESC
        """
        sql += (
            """
            OFFSET %(offset)s
            LIMIT %(limit)s;
        """
            if skip and limit
            else ";"
        )
        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                sql,
                params,
            )
            return await cur.fetchall()

    @classmethod
    async def delete(cls, db: Connection, user_sub: str) -> bool:
        """Delete a user and their related data."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                UPDATE task_events SET user_sub = NULL WHERE user_sub = %(user_sub)s;
            """,
                {"user_sub": user_sub},
            )
            await cur.execute(
                """
                UPDATE projects SET author_sub = NULL WHERE author_sub = %(user_sub)s;
            """,
                {"user_sub": user_sub},
            )
            await cur.execute(
                """
                DELETE FROM organisation_managers WHERE user_sub = %(user_sub)s;
            """,
                {"user_sub": user_sub},
            )
            await cur.execute(
                """
                DELETE FROM user_roles WHERE user_sub = %(user_sub)s;
            """,
                {"user_sub": user_sub},
            )
            await cur.execute(
                """
                DELETE FROM users WHERE id = %(user_sub)s;
            """,
                {"user_sub": user_sub},
            )

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
            ON CONFLICT (sub) DO UPDATE
            SET
                role = EXCLUDED.role,
                mapping_level = EXCLUDED.mapping_level,
                name = EXCLUDED.name,
                api_key = EXCLUDED.api_key
        """

        sql = f"""
            INSERT INTO users
                ({columns})
            VALUES
                ({value_placeholders})
            {conflict_statement if ignore_conflict else ""}
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

    @classmethod
    async def update(
        cls, db: Connection, user_sub: str, user_update: "UserUpdate"
    ) -> Self:
        """Update a specific user record."""
        model_dump = dump_and_check_model(user_update)
        placeholders = [f"{key} = %({key})s" for key in model_dump.keys()]
        sql = f"""
            UPDATE users
            SET {", ".join(placeholders)}
            WHERE sub = %(user_sub)s
            RETURNING *;
        """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                sql,
                {"user_sub": user_sub, **model_dump},
            )
            updated_user = await cur.fetchone()

        if updated_user is None:
            msg = f"Failed to update user: {user_sub}"
            log.error(msg)
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
            )

        return updated_user


class DbUserInvite(BaseModel):
    """Table user_invites."""

    token: Optional[UUID] = None
    project_id: Optional[int] = None
    osm_username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[ProjectRole] = None
    expires_at: Optional[AwareDatetime] = None
    used_at: Optional[AwareDatetime] = None
    created_at: Optional[AwareDatetime] = None

    @classmethod
    async def one(cls, db: Connection, token: str) -> Self:
        """Get a user invite record by it's token."""
        async with db.cursor(row_factory=class_row(cls)) as cur:
            sql = """
                SELECT *
                FROM user_invites
                WHERE token = %(token)s;
            """

            await cur.execute(
                sql,
                {"token": token},
            )
            db_user_invite = await cur.fetchone()

        if db_user_invite is None:
            raise KeyError(f"User invite token ({token}) not found.")

        return db_user_invite

    @classmethod
    async def all(
        cls,
        db: Connection,
        project_id: int,
    ) -> Optional[list[Self]]:
        """Fetch all user invites for a project."""
        sql = """
            SELECT * FROM user_invites
            WHERE project_id = %(project_id)s
            ORDER BY created_at DESC;
        """
        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                sql,
                {"project_id": project_id},
            )
            return await cur.fetchall()

    @classmethod
    async def delete(cls, db: Connection, token: str) -> None:
        """Delete a user and their related data."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM user_invites WHERE token = %(token)s;
            """,
                {"token": token},
            )

    @classmethod
    async def create(
        cls,
        db: Connection,
        project_id: int,
        user_in: "UserInviteIn",
    ) -> Self:
        """Create a new user invite."""
        model_dump = dump_and_check_model(user_in)
        model_dump.update({"project_id": project_id})
        columns = ", ".join(model_dump.keys())
        value_placeholders = ", ".join(f"%({key})s" for key in model_dump.keys())

        sql = f"""
            INSERT INTO user_invites
                ({columns})
            VALUES
                ({value_placeholders})
            RETURNING *;
        """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql, model_dump)
            new_user_invite = await cur.fetchone()

        if new_user_invite is None:
            msg = f"Unknown SQL error for data: {model_dump}"
            log.error(f"Failed user invite creation: {model_dump}")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
            )

        return new_user_invite

    @classmethod
    async def update(
        cls, db: Connection, token: UUID, user_update: "UserInviteUpdate"
    ) -> Self:
        """Update the a user invite record."""
        model_dump = dump_and_check_model(user_update)
        placeholders = [f"{key} = %({key})s" for key in model_dump.keys()]
        sql = f"""
            UPDATE user_invites
            SET {", ".join(placeholders)}
            WHERE token = %(token)s
            RETURNING *;
        """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                sql,
                {"token": token, **model_dump},
            )
            updated_user_invite = await cur.fetchone()

        if updated_user_invite is None:
            msg = f"Failed to update user invite: {token}"
            log.error(msg)
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
            )

        return updated_user_invite

    def is_expired(self) -> bool:
        """Helper to check if invite is expired."""
        if bool(self.used_at):
            return True
        if self.expires_at:
            return timestamp() > self.expires_at
        return False


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
    created_by: Optional[str] = None  # this is not foreign key linked intentionally
    associated_email: Optional[str] = None
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
    async def primary_org(cls, db: Connection) -> Self:
        """Fetch the first organisation (lowest ID)."""
        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute("SELECT * FROM organisations ORDER BY id LIMIT 1;")
            db_org = await cur.fetchone()
            if db_org is None:
                raise KeyError("No organisations found.")
        return db_org

    @classmethod
    async def all(
        cls, db: Connection, current_user_sub: str = ""
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
                        WHERE sub = %(user_sub)s) = 'ADMIN'
                        THEN TRUE
                    ELSE approved
                END = TRUE
            ORDER BY created_at DESC;
        """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql, {"user_sub": current_user_sub})
            return await cur.fetchall()

    @classmethod
    async def create(
        cls,
        db: Connection,
        org_in: "OrganisationIn",
        user_sub: str,
        new_logo: UploadFile,
        ignore_conflict: bool = False,
    ) -> Optional[Self]:
        """Create a new organisation."""
        # Set requesting user to the org owner
        org_in.created_by = user_sub

        model_dump = dump_and_check_model(org_in)
        columns = ", ".join(model_dump.keys())
        value_placeholders = ", ".join(f"%({key})s" for key in model_dump.keys())

        sql = f"""
            INSERT INTO organisations
                ({columns})
            VALUES
                ({value_placeholders})
            {'ON CONFLICT ("name") DO NOTHING' if ignore_conflict else ""}
            RETURNING *;
        """

        try:
            async with db.cursor(row_factory=class_row(cls)) as cur:
                await cur.execute(sql, model_dump)
                new_org = await cur.fetchone()

            if new_org and new_org.logo is None and new_logo:
                from app.organisations.organisation_schemas import OrganisationUpdate

                logo_url = await cls.upload_logo(new_org.id, new_logo)
                await cls.update(db, new_org.id, OrganisationUpdate(logo=logo_url))

            return new_org
        except UniqueViolation as e:
            # Return conflict error when organisation name already exists
            log.error(f"Organisation named ({org_in.name}) already exists!")
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail=f"Organisation named ({org_in.name}) already exists!",
            ) from e

        except Exception as e:
            # Log errors only for actual failures (e.g., DB errors)
            msg = f"Unknown SQL error for data: {model_dump}"
            log.error(f"User ({user_sub}) failed organisation creation: {e}")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
            ) from e

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
            SET {", ".join(placeholders)}
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
        try:
            sql = """
                WITH deleted_org_managers AS (
                    DELETE FROM organisation_managers
                    WHERE organisation_id = %(org_id)s
                    RETURNING organisation_id
                ),
                deleted_org AS (
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
                return True

        except psycopg.errors.ForeignKeyViolation as e:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="""Cannot delete organization with existing projects.
                Delete all projects first.""",
            ) from e
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Failed to delete organization: {e}",
            ) from e

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
    user_sub: str

    # calculated
    username: Optional[str] = ""
    profile_img: Optional[str] = ""

    @classmethod
    async def create(
        cls,
        db: Connection,
        org_id: int,
        user_sub: str,
    ) -> Self:
        """Add a new organisation manager.

        Args:
            db (Connection): The database connection.
            org_id (int): The organisation ID.
            user_sub (int): The user ID to add as manager.

        Returns:
            Self: An instance of DbOrganisationManagers.
        """
        log.info(f"Adding user ({user_sub}) as org ({org_id}) admin")
        sql = """
            INSERT INTO public.organisation_managers
                (organisation_id, user_sub)
            VALUES
                (%(org_id)s, %(user_sub)s)
            ON CONFLICT (organisation_id, user_sub) DO NOTHING;
        """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            data = {
                "org_id": org_id,
                "user_sub": user_sub,
            }
            await cur.execute(sql, data)

    @classmethod
    async def get(
        cls,
        db: Connection,
        org_id: int,
        user_sub: Optional[str] = None,
    ) -> Optional[list[Self]]:
        """Get organisation manager by organisation and user ID."""
        async with db.cursor(row_factory=class_row(cls)) as cur:
            sql = """
                SELECT
                    om.organisation_id,
                    om.user_sub,
                    u.username,
                    u.profile_img
                FROM organisation_managers AS om
                INNER JOIN users AS u
                    ON u.sub = om.user_sub
                WHERE om.organisation_id = %(org_id)s
            """
            params = {"org_id": org_id}
            if user_sub:
                sql += " AND user_sub = %(user_sub)s"
                params["user_sub"] = user_sub
            sql += ";"
            await cur.execute(sql, params)
            return await cur.fetchall()

    @classmethod
    async def delete(cls, db: Connection, user_sub: str):
        """Delete an organization manager.

        Args:
            db: Database connection
            user_sub: The subject ID of the user to remove

        Returns:
            None
        """
        async with db.cursor() as cur:
            await cur.execute(
                "DELETE FROM organisation_managers WHERE user_sub = %(user_sub)s;",
                {"user_sub": user_sub},
            )


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
    user_sub: Optional[str] = None
    team_id: Optional[UUID] = None
    username: Optional[str] = None
    comment: Optional[str] = None
    created_at: Optional[AwareDatetime] = None

    # Computed
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
                the.*,
                u.profile_img
            FROM
                public.task_events the
            LEFT JOIN
                users u ON u.sub = the.user_sub
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
        username = (
            "NULL"
            if model_dump.get("user_sub") is None
            else "(SELECT username FROM users WHERE sub = %(user_sub)s)"
        )

        # NOTE the project_id need not be passed, as it's extracted from the task
        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                f"""
                    WITH inserted AS (
                        INSERT INTO public.task_events (
                            event_id,
                            project_id,
                            username,
                            {columns}
                        )
                        VALUES (
                            gen_random_uuid(),
                            (SELECT project_id FROM tasks WHERE id = %(task_id)s),
                            {username},
                            {value_placeholders}
                        )
                        RETURNING *
                    )
                    SELECT
                        inserted.*,
                        CASE WHEN inserted.user_sub IS NOT NULL THEN
                            (SELECT profile_img FROM users
                                WHERE sub = inserted.user_sub
                            )
                        ELSE
                            NULL
                        END as profile_img
                    FROM inserted;
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


class DbProjectTeam(BaseModel):
    """Table project_teams."""

    team_id: UUID
    team_name: Optional[str] = None
    project_id: int

    # Computed
    users: Optional[list[dict]] = []

    @classmethod
    async def one(cls, db: Connection, team_id: UUID) -> Self:
        """Fetch a single team by its ID along with user details."""
        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                """
                SELECT pt.team_id, pt.team_name, pt.project_id,
                COALESCE(
                    JSON_AGG(
                        JSON_BUILD_OBJECT(
                            'sub', u.sub,
                            'username', u.username,
                            'profile_img', u.profile_img
                        )
                    ) FILTER (WHERE u.sub IS NOT NULL), '[]'
                ) AS users
                FROM project_teams pt
                LEFT JOIN project_team_users ptu
                    ON pt.team_id = ptu.team_id
                LEFT JOIN users u
                    ON ptu.user_sub = u.sub
                WHERE pt.team_id = %(team_id)s
                GROUP BY pt.team_id;
                """,
                {"team_id": team_id},
            )
            team = await cur.fetchone()

        if team is None:
            raise KeyError(f"Team ({team_id}) not found.")

        return team

    @classmethod
    async def create(cls, db: Connection, team_in: "ProjectTeamIn") -> Self:
        """Create a new team for a project."""
        model_dump = dump_and_check_model(team_in)
        columns = ", ".join(model_dump.keys())
        value_placeholders = ", ".join(f"%({key})s" for key in model_dump.keys())

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                f"""
                    INSERT INTO project_teams
                        ({columns})
                    VALUES
                        ({value_placeholders})
                    RETURNING *;
                """,
                model_dump,
            )
            return await cur.fetchone()

    @classmethod
    async def update(
        cls, db: Connection, team_id: UUID, team_update: "ProjectTeamIn"
    ) -> Self:
        """Update a team for a project."""
        model_dump = dump_and_check_model(team_update)
        placeholders = ", ".join(f"{key} = %({key})s" for key in model_dump.keys())
        sql = f"""
            UPDATE project_teams
                SET {placeholders}
            WHERE team_id = %(team_id)s
            RETURNING *;
        """
        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql, {"team_id": team_id, **model_dump})
            updated_team = await cur.fetchone()

        if updated_team is None:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Failed to update team {team_id}",
            )
        return updated_team

    @classmethod
    async def delete(cls, db: Connection, team_id: str):
        """Delete a team."""
        async with db.cursor() as cur:
            await cur.execute(
                "DELETE FROM project_teams WHERE team_id = %(team_id)s;",
                {"team_id": team_id},
            )
            await cur.execute(
                "DELETE FROM project_team_users WHERE team_id = %(team_id)s;",
                {"team_id": team_id},
            )

    @classmethod
    async def all(cls, db: Connection, project_id: int) -> list[Self]:
        """Fetch all teams for a project along with users."""
        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                """
                SELECT pt.team_id, pt.team_name, pt.project_id,
                COALESCE(
                    JSON_AGG(
                        JSON_BUILD_OBJECT(
                            'sub', u.sub,
                            'username', u.username,
                            'profile_img', u.profile_img
                        )
                    ) FILTER (WHERE u.sub IS NOT NULL), '[]'
                ) AS users
                FROM project_teams pt
                LEFT JOIN project_team_users ptu ON pt.team_id = ptu.team_id
                LEFT JOIN users u ON ptu.user_sub = u.sub
                WHERE pt.project_id = %(project_id)s
                GROUP BY pt.team_id;
                """,
                {"project_id": project_id},
            )
            teams = await cur.fetchall()

        return teams


class DbProjectTeamUser(BaseModel):
    """Table project_team_users."""

    team_id: UUID
    user_sub: str

    @classmethod
    async def create(cls, db: Connection, team_id: UUID, user_subs: List[str]):
        """Add users to a team."""
        model_dump = [
            {"team_id": team_id, "user_sub": user_sub} for user_sub in user_subs
        ]

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.executemany(
                """
                    INSERT INTO public.project_team_users
                        (team_id, user_sub)
                    VALUES
                        (%(team_id)s, %(user_sub)s)
                    ON CONFLICT (team_id, user_sub) DO NOTHING;
                """,
                model_dump,
            )

    @classmethod
    async def delete(cls, db: Connection, team_id: UUID, user_subs: List[str]):
        """Remove users from a team."""
        model_dump = [
            {"team_id": team_id, "user_sub": user_sub} for user_sub in user_subs
        ]

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.executemany(
                """
                    DELETE FROM public.project_team_users
                    WHERE team_id = %(team_id)s AND user_sub = %(user_sub)s;
                """,
                model_dump,
            )


class DbTask(BaseModel):
    """Table tasks."""

    id: int
    outline: Optional[dict] = None
    project_id: Optional[int] = None
    project_task_index: Optional[int] = None
    feature_count: Optional[int] = None

    # Calculated
    task_state: Optional[MappingState] = None
    actioned_by_uid: Optional[str] = None
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
                        COALESCE(latest_event.user_sub, NULL) AS actioned_by_uid,
                        COALESCE(latest_event.username, NULL) AS actioned_by_username
                    FROM
                        tasks
                    LEFT JOIN LATERAL (
                        SELECT
                            th.event,
                            th.state,
                            th.user_sub,
                            u.username
                        FROM
                            task_events th
                        LEFT JOIN
                            users u ON u.sub = th.user_sub
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
                COALESCE(latest_event.user_sub, NULL) AS actioned_by_uid,
                COALESCE(latest_event.username, NULL) AS actioned_by_username
            FROM
                tasks
            LEFT JOIN LATERAL (
                SELECT
                    th.event,
                    th.state,
                    th.user_sub,
                    u.username
                FROM
                    task_events th
                LEFT JOIN
                    users u ON u.sub = th.user_sub
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
            project_id (int): The project ID.
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
                f"(%(project_id)s,{index + 1},ST_GeomFromGeoJSON(%({feature_index})s))"
            )
            # Must be string json for db input
            data[feature_index] = json.dumps(feature["geometry"])
        data["project_id"] = project_id

        # Join the values list into the SQL statement
        sql += ", ".join(values) + " RETURNING True;"

        async with db.cursor() as cur:
            await cur.execute(sql, data)
            result = await cur.fetchall()

            if success := bool(result):
                update_project_sql = """
                    UPDATE projects
                    SET total_tasks = (
                        SELECT COALESCE(MAX(project_task_index), 0)
                        FROM public.tasks WHERE project_id = %(project_id)s
                    )
                    WHERE id = %(project_id)s;
                """
                log.debug(f"Updating total_tasks count for project ({project_id})")
                await cur.execute(update_project_sql, {"project_id": project_id})

            else:
                log.error(f"Failed to insert task areas into db. Result: {result}")

        return success


class DbProject(BaseModel):
    """Table projects."""

    id: int
    name: str
    outline: Optional[dict] = None
    odkid: Optional[int] = None
    author_sub: Optional[str] = None
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
    osm_category: Optional[str] = None
    odk_form_id: Optional[str] = None
    odk_form_xml: Optional[str] = None
    xlsform_content: Optional[bytes] = None
    mapper_level: Optional[MappingLevel] = None
    priority: Optional[ProjectPriority] = None
    featured: Optional[bool] = None
    odk_central_url: Optional[str] = None
    odk_central_user: Optional[str] = None
    odk_central_password: Optional[str] = None
    odk_token: Optional[str] = None
    data_extract_url: Optional[str] = None
    task_split_dimension: Optional[int] = None
    task_num_buildings: Optional[int] = None
    primary_geom_type: Optional[DbGeomType] = None  # the main geometries surveyed
    new_geom_type: Optional[DbGeomType] = None  # when new geometries are drawn
    geo_restrict_distance_meters: Optional[PositiveInt] = None
    geo_restrict_force_error: Optional[bool] = None
    use_odk_collect: Optional[bool] = None
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
    total_tasks: Optional[int] = None
    num_contributors: Optional[int] = None
    total_submissions: Optional[int] = 0
    tasks_mapped: Optional[int] = 0
    tasks_validated: Optional[int] = 0
    tasks_bad: Optional[int] = 0

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
    async def one(
        cls,
        db: Connection,
        project_id: int,
        minimal: bool = False,
        warn_on_missing_token: bool = True,
    ) -> Self:
        """Get project by ID, including all tasks and other details."""
        # Simpler query without additional metadata
        if minimal:
            sql = """
                SELECT
                    p.*,
                    project_org.name AS organisation_name,
                    ST_AsGeoJSON(p.outline)::jsonb AS outline,
                    ST_AsGeoJSON(ST_Centroid(p.outline))::jsonb AS centroid,
                    COALESCE(
                        JSON_AGG(
                            JSON_BUILD_OBJECT(
                                'id', t.id,
                                'project_id', t.project_id,
                                'project_task_index', t.project_task_index,
                                'outline', ST_AsGeoJSON(t.outline)::jsonb,
                                'feature_count', t.feature_count
                            )
                        ) FILTER (WHERE t.id IS NOT NULL), '[]'::json
                    ) AS tasks
                FROM
                    projects p
                LEFT JOIN
                    tasks t ON t.project_id = %(project_id)s
                LEFT JOIN
                    organisations project_org ON p.organisation_id = project_org.id
                WHERE
                    p.id = %(project_id)s AND (
                        t.project_id = %(project_id)s
                            -- Also required to return a project with if tasks
                            OR t.project_id IS NULL
                    )
                GROUP BY p.id, project_org.name;
            """

        # Full query with all additional calculated fields
        else:
            sql = """
                WITH latest_status_per_task AS (
                    SELECT DISTINCT ON (task_id)
                        th.task_id,
                        th.event,
                        th.state,
                        th.created_at,
                        th.user_sub,
                        u.username AS username
                    FROM
                        task_events th
                    LEFT JOIN
                        users u ON u.sub = th.user_sub
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
                                    latest_status_per_task.user_sub,
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

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                sql,
                {"project_id": project_id},
            )
            db_project = await cur.fetchone()

        if db_project is None:
            raise KeyError(f"Project ({project_id}) not found.")

        if warn_on_missing_token and db_project.odk_token is None:
            log.warning(
                f"Project ({db_project.id}) has no 'odk_token' set. "
                "The QRCode will not work!"
            )

        return db_project

    @classmethod
    async def all(
        cls,
        db: Connection,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        current_user: Optional[str] = None,
        org_id: Optional[int] = None,
        user_sub: Optional[str] = None,
        hashtags: Optional[list[str]] = None,
        search: Optional[str] = None,
        minimal: bool = False,
        status: Optional[ProjectStatus] = None,
    ) -> Optional[list[Self]]:
        """Fetch all projects with optional filters for user, hashtags, and search."""
        if current_user:
            access_info = await cls._get_user_access_level(db, current_user)
        else:
            access_info = None

        filters, params = cls._build_query_filters(
            skip, limit, org_id, user_sub, hashtags, search, access_info, status
        )
        sql = cls._construct_sql_query(filters, minimal, skip, limit)

        # Execute query and return results
        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()

    @classmethod
    async def _get_user_access_level(
        cls, db: Connection, current_user: Optional[str]
    ) -> dict:
        """Extract user context information for authorization checks."""
        access_info = {}
        db_user = await DbUser.one(db, current_user.sub)
        managed_orgs = db_user.orgs_managed if hasattr(db_user, "orgs_managed") else []
        access_info["is_superadmin"] = db_user.role == UserRole.ADMIN
        access_info["managed_org_ids"] = managed_orgs
        access_info["user_sub"] = current_user.sub

        return access_info

    @classmethod
    def _build_query_filters(
        cls,
        skip: Optional[int],
        limit: Optional[int],
        org_id: Optional[int],
        user_sub: Optional[str],
        hashtags: Optional[list[str]],
        search: Optional[str],
        access_info: Optional[dict] = None,
        status: Optional[ProjectStatus] = None,
    ) -> tuple[list[str], dict, bool]:
        """Build query filters and parameters based on provided criteria."""

        def normalize_search_input(raw: str) -> str:
            """Normalize user search string.

            remove extra spaces, lowercase, and wrap with '%'.
            """
            cleaned = " ".join(raw.lower().split())
            return f"%{cleaned}%" if cleaned else None

        normalized_search = normalize_search_input(search) if search else None

        # Build basic filters
        filters_map = {
            "p.organisation_id = %(org_id)s": org_id,
            "p.author_sub = %(user_sub)s": user_sub,  # project author
            "p.hashtags && %(hashtags)s": hashtags,
            "p.status = %(status)s": status,
            
            # Improved search: replace dashes and underscores in slug with space
            (
                "LOWER(REPLACE(REPLACE(p.slug, '-', ' '), '_', ' ')) ILIKE %(search)s"
            ): normalized_search,
        }

        filters = [
            condition for condition, value in filters_map.items() if value is not None
        ]

        # Add visibility filter based on user authorization
        visibility_filter = cls._build_visibility_filter(access_info)
        if visibility_filter:
            filters.append(visibility_filter)

        params = {
            key: value
            for key, value in {
                "offset": skip,
                "limit": limit,
                "org_id": org_id,
                "user_sub": user_sub,
                "hashtags": hashtags,
                "search": f"%{search}%" if search else None,
                "status": status,
            }.items()
            if value is not None
        }

        if access_info:
            params["current_user_sub"] = access_info["user_sub"]
            if access_info["managed_org_ids"]:
                params["managed_org_ids"] = access_info["managed_org_ids"]

        return filters, params

    @classmethod
    def _build_visibility_filter(
        cls, access_info: Optional[dict] = None
    ) -> Optional[str]:
        """Build visibility filter based on user context."""
        # Not logged in, so return public projects only, excluding drafts
        if access_info is None:
            return """
        (
            p.visibility = 'PUBLIC'
            AND p.status != 'DRAFT'
        )
        """

        if access_info["is_superadmin"]:
            # Superadmin sees everything, no filters
            return None

        if access_info["managed_org_ids"]:
            # Org managers see all projects in their orgs including drafts
            return """
            (
                (p.visibility = 'PUBLIC' AND p.status != 'DRAFT')
                OR p.organisation_id = ANY(%(managed_org_ids)s)
            )
        """

        # Regular users see:
        # 1. Public non-draft projects
        # 2. Projects they have access to:
        #    - If Any user is assigned as a project manager in any project,
        # can see public projects and assigned project even it is draft
        return """
        (
            (p.visibility = 'PUBLIC' AND p.status != 'DRAFT')
            OR
            EXISTS (
                SELECT 1 FROM user_roles ur
                WHERE ur.project_id = p.id
                AND ur.user_sub = %(current_user_sub)s
                AND (
                    ur.role = 'PROJECT_MANAGER'
                    OR p.status != 'DRAFT'
                )
            )
        )
    """

    @classmethod
    def _construct_sql_query(
        cls,
        filters: list,
        minimal: bool,
        skip: Optional[int],
        limit: Optional[int],
    ) -> str:
        """Construct SQL query based on filters and query type."""
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

        sql = f"""
            WITH filtered_projects AS (
                SELECT p.* FROM projects p
                {where_clause}
            )
        """

        # Add appropriate SELECT based on minimal flag
        if minimal:
            sql += cls._minimal_select_query()
        else:
            sql += cls._full_select_query()

        if skip is not None and limit is not None:
            sql += """
                OFFSET %(offset)s
                LIMIT %(limit)s;
            """
        else:
            sql += ";"

        return sql

    @classmethod
    def _minimal_select_query(cls) -> str:
        """Return minimal SELECT query for mapper frontend."""
        return """
            SELECT
                fp.id,
                fp.name,
                fp.location_str,
                fp.short_description,
                fp.status,
                project_org.logo AS organisation_logo
            FROM
                filtered_projects fp
            LEFT JOIN
                organisations project_org ON fp.organisation_id = project_org.id
            ORDER BY
                fp.created_at DESC
        """

    @classmethod
    def _full_select_query(cls) -> str:
        """Return full SELECT query with all project details."""
        return """
            SELECT
                fp.*,
                ST_AsGeoJSON(fp.outline)::jsonb AS outline,
                ST_AsGeoJSON(ST_Centroid(fp.outline))::jsonb AS centroid,
                project_org.logo AS organisation_logo,
                fp.total_tasks,
                stats.num_contributors,
                stats.total_submissions,
                stats.tasks_mapped,
                stats.tasks_bad,
                stats.tasks_validated
            FROM
                filtered_projects fp
            LEFT JOIN
                organisations project_org ON fp.organisation_id = project_org.id
            LEFT JOIN
                mv_project_stats stats ON fp.id = stats.project_id
            ORDER BY
                fp.created_at DESC
        """

    @classmethod
    async def create(cls, db: Connection, project_in: "StubProjectIn") -> Self:
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
            SET {", ".join(placeholders)}
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
                DELETE FROM user_invites WHERE project_id = %(project_id)s;
            """,
                {"project_id": project_id},
            )
            await cur.execute(
                """
                DELETE FROM projects WHERE id = %(project_id)s;
            """,
                {"project_id": project_id},
            )


class DbOdkEntities(BaseModel):
    """Table odk_entities.

    Mirror tracking the status of Entities in ODK.
    """

    entity_id: UUID
    status: EntityState
    project_id: int
    task_id: Optional[int]
    osm_id: int
    submission_ids: str
    # NOTE geometry is only set if the geom is 'new' or 'bad'
    geometry: str
    # NOTE previous we had field is_new, replaced by created_by
    # NOTE as is_new is implicitly true if created_by is set
    created_by: str

    @classmethod
    async def upsert(
        cls,
        db: Connection,
        project_id: int,
        entities: list[Self],
        batch_size: int = 10000,
    ) -> bool:
        """Update or insert Entity data in batches, with statuses.

        Args:
            db (Connection): The database connection.
            project_id (int): The project ID.
            entities (list[Self]): List of DbOdkEntities objects.
            batch_size (int): Number of entities to process in each batch.

        Returns:
            bool: Success or failure.
        """
        log.info(
            f"Updating Field-TM database Entities for project {project_id} "
            f"with ({len(entities)}) features in batches of {batch_size}"
        )

        result = []

        for batch_start in range(0, len(entities), batch_size):
            batch = entities[batch_start : batch_start + batch_size]
            sql = """
                INSERT INTO public.odk_entities
                    (entity_id, status, project_id, task_id,
                    osm_id, submission_ids, geometry, created_by)
                VALUES
            """

            # Prepare data for batch insert
            values = []
            data = {}
            for index, entity in enumerate(batch):
                entity_index = f"entity_{batch_start + index}"
                values.append(
                    f"(%({entity_index}_entity_id)s, "
                    f"%({entity_index}_status)s, "
                    f"%({entity_index}_project_id)s, "
                    f"%({entity_index}_task_id)s, "
                    f"%({entity_index}_osm_id)s, "
                    f"%({entity_index}_submission_ids)s, "
                    f"%({entity_index}_geometry)s, "
                    f"%({entity_index}_created_by)s)"
                )
                data[f"{entity_index}_entity_id"] = entity["id"]
                data[f"{entity_index}_status"] = EntityState(int(entity["status"])).name
                data[f"{entity_index}_project_id"] = project_id
                task_id = entity["task_id"]
                data[f"{entity_index}_task_id"] = (
                    int(task_id) if task_id not in (None, "", "None") else None
                )
                data[f"{entity_index}_osm_id"] = entity["osm_id"]
                data[f"{entity_index}_submission_ids"] = entity["submission_ids"]
                data[f"{entity_index}_osm_id"] = entity["osm_id"]
                # Only copy geometry if new geom (created_by), or marked bad
                should_include_geom = (
                    entity["status"] == "6" or entity["created_by"] != ""
                )
                data[f"{entity_index}_geometry"] = (
                    entity["geometry"] if should_include_geom else ""
                )
                data[f"{entity_index}_created_by"] = entity["created_by"]

            sql += (
                ", ".join(values)
                + """
                ON CONFLICT (entity_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    task_id = EXCLUDED.task_id,
                    osm_id = EXCLUDED.osm_id,
                    submission_ids = EXCLUDED.submission_ids,
                    geometry = EXCLUDED.geometry,
                    created_by = EXCLUDED.created_by
                RETURNING True;
            """
            )

            async with db.cursor() as cur:
                await cur.execute(sql, data)
                batch_result = await cur.fetchall()
                if not batch_result:
                    log.warning(
                        f"Batch failed at batch {batch_start} for project {project_id}"
                    )
                result.extend(batch_result)

        return bool(result)

    @classmethod
    async def update(
        cls, db: Connection, entity_uuid: str, entity_update: "OdkEntitiesUpdate"
    ) -> bool:
        """Update the entity value in the Field-TM db."""
        model_dump = dump_and_check_model(entity_update)
        placeholders = [f"{key} = %({key})s" for key in model_dump.keys()]
        sql = f"""
            UPDATE odk_entities
            SET {", ".join(placeholders)}
            WHERE entity_id = %(entity_uuid)s
            RETURNING entity_id;
        """

        async with db.cursor() as cur:
            await cur.execute(
                sql,
                {"entity_uuid": entity_uuid, **model_dump},
            )
            success = await cur.fetchone()

        if not success:
            msg = f"Failed to update entity with UUID: {entity_uuid}"
            log.error(msg)
            return False

        return True

    @classmethod
    async def delete(
        cls,
        db: Connection,
        uuid: str,
    ):
        """Delete an entity."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM odk_entities WHERE entity_id = %(uuid)s;
            """,
                {"uuid": uuid},
            )
            if cur.rowcount == 0:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"Entity with UUID {uuid} not found in database.",
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
            SET {", ".join(placeholders)}
            WHERE id = %(task_id)s
            RETURNING *;
        """

        # This is a workaround as the db connection can often timeout,
        # before the background job is finished processing
        pool = database.get_db_connection_pool()
        async with pool as pool_instance:
            async with pool_instance.connection() as conn:
                async with conn.cursor(row_factory=class_row(cls)) as cur:
                    await cur.execute(sql, {"task_id": task_id, **model_dump})
                    updated_task = await cur.fetchone()

        if updated_task is None:
            msg = f"Failed to update background task with ID: {task_id}"
            log.error(msg)
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
            )

        return updated_task

    @classmethod
    async def delete(cls, db: Connection, background_task_id: UUID) -> bool:
        """Delete a background task entry."""
        sql = """
            DELETE from background_tasks
            WHERE id = %(background_task_id)s
            RETURNING id;
        """

        async with db.cursor() as cur:
            await cur.execute(sql, {"background_task_id": background_task_id})
            success = await cur.fetchone()

        if success:
            return True
        return False


class DbBasemap(BaseModel):
    """Table tiles_path.

    TODO for now we generate the basemap entry in Field-TM.
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
        basemap_id: UUID,
        basemap_update: "BasemapUpdate",
    ) -> Self:
        """Update values for a basemap."""
        model_dump = dump_and_check_model(basemap_update)
        placeholders = [f"{key} = %({key})s" for key in model_dump.keys()]
        sql = f"""
            UPDATE basemaps
            SET {", ".join(placeholders)}
            WHERE id = %(basemap_id)s
            RETURNING *;
        """

        # This is a workaround as the db connection can often timeout,
        # before the basemap is finished processing
        pool = database.get_db_connection_pool()
        async with pool as pool_instance:
            async with pool_instance.connection() as conn:
                async with conn.cursor(row_factory=class_row(cls)) as cur:
                    await cur.execute(sql, {"basemap_id": basemap_id, **model_dump})
                    updated_basemap = await cur.fetchone()

        if updated_basemap is None:
            msg = f"Failed to update basemap with ID: {basemap_id}"
            log.error(msg)
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
            )

        return updated_basemap

    @classmethod
    async def delete(cls, db: Connection, basemap_id: UUID) -> bool:
        """Delete a basemap."""
        sql = """
            DELETE from basemaps
            WHERE id = %(basemap_id)s
            RETURNING id;
        """

        async with db.cursor() as cur:
            await cur.execute(sql, {"basemap_id": basemap_id})
            success = await cur.fetchone()

        if success:
            return True
        return False


def slugify(name: Optional[str]) -> Optional[str]:
    """Return a sanitised URL slug from a name."""
    if name is None:
        return None
    # Remove special characters and replace spaces with hyphens
    slug = sub(r"[^\w\s-]", "", name).strip().lower().replace(" ", "-")
    # Remove consecutive hyphens
    slug = sub(r"[-\s]+", "-", slug)
    return slug
