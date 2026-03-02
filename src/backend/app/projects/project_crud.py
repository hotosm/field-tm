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
"""Logic for Field-TM project routes."""

import ast
import json
import logging
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from traceback import format_exc
from typing import Optional

import aiohttp
import geojson
import segno
from litestar import Request
from litestar import status_codes as status
from litestar.exceptions import HTTPException
from osm_data_client import (
    RawDataClient,
    RawDataClientConfig,
    RawDataOutputOptions,
    RawDataResult,
)
from osm_fieldwork.conversion_to_xlsform import convert_to_xlsform
from osm_fieldwork.OdkCentral import OdkAppUser
from osm_login_python.core import Auth
from psycopg import AsyncConnection, sql
from psycopg.rows import class_row

from app.auth.providers.osm import get_osm_token, send_osm_message
from app.central import central_crud, central_deps, central_schemas
from app.config import settings
from app.db.enums import FieldMappingApp, ProjectStatus, XLSFormType
from app.db.models import (
    DbProject,
    DbUser,
)
from app.db.postgis_utils import (
    flatgeobuf_to_featcol,
    split_geojson_by_task_areas,
)
from app.helpers.geometry_utils import (
    get_featcol_dominant_geom_type,
    javarosa_to_geojson_geom,
)
from app.helpers.helper_schemas import PaginationInfo
from app.projects import project_deps

log = logging.getLogger(__name__)


async def generate_data_extract(
    project_id: int,
    aoi: geojson.FeatureCollection | geojson.Feature | dict,
    geom_type: str,
    config_json=None,
    centroid: bool = False,
    use_st_within: bool = True,
) -> RawDataResult:  # noqa: PLR0913
    """Request a new data extract in flatgeobuf format.

    Args:
        project_id (int): Id (primary key) of the project.
        aoi (geojson.FeatureCollection | geojson.Feature | dict]):
            Area of interest for data extraction.
        geom_type (str): Type of geometry to extract.
        config_json (Optional[json], optional):
            Configuration for data extraction. Defaults to None.
        centroid (bool): Generate centroid of polygons.
        use_st_within (bool): Include features within the AOI.

    Raises:
        HTTPException:
            When necessary parameters are missing or data extraction fails.

    Returns:
        str:
            URL for the geojson data extract.
    """
    if not config_json:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "To generate a new data extract a extract_config must be specified."
            ),
        )
    config = RawDataClientConfig(
        access_token=settings.RAW_DATA_API_AUTH_TOKEN.get_secret_value()
        if settings.RAW_DATA_API_AUTH_TOKEN
        else None
    )
    extra_params = {
        "fileName": (
            f"fmtm_{settings.FMTM_DOMAIN}_data_extract_{project_id}"
            if settings.RAW_DATA_API_AUTH_TOKEN
            else f"fmtm_extract_{project_id}"
        ),
        "outputType": "geojson",
        "geometryType": [geom_type],
        "bindZip": False,
        "centroid": centroid,
        "use_st_within": (False if geom_type == "line" else use_st_within),
        "filters": config_json,
    }

    try:
        result = await RawDataClient(config).get_osm_data(
            aoi,
            output_options=RawDataOutputOptions(download_file=False),
            **extra_params,
        )

        return result
    except Exception as e:
        log.error("Raw data API request failed")
        if "status 406" in str(e) and "Area" in str(e):
            try:
                # Extract the error dict part
                error_str = str(e).split("status 406:")[-1].strip()
                error_dict = ast.literal_eval(error_str)
                msg = error_dict["detail"][0]["msg"]
            except Exception:
                msg = """Selected area is too large.
                Please select an area smaller than 200 km²."""

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=msg,
            ) from e

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to generate data extract from the raw data API.",
        ) from e


# ---------------------------
# ---- SUPPORT FUNCTIONS ----
# ---------------------------


