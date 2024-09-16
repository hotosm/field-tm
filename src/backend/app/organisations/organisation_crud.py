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
"""Logic for organisation management."""

from io import BytesIO
from typing import Optional

from fastapi import File, HTTPException, Response, UploadFile
from loguru import logger as log
from sqlalchemy import text, update
from sqlalchemy.orm import Session

from app.auth.auth_schemas import AuthUser
from app.config import encrypt_value, settings
from app.db import db_models
from app.models.enums import HTTPStatus
from app.organisations.organisation_deps import (
    check_org_exists,
    get_organisation_by_name,
)
from app.organisations.organisation_schemas import OrganisationEdit, OrganisationIn
from app.s3 import add_obj_to_bucket


async def init_admin_org(db: Session):
    """Init admin org and user at application startup."""
    insert_org_sql = text(
        """
        -- Start a transaction
        BEGIN;

        -- Insert HOTOSM organisation
        INSERT INTO public.organisations (
            name,
            slug,
            logo,
            description,
            url,
            type,
            approved,
            odk_central_url,
            odk_central_user,
            odk_central_password
        )
        VALUES (
            'HOTOSM',
            'hotosm',
            'https://avatars.githubusercontent.com/u/458752?s=280&v=4',
            'Humanitarian OpenStreetMap Team.',
            'https://hotosm.org',
            'FREE',
            true,
            :odk_url,
            :odk_user,
            :odk_pass
        )
        ON CONFLICT ("name") DO NOTHING
        RETURNING id;
    """
    )

    insert_users_sql = text(
        """
        -- Insert localadmin admin user
        INSERT INTO public.users (
            id,
            username,
            role,
            name,
            email_address,
            is_email_verified,
            mapping_level,
            tasks_mapped,
            tasks_validated,
            tasks_invalidated
        )
        VALUES (
            :admin_user_id,
            :admin_username,
            'ADMIN',
            'Admin',
            'admin@fmtm.dev',
            true,
            'ADVANCED',
            0,
            0,
            0
        )
        ON CONFLICT ("username") DO NOTHING;

        -- Set localadmin user as org admin
        WITH org_cte AS (
            SELECT id FROM public.organisations
            WHERE name = 'HOTOSM'
        )
        INSERT INTO public.organisation_managers (organisation_id, user_id)
        SELECT (SELECT id FROM org_cte), :admin_user_id
        ON CONFLICT DO NOTHING;

        -- Insert svcfmtm user (for temp auth)
        INSERT INTO public.users (
            id,
            username,
            role,
            name,
            email_address,
            is_email_verified,
            mapping_level,
            tasks_mapped,
            tasks_validated,
            tasks_invalidated
        )
        VALUES (
            :svc_user_id,
            :svc_username,
            'MAPPER',
            'FMTM Service Account',
            :odk_user,
            true,
            'BEGINNER',
            0,
            0,
            0
        )
        ON CONFLICT ("username") DO UPDATE
        SET
            role = EXCLUDED.role,
            mapping_level = EXCLUDED.mapping_level,
            name = EXCLUDED.name;

        -- Commit the transaction
        COMMIT;
    """
    )

    result = db.execute(
        insert_org_sql,
        {
            "odk_url": settings.ODK_CENTRAL_URL,
            "odk_user": settings.ODK_CENTRAL_USER,
            "odk_pass": encrypt_value(settings.ODK_CENTRAL_PASSWD),
        },
    )

    # NOTE only upload org logo on first org creation (RETURNING statement)
    org_id = result.scalar()
    if org_id:
        logo_path = "/opt/app/images/hot-org-logo.png"
        with open(logo_path, "rb") as logo_file:
            org_logo = UploadFile(BytesIO(logo_file.read()))
        await upload_logo_to_s3(org_id, org_logo)

    result = db.execute(
        insert_users_sql,
        {
            "admin_user_id": 1,
            "admin_username": "localadmin",
            "svc_user_id": 20386219,
            "svc_username": "svcfmtm",
            "odk_user": settings.ODK_CENTRAL_USER,
        },
    )


async def get_organisations(
    db: Session,
    current_user: AuthUser,
):
    """Get all orgs.

    Also returns unapproved orgs if admin user.
    """
    user_id = current_user.id

    sql = text(
        """
        SELECT *
        FROM organisations
        WHERE
            CASE
                WHEN (SELECT role FROM users WHERE id = :user_id) = 'ADMIN' THEN TRUE
                ELSE approved
            END = TRUE;
    """
    )
    return db.execute(sql, {"user_id": user_id}).all()


async def get_my_organisations(
    db: Session,
    current_user: AuthUser,
):
    """Get organisations filtered by the current user.

    TODO add extra UNION for all associated projects to user.

    Args:
        db (Session): The database session.
        current_user (AuthUser): The current user.

    Returns:
        list[dict]: A list of organisation objects to be serialised.
    """
    user_id = current_user.id

    sql = text(
        """
        SELECT DISTINCT org.*
        FROM organisations org
        JOIN organisation_managers managers
            ON managers.organisation_id = org.id
        WHERE managers.user_id = :user_id

        UNION

        SELECT DISTINCT org.*
        FROM organisations org
        JOIN projects project
            ON project.organisation_id = org.id
        WHERE project.author_id = :user_id;
    """
    )
    return db.execute(sql, {"user_id": user_id}).all()


async def get_unapproved_organisations(
    db: Session,
) -> list[db_models.DbOrganisation]:
    """Get unapproved orgs."""
    return db.query(db_models.DbOrganisation).filter_by(approved=False)


