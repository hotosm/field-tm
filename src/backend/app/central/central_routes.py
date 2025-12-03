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
"""Routes to relay requests to ODK Central server."""

import json
import re
from io import BytesIO
from typing import Annotated
from uuid import UUID
from typing import Annotated, Dict, List

import pandas as pd
from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response, StreamingResponse
from geojson_pydantic import FeatureCollection
from loguru import logger as log
from osm_fieldwork.form_components.translations import INCLUDED_LANGUAGES
from osm_fieldwork.OdkCentralAsync import OdkCentral
from psycopg import Connection
from psycopg.rows import dict_row
from pyodk._endpoints.entities import Entity

from app.auth.auth_deps import login_required
from app.auth.auth_schemas import AuthUser, ProjectUserDict
from app.auth.roles import Mapper, ProjectManager
from app.central import central_crud, central_deps, central_schemas
from app.db.database import db_conn
from app.db.enums import HTTPStatus
from app.db.models import DbOdkEntities, DbProject
from app.db.postgis_utils import add_required_geojson_properties
from app.projects.project_schemas import ProjectUpdate

router = APIRouter(
    prefix="/central",
    tags=["central"],
    responses={404: {"description": "Not found"}},
)


@router.get("/projects")
async def list_projects():
    """List projects in Central."""
    # TODO update for option to pass credentials by user
    # NOTE runs in separate thread using run_in_threadpool
    projects = await run_in_threadpool(lambda: central_crud.list_odk_projects())
    if projects is None:
        return {"message": "No projects found"}
    return JSONResponse(content={"projects": projects})


@router.get("/list-forms")
async def get_form_lists(
    current_user: Annotated[AuthUser, Depends(login_required)],
    db: Annotated[Connection, Depends(db_conn)],
) -> list:
    """Get a list of all XLSForms available in Field-TM.

    Returns:
        dict: JSON of {id:title} with each XLSForm record.
    """
    forms = await central_crud.get_form_list(db)
    return forms


@router.post("/validate-form")
async def validate_form(
    # NOTE we do not set any roles on this endpoint yet
    # FIXME once sub project creation implemented, this should be manager only
    current_user: Annotated[AuthUser, Depends(login_required)],
    xlsform: Annotated[BytesIO, Depends(central_deps.read_xlsform)],
    debug: bool = False,
    use_odk_collect: bool = False,
    need_verification_fields: bool = True,
    mandatory_photo_upload: bool = False,
    default_language: str = "english",
):
    """Basic validity check for uploaded XLSForm.

    Parses the form using ODK pyxform to check that it is valid.

    If the `debug` param is used, the form is returned for inspection.
    NOTE that this debug form has additional fields appended and should
        not be used for Field-TM project creation.

    NOTE this provides a basic sanity check, some fields are omitted
    so the form is not usable in production:
        - new_geom_type
    """
    if debug:
        xform_id, updated_form = await central_crud.append_fields_to_user_xlsform(
            xlsform,
            need_verification_fields=need_verification_fields,
            mandatory_photo_upload=mandatory_photo_upload,
            default_language=default_language,
            use_odk_collect=use_odk_collect,
        )
        return StreamingResponse(
            updated_form,
            media_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            headers={"Content-Disposition": f"attachment; filename={xform_id}.xlsx"},
        )
    else:
        await central_crud.validate_and_update_user_xlsform(
            xlsform,
            need_verification_fields=need_verification_fields,
            mandatory_photo_upload=mandatory_photo_upload,
            default_language=default_language,
            use_odk_collect=use_odk_collect,
        )
        return JSONResponse(
            status_code=HTTPStatus.OK,
            content={"message": "Your form is valid"},
        )