async def read_and_insert_xlsforms(db: AsyncConnection, directory: str) -> None:
    """Read the list of XLSForms from the disk and sync them with the database."""
    async with db.cursor() as cur:
        existing_db_forms = set()

        # Collect all existing XLSForm titles from the database
        select_existing_query = """
            SELECT title FROM template_xlsforms;
        """
        await cur.execute(select_existing_query)
        existing_db_forms = {row[0] for row in await cur.fetchall()}

        # Insert or update new XLSForms from disk
        for yaml_type in XLSFormType:
            file_name = yaml_type.name
            form_type = yaml_type.value
            file_path = Path(directory) / f"{file_name}.yaml"

            if not file_path.exists():
                log.warning(f"{file_path} does not exist!")
                continue

            if file_path.stat().st_size == 0:
                log.warning(f"{file_path} is empty!")
                continue

            try:
                data = convert_to_xlsform(str(file_path))

            except Exception:
                log.exception(
                    f"Error occurred during in-memory conversion for {file_path}"
                )

            try:
                insert_query = """
                    INSERT INTO template_xlsforms (title, xls)
                    VALUES (%(title)s, %(xls)s)
                    ON CONFLICT (title) DO UPDATE
                    SET xls = EXCLUDED.xls
                """
                await cur.execute(insert_query, {"title": form_type, "xls": data})
                log.info(f"XLSForm for '{form_type}' inserted/updated in the database")

            except Exception as e:
                log.exception(
                    f"Failed to insert or update {form_type} in the database. "
                    f"Error: {e}",
                    stack_info=True,
                )

        # Determine the forms that need to be deleted (those in the DB but
        # not in the current XLSFormType)
        required_forms = {yaml_type.value for yaml_type in XLSFormType}
        forms_to_delete = existing_db_forms - required_forms

        if forms_to_delete:
            delete_query = """
                DELETE FROM template_xlsforms WHERE title = ANY(%(titles)s)
            """
            await cur.execute(delete_query, {"titles": list(forms_to_delete)})
            log.info(f"Deleted XLSForms from the database: {forms_to_delete}")


async def generate_odk_central_project_content(
    project_odk_id: int,
    project_odk_form_id: str,
    odk_credentials: central_schemas.ODKCentral,
    xlsform: BytesIO,
    task_extract_dict: Optional[dict[int, geojson.FeatureCollection]] = None,
    entity_properties: Optional[list[str]] = None,
) -> str:  # noqa: PLR0913
    """Populate the project in ODK Central with XForm, Appuser, Permissions."""
    entities_list = []
    if task_extract_dict:
        entities_list = await central_crud.task_geojson_dict_to_entity_values(
            task_extract_dict
        )

    default_style = {
        "fill": "#1a1a1a",
        "marker-color": "#1a1a1a",
        "stroke": "#000000",
        "stroke-width": "6",
    }

    for entity in entities_list:
        data = entity["data"]
        for key, value in default_style.items():
            data.setdefault(key, value)

    log.debug("Creating project ODK dataset named 'features'")
    await central_crud.create_entity_list(
        odk_credentials,
        project_odk_id,
        properties=entity_properties,
        dataset_name="features",
        entities_list=entities_list,
    )

    # Do final check of XLSForm validity + return parsed XForm
    xform = await central_crud.read_and_test_xform(xlsform)

    # Upload survey XForm
    log.info("Uploading survey XForm to ODK Central")
    await central_crud.create_odk_xform(
        project_odk_id,
        xform,
        odk_credentials,
    )

    return await central_crud.get_appuser_token(
        project_odk_form_id,
        project_odk_id,
        odk_credentials,
    )


def _with_default_entity_properties(entity_properties: list[str]) -> list[str]:
    """Append the standard styling/system fields expected by generated entities."""
    default_fields = [
        "created_by",
        "fill",
        "marker-color",
        "stroke",
        "stroke-width",
    ]
    for field in default_fields:
        if field not in entity_properties:
            entity_properties.append(field)
    return entity_properties


def _feature_collection_from_features(features: list[dict]) -> dict | None:
    """Wrap features as a FeatureCollection when non-empty."""
    if not features:
        return None
    return {"type": "FeatureCollection", "features": features}


async def _task_boundaries_from_odk(
    project: DbProject,
    odk_credentials: Optional[central_schemas.ODKCentral],
) -> dict | None:
    """Fetch task boundaries from ODK entities when available."""
    if not (
        project.field_mapping_app == FieldMappingApp.ODK and project.external_project_id
    ):
        return None

    try:
        async with central_deps.get_odk_dataset(odk_credentials) as odk_central:
            entity_data = await odk_central.getEntityData(
                project.external_project_id,
                "tasks",
                include_metadata=False,
            )
    except Exception as e:
        log.warning(
            "Could not fetch task boundaries from ODK for project %s: %s",
            project.id,
            e,
        )
        return None

    if not isinstance(entity_data, list):
        return None

    features = []
    for entity in entity_data:
        if not entity.get("geometry"):
            continue
        geom = await javarosa_to_geojson_geom(entity["geometry"])
        features.append(
            {
                "type": "Feature",
                "geometry": geom,
                "properties": entity.get("properties", {}),
            }
        )

    return _feature_collection_from_features(features)


