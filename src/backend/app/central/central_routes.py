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
from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response, StreamingResponse
from geojson_pydantic import FeatureCollection
from loguru import logger as log
from osm_fieldwork.OdkCentralAsync import OdkCentral
from psycopg import Connection
from psycopg.rows import dict_row

from app.auth.auth_deps import login_required
from app.auth.auth_schemas import AuthUser, ProjectUserDict
from app.auth.roles import mapper, project_manager
from app.central import central_crud, central_deps
from app.db.database import db_conn
from app.db.enums import HTTPStatus
from app.db.models import DbProject
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
):
    """Basic validity check for uploaded XLSForm.

    Parses the form using ODK pyxform to check that it is valid.

    If the `debug` param is used, the form is returned for inspection.
    NOTE that this debug form has additional fields appended and should
        not be used for Field-TM project creation.

    NOTE this provides a basic sanity check, some fields are omitted
    so the form is not usable in production:
        - additional_entities
        - new_geom_type
    """
    if debug:
        xform_id, updated_form = await central_crud.append_fields_to_user_xlsform(
            xlsform,
            need_verification_fields=need_verification_fields,
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
            use_odk_collect=use_odk_collect,
        )
        return JSONResponse(
            status_code=HTTPStatus.OK,
            content={"message": "Your form is valid"},
        )


@router.post("/update-form")
async def update_project_form(
    xlsform: Annotated[BytesIO, Depends(central_deps.read_xlsform)],
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[ProjectUserDict, Depends(project_manager)],
    xform_id: str = Form(...),
    # FIXME add back in capability to update osm_category
    # osm_category: XLSFormType = Form(...),
):
    """Update the XForm data in ODK Central & Field-TM DB."""
    project = project_user_dict["project"]

    # Update ODK Central form data
    await central_crud.update_project_xform(
        xform_id,
        project.odkid,
        xlsform,
        project.odk_credentials,
    )

    sql = """
        UPDATE projects
        SET
            xlsform_content = %(xls_data)s
        WHERE
            id = %(project_id)s
        RETURNING id, hashtags;
    """
    async with db.cursor() as cur:
        await cur.execute(
            sql,
            {
                "xls_data": xlsform.getvalue(),
                "project_id": project.id,
            },
        )
        await db.commit()

    return JSONResponse(
        status_code=HTTPStatus.OK,
        content={"message": f"Successfully updated the form for project {project.id}"},
    )


@router.get("/download-form")
async def download_form(
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
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
    current_user: Annotated[AuthUser, Depends(project_manager)],
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
    current_user: Annotated[AuthUser, Depends(project_manager)],
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
            await odk_central.s3_sync()

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


@router.post("/get-form-media", response_model=dict[str, str])
async def get_form_media(
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
):
    """Return the project form attachments as a list of files."""
    project = project_user.get("project")
    project_id = project.id
    project_odk_id = project.odkid
    project_xform_id = project.odk_form_id
    project_odk_creds = project.odk_credentials

    try:
        return await central_crud.get_form_media(
            project_xform_id,
            project_odk_id,
            project_odk_creds,
        )

    except Exception as e:
        log.exception(f"Error: {e}")
        msg = (
            f"Failed to get form media for Field-TM project ({project_id}) "
            f"ODK project ({project_odk_id}) form ID ({project_xform_id})"
        )
        log.error(msg)
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=msg,
        ) from e


@router.post("/entity")
async def add_new_entity(
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[ProjectUserDict, Depends(mapper)],
    geojson: FeatureCollection,
):
    """Create an Entity for the project in ODK.

    NOTE a FeatureCollection must be uploaded.
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
        featcol["features"][0]["properties"]["project_id"] = project.id

        # Get task_id of the feature if inside task boundary
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

        task_id = ""
        if result and (task_id := result.get("task_id")):
            featcol["features"][0]["properties"]["task_id"] = task_id

        entities_list = await central_crud.task_geojson_dict_to_entity_values(
            {task_id: featcol}
        )

        if not entities_list:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="No valid entities found"
            )

        # Create entity in ODK
        return await central_crud.create_entity(
            project_odk_creds,
            project_odk_id,
            properties=list(featcol["features"][0]["properties"].keys()),
            entity=entities_list[0],
            dataset_name="features",
        )

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


@router.get("/form-xml")
async def get_project_form_xml_route(
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
) -> str:
    """Get the raw XML from ODK Central for a project."""
    project = project_user.get("project")
    odk_creds = project.odk_credentials
    odkid = project.odkid
    odk_form_id = project.odk_form_id
    # Run separate thread in event loop to avoid blocking with sync code
    form_xml = await run_in_threadpool(
        central_crud.get_project_form_xml,
        odk_creds,
        odkid,
        odk_form_id,
    )
    return Response(content=form_xml, media_type="application/xml")
