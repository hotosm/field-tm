"""External REST API routes for progressive project creation."""

from __future__ import annotations

import base64
from io import BytesIO

from litestar import Router, delete, get, post
from litestar import status_codes as status
from litestar.di import Provide
from litestar.exceptions import HTTPException
from psycopg import AsyncConnection

from app.api.api_schemas import (
    CreateProjectRequest,
    DataExtractRequest,
    DataExtractResponse,
    FinalizeRequest,
    FinalizeResponse,
    ProjectResponse,
    SplitRequest,
    SplitResponse,
    XLSFormRequest,
)
from app.auth.api_key import api_key_required
from app.auth.auth_schemas import AuthUser
from app.db.database import db_conn
from app.db.enums import FieldMappingApp
from app.db.models import DbProject, DbTemplateXLSForm
from app.projects.project_services import (
    ConflictError,
    NotFoundError,
    ServiceError,
    ValidationError,
    create_project_stub,
    download_osm_data,
    finalize_odk_project,
    finalize_qfield_project,
    process_xlsform,
    save_data_extract,
    save_task_areas,
    split_aoi,
)


def _map_service_error(exc: ServiceError) -> HTTPException:
    """Convert service-layer exceptions to HTTP errors for API responses."""
    if isinstance(exc, ValidationError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )
    if isinstance(exc, ConflictError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        )
    if isinstance(exc, NotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=exc.message,
    )


def _enum_to_value(value):
    """Convert enum-like values to plain JSON-serializable primitives."""
    return value.value if hasattr(value, "value") else value


@post(
    "/projects",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(api_key_required),
    },
    status_code=status.HTTP_201_CREATED,
)
async def api_create_project(
    db: AsyncConnection, auth_user: AuthUser, data: CreateProjectRequest
) -> ProjectResponse:
    """Step 1: Create a project stub."""
    try:
        project = await create_project_stub(
            db=db,
            project_name=data.project_name,
            field_mapping_app=data.field_mapping_app,
            description=data.description,
            outline=data.outline,
            hashtags=data.hashtags or [],
            user_sub=auth_user.sub,
        )
        await db.commit()
        return ProjectResponse(
            id=project.id,
            project_name=project.project_name,
            field_mapping_app=_enum_to_value(project.field_mapping_app),
            status=str(_enum_to_value(project.status)),
        )
    except ServiceError as exc:
        raise _map_service_error(exc) from exc


@post(
    "/projects/{project_id:int}/xlsform",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(api_key_required),
    },
)
async def api_attach_xlsform(
    project_id: int, db: AsyncConnection, data: XLSFormRequest
) -> dict:
    """Step 2: Attach XLSForm from template or base64 payload."""
    try:
        if data.template_form_id is not None:
            template = await DbTemplateXLSForm.one(db, data.template_form_id)
            if not template.xls:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Template XLSForm content is empty.",
                )
            xlsform_bytes = BytesIO(template.xls)
        else:
            xls_content = base64.b64decode(data.xlsform_base64.encode("utf-8"))
            xlsform_bytes = BytesIO(xls_content)

        await process_xlsform(
            db=db,
            project_id=project_id,
            xlsform_bytes=xlsform_bytes,
            need_verification_fields=data.need_verification_fields,
            mandatory_photo_upload=data.mandatory_photo_upload,
            use_odk_collect=data.use_odk_collect,
            default_language=data.default_language,
        )
        return {"project_id": project_id, "xlsform_attached": True}
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid xlsform_base64 payload.",
        ) from exc
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ServiceError as exc:
        raise _map_service_error(exc) from exc


@post(
    "/projects/{project_id:int}/data-extract",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(api_key_required),
    },
)
async def api_data_extract(
    project_id: int, db: AsyncConnection, data: DataExtractRequest
) -> DataExtractResponse:
    """Step 3: Save provided geojson or fetch OSM data then save extract."""
    try:
        if data.geojson is not None:
            geojson = data.geojson
        else:
            geojson = await download_osm_data(
                db=db,
                project_id=project_id,
                osm_category=data.osm_category.name,
                geom_type=data.geom_type.value,
                centroid=data.centroid,
            )

        feature_count = await save_data_extract(
            db=db,
            project_id=project_id,
            geojson_data=geojson,
        )
        return DataExtractResponse(project_id=project_id, feature_count=feature_count)
    except ServiceError as exc:
        raise _map_service_error(exc) from exc


