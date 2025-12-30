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
"""Routes to relay requests to ODK Central server (Litestar)."""

import logging
import re
from io import BytesIO

import pandas as pd
from anyio import to_thread
from litestar import Response, Router, get, post
from litestar import status_codes as status
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body, Parameter
from osm_fieldwork.form_components.translations import INCLUDED_LANGUAGES
from osm_fieldwork.OdkCentralAsync import OdkCentral
from psycopg import AsyncConnection

from app.auth.auth_deps import login_required, public_endpoint
from app.auth.auth_schemas import AuthUser, ProjectUserDict
from app.auth.roles import mapper, project_manager
from app.central import central_crud, central_schemas
from app.db.database import db_conn
from app.db.models import DbProject
from app.projects.project_schemas import ProjectUpdate

log = logging.getLogger(__name__)


@get(
    "/projects",
    summary="List projects in Central.",
)
async def list_projects() -> dict[str, object]:
    """List projects in Central."""
    # TODO update for option to pass credentials by user
    # NOTE runs in separate thread using anyio.to_thread.run_sync
    projects = await to_thread.run_sync(central_crud.list_odk_projects)
    if projects is None:
        return {"message": "No projects found"}
    return {"projects": projects}


@get(
    "/list-forms",
    summary="Get a list of all XLSForms available in Field-TM.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
)
async def get_form_lists(
    db: AsyncConnection,
) -> list:
    """Get a list of all XLSForms available in Field-TM.

    Returns:
        dict: JSON of {id:title} with each XLSForm record.
    """
    forms = await central_crud.get_form_list(db)
    return forms


async def _validate_xlsform_extension(xlsform: UploadFile) -> BytesIO:
    """Validate an uploaded XLSForm has .xls or .xlsx extension and return bytes."""
    from pathlib import Path

    filename = Path(xlsform.filename or "")
    file_ext = filename.suffix.lower()

    allowed_extensions = [".xls", ".xlsx"]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide a valid .xls or .xlsx file",
        )

    return BytesIO(await xlsform.read())


@post(
    "/validate-form",
    summary="Basic validity check for uploaded XLSForm.",
    dependencies={
        "auth_user": Provide(login_required),
    },
)
async def validate_form(
    xlsform: UploadFile,
    debug: bool = Parameter(default=False),
    use_odk_collect: bool = Parameter(default=False),
    need_verification_fields: bool = Parameter(default=True),
    mandatory_photo_upload: bool = Parameter(default=False),
    default_language: str = Parameter(default="english"),
) -> dict:
    """Basic validity check for uploaded XLSForm.

    Parses the form using ODK pyxform to check that it is valid.

    If the `debug` param is used, the form is returned for inspection.
    NOTE that this debug form has additional fields appended and should
        not be used for Field-TM project creation.

    NOTE this provides a basic sanity check, some fields are omitted
    so the form is not usable in production:
        - new_geom_type
    """
    xlsform_bytes = await _validate_xlsform_extension(xlsform)

    if debug:
        xform_id, updated_form = await central_crud.append_fields_to_user_xlsform(
            xlsform_bytes,
            need_verification_fields=need_verification_fields,
            mandatory_photo_upload=mandatory_photo_upload,
            default_language=default_language,
            use_odk_collect=use_odk_collect,
        )
        return Response(
            content=updated_form.getvalue(),
            media_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            headers={"Content-Disposition": f"attachment; filename={xform_id}.xlsx"},
            status_code=status.HTTP_200_OK,
        )

    await central_crud.validate_and_update_user_xlsform(
        xlsform_bytes,
        need_verification_fields=need_verification_fields,
        mandatory_photo_upload=mandatory_photo_upload,
        default_language=default_language,
        use_odk_collect=use_odk_collect,
    )
    return {"message": "Your form is valid"}