@router.post("/upload-xlsform")
async def upload_project_xlsform(
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
    xlsform_upload: Annotated[BytesIO, Depends(central_deps.read_xlsform)],
    need_verification_fields: bool = True,
    mandatory_photo_upload: bool = False,
    # FIXME this var should be probably be refactored to project.field_mapping_app
    default_language: str = "english",
    use_odk_collect: bool = False,
):
    """Upload the final XLSForm for the project."""
    project = project_user.get("project")
    project_id = project.id
    new_geom_type = project.new_geom_type
    form_name = f"FMTM_Project_{project.id}"

    # Validate uploaded form
    await central_crud.validate_and_update_user_xlsform(
        xlsform=xlsform_upload,
        form_name=form_name,
        new_geom_type=new_geom_type,
        need_verification_fields=need_verification_fields,
        mandatory_photo_upload=mandatory_photo_upload,
        default_language=default_language,
        use_odk_collect=use_odk_collect,
    )

    xform_id, project_xlsform = await central_crud.append_fields_to_user_xlsform(
        xlsform=xlsform_upload,
        form_name=form_name,
        new_geom_type=new_geom_type,
        need_verification_fields=need_verification_fields,
        mandatory_photo_upload=mandatory_photo_upload,
        default_language=default_language,
        use_odk_collect=use_odk_collect,
    )

    # Write XLS form content to db
    xlsform_bytes = project_xlsform.getvalue()
    if len(xlsform_bytes) == 0 or not xform_id:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="There was an error modifying the XLSForm!",
        )
    log.debug(f"Setting project XLSForm db data for xFormId: {xform_id}")
    await DbProject.update(
        db,
        project_id,
        ProjectUpdate(
            xlsform_content=xlsform_bytes,
            odk_form_id=xform_id,
        ),
    )
    await db.commit()

    return JSONResponse(
        status_code=HTTPStatus.OK,
        content={"message": "Your form is valid"},
    )


@router.post("/update-form")
async def update_project_form(
    xlsform: Annotated[BytesIO, Depends(central_deps.read_xlsform)],
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[
        ProjectUserDict, Depends(ProjectManager(check_completed=True))
    ],
    xform_id: str = Form(...),
    # FIXME add back in capability to update osm_category
    # osm_category: XLSFormType = Form(...),
):
    """Update the XForm data in ODK Central & Field-TM DB."""
    project = project_user_dict["project"]
    await central_crud.update_project_xlsform(
        db,
        project,
        xlsform,
        xform_id,
    )

    return JSONResponse(
        status_code=HTTPStatus.OK,
        content={"message": f"Successfully updated the form for project {project.id}"},
    )


def normalize_col(col: str) -> str:
    """Normalize a column name by removing language codes in parentheses."""
    col = re.sub(r"\([^)]*\)", "", col)
    return col.strip().lower()


def detect_languages(xls: Dict[str, pd.DataFrame]) -> Dict[str, List[str] | str | None]:
    """Detects languages available in an uploaded XLSForm.

    Returns a dictionary with two keys:
        - "detected_languages": a list of language codes detected in the form, in the
        order found.
        - "default_language": the default language of the form, or None if no default
        language is specified.

    Language detection is done by checking column names in the form for language codes
    in parentheses, and by checking the "default_language" column in the "settings"
    sheet.

    NOTE: This function assumes that the uploaded XLSForm is valid and has been parsed
    into a dictionary with sheet names as keys and pandas DataFrames as values.
    """
    detected = []
    default_lang = None

    settings = xls.get("settings")
    if settings is not None and "default_language" in settings.columns:
        raw = str(settings["default_language"].iloc[0]).strip()
        default_lang = raw.split("(")[0].lower()

    for df in xls.values():
        if df.empty:
            continue

        for col in df.columns:
            col_norm = normalize_col(col)
            match = re.match(r"^(label|hint|required_message)::(\w+)$", col_norm)
            if match:
                lang = match.group(2)
                if lang in INCLUDED_LANGUAGES and lang not in detected:
                    detected.append(lang)

    return {
        "detected_languages": detected,
        "default_language": default_lang,
    }