@post(
    "/projects/{project_id:int}/split",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(api_key_required),
    },
)
async def api_split(
    project_id: int, db: AsyncConnection, data: SplitRequest
) -> SplitResponse:
    """Step 4: Split AOI and save task areas."""
    try:
        tasks_geojson = await split_aoi(
            db=db,
            project_id=project_id,
            algorithm=data.algorithm.value,
            no_of_buildings=data.no_of_buildings,
            dimension_meters=data.dimension_meters,
            include_roads=data.include_roads,
            include_rivers=data.include_rivers,
            include_railways=data.include_railways,
            include_aeroways=data.include_aeroways,
        )
        task_count = await save_task_areas(
            db=db, project_id=project_id, tasks_geojson=tasks_geojson
        )
        return SplitResponse(
            project_id=project_id, task_count=task_count, is_empty=(tasks_geojson == {})
        )
    except ServiceError as exc:
        raise _map_service_error(exc) from exc


@post(
    "/projects/{project_id:int}/finalize",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(api_key_required),
    },
)
async def api_finalize(
    project_id: int, db: AsyncConnection, data: FinalizeRequest
) -> FinalizeResponse:
    """Step 5: Finalize project creation in ODK/QField."""
    project = await DbProject.one(db, project_id)
    if not project.field_mapping_app:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project field mapping app is not set.",
        )

    manager_username = None
    manager_password = None

    try:
        if project.field_mapping_app == FieldMappingApp.ODK:
            has_custom_odk = (
                data.external_project_instance_url
                and data.external_project_username
                and data.external_project_password
            )
            custom_odk = data if has_custom_odk else None
            odk_result = await finalize_odk_project(
                db=db, project_id=project_id, custom_odk_creds=custom_odk
            )
            downstream_url = odk_result.odk_url
            manager_username = odk_result.manager_username
            manager_password = odk_result.manager_password
        else:
            has_custom_qfield = (
                data.qfield_cloud_url
                and data.qfield_cloud_user
                and data.qfield_cloud_password
            )
            custom_qfield = data if has_custom_qfield else None
            downstream_url = await finalize_qfield_project(
                db=db, project_id=project_id, custom_qfield_creds=custom_qfield
            )
    except ServiceError as exc:
        raise _map_service_error(exc) from exc

    if data.cleanup:
        await DbProject.delete(db, project_id)
        await db.commit()

    return FinalizeResponse(
        project_id=project_id,
        downstream_url=downstream_url,
        cleanup=data.cleanup,
        manager_username=manager_username,
        manager_password=manager_password,
    )


@delete(
    "/projects/{project_id:int}",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(api_key_required),
    },
    status_code=status.HTTP_204_NO_CONTENT,
)
async def api_delete_project(project_id: int, db: AsyncConnection) -> None:
    """Delete project from Field-TM database."""
    await DbProject.delete(db, project_id)
    await db.commit()


@get("/projects", dependencies={"db": Provide(db_conn)})
async def api_list_projects(db: AsyncConnection) -> list[dict]:
    """Public endpoint to list projects."""
    projects = await DbProject.all(db, skip=0, limit=100)
    return [
        {
            "id": project.id,
            "project_name": project.project_name,
            "description": project.description,
            "status": _enum_to_value(project.status),
            "field_mapping_app": _enum_to_value(project.field_mapping_app),
        }
        for project in (projects or [])
    ]


@get("/projects/{project_id:int}", dependencies={"db": Provide(db_conn)})
async def api_get_project(project_id: int, db: AsyncConnection) -> dict:
    """Public endpoint to get a single project."""
    try:
        project = await DbProject.one(db, project_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project ({project_id}) not found.",
        ) from exc
    return {
        "id": project.id,
        "project_name": project.project_name,
        "description": project.description,
        "status": _enum_to_value(project.status),
        "field_mapping_app": _enum_to_value(project.field_mapping_app),
        "outline": project.outline,
        "hashtags": project.hashtags,
        "location_str": project.location_str,
    }


api_router = Router(
    path="/api/v1",
    tags=["api"],
    route_handlers=[
        api_create_project,
        api_attach_xlsform,
        api_data_extract,
        api_split,
        api_finalize,
        api_delete_project,
        api_list_projects,
        api_get_project,
    ],
)