@post(
    "/upload-xlsform",
    summary="Upload the final XLSForm for the project.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def upload_project_xlsform(
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
    project_id: int = Parameter(),
    need_verification_fields: bool = Parameter(default=True),
    mandatory_photo_upload: bool = Parameter(default=False),
    # FIXME this var should be probably be refactored to project.field_mapping_app
    default_language: str = Parameter(default="english"),
    use_odk_collect: bool = Parameter(default=False),
) -> dict:
    """Upload the final XLSForm for the project."""
    project = current_user.get("project")
    project_id = project.id
    form_name = f"FMTM_Project_{project.id}"

    # Validate uploaded form
    xlsform_bytes = await _validate_xlsform_extension(data)

    await central_crud.validate_and_update_user_xlsform(
        xlsform=xlsform_bytes,
        form_name=form_name,
        need_verification_fields=need_verification_fields,
        mandatory_photo_upload=mandatory_photo_upload,
        default_language=default_language,
        use_odk_collect=use_odk_collect,
    )

    xform_id, project_xlsform = await central_crud.append_fields_to_user_xlsform(
        xlsform=xlsform_bytes,
        form_name=form_name,
        need_verification_fields=need_verification_fields,
        mandatory_photo_upload=mandatory_photo_upload,
        default_language=default_language,
        use_odk_collect=use_odk_collect,
    )

    # Write XLS form content to db
    xlsform_db_bytes = project_xlsform.getvalue()
    if len(xlsform_db_bytes) == 0 or not xform_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="There was an error modifying the XLSForm!",
        )
    log.debug(f"Setting project XLSForm db data for xFormId: {xform_id}")
    await DbProject.update(
        db,
        project_id,
        ProjectUpdate(
            xlsform_content=xlsform_db_bytes,
            odk_form_id=xform_id,
        ),
    )
    await db.commit()

    return {"message": "Your form is valid"}


@post(
    "/detect-form-languages",
    summary="Detect languages available in an uploaded XLSForm.",
    dependencies={
        "auth_user": Provide(login_required),
    },
)
async def detect_form_languages(
    data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
) -> dict:
    """Detect languages available in an uploaded XLSForm."""
    xlsform_bytes = await _validate_xlsform_extension(data)
    xlsform = pd.read_excel(xlsform_bytes, sheet_name=None)
    detected_languages = []

    settings_df = xlsform.get("settings")
    default_language = (
        settings_df["default_language"].iloc[0].split("(")[0].strip().lower()
        if settings_df is not None and "default_language" in settings_df
        else None
    )

    for sheet_df in xlsform.values():
        if sheet_df.empty:
            continue

        sheet_df.columns = sheet_df.columns.str.lower()
        for col in sheet_df.columns:
            if any(
                col.startswith(f"{base_col}::")
                for base_col in ["label", "hint", "required_message"]
            ):
                match = re.match(r"^(label|hint|required_message)::(\w+)", col)
                if match and match.group(2) in INCLUDED_LANGUAGES:
                    if match.group(2) not in detected_languages:
                        detected_languages.append(match.group(2))

    if default_language and default_language.lower() not in detected_languages:
        detected_languages.append(default_language.lower())

    return {
        "detected_languages": detected_languages,  # in the order found in form
        "default_language": [default_language] if default_language else [],
        "supported_languages": list(INCLUDED_LANGUAGES.keys()),
    }


@get(
    "/download-form",
    summary="Download the XLSForm for a project.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def download_form(
    current_user: ProjectUserDict,
    db: AsyncConnection,
    auth_user: AuthUser,
    project_id: int = Parameter(),
) -> Response[bytes]:
    """Download the XLSForm for a project."""
    project = current_user.get("project")

    headers = {
        "Content-Disposition": f"attachment; filename={project.id}_xlsform.xlsx",
        "Content-Type": "application/media",
    }
    return Response(content=project.xlsform_content, headers=headers)


@post(
    "/refresh-appuser-token",
    summary="Refreshes the token for the app user associated with a specific project.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def refresh_appuser_token(
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    project_id: int = Parameter(),
) -> dict:
    """Refreshes the token for the app user associated with a specific project.

    Response:
        {
            "status_code": status.HTTP_200_OK,
            "message": "App User token has been successfully refreshed.",
        }
    """
    project = current_user.get("project")
    project_id = project.id
    project_odk_id = project.external_project_id
    project_xform_id = project.odk_form_id
    # ODK credentials not stored on project, use None to fall back to env vars
    project_odk_creds = None

    try:
        odk_token = await central_crud.get_appuser_token(
            project_xform_id,
            project_odk_id,
            project_odk_creds,
        )
        await DbProject.update(
            db,
            project_id,
            ProjectUpdate(
                odk_token=odk_token,
            ),
        )

        return {
            "message": "App User token has been successfully refreshed.",
        }

    except Exception as e:
        log.exception(f"Error: {e}", stack_info=True)
        msg = f"failed to refresh the appuser token for project {project_id}"
        log.error(msg)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=msg,
        ) from e