async def upload_logo_to_s3(org_id: int, logo_file: UploadFile) -> str:
    """Upload logo using standardised /{org_id}/logo.png format.

    Browsers treat image mimetypes the same, regardless of extension,
    so it should not matter if a .jpg is renamed .png.

    Args:
        org_id (int): The organisation id in the database.
        logo_file (UploadFile): The logo image uploaded to FastAPI.

    Returns:
        logo_url(str): The S3 URL for the logo file.
    """
    logo_path = f"/{org_id}/logo.png"

    file_bytes = await logo_file.read()
    file_obj = BytesIO(file_bytes)

    add_obj_to_bucket(
        settings.S3_BUCKET_NAME,
        file_obj,
        logo_path,
        content_type=logo_file.content_type,
    )

    logo_url = f"{settings.S3_DOWNLOAD_ROOT}/{settings.S3_BUCKET_NAME}{logo_path}"

    return logo_url


async def create_organisation(
    db: Session,
    org_model: OrganisationIn,
    current_user: AuthUser,
    logo: Optional[UploadFile] = File(None),
) -> db_models.DbOrganisation:
    """Creates a new organisation with the given name, description, url, type, and logo.

    Saves the logo file S3 bucket under /{org_id}/logo.png.

    Args:
        db (Session): database session
        org_model (OrganisationIn): Pydantic model for organisation input.
        logo (UploadFile, optional): logo file of the organisation.
            Defaults to File(...).
        current_user: logged in user.

    Returns:
        DbOrganisation: SQLAlchemy Organisation model.
    """
    if await get_organisation_by_name(db, org_name=org_model.name):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"Organisation already exists with the name ({org_model.name})",
        )

    # Required to check if exists on error
    db_organisation = None

    try:
        # Create new organisation without logo set
        db_organisation = db_models.DbOrganisation(**org_model.model_dump())
        db_organisation.user_id = current_user.id

        db.add(db_organisation)
        db.commit()
        # Refresh to get the assigned org id
        db.refresh(db_organisation)

        # Update the logo field in the database with the correct path
        if logo:
            db_organisation.logo = await upload_logo_to_s3(db_organisation.id, logo)
        db.commit()

    except Exception as e:
        log.exception(e)
        log.debug("Rolling back changes to db organisation")
        # Rollback any changes
        db.rollback()
        # Delete the failed organisation entry
        if db_organisation:
            log.debug(f"Deleting created organisation ID {db_organisation.id}")
            db.delete(db_organisation)
            db.commit()
        raise HTTPException(
            status_code=400, detail=f"Error creating organisation: {e}"
        ) from e

    return db_organisation


async def update_organisation(
    db: Session,
    organisation: db_models.DbOrganisation,
    values: OrganisationEdit,
    logo: UploadFile(None),
) -> db_models.DbOrganisation:
    """Update an existing organisation database entry.

    Args:
        db (Session): database session
        organisation (DbOrganisation): Editing database model.
        values (OrganisationEdit): Pydantic model for organisation edit.
        logo (UploadFile, optional): logo file of the organisation.
            Defaults to File(...).

    Returns:
        DbOrganisation: SQLAlchemy Organisation model.
    """
    if not (updated_fields := values.dict(exclude_none=True)):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=f"No values were provided to update organisation {organisation.id}",
        )

    update_cmd = (
        update(db_models.DbOrganisation)
        .where(db_models.DbOrganisation.id == organisation.id)
        .values(**updated_fields)
    )
    db.execute(update_cmd)

    if logo:
        organisation.logo = await upload_logo_to_s3(organisation.id, logo)

    db.commit()
    db.refresh(organisation)

    return organisation


async def delete_organisation(
    db: Session,
    organisation: db_models.DbOrganisation,
) -> Response:
    """Delete an existing organisation database entry.

    Args:
        db (Session): database session
        organisation (DbOrganisation): Database model to delete.

    Returns:
        bool: If deletion was successful.
    """
    db.delete(organisation)
    db.commit()

    return Response(status_code=HTTPStatus.NO_CONTENT)


async def add_organisation_admin(db: Session, org_id: int, user_id: int):
    """Adds a user as an admin to the specified organisation.

    Args:
        db (Session): The database session.
        org_id (int): The organisation ID.
        user_id (int): The user ID to add as manager.

    Returns:
        Response: The HTTP response with status code 200.
    """
    log.info(f"Adding user ({user_id}) as org ({org_id}) admin")
    sql = text(
        """
        INSERT INTO public.organisation_managers
        (organisation_id, user_id) VALUES (:org_id, :user_id)
        ON CONFLICT DO NOTHING;
    """
    )

    db.execute(
        sql,
        {
            "org_id": org_id,
            "user_id": user_id,
        },
    )

    db.commit()

    return Response(status_code=HTTPStatus.OK)


async def approve_organisation(db, org_id: int):
    """Approves an oranisation request made by the user .

    Args:
        db: The database session.
        org_id (int): The organisation ID.

    Returns:
        Response: An HTTP response with the status code 200.
    """
    org_obj = await check_org_exists(db, org_id, check_approved=False)

    org_obj.approved = True
    db.commit()

    return org_obj


async def get_unapproved_org_detail(db, org_id):
    """Returns detail of an unapproved organisation.

    Args:
        db: The database session.
        org_id: ID of unapproved organisation.
    """
    return (
        db.query(db_models.DbOrganisation).filter_by(approved=False, id=org_id).first()
    )