def get_media_files(xls: Dict[str, pd.DataFrame], langs: Dict[str, List[str] | str]):
    """Extracts a list of media files from an XLSForm.

    The function first checks if the "choices" sheet is present and not empty. If so, it
    normalizes the column names and checks for the presence of a column to extract from.

    The column to extract from is determined by the following priority rules:
        1. If a default language is specified, use the column with that language code.
        2. If no default language is specified, but at least one language is detected,
        use the first detected language.
        3. If no default language is specified and no languages are detected, use the
        plain "image" column.

    If no column is found to extract from, an empty list is returned. Otherwise, the
    list of media files is sorted and returned.
    """
    choices = xls.get("choices")
    if choices is None or choices.empty:
        return []

    df = choices.copy()
    df.columns = [normalize_col(c) for c in df.columns]

    pattern = re.compile(r"^(image|media::image)(::\w+)?$")

    possible_cols = [c for c in df.columns if pattern.match(c)]

    if not possible_cols:
        return []

    return sorted(
        {str(v).strip() for v in df[possible_cols[0]].dropna() if str(v).strip()}
    )


@router.post("/detect-form-languages-and-media")
async def detect_form_languages_and_media(
    xlsform: BytesIO = Depends(central_deps.read_xlsform),
):
    """Detects languages and media files available in an uploaded XLSForm.

    Returns a JSON response with the following keys:
        - "detected_languages": a list of language codes detected in the
            form, in the order found.
        - "default_language": the default language of the form, or None if
            no default language is specified.
        - "supported_languages": a list of supported language codes.
        - "media_files": a list of media files extracted from the form.
    """
    xls = pd.read_excel(xlsform, sheet_name=None, engine="calamine")

    langs = detect_languages(xls)
    media = get_media_files(xls, langs)

    return JSONResponse(
        status_code=HTTPStatus.OK,
        content={
            "detected_languages": langs["detected_languages"],
            "default_language": [langs["default_language"]]
            if langs["default_language"]
            else [],
            "supported_languages": list(INCLUDED_LANGUAGES.keys()),
            "media_files": media,
        },
    )


@router.get("/download-form")
async def download_form(
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
):
    """Download the XLSForm for a project."""
    project = project_user.get("project")

    headers = {
        "Content-Disposition": f"attachment; filename={project.id}_xlsform.xlsx",
        "Content-Type": "application/media",
    }
    return Response(content=project.xlsform_content, headers=headers)