async def _task_boundaries_from_qfield(
    db: AsyncConnection,
    project_id: int,
) -> dict | None:
    """Fetch task boundaries from the temporary QField table when present."""
    try:
        async with db.cursor(row_factory=class_row(dict)) as cur:
            temp_table_sql = sql.SQL(
                """
                SELECT
                    task_index,
                    ST_AsGeoJSON(outline)::jsonb AS outline
                FROM {table_name}
                ORDER BY task_index;
            """
            ).format(table_name=sql.Identifier(f"temp_task_boundaries_{project_id}"))
            await cur.execute(temp_table_sql)
            db_tasks = await cur.fetchall()
    except Exception as e:
        log.warning(
            "Could not fetch task boundaries from temp table for QField project %s: %s",
            project_id,
            e,
        )
        return None

    features = [
        {
            "type": "Feature",
            "geometry": task["outline"],
            "properties": {"task_id": task["task_index"]},
        }
        for task in db_tasks
        if task.get("outline")
    ]
    return _feature_collection_from_features(features)


async def _get_task_boundaries(
    db: AsyncConnection,
    project: DbProject,
    odk_credentials: Optional[central_schemas.ODKCentral],
) -> dict | None:
    """Resolve task boundaries from the active downstream storage."""
    odk_boundaries = await _task_boundaries_from_odk(project, odk_credentials)
    if odk_boundaries:
        return odk_boundaries

    if project.field_mapping_app == FieldMappingApp.QFIELD:
        return await _task_boundaries_from_qfield(db, project.id)

    return None


async def _build_task_extracts(
    db: AsyncConnection,
    project: DbProject,
    feature_collection: dict,
    odk_credentials: Optional[central_schemas.ODKCentral],
) -> tuple[list[str], dict[int, dict]]:
    """Build entity property names and per-task extracts from the data extract."""
    first_feature = next(iter(feature_collection.get("features", [])), {})
    if not (first_feature and "properties" in first_feature):
        return [], {}

    entity_properties = _with_default_entity_properties(
        list(first_feature["properties"].keys())
    )
    task_boundaries = await _get_task_boundaries(db, project, odk_credentials)
    task_extract_dict = await split_geojson_by_task_areas(
        db,
        feature_collection,
        project.id,
        task_boundaries,
    )
    if task_extract_dict or not feature_collection:
        return entity_properties, task_extract_dict

    log.info(
        "No task boundaries found for project %s. Using whole AOI as single task.",
        project.id,
    )
    return entity_properties, {1: feature_collection}


async def _resolve_project_form_upload(
    project: DbProject,
) -> tuple[int, str, BytesIO]:
    """Validate project XLSForm content and extract the ODK form id."""
    if not project.xlsform_content:
        msg = f"No XLSForm content found for project ({project.id})"
        log.error(msg)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=msg,
        )

    xlsform_bytes = BytesIO(project.xlsform_content)
    project_odk_form_id, _ = await central_crud.append_fields_to_user_xlsform(
        xlsform=xlsform_bytes,
        form_name=f"FMTM_Project_{project.id}",
    )
    xlsform_bytes.seek(0)
    return project.external_project_id, project_odk_form_id, xlsform_bytes


async def generate_project_files(
    db: AsyncConnection,
    project_id: int,
    odk_credentials: Optional[central_schemas.ODKCentral] = None,
) -> bool:
    """Generate the files for a project.

    QR code (appuser), ODK XForm, ODK Entities from OSM data extract.

    Args:
        project_id(int): id of the Field-TM project.
        db (Connection): The database connection, newly generated.
        odk_credentials: Optional custom ODK credentials (None uses env vars).

    Returns:
        bool: True if success.
    """
    try:
        project = await project_deps.get_project_by_id(db, project_id)
        log.info(f"Starting generate_project_files for project {project_id}")

        # Extract data extract from flatgeobuf
        log.debug("Getting data extract geojson from flatgeobuf")
        feature_collection = await get_project_features_geojson(db, project)
        entity_properties, task_extract_dict = await _build_task_extracts(
            db,
            project,
            feature_collection,
            odk_credentials,
        )
        (
            project_odk_id,
            project_odk_form_id,
            xlsform_bytes,
        ) = await _resolve_project_form_upload(project)

        odk_token = await generate_odk_central_project_content(
            project_odk_id,
            project_odk_form_id,
            odk_credentials,
            xlsform_bytes,
            task_extract_dict,
            entity_properties,
        )

        log.debug(
            f"Generated ODK token for Field-TM project ({project_id}) "
            f"ODK project {project_odk_id}: "
            f"{type(odk_token)} "
            f"({odk_token[:15] if odk_token else 'None'}...)"
        )
        return True
    except Exception as e:
        log.debug(str(format_exc()))
        log.exception(
            f"Error generating project files for project {project_id}: {e}",
            stack_info=True,
        )
        return False


