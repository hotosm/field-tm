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
import logging
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date
from re import sub
from typing import Any, Mapping, Optional, Self

from litestar import status_codes as status
from litestar.exceptions import HTTPException
from psycopg import AsyncConnection
from psycopg.rows import class_row
from pydantic import AwareDatetime, BaseModel

from app.config import settings
from app.db.enums import (
    FieldMappingApp,
    ProjectRole,
    ProjectStatus,
    ProjectVisibility,
    XLSFormType,
)

log = logging.getLogger(__name__)


def dump_and_check_model(db_model: Any) -> dict:
    """Dump the Pydantic model, removing None and default values.

    Also validates to check the model is not empty for insert / update.
    """
    if isinstance(db_model, BaseModel):
        model_dump = db_model.model_dump(exclude_none=True, exclude_unset=True)
    elif is_dataclass(db_model):
        model_dump = {
            key: value for key, value in asdict(db_model).items() if value is not None
        }
    elif isinstance(db_model, Mapping):
        model_dump = {
            key: value for key, value in db_model.items() if value is not None
        }
    else:
        raise TypeError(
            f"Unsupported model type for dump_and_check_model: {type(db_model)!r}"
        )

    if not model_dump:
        log.error("Attempted create or update with no data.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided."
        )

    return model_dump


@dataclass(slots=True)
class DbUser:
    """Table users."""

    sub: Optional[str] = None
    username: Optional[str] = None
    is_admin: Optional[bool] = False
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    profile_img: Optional[str] = None
    email_address: Optional[str] = None
    registered_at: Optional[AwareDatetime] = None
    last_login_at: Optional[AwareDatetime] = None

    # Relationships
    project_roles: Optional[dict[int, ProjectRole]] = None  # project:role pairs

    @classmethod
    async def one(cls, db: AsyncConnection, user_subidentifier: str) -> Self:
        """Get a user either by ID or username."""
        async with db.cursor(row_factory=class_row(cls)) as cur:
            sql = """
                SELECT *
                FROM users
                WHERE sub ILIKE %(user_subidentifier)s;
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
        db: AsyncConnection,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        search: Optional[str] = None,
        username: Optional[str] = None,
        signin_type: Optional[str] = None,
        last_login_after: Optional[date] = None,
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

        if last_login_after:
            filters.append("last_login_at >= %(last_login_after)s")
            params["last_login_after"] = last_login_after

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
    async def delete(cls, db: AsyncConnection, user_sub: str) -> bool:
        """Delete a user and their related data."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                UPDATE projects SET created_by_sub = NULL
                WHERE created_by_sub = %(user_sub)s;
            """,
                {"user_sub": user_sub},
            )
            await cur.execute(
                """
                DELETE FROM users WHERE sub = %(user_sub)s;
            """,
                {"user_sub": user_sub},
            )
            return True

    @classmethod
    async def create(
        cls,
        db: AsyncConnection,
        user_in: Self,
        ignore_conflict: bool = False,
    ) -> Self:
        """Create a new user."""
        model_dump = dump_and_check_model(user_in)
        columns = ", ".join(model_dump.keys())
        value_placeholders = ", ".join(f"%({key})s" for key in model_dump.keys())
        conflict_statement = """
            ON CONFLICT (sub) DO UPDATE
            SET
                username = EXCLUDED.username,
                is_admin = EXCLUDED.is_admin,
                name = EXCLUDED.name,
                city = EXCLUDED.city,
                country = EXCLUDED.country,
                profile_img = EXCLUDED.profile_img,
                email_address = EXCLUDED.email_address
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
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=msg,
            )

        return new_user

    @classmethod
    async def update(
        cls, db: AsyncConnection, user_sub: str, user_update: Self
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
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=msg,
            )

        return updated_user


@dataclass(slots=True)
class DbTemplateXLSForm:
    """Table template_xlsforms.

    XLSForm templates and custom uploads.
    """

    id: Optional[int] = None
    title: Optional[str] = None
    xls: Optional[bytes] = None

    @classmethod
    async def all(
        cls,
        db: AsyncConnection,
    ) -> Optional[list[Self]]:
        """Fetch all XLSForms."""
        include_categories = [category.value for category in XLSFormType]

        sql = """
            SELECT
                id, title
            FROM template_xlsforms
            WHERE title IN (
                SELECT UNNEST(%(categories)s::text[])
            );
            """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql, {"categories": include_categories})
            forms = await cur.fetchall()

        # Don't include 'xls' field in the response
        return [{"id": form.id, "title": form.title} for form in forms]