@post(
    "/upload-form-media",
    summary="Upload media attachments to a form in Central.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
    status_code=status.HTTP_200_OK,
)
async def upload_form_media(
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    db: AsyncConnection,
    media_attachments: list[UploadFile],
    project_id: int = Parameter(),
) -> None:
    """Upload media attachments to a form in Central."""
    project = current_user.get("project")
    project_id = project.id
    project_odk_id = project.external_project_id
    project_xform_id = project.odk_form_id
    # ODK credentials not stored on project, use None to fall back to env vars
    project_odk_creds = None

    # Read all uploaded form media for upload to ODK Central
    file_data_dict = {
        file.filename: BytesIO(await file.read()) for file in media_attachments
    }

    try:
        await central_crud.upload_form_media(
            project_xform_id,
            project_odk_id,
            project_odk_creds,
            file_data_dict,
        )

        async with OdkCentral(
            url=project_odk_creds.odk_central_url,
            user=project_odk_creds.odk_central_user,
            passwd=project_odk_creds.odk_central_password,
        ) as odk_central:
            try:
                await odk_central.s3_sync()
            except Exception:
                log.warning(
                    "Fails to sync media to S3 - is the linked ODK Central "
                    "instance correctly configured?"
                )

        return None

    except Exception as e:
        log.exception(f"Error: {e}")
        msg = (
            f"Failed to upload form media for Field-TM project ({project_id}) "
            f"ODK project ({project_odk_id}) form ID ({project_xform_id})"
        )
        log.error(msg)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=msg,
        ) from e


@post(
    "/list-form-media",
    summary="A list of required media to upload for a form.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def list_form_media(
    current_user: ProjectUserDict,
    db: AsyncConnection,
    auth_user: AuthUser,
    project_id: int = Parameter(),
) -> list[dict]:
    """A list of required media to upload for a form."""
    project = current_user.get("project")
    project_id = project.id
    project_odk_id = project.external_project_id
    project_xform_id = project.odk_form_id
    # ODK credentials not stored on project, use None to fall back to env vars
    project_odk_creds = None

    try:
        form_media = await central_crud.list_form_media(
            project_xform_id,
            project_odk_id,
            project_odk_creds,
        )

        return form_media
    except Exception as e:
        msg = (
            f"Failed to list all form media for Field-TM project ({project_id}) "
            f"ODK project ({project_odk_id}) form ID ({project_xform_id})"
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=msg,
        ) from e


@post(
    "/get-form-media",
    summary="Return the project form attachments as a list of files.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def get_form_media(
    current_user: ProjectUserDict,
    db: AsyncConnection,
    auth_user: AuthUser,
    project_id: int = Parameter(),
) -> dict[str, str]:
    """Return the project form attachments as a list of files."""
    project = current_user.get("project")
    project_id = project.id
    project_odk_id = project.external_project_id
    project_xform_id = project.odk_form_id
    # ODK credentials not stored on project, use None to fall back to env vars
    project_odk_creds = None

    try:
        form_media = await central_crud.get_form_media(
            project_xform_id,
            project_odk_id,
            project_odk_creds,
        )

        if form_media and not all(isinstance(v, str) for v in form_media.values()):
            msg = f"Form attachments for project {project_id} may not be uploaded yet!"
            log.warning(msg)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=msg,
            )

        # form_media is a mapping of filenames to URLs (all strings)
        return form_media  # type: ignore[return-value]
    except Exception as e:
        msg = (
            f"Failed to get all form media for Field-TM project ({project_id}) "
            f"ODK project ({project_odk_id}) form ID ({project_xform_id})"
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=msg,
        ) from e


@post(
    "/test-credentials",
    summary="Test ODK Central credentials by attempting to open a session.",
    status_code=status.HTTP_200_OK,
    dependencies={
        "db": Provide(db_conn),
        "current_user": Provide(public_endpoint),
    },
)
async def odk_creds_test(
    odk_central_url: str | None = Parameter(default=None),
    odk_central_user: str | None = Parameter(default=None),
    odk_central_password: str | None = Parameter(default=None),
) -> None:
    """Test ODK Central credentials by attempting to open a session."""
    # Construct ODKCentral model from individual query parameters
    odk_creds = central_schemas.ODKCentral(
        odk_central_url=odk_central_url,
        odk_central_user=odk_central_user,
        odk_central_password=odk_central_password,
    )
    await central_crud.odk_credentials_test(odk_creds)
    return None


central_router = Router(
    path="/central",
    tags=["central"],
    route_handlers=[
        list_projects,
        get_form_lists,
        validate_form,
        upload_project_xlsform,
        detect_form_languages,
        download_form,
        refresh_appuser_token,
        upload_form_media,
        list_form_media,
        get_form_media,
        odk_creds_test,
    ],
)