def _empty_feature_collection_json() -> str:
    """Return an empty GeoJSON feature collection as JSON text."""
    return json.dumps({"type": "FeatureCollection", "features": []})


def _serialize_stored_task_areas(task_areas_geojson) -> str | None:
    """Serialize task areas stored directly on the project row."""
    if task_areas_geojson is None:
        return None
    if task_areas_geojson == {}:
        return _empty_feature_collection_json()
    if isinstance(task_areas_geojson, dict):
        return json.dumps(task_areas_geojson)
    if isinstance(task_areas_geojson, str):
        return task_areas_geojson
    return None


def _project_odk_credentials_from_settings() -> central_schemas.ODKCentral:
    """Build ODK credentials from environment settings."""
    return central_schemas.ODKCentral(
        external_project_instance_url=settings.ODK_CENTRAL_URL,
        external_project_username=settings.ODK_CENTRAL_USER,
        external_project_password=settings.ODK_CENTRAL_PASSWD.get_secret_value()
        if settings.ODK_CENTRAL_PASSWD
        else "",
    )


async def _task_geometry_from_odk(project: DbProject) -> str | None:
    """Load task geometry from ODK entities and serialize as GeoJSON."""
    if not (
        project.field_mapping_app == FieldMappingApp.ODK and project.external_project_id
    ):
        return None

    try:
        async with central_deps.get_odk_dataset(
            _project_odk_credentials_from_settings()
        ) as odk_central:
            entity_data = await odk_central.getEntityData(
                project.external_project_id,
                "tasks",
                include_metadata=False,
            )
    except Exception as e:
        log.warning(
            "Failed to fetch task boundaries from ODK for project %s: %s",
            project.id,
            e,
        )
        return None

    if not isinstance(entity_data, list):
        return None

    features = []
    for entity in entity_data:
        if not entity.get("geometry"):
            continue
        geom = await javarosa_to_geojson_geom(entity["geometry"])
        task_id = entity.get("task_id", entity.get("__id", ""))
        features.append(
            {
                "type": "Feature",
                "geometry": geom,
                "properties": {"task_id": task_id, **(entity.get("properties", {}))},
            }
        )

    if not features:
        return None
    return json.dumps({"type": "FeatureCollection", "features": features})


async def _task_geometry_from_qfield(
    db: AsyncConnection,
    project_id: int,
) -> str | None:
    """Load task geometry from the temporary QField task boundary table."""
    feature_collection = await _task_boundaries_from_qfield(db, project_id)
    if not feature_collection:
        return None
    return json.dumps(feature_collection)


async def get_task_geometry(db: AsyncConnection, project_id: int):
    """Retrieves the geometry of tasks associated with a project.

    Task boundaries are stored in the database as task_areas_geojson (for preview),
    or in ODK Central as entities (dataset: "tasks") after finalization,
    or in a temporary table for QField projects.

    Args:
        db (Connection): The database connection.
        project_id (int): The ID of the project.

    Returns:
        str: A geojson of the task boundaries
    """
    # Get project to check if it has task areas stored in database
    project = await project_deps.get_project_by_id(db, project_id)
    stored_task_areas = _serialize_stored_task_areas(project.task_areas_geojson)
    if stored_task_areas is not None:
        return stored_task_areas

    odk_task_geometry = await _task_geometry_from_odk(project)
    if odk_task_geometry is not None:
        return odk_task_geometry

    if project.field_mapping_app == FieldMappingApp.QFIELD:
        qfield_task_geometry = await _task_geometry_from_qfield(db, project_id)
        if qfield_task_geometry is not None:
            return qfield_task_geometry

    return _empty_feature_collection_json()