@router.post("/refresh-appuser-token")
async def refresh_appuser_token(
    current_user: Annotated[AuthUser, Depends(ProjectManager())],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Refreshes the token for the app user associated with a specific project.

    Response:
        {
            "status_code": HTTPStatus.OK,
            "message": "App User token has been successfully refreshed.",
        }
    """
    project = current_user.get("project")
    project_id = project.id
    project_odk_id = project.odkid
    project_xform_id = project.odk_form_id
    project_odk_creds = project.odk_credentials

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

        return JSONResponse(
            content={
                "message": "App User token has been successfully refreshed.",
            }
        )

    except Exception as e:
        log.exception(f"Error: {e}", stack_info=True)
        msg = f"failed to refresh the appuser token for project {project_id}"
        log.error(msg)
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=msg,
        ) from e


@router.post("/upload-form-media")
async def upload_form_media(
    current_user: Annotated[AuthUser, Depends(ProjectManager())],
    media_attachments: Annotated[
        dict[str, BytesIO], Depends(central_deps.read_form_media)
    ],
):
    """Upload media attachments to a form in Central."""
    project = current_user.get("project")
    project_id = project.id
    project_odk_id = project.odkid
    project_xform_id = project.odk_form_id
    project_odk_creds = project.odk_credentials

    try:
        await central_crud.upload_form_media(
            project_xform_id,
            project_odk_id,
            project_odk_creds,
            media_attachments,
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

        return Response(status_code=HTTPStatus.OK)

    except Exception as e:
        log.exception(f"Error: {e}")
        msg = (
            f"Failed to upload form media for Field-TM project ({project_id}) "
            f"ODK project ({project_odk_id}) form ID ({project_xform_id})"
        )
        log.error(msg)
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=msg,
        ) from e


@router.post("/list-form-media", response_model=list[dict])
async def list_form_media(
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
):
    """A list of required media to upload for a form."""
    project = project_user.get("project")
    project_id = project.id
    project_odk_id = project.odkid
    project_xform_id = project.odk_form_id
    project_odk_creds = project.odk_credentials

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
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=msg,
        ) from e


@router.post("/get-form-media", response_model=dict[str, str])
async def get_form_media(
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
):
    """Return the project form attachments as a list of files."""
    project = project_user.get("project")
    project_id = project.id
    project_odk_id = project.odkid
    project_xform_id = project.odk_form_id
    project_odk_creds = project.odk_credentials

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
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail=msg,
            )

        return form_media
    except Exception as e:
        msg = (
            f"Failed to get all form media for Field-TM project ({project_id}) "
            f"ODK project ({project_odk_id}) form ID ({project_xform_id})"
        )
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=msg,
        ) from e


@router.post("/entity")
async def add_new_entity(
    db: Annotated[Connection, Depends(db_conn)],
    entity_uuid: UUID,
    project_user_dict: Annotated[
        ProjectUserDict, Depends(Mapper(check_completed=True))
    ],
    geojson: FeatureCollection,
) -> Entity:
    """Create an Entity for the project in ODK.

    NOTE a FeatureCollection must be uploaded.
    NOTE response time is reasonably slow ~500ms due to Central round trip.
    """
    try:
        project = project_user_dict.get("project")
        project_odk_id = project.odkid
        project_odk_creds = project.odk_credentials

        featcol_dict = geojson.model_dump()
        features = featcol_dict.get("features")
        if not features or not isinstance(features, list):
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="Invalid GeoJSON format"
            )

        # Add required properties and extract entity data
        featcol = add_required_geojson_properties(featcol_dict)

        # Get task_id of the feature if inside task boundary and not set already
        # NOTE this should come from the frontend, but might have failed
        if featcol["features"][0]["properties"].get("task_id", None) is None:
            async with db.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT t.project_task_index AS task_id
                    FROM tasks t
                    WHERE t.project_id = %s
                    AND ST_Within(
                        ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326),
                        t.outline
                    )
                    LIMIT 1;
                    """,
                    (project.id, json.dumps(features[0].get("geometry"))),
                )
                result = await cur.fetchone()
            if result:
                featcol["features"][0]["properties"]["task_id"] = result.get(
                    "task_id", ""
                )

        entities_list = await central_crud.task_geojson_dict_to_entity_values(
            {featcol["features"][0]["properties"]["task_id"]: featcol}
        )

        if not entities_list:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="No valid entities found"
            )

        # Create entity in ODK
        new_entity = await central_crud.create_entity(
            project_odk_creds,
            entity_uuid,
            project_odk_id,
            properties=list(featcol["features"][0]["properties"].keys()),
            entity=entities_list[0],
            dataset_name="features",
        )

        # Sync ODK entities from Central --> FieldTM database (trigger electric sync)
        project_entities = await central_crud.get_entities_data(
            project_odk_creds, project_odk_id
        )
        await DbOdkEntities.upsert(db, project.id, project_entities)

        return new_entity

    except HTTPException as http_err:
        log.error(f"HTTP error: {http_err.detail}")
        raise
    except Exception as e:
        log.debug(e)
        log.exception("Unexpected error during entity creation")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Entity creation failed",
        ) from e


@router.post("/test-credentials")
async def odk_creds_test(
    odk_creds: Annotated[central_schemas.ODKCentral, Depends()],
):
    """Test ODK Central credentials by attempting to open a session."""
    await central_crud.odk_credentials_test(odk_creds)
    return Response(status_code=HTTPStatus.OK)