@dataclass(slots=True)
class DbProject:
    """Table projects."""

    id: Optional[int] = None
    field_mapping_app: Optional[FieldMappingApp] = None
    external_project_instance_url: Optional[str] = None
    external_project_id: Optional[int] = None
    external_project_username: Optional[str] = None
    external_project_password_encrypted: Optional[str] = None
    created_by_sub: Optional[str] = None
    project_name: Optional[str] = None
    description: Optional[str] = None
    slug: Optional[str] = None
    location_str: Optional[str] = None
    outline: Optional[dict] = None
    status: Optional[ProjectStatus] = None
    visibility: Optional[ProjectVisibility] = None
    xlsform_content: Optional[bytes] = None
    hashtags: Optional[list[str]] = None
    custom_tms_url: Optional[str] = None
    created_at: Optional[AwareDatetime] = None
    updated_at: Optional[AwareDatetime] = None
    # Encrypted ODK appuser token (may be null until generated)
    odk_token: Optional[str] = None

    @classmethod
    async def one(
        cls,
        db: AsyncConnection,
        project_id: int,
        minimal: Optional[bool] = None,
        warn_on_missing_token: Optional[bool] = None,
    ) -> Self:
        """Get project by ID."""
        sql = """
            SELECT
                p.*,
                ST_AsGeoJSON(p.outline)::jsonb AS outline
            FROM
                projects p
            WHERE
                p.id = %(project_id)s;
        """

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                sql,
                {"project_id": project_id},
            )
            db_project = await cur.fetchone()

        if db_project is None:
            raise KeyError(f"Project ({project_id}) not found.")

        return db_project

    @classmethod
    async def all(
        cls,
        db: AsyncConnection,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        user_sub: Optional[str] = None,
        hashtags: Optional[list[str]] = None,
        search: Optional[str] = None,
        status: Optional[ProjectStatus] = None,
        field_mapping_app: Optional[FieldMappingApp] = None,
        country: Optional[str] = None,
    ) -> Optional[list[Self]]:
        """Fetch all projects with optional filters."""
        filters = []
        params = {}

        if user_sub:
            filters.append("created_by_sub = %(user_sub)s")
            params["user_sub"] = user_sub

        if hashtags:
            filters.append("hashtags && %(hashtags)s")
            params["hashtags"] = hashtags

        if status:
            filters.append("status = %(status)s")
            params["status"] = status

        if search:
            filters.append(
                "LOWER(REPLACE(REPLACE(slug, '-', ' '), '_', ' ')) ILIKE %(search)s"
            )
            params["search"] = f"%{search}%"

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

        sql = f"""
            SELECT
                p.*,
                ST_AsGeoJSON(p.outline)::jsonb AS outline
            FROM projects p
            {where_clause}
            ORDER BY created_at DESC
        """

        if skip is not None and limit is not None:
            sql += """
                OFFSET %(offset)s
                LIMIT %(limit)s;
            """
            params["offset"] = skip
            params["limit"] = limit
        else:
            sql += ";"

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()

    @classmethod
    async def create(cls, db: AsyncConnection, project_in: Self) -> Self:
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
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=msg,
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
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=msg,
            )

        return updated_project

    @classmethod
    async def update(
        cls,
        db: AsyncConnection,
        project_id: int,
        project_update: Self,
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
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=msg,
            )

        return updated_project

    @classmethod
    async def delete(cls, db: AsyncConnection, project_id: int) -> None:
        """Delete a project."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM projects WHERE id = %(project_id)s;
            """,
                {"project_id": project_id},
            )


def slugify(name: Optional[str]) -> Optional[str]:
    """Return a sanitised URL slug from a name."""
    if name is None:
        return None
    # Remove special characters and replace spaces with hyphens
    slug = sub(r"[^\w\s-]", "", name).strip().lower().replace(" ", "-")
    # Remove consecutive hyphens
    slug = sub(r"[-\s]+", "-", slug)
    return slug