async def get_project_features_geojson(
    db: AsyncConnection,
    db_project: DbProject,
    task_id: Optional[int] = None,
) -> geojson.FeatureCollection:
    """Get a geojson of all features for a task."""
    project_id = db_project.id
    data_extract_geojson = _stored_data_extract_geojson(db_project)
    if data_extract_geojson is None:
        data_extract_geojson = await _download_data_extract_geojson(db, db_project)
        use_empty_default = False
    else:
        use_empty_default = True
    if data_extract_geojson is None:
        return {"type": "FeatureCollection", "features": []}

    return await _task_filtered_feature_collection(
        db,
        data_extract_geojson,
        project_id,
        task_id,
        use_empty_default=use_empty_default,
    )


def _stored_data_extract_geojson(db_project: DbProject) -> dict | None:
    """Return the stored FeatureCollection when available."""
    data_extract_geojson = getattr(db_project, "data_extract_geojson", None)
    if (
        isinstance(data_extract_geojson, dict)
        and data_extract_geojson.get("type") == "FeatureCollection"
    ):
        return data_extract_geojson
    return None


async def _download_data_extract_geojson(
    db: AsyncConnection,
    db_project: DbProject,
) -> dict | None:
    """Download and convert the legacy flatgeobuf extract when needed."""
    data_extract_url = getattr(db_project, "data_extract_url", None)
    if not data_extract_url:
        return None

    project_id = db_project.id
    data_extract_url = data_extract_url.replace(
        settings.S3_DOWNLOAD_ROOT,
        settings.S3_ENDPOINT,
    )
    async with (
        aiohttp.ClientSession() as session,
        session.get(data_extract_url) as response,
    ):
        if not response.ok:
            msg = f"Download failed for data extract, project ({project_id})"
            log.error(msg)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=msg,
            )
        log.debug("Converting FlatGeobuf to GeoJSON")
        data_extract_geojson = await flatgeobuf_to_featcol(db, await response.read())

    if data_extract_geojson:
        return data_extract_geojson

    msg = f"Failed to convert flatgeobuf --> geojson for project ({project_id})"
    log.error(msg)
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=msg,
    )


async def _task_filtered_feature_collection(
    db: AsyncConnection,
    data_extract_geojson: dict,
    project_id: int,
    task_id: int | None,
    use_empty_default: bool = True,
) -> geojson.FeatureCollection:
    """Return either the full extract or the task-specific split subset."""
    if not task_id:
        return data_extract_geojson

    geom_type = get_featcol_dominant_geom_type(data_extract_geojson)
    split_extract_dict = await split_geojson_by_task_areas(
        db,
        data_extract_geojson,
        project_id,
        geom_type=geom_type,
    )
    if use_empty_default:
        return split_extract_dict.get(
            task_id,
            {"type": "FeatureCollection", "features": []},
        )
    return split_extract_dict[task_id]


async def get_pagination(page: int, count: int, results_per_page: int, total: int):
    """Pagination result for splash page."""
    total_pages = (total + results_per_page - 1) // results_per_page
    has_next = (page * results_per_page) < total
    has_prev = page > 1

    pagination = PaginationInfo(
        has_next=has_next,
        has_prev=has_prev,
        next_num=page + 1 if has_next else None,
        page=page,
        pages=total_pages,
        prev_num=page - 1 if has_prev else None,
        per_page=results_per_page,
        total=total,
    )

    return pagination


async def get_paginated_projects(  # noqa: PLR0913
    db: AsyncConnection,
    page: int,
    results_per_page: int,
    user_sub: Optional[str] = None,
    hashtags: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[ProjectStatus] = None,
    field_mapping_app: Optional[FieldMappingApp] = None,
    country: Optional[str] = None,
) -> dict:  # noqa: PLR0913
    """Helper function to fetch paginated projects with optional filters."""
    if hashtags:
        hashtags = hashtags.split(",")

    # Get subset of projects
    projects = await DbProject.all(
        db,
        user_sub=user_sub,
        hashtags=hashtags,
        search=search,
        status=status,
        field_mapping_app=field_mapping_app,
        country=country,
    )
    start_index = (page - 1) * results_per_page
    end_index = start_index + results_per_page
    paginated_projects = projects[start_index:end_index] if projects else []

    pagination = await get_pagination(
        page,
        len(paginated_projects),
        results_per_page,
        len(projects) if projects else 0,
    )

    from app.helpers.helper_schemas import PaginatedResponse

    return PaginatedResponse[DbProject](
        results=paginated_projects,
        pagination=pagination,
    )


