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
import zlib
from asyncio import to_thread
from base64 import b64encode
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from traceback import format_exc
from typing import Optional

from litestar import status_codes as status
from litestar.exceptions import HTTPException
from osm_data_client import (
    RawDataClient,
    RawDataClientConfig,
    RawDataOutputOptions,
    RawDataResult,
)
from osm_fieldwork.conversion_to_xlsform import convert_to_xlsform
from psycopg import AsyncConnection, sql
from psycopg.rows import class_row

from app.central import central_crud, central_deps, central_schemas
from app.config import settings
from app.db.enums import FieldMappingApp, ProjectStatus, XLSFormType
from app.db.models import (
    DbProject,
)
from app.db.postgis_utils import (
    split_geojson_by_task_areas,
)
from app.helpers.geometry_utils import (
    get_featcol_dominant_geom_type,
    javarosa_to_geojson_geom,
)
from app.i18n import _
from app.projects import project_deps

log = logging.getLogger(__name__)


async def generate_data_extract(
    project_id: int,
    aoi: dict,
    geom_types: list[str],
    config_json=None,
    centroid: bool = False,
    use_st_within: bool = True,
) -> RawDataResult:  # noqa: PLR0913
    """Request an OSM extract and return its download URL.

    geom_types selects raw-data-api tables via point, line, and polygon;
    multiple types union their results. Raises HTTPException on invalid
    parameters or extraction failure.
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
            f"ftm_{settings.FTM_DOMAIN}_data_extract_{project_id}"
            if settings.RAW_DATA_API_AUTH_TOKEN
            else f"ftm_extract_{project_id}"
        ),
        "outputType": "geojson",
        "geometryType": geom_types,
        "bindZip": False,
        "centroid": centroid,
        "use_st_within": (False if "line" in geom_types else use_st_within),
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
                error_str = str(e).split("status 406:")[-1].strip()
                error_dict = ast.literal_eval(error_str)
                msg = error_dict["detail"][0]["msg"]
            except Exception:
                msg = _(
                    "Selected area is too large. "
                    "Please select an area smaller than 200 km²."
                )

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=msg,
            ) from e

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_("Failed to generate data extract from the raw data API."),
        ) from e


# ---- SUPPORT FUNCTIONS ----


async def read_and_insert_xlsforms(db: AsyncConnection, directory: str) -> None:
    """Read the list of XLSForms from the disk and sync them with the database."""
    async with db.cursor() as cur:
        existing_db_forms = set()

        select_existing_query = """
            SELECT title FROM template_xlsforms;
        """
        await cur.execute(select_existing_query)
        existing_db_forms = {row[0] for row in await cur.fetchall()}

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
                continue

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


async def fail_stale_jobs(db: AsyncConnection) -> None:
    """Fail background jobs left running by a crash or restart.

    Background work runs as in-process asyncio tasks, so anything still
    "in progress" well after it started can never finish.
    """
    retry_msg = _("This job was interrupted. Please try again.")
    statements = [
        """
        UPDATE projects
        SET creation_status = 'failed',
            creation_error = %(msg)s,
            creation_updated_at = now()
        WHERE creation_status = 'in_progress'
          AND coalesce(creation_updated_at, updated_at) < %(cutoff)s
        """,
        """
        UPDATE projects
        SET basemap_attach_status = 'failed',
            basemap_attach_error = %(msg)s,
            basemap_attach_updated_at = now()
        WHERE basemap_attach_status = 'in_progress'
          AND coalesce(basemap_attach_updated_at, updated_at) < %(cutoff)s
        """,
        """
        UPDATE projects
        SET basemap_status = 'failed'
        WHERE basemap_status = 'searching' AND updated_at < %(cutoff)s
        """,
        "DELETE FROM qgis_jobs WHERE created_at < now() - interval '1 hour'",
    ]
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
    async with db.cursor() as cur:
        for statement in statements:
            await cur.execute(statement, {"msg": retry_msg, "cutoff": cutoff})
    await db.commit()


async def claim_simple_project_basemap_generation(
    db: AsyncConnection,
    project_id: int,
) -> bool:
    """Atomically claim a simple-flow project for basemap autostart generation."""
    claim_sql = """
        UPDATE projects
        SET
            basemap_status = 'generating',
            basemap_url = NULL,
            basemap_attach_status = 'pending_autostart',
            basemap_attach_error = NULL,
            basemap_attach_updated_at = NULL,
            updated_at = NOW()
        WHERE id = %(project_id)s
          AND field_mapping_app::text = %(field_mapping_app)s
          AND status::text = %(project_status)s
          AND (
              basemap_stac_item_id IS NULL
              OR BTRIM(basemap_stac_item_id) = ''
          )
          AND COALESCE(BTRIM(basemap_status), '') IN ('', 'generating', 'failed')
        RETURNING id;
    """

    async with db.cursor() as cur:
        await cur.execute(
            claim_sql,
            {
                "project_id": project_id,
                "field_mapping_app": FieldMappingApp.QFIELD.value,
                "project_status": ProjectStatus.PUBLISHED.value,
            },
        )
        claimed_row = await cur.fetchone()

    if not claimed_row:
        return False

    await db.commit()
    return True


async def generate_odk_central_project_content(
    project_odk_id: int,
    project_odk_form_id: str,
    odk_credentials: central_schemas.ODKCentral,
    xlsform: BytesIO,
    task_extract_dict: Optional[dict[int, dict]] = None,
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

    xform = await central_crud.read_and_test_xform(xlsform)

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
        async with central_deps.pyodk_client(odk_credentials) as client:
            table = await to_thread(
                client.entities.get_table,
                entity_list_name="tasks",
                project_id=project.external_project_id,
            )
        entity_data = table.get("value")
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
        form_name=f"FTM_Project_{project.id}",
    )
    xlsform_bytes.seek(0)
    return project.external_project_id, project_odk_form_id, xlsform_bytes


async def generate_project_files(
    db: AsyncConnection,
    project_id: int,
    odk_credentials: Optional[central_schemas.ODKCentral] = None,
) -> bool:
    """Generate the project's ODK appuser, QR code, XForm, and entities.

    odk_credentials=None uses deployment credentials. Returns True on success.
    """
    try:
        project = await project_deps.get_project_by_id(db, project_id)
        log.info(f"Starting generate_project_files for project {project_id}")

        log.debug("Getting stored data extract GeoJSON")
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


async def get_project_features_geojson(
    db: AsyncConnection,
    db_project: DbProject,
    task_id: Optional[int] = None,
) -> dict:
    """Get a geojson of all features for a task."""
    project_id = db_project.id
    data_extract_geojson = _stored_data_extract_geojson(db_project)
    if data_extract_geojson is None:
        return {"type": "FeatureCollection", "features": []}

    return await _task_filtered_feature_collection(
        db,
        data_extract_geojson,
        project_id,
        task_id,
        use_empty_default=True,
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


async def _task_filtered_feature_collection(
    db: AsyncConnection,
    data_extract_geojson: dict,
    project_id: int,
    task_id: int | None,
    use_empty_default: bool = True,
) -> dict:
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
            json={"displayName": "fieldtm_user"},
        )
        created_user.raise_for_status()
        return (created_user.json() or {}).get("token")


def _odk_qr_data(
    project: DbProject,
    odk_central: central_schemas.ODKCentral,
    appuser_token: str,
    username: str,
) -> str:
    """Build the ODK Collect settings QR payload."""
    odk_base_url = (odk_central.external_project_instance_url or "").rstrip("/")
    settings_payload = {
        "general": {
            "server_url": (
                f"{odk_base_url}/v1/key/{appuser_token}/projects"
                f"/{project.external_project_id}"
            ),
            "form_update_mode": "match_exactly",
            "basemap_source": "osm",
            "autosend": "wifi_and_cellular",
            "metadata_username": username,
            "metadata_email": "",
        },
        "project": {"name": f"{project.project_name}"},
        "admin": {},
    }
    return b64encode(zlib.compress(json.dumps(settings_payload).encode())).decode()


def _qfield_qr_data(project: DbProject) -> str:
    """Build the QField project QR payload."""
    if not project.external_project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_("QField project ID not found."),
        )

    return f"qfield://cloud?project={project.external_project_id}"


async def get_project_qr_data(
    db: AsyncConnection,
    project_id: int,
    username: str = "fieldtm_user",
) -> str:
    """Return the published project's QR payload for the browser to render.

    Raises HTTPException if the project or required data is missing.
    """
    project = await project_deps.get_project_by_id(db, project_id)

    if not project.project_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_("Project name not found."),
        )

    if project.field_mapping_app == FieldMappingApp.ODK:
        if not project.external_project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_("ODK project ID not found."),
            )

        odk_central = _project_odk_qr_credentials(project)
        appuser_token = await _get_or_create_appuser_token(project, odk_central)

        if not appuser_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_("Appuser token not found."),
            )

        qr_data = _odk_qr_data(
            project,
            odk_central,
            appuser_token,
            username,
        )
    elif project.field_mapping_app == FieldMappingApp.QFIELD:
        qr_data = _qfield_qr_data(project)
    else:
        qr_data = None

    if not qr_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_("Failed to generate QR code."),
        )

    return qr_data
