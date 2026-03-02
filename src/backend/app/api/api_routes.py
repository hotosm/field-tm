"""External REST API routes for project creation."""

from __future__ import annotations

import base64
from io import BytesIO

from litestar import Request, Router, delete, get, post
from litestar import status_codes as status
from litestar.di import Provide
from litestar.exceptions import HTTPException
from psycopg import AsyncConnection

from app.api.api_schemas import (
    CreateProjectRequest,
    CreateProjectResponse,
)
from app.auth.api_key import api_key_required
from app.central.central_schemas import ODKCentral
from app.config import settings
from app.db.database import db_conn
from app.db.enums import FieldMappingApp
from app.db.models import DbProject, DbTemplateXLSForm
from app.projects.project_schemas import ProjectUpdate
from app.projects.project_services import (
    ConflictError,
    NotFoundError,
    ServiceError,
    SplitAoiOptions,
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


def _build_fmtm_url(project_id: int) -> str:
    """Build the FieldTM project page URL."""
    domain = settings.FMTM_DOMAIN
    port_suffix = f":{settings.FMTM_DEV_PORT}" if settings.FMTM_DEV_PORT else ""
    scheme = "http" if "localhost" in domain else "https"
    return f"{scheme}://{domain}{port_suffix}/projects/{project_id}"


async def _cleanup_project(db: AsyncConnection, project_id: int | None) -> None:
    """Delete a partially-created project on workflow failure or cleanup."""
    if project_id is None:
        return

    await DbProject.delete(db, project_id)
    await db.commit()


async def _resolve_xlsform_bytes(
    db: AsyncConnection,
    data: CreateProjectRequest,
) -> BytesIO:
    """Load XLSForm bytes from a template or inline base64 payload."""
    if data.template_form_id is not None:
        template = await DbTemplateXLSForm.one(db, data.template_form_id)
        if not template.xls:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template XLSForm content is empty.",
            )
        return BytesIO(template.xls)

    xls_content = base64.b64decode(data.xlsform_base64.encode("utf-8"))
    return BytesIO(xls_content)


async def _save_requested_data_extract(
    db: AsyncConnection,
    project_id: int,
    data: CreateProjectRequest,
) -> None:
    """Persist either provided GeoJSON, downloaded OSM data, or an empty collection."""
    if data.geojson is not None:
        await save_data_extract(db=db, project_id=project_id, geojson_data=data.geojson)
        await db.commit()
        return

    if data.osm_category is not None:
        geojson = await download_osm_data(
            db=db,
            project_id=project_id,
            osm_category=data.osm_category.name,
            geom_type=data.geom_type.value,
            centroid=data.centroid,
        )
        await save_data_extract(db=db, project_id=project_id, geojson_data=geojson)
        await db.commit()
        return

    await DbProject.update(
        db,
        project_id,
        ProjectUpdate(
            data_extract_geojson={"type": "FeatureCollection", "features": []}
        ),
    )
    await db.commit()


async def _split_project_if_requested(
    db: AsyncConnection,
    project_id: int,
    data: CreateProjectRequest,
) -> None:
    """Split the project AOI when an algorithm is supplied."""
    if data.algorithm is None:
        return

    tasks_geojson = await split_aoi(
        db=db,
        project_id=project_id,
        options=SplitAoiOptions(
            algorithm=data.algorithm.value,
            no_of_buildings=data.no_of_buildings,
            dimension_meters=data.dimension_meters,
            include_roads=data.include_roads,
            include_rivers=data.include_rivers,
            include_railways=data.include_railways,
            include_aeroways=data.include_aeroways,
        ),
    )
    await save_task_areas(db=db, project_id=project_id, tasks_geojson=tasks_geojson)
    await db.commit()


def _build_custom_odk_credentials(
    data: CreateProjectRequest,
) -> ODKCentral | None:
    """Build per-request ODK credentials when all custom fields are present."""
    has_custom_odk = (
        data.external_project_instance_url
        and data.external_project_username
        and data.external_project_password
    )
    if not has_custom_odk:
        return None

    return ODKCentral(
        external_project_instance_url=data.external_project_instance_url,
        external_project_username=data.external_project_username,
        external_project_password=data.external_project_password,
    )


async def _finalize_project(
    db: AsyncConnection,
    project: DbProject,
    project_id: int,
    data: CreateProjectRequest,
) -> tuple[str, str | None, str | None]:
    """Finalize the project in ODK or QField and return downstream access details."""
    if project.field_mapping_app == FieldMappingApp.ODK:
        odk_result = await finalize_odk_project(
            db=db,
            project_id=project_id,
            custom_odk_creds=_build_custom_odk_credentials(data),
        )
        return (
            odk_result.odk_url,
            odk_result.manager_username,
            odk_result.manager_password,
        )

    has_custom_qfield = (
        data.qfield_cloud_url and data.qfield_cloud_user and data.qfield_cloud_password
    )
    downstream_url = await finalize_qfield_project(
        db=db,
        project_id=project_id,
        custom_qfield_creds=(data if has_custom_qfield else None),
    )
    return downstream_url, None, None


@post(
    "/projects",
    dependencies={
        "db": Provide(db_conn),
    },
    status_code=status.HTTP_201_CREATED,
)
async def api_create_project(
    request: Request,
    db: AsyncConnection,
    data: CreateProjectRequest,
) -> CreateProjectResponse:
    """Create a complete project end-to-end in a single request.

    Runs all five steps — stub, XLSForm, data extract, split, finalize —
    and returns the FieldTM project URL plus downstream credentials.
    """
    auth_user = await api_key_required(request, db)
    project_id: int | None = None

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
        project_id = project.id

        xlsform_bytes = await _resolve_xlsform_bytes(db, data)
        await process_xlsform(
            db=db,
            project_id=project_id,
            xlsform_bytes=xlsform_bytes,
            need_verification_fields=data.need_verification_fields,
            mandatory_photo_upload=data.mandatory_photo_upload,
            use_odk_collect=data.use_odk_collect,
            default_language=data.default_language,
        )
        await db.commit()

        await _save_requested_data_extract(db, project_id, data)
        await _split_project_if_requested(db, project_id, data)
        downstream_url, manager_username, manager_password = await _finalize_project(
            db,
            project,
            project_id,
            data,
        )

        await db.commit()

    except (ValueError, TypeError) as exc:
        await _cleanup_project(db, project_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except HTTPException:
        await _cleanup_project(db, project_id)
        raise
    except ServiceError as exc:
        await _cleanup_project(db, project_id)
        raise _map_service_error(exc) from exc

    fmtm_url = None if data.cleanup else _build_fmtm_url(project_id)

    if data.cleanup:
        await _cleanup_project(db, project_id)

    return CreateProjectResponse(
        project_id=project_id,
        fmtm_url=fmtm_url,
        downstream_url=downstream_url,
        manager_username=manager_username,
        manager_password=manager_password,
    )


@delete(
    "/projects/{project_id:int}",
    dependencies={
        "db": Provide(db_conn),
    },
    status_code=status.HTTP_204_NO_CONTENT,
)
async def api_delete_project(
    request: Request, project_id: int, db: AsyncConnection
) -> None:
    """Delete project from Field-TM database."""
    await api_key_required(request, db)
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
        api_delete_project,
        api_list_projects,
        api_get_project,
    ],
)