async def send_project_manager_message(
    request: Request,
    project: DbProject,
    new_manager: DbUser,
    osm_auth: Auth,
):
    """Send message to the new project manager after assigned."""
    log.info(f"Sending message to new project manager ({new_manager.username}).")

    osm_token = get_osm_token(request, osm_auth)
    project_url = f"{settings.FMTM_DOMAIN}/project/{project.id}"
    if not project_url.startswith("http"):
        project_url = f"https://{project_url}"

    message_content = dedent(f"""
        You have been assigned to the project **{project.project_name}** as a
        manager. You can now manage the project and its tasks.

        [Click here to view the project]({project_url})

        Thank you for being a part of our platform!
    """)

    send_osm_message(
        osm_token=osm_token,
        osm_sub=new_manager.sub,
        title=f"You have been assigned to project {project.project_name} as a manager",
        body=message_content,
    )
    log.info(f"Message sent to new project manager ({new_manager.username}).")


def _project_odk_qr_credentials(project: DbProject) -> central_schemas.ODKCentral:
    """Resolve ODK credentials for QR-code generation and app-user lookup."""
    project_odk_creds = project.get_odk_credentials()
    if project_odk_creds is not None:
        return project_odk_creds

    odk_base_url = (
        project.external_project_instance_url
        or settings.ODK_CENTRAL_PUBLIC_URL
        or settings.ODK_CENTRAL_URL
    )
    return central_schemas.ODKCentral(
        external_project_instance_url=odk_base_url,
        external_project_username=settings.ODK_CENTRAL_USER,
        external_project_password=settings.ODK_CENTRAL_PASSWD.get_secret_value()
        if settings.ODK_CENTRAL_PASSWD
        else "",
    )


async def _get_or_create_appuser_token(
    project: DbProject,
    odk_central: central_schemas.ODKCentral,
) -> str:
    """Get an existing app-user token or create one if none exists."""
    async with central_deps.pyodk_client(odk_central) as client:
        appusers_response = client.session.get(
            f"projects/{project.external_project_id}/app-users"
        )
        appusers_response.raise_for_status()
        appusers = appusers_response.json() or []
        appuser_token = next(
            (app_user.get("token") for app_user in appusers if app_user.get("token")),
            None,
        )
        if appuser_token:
            return appuser_token

        created_user = client.session.post(
            f"projects/{project.external_project_id}/app-users",
            json={"displayName": "fmtm_user"},
        )
        created_user.raise_for_status()
        return (created_user.json() or {}).get("token")


def _odk_qrcode_data_url(
    project: DbProject,
    odk_central: central_schemas.ODKCentral,
    appuser_token: str,
    username: str,
) -> str:
    """Generate the ODK QR code data URL."""
    appuser_obj = OdkAppUser(
        odk_central.external_project_instance_url,
        odk_central.external_project_username,
        odk_central.external_project_password,
    )
    qrcode = appuser_obj.createQRCode(
        odk_id=project.external_project_id,
        project_name=project.project_name,
        appuser_token=appuser_token,
        basemap="osm",
        osm_username=username,
    )
    return qrcode.png_data_uri(scale=5)


def _qfield_qrcode_data_url(project: DbProject) -> str:
    """Generate the QField QR code data URL."""
    if not project.external_project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QField project ID not found.",
        )

    qfield_url = f"qfield://cloud?project={project.external_project_id}"
    qrcode = segno.make(qfield_url, micro=False)
    return qrcode.png_data_uri(scale=6)


async def get_project_qrcode(
    db: AsyncConnection,
    project_id: int,
    username: str = "fieldtm_user",
) -> str:
    """Generate and return QR code for a published project.

    Args:
        db (AsyncConnection): Database connection.
        project_id (int): Project ID.
        username (str, optional): OSM username for ODK metadata.
            Defaults to "fieldtm_user".

    Returns:
        str: Base64 data URL of the QR code image.

    Raises:
        HTTPException: If project or required data is missing.
    """
    # Get fresh project data
    project = await project_deps.get_project_by_id(db, project_id)

    if not project.project_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project name not found.",
        )

    if project.field_mapping_app == FieldMappingApp.ODK:
        if not project.external_project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ODK project ID not found.",
            )

        odk_central = _project_odk_qr_credentials(project)
        appuser_token = await _get_or_create_appuser_token(project, odk_central)

        if not appuser_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appuser token not found.",
            )

        qr_code_data_url = _odk_qrcode_data_url(
            project,
            odk_central,
            appuser_token,
            username,
        )
    elif project.field_mapping_app == FieldMappingApp.QFIELD:
        qr_code_data_url = _qfield_qrcode_data_url(project)
    else:
        qr_code_data_url = None

    if not qr_code_data_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate QR code.",
        )

    return qr_code_data_url
