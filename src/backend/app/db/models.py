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
from typing import TYPE_CHECKING, Any, Mapping, Optional, Self

from litestar import status_codes as status
from litestar.exceptions import HTTPException
from psycopg import AsyncConnection, sql
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

if TYPE_CHECKING:
    from app.central.central_schemas import ODKCentral

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
    async def all(  # noqa: PLR0913
        cls,
        db: AsyncConnection,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        search: Optional[str] = None,
        username: Optional[str] = None,
        signin_type: Optional[str] = None,
        last_login_after: Optional[date] = None,
    ) -> Optional[list[Self]]:  # noqa: PLR0913
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

        query = sql.SQL("SELECT * FROM users")
        if filters:
            query += sql.SQL(" WHERE ")
            query += sql.SQL(" AND ").join(sql.SQL(clause) for clause in filters)
        query += sql.SQL(" ORDER BY registered_at DESC")
        if skip and limit:
            query += sql.SQL(" OFFSET %(offset)s LIMIT %(limit)s;")
        else:
            query += sql.SQL(";")
        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(query, params)
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
        columns = sql.SQL(", ").join(sql.Identifier(key) for key in model_dump)
        value_placeholders = sql.SQL(", ").join(
            sql.Placeholder(key) for key in model_dump
        )
        conflict_statement = sql.SQL(
            """
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
        )

        query = sql.SQL(
            "INSERT INTO users ({columns}) VALUES ({values}) {conflict} RETURNING *;"
        ).format(
            columns=columns,
            values=value_placeholders,
            conflict=conflict_statement if ignore_conflict else sql.SQL(""),
        )

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(query, model_dump)
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
        placeholders = sql.SQL(", ").join(
            sql.SQL("{column} = {value}").format(
                column=sql.Identifier(key),
                value=sql.Placeholder(key),
            )
            for key in model_dump
        )
        query = sql.SQL(
            "UPDATE users SET {placeholders} WHERE sub = %(user_sub)s RETURNING *;"
        ).format(placeholders=placeholders)

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                query,
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
class DbApiKey:
    """Table api_keys."""

    id: Optional[int] = None
    user_sub: Optional[str] = None
    key_hash: Optional[str] = None
    name: Optional[str] = None
    created_at: Optional[AwareDatetime] = None
    last_used_at: Optional[AwareDatetime] = None
    is_active: Optional[bool] = True

    @classmethod
    async def create(cls, db: AsyncConnection, api_key_in: Self) -> Self:
        """Create a new API key record."""
        model_dump = dump_and_check_model(api_key_in)
        columns = sql.SQL(", ").join(sql.Identifier(key) for key in model_dump)
        value_placeholders = sql.SQL(", ").join(
            sql.Placeholder(key) for key in model_dump
        )

        query = sql.SQL(
            """
            INSERT INTO api_keys ({columns})
            VALUES ({values})
            ON CONFLICT (key_hash) DO UPDATE
            SET
                user_sub = EXCLUDED.user_sub,
                name = EXCLUDED.name,
                is_active = TRUE
            RETURNING *;
        """
        ).format(columns=columns, values=value_placeholders)

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(query, model_dump)
            new_api_key = await cur.fetchone()

        if new_api_key is None:
            msg = f"Unknown SQL error for data: {model_dump}"
            log.error(f"API key creation failed: {msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=msg,
            )

        return new_api_key

    @classmethod
    async def get_by_hash(
        cls, db: AsyncConnection, key_hash: str, active_only: bool = True
    ) -> Optional[Self]:
        """Get API key record by hash."""
        sql = """
            SELECT *
            FROM api_keys
            WHERE key_hash = %(key_hash)s
        """
        params: dict[str, Any] = {"key_hash": key_hash}
        if active_only:
            sql += " AND is_active = TRUE"
        sql += ";"

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(sql, params)
            return await cur.fetchone()

    @classmethod
    async def all_for_user(cls, db: AsyncConnection, user_sub: str) -> list[Self]:
        """List all API keys for a user."""
        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                """
                SELECT *
                FROM api_keys
                WHERE user_sub = %(user_sub)s
                ORDER BY created_at DESC;
            """,
                {"user_sub": user_sub},
            )
            rows = await cur.fetchall()

        return rows or []

    @classmethod
    async def deactivate(
        cls, db: AsyncConnection, key_id: int, user_sub: str
    ) -> Optional[Self]:
        """Deactivate an API key owned by a given user."""
        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                """
                UPDATE api_keys
                SET is_active = FALSE
                WHERE id = %(key_id)s
                  AND user_sub = %(user_sub)s
                RETURNING *;
            """,
                {"key_id": key_id, "user_sub": user_sub},
            )
            return await cur.fetchone()

    @classmethod
    async def touch_last_used(cls, db: AsyncConnection, key_id: int) -> None:
        """Update API key last used timestamp."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                UPDATE api_keys
                SET last_used_at = NOW()
                WHERE id = %(key_id)s;
            """,
                {"key_id": key_id},
            )


@dataclass(slots=True)
class DbTemplateXLSForm:
    """Table template_xlsforms.

    XLSForm templates and custom uploads.
    """

    id: Optional[int] = None
    title: Optional[str] = None
    xls: Optional[bytes] = None

    @classmethod
    async def all(  # noqa: PLR0913
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

    @classmethod
    async def one(cls, db: AsyncConnection, template_id: int) -> Self:
        """Fetch one XLSForm template by id (includes binary xls content)."""
        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(
                """
                SELECT id, title, xls
                FROM template_xlsforms
                WHERE id = %(template_id)s;
            """,
                {"template_id": template_id},
            )
            form = await cur.fetchone()

        if form is None:
            raise KeyError(f"Template XLSForm ({template_id}) not found.")

        return form


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
    # GeoJSON data extract stored directly in database (replaces S3 URL approach)
    data_extract_geojson: Optional[dict] = None
    # GeoJSON task areas/boundaries stored directly in database
    task_areas_geojson: Optional[dict] = None

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
    async def all(  # noqa: PLR0913
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
    ) -> Optional[list[Self]]:  # noqa: PLR0913
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

        query = sql.SQL(
            """
            SELECT
                p.*,
                ST_AsGeoJSON(p.outline)::jsonb AS outline
            FROM projects p
        """
        )
        if filters:
            query += sql.SQL(" WHERE ")
            query += sql.SQL(" AND ").join(sql.SQL(clause) for clause in filters)
        query += sql.SQL(" ORDER BY created_at DESC")

        if skip is not None and limit is not None:
            query += sql.SQL(" OFFSET %(offset)s LIMIT %(limit)s;")
            params["offset"] = skip
            params["limit"] = limit
        else:
            query += sql.SQL(";")

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(query, params)
            return await cur.fetchall()

    @classmethod
    async def count(cls, db: AsyncConnection) -> int:
        """Return total project count."""
        async with db.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM projects;")
            result = await cur.fetchone()
        return int(result[0] if result and result[0] is not None else 0)

    @classmethod
    async def create(cls, db: AsyncConnection, project_in: Self) -> Self:
        """Create a new project in the database."""
        model_dump = dump_and_check_model(project_in)

        # Handle ODK credentials encryption
        if (
            hasattr(project_in, "external_project_password")
            and project_in.external_project_password
        ):
            from app.central.central_schemas import ODKCentral

            odk_creds = ODKCentral(
                external_project_instance_url=project_in.external_project_instance_url,
                external_project_username=project_in.external_project_username,
                external_project_password=project_in.external_project_password,
            )
            odk_data = odk_creds.prepare_for_db()
            # Update model_dump with encrypted password
            model_dump.update(odk_data)
            # Remove plaintext password if present
            model_dump.pop("external_project_password", None)

        columns = []
        value_placeholders: list[sql.Composable] = []

        for key in model_dump:
            columns.append(key)
            if key == "outline":
                value_placeholders.append(
                    sql.SQL("ST_GeomFromGeoJSON({})").format(sql.Placeholder(key))
                )
                # Must be string json for db input
                model_dump[key] = json.dumps(model_dump[key])
            elif key == "data_extract_geojson" and isinstance(model_dump[key], dict):
                # Convert GeoJSON dict to JSON string for JSONB column
                value_placeholders.append(
                    sql.SQL("{}::jsonb").format(sql.Placeholder(key))
                )
                model_dump[key] = json.dumps(model_dump[key])
            else:
                value_placeholders.append(sql.Placeholder(key))

        insert_sql = sql.SQL(
            """
                INSERT INTO projects
                    ({columns})
                VALUES
                    ({values})
                RETURNING
                    *,
                    ST_AsGeoJSON(outline)::jsonb AS outline;
            """
        ).format(
            columns=sql.SQL(", ").join(sql.Identifier(key) for key in columns),
            values=sql.SQL(", ").join(value_placeholders),
        )
        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(insert_sql, model_dump)
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

        # Handle ODK credentials encryption
        if (
            hasattr(project_update, "external_project_password")
            and project_update.external_project_password
        ):
            from app.central.central_schemas import ODKCentral

            odk_creds = ODKCentral(
                external_project_instance_url=project_update.external_project_instance_url,
                external_project_username=project_update.external_project_username,
                external_project_password=project_update.external_project_password,
            )
            odk_data = odk_creds.prepare_for_db()
            # Update model_dump with encrypted password
            model_dump.update(odk_data)
            # Remove plaintext password if present
            model_dump.pop("external_project_password", None)

        # Convert dict/JSONB fields to JSON strings for database
        for key in list(model_dump.keys()):
            if (
                key == "data_extract_geojson"
                and isinstance(model_dump[key], dict)
                or key == "task_areas_geojson"
                and isinstance(model_dump[key], dict)
            ):
                # Convert GeoJSON dict to JSON string for JSONB column
                model_dump[key] = json.dumps(model_dump[key])

        placeholders: list[sql.Composable] = []
        for key in model_dump:
            if key == "task_areas_geojson":
                placeholders.append(
                    sql.SQL("{column} = {value}::jsonb").format(
                        column=sql.Identifier(key),
                        value=sql.Placeholder(key),
                    )
                )
            else:
                placeholders.append(
                    sql.SQL("{column} = {value}").format(
                        column=sql.Identifier(key),
                        value=sql.Placeholder(key),
                    )
                )

        # NOTE we want a trackable hashtag DOMAIN-PROJECT_ID
        if "hashtags" in model_dump:
            fmtm_hashtag = f"#{settings.FMTM_DOMAIN}-{project_id}"
            if fmtm_hashtag not in model_dump["hashtags"]:
                model_dump["hashtags"].append(fmtm_hashtag)

        query = sql.SQL(
            """
            UPDATE projects
            SET {placeholders}
            WHERE id = %(project_id)s
            RETURNING
                *,
                ST_AsGeoJSON(outline)::jsonb AS outline;
        """
        ).format(placeholders=sql.SQL(", ").join(placeholders))

        async with db.cursor(row_factory=class_row(cls)) as cur:
            await cur.execute(query, {"project_id": project_id, **model_dump})
            updated_project = await cur.fetchone()

        if updated_project is None:
            msg = f"Failed to update project with ID: {project_id}"
            log.error(msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=msg,
            )

        return updated_project

    def get_odk_credentials(self) -> Optional["ODKCentral"]:
        """Get ODK credentials from project (decrypted).

        Returns None if no credentials are set.
        """
        from app.central.central_schemas import ODKCentral

        has_complete_creds = all(
            [
                self.external_project_instance_url,
                self.external_project_username,
                self.external_project_password_encrypted,
            ]
        )

        if not has_complete_creds:
            return None

        return ODKCentral.from_db(
            url=self.external_project_instance_url,
            username=self.external_project_username,
            password_encrypted=self.external_project_password_encrypted,
        )

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
