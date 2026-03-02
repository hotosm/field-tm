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
"""Logic for interaction with ODK Central & data."""

import csv
import json
import logging
import secrets
import string
from asyncio import gather
from contextlib import suppress
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Union
from uuid import UUID, uuid4

import geojson
from geojson_aoi import parse_aoi
from litestar import status_codes as status
from litestar.exceptions import HTTPException
from osm_fieldwork.update_xlsform import append_field_mapping_fields
from psycopg import AsyncConnection
from pyodk.errors import PyODKError
from pyxform.xls2xform import convert as xform_convert

from app.central import central_deps, central_schemas
from app.config import settings
from app.db.enums import DbGeomType
from app.db.models import DbProject, DbTemplateXLSForm
from app.helpers.geometry_utils import (
    geojson_to_javarosa_geom,
    javarosa_to_geojson_geom,
)
from app.projects import project_schemas
from app.s3 import strip_presigned_url_for_local_dev

log = logging.getLogger(__name__)

MIN_PYODK_ERROR_ARGS = 2
HTTP_ERROR_STATUS_CODE = 400


def _extract_dataset_property_names(payload: object) -> set[str]:
    """Extract dataset property names from Central API payloads."""
    if isinstance(payload, dict):
        payload = payload.get("value", payload.get("properties", payload))

    if not isinstance(payload, list):
        return set()

    names: set[str] = set()
    for item in payload:
        if isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str) and name:
                names.add(name)
        elif isinstance(item, str) and item:
            names.add(item)

    return names


def _is_duplicate_form_conflict(exc: Exception) -> bool:
    """Check whether an ODK error means the form already exists."""
    if _is_pyodk_duplicate_form_conflict(exc):
        return True

    msg = str(exc)
    return "409" in msg and "already exists" in msg and "xmlFormId" in msg


def _is_pyodk_duplicate_form_conflict(exc: Exception) -> bool:
    """Check PyODK-specific conflict metadata for duplicate forms."""
    if not isinstance(exc, PyODKError):
        return False

    if _matches_duplicate_form_error_code(exc):
        return True

    response = _get_pyodk_error_response(exc)
    if getattr(response, "status_code", None) != status.HTTP_409_CONFLICT:
        return False

    return _duplicate_form_conflict_from_body(_safe_response_json(response))


def _matches_duplicate_form_error_code(exc: PyODKError) -> bool:
    """Use PyODK's central error inspection when available."""
    try:
        return exc.is_central_error(409.3)
    except Exception as err:
        log.debug("Unable to inspect PyODK conflict details: %s", err)
        return False


def _get_pyodk_error_response(exc: PyODKError):
    """Return the response object attached to a PyODKError if present."""
    if len(exc.args) < MIN_PYODK_ERROR_ARGS:
        return None
    return exc.args[1]


def _safe_response_json(response) -> dict:
    """Best-effort JSON decode for PyODK error responses."""
    if response is None:
        return {}

    try:
        body = response.json()
    except Exception:
        return {}

    return body if isinstance(body, dict) else {}


def _duplicate_form_conflict_from_body(body: dict) -> bool:
    """Check Central conflict payload details for duplicate form markers."""
    details = body.get("details", {})
    if isinstance(details, dict):
        fields = details.get("fields", [])
        if isinstance(fields, list) and {"projectId", "xmlFormId"}.issubset(fields):
            return True

    return "xmlFormId" in str(body.get("message", ""))


async def list_odk_projects(
    odk_central: Optional[central_schemas.ODKCentral] = None,
):
    """List all projects on a remote ODK Server."""
    try:
        async with central_deps.pyodk_client(odk_central) as client:
            return [project.model_dump() for project in client.projects.list()]
    except Exception as e:
        log.exception(f"Error listing ODK projects: {e}", stack_info=True)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing projects on ODK Central: {e}",
        ) from e


async def create_odk_project(
    name: str, odk_central: Optional[central_schemas.ODKCentral] = None
):
    """Create a project on a remote ODK Server.

    Appends Field-TM to the project name to help identify on shared servers.
    """
    try:
        project_name = f"Field-TM {name}"
        log.debug(f"Attempting ODKCentral project creation: {project_name}")
        async with central_deps.pyodk_client(odk_central) as client:
            response = client.session.post("projects", json={"name": project_name})
            if not response.ok:
                detail = response.text or "Could not authenticate to ODK Central."
                raise HTTPException(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=detail,
                )
            result = response.json()

        log.debug(f"ODK Central response: {result}")
        log.info(f"Project {name} available on the ODK Central server.")
        return result
    except Exception as e:
        log.exception(f"Error: {e}", stack_info=True)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating project on ODK Central: {e}",
        ) from e


async def delete_odk_project(
    project_id: int, odk_central: Optional[central_schemas.ODKCentral] = None
):
    """Delete a project from a remote ODK Server."""
    # FIXME: when a project is deleted from Central, we have to update the
    # external_project_id in the projects table
    try:
        async with central_deps.pyodk_client(odk_central) as client:
            response = client.session.delete(f"projects/{project_id}")
            response.raise_for_status()
            result = response
        log.info(f"Project {project_id} has been deleted from the ODK Central server.")
        return result
    except Exception:
        return "Could not delete project from central odk"


async def create_odk_xform(
    odk_id: int,
    xform_data: BytesIO,
    odk_credentials: Optional[central_schemas.ODKCentral],
) -> None:
    """Create an XForm on a remote ODK Central server.

    Args:
        odk_id (str): Project ID for ODK Central.
        xform_data (BytesIO): XForm data to set.
        odk_credentials (ODKCentral): Creds for ODK Central.

    Returns: None
    """
    try:
        form_definition: str | bytes = xform_data.getvalue()
        # pyodk validates bytes as XLS/XLSX only; XML must be passed as text.
        with suppress(UnicodeDecodeError):
            form_definition = form_definition.decode("utf-8")

        async with central_deps.pyodk_client(odk_credentials) as client:
            try:
                client.forms.create(
                    definition=form_definition,
                    project_id=odk_id,
                    ignore_warnings=True,
                )
            except PyODKError as e:
                if _is_duplicate_form_conflict(e):
                    log.info(
                        "Form already exists in ODK project %s; "
                        "treating upload as idempotent success.",
                        odk_id,
                    )
                    return
                raise
    except Exception as e:
        log.exception(f"Error: {e}", stack_info=True)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Failed to upload form to ODK Central: {e}"},
        ) from e


async def list_submissions(
    project_id: int,
    odk_central: Optional[central_schemas.ODKCentral] = None,
    form_id: Optional[str] = None,
):
    """List all submissions for a project, aggregated from associated users."""
    if not form_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="form_id is required to list submissions with pyodk.",
        )

    async with central_deps.pyodk_client(odk_central) as client:
        return [
            submission.model_dump()
            for submission in client.submissions.list(
                project_id=project_id,
                form_id=form_id,
            )
        ]


async def get_form_list(db: AsyncConnection) -> list:
    """Returns the list of {id:title} for XLSForms in the database."""
    try:
        return await DbTemplateXLSForm.all(db)
    except Exception as e:
        log.exception(f"Error: {e}", stack_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


async def read_and_test_xform(input_data: BytesIO) -> None:
    """Read and validate an XForm.

    Args:
        input_data (BytesIO): form to be tested.

    Returns:
        BytesIO: the converted XML representation of the XForm.
    """
    try:
        log.debug(
            f"Parsing XLSForm --> XML data: input type {type(input_data)} | "
            f"data length {input_data.getbuffer().nbytes}"
        )
        # NOTE pyxform.xls2xform.convert returns a ConvertResult object
        return BytesIO(xform_convert(input_data).xform.encode("utf-8"))
    except Exception as e:
        log.exception(f"Error: {e}", stack_info=True)
        msg = f"XLSForm is invalid: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=msg,
        ) from e


async def append_fields_to_user_xlsform(
    xlsform: BytesIO,
    form_name: str = "buildings",
    new_geom_type: Optional[DbGeomType] = DbGeomType.POLYGON,
    need_verification_fields: bool = True,
    mandatory_photo_upload: bool = False,
    default_language: str = "english",
    use_odk_collect: bool = False,
) -> tuple[str, BytesIO]:  # noqa: PLR0913
    """Helper to return the intermediate XLSForm prior to convert."""
    log.debug("Appending mandatory Field-TM fields to XLSForm")
    return await append_field_mapping_fields(
        xlsform,
        form_name=form_name,
        new_geom_type=new_geom_type,
        need_verification_fields=need_verification_fields,
        mandatory_photo_upload=mandatory_photo_upload,
        default_language=default_language,
        use_odk_collect=use_odk_collect,
    )


async def validate_and_update_user_xlsform(
    xlsform: BytesIO,
    default_language: str = "english",
    form_name: str = "buildings",
    new_geom_type: Optional[DbGeomType] = DbGeomType.POLYGON,
    need_verification_fields: bool = True,
    mandatory_photo_upload: bool = False,
    use_odk_collect: bool = False,
) -> BytesIO:  # noqa: PLR0913
    """Wrapper to append mandatory fields and validate user uploaded XLSForm."""
    xform_id, updated_file_bytes = await append_fields_to_user_xlsform(
        xlsform,
        form_name=form_name,
        new_geom_type=new_geom_type,
        need_verification_fields=need_verification_fields,
        mandatory_photo_upload=mandatory_photo_upload,
        default_language=default_language,
        use_odk_collect=use_odk_collect,
    )

    # Validate and return the form
    log.debug("Validating uploaded XLS form")
    return await read_and_test_xform(updated_file_bytes)


async def update_odk_central_xform(
    xform_id: str,
    odk_id: int,
    xlsform: BytesIO,
    odk_credentials: central_schemas.ODKCentral,
) -> None:
    """Update and publish the XForm for a project.

    Args:
        xform_id (str): The UUID of the existing XForm in ODK Central.
        odk_id (int): ODK Central form ID.
        xlsform (UploadFile): XForm data.
        odk_credentials (central_schemas.ODKCentral): ODK Central creds.

    Returns: None
    """
    xform_bytesio = await read_and_test_xform(xlsform)

    async with central_deps.pyodk_client(odk_credentials) as client:
        client.forms.update(
            project_id=odk_id,
            form_id=xform_id,
            definition=xform_bytesio.getvalue(),
        )


async def update_project_xlsform(
    db: AsyncConnection,
    project: DbProject,
    xlsform: BytesIO,
    xform_id: str,
):
    """Update both the ODK Central and FieldTM XLSForm."""
    # Update ODK Central form data
    await update_odk_central_xform(
        xform_id,
        project.external_project_id,
        xlsform,
        None,  # ODK credentials not stored on project, use env vars
    )

    await DbProject.update(
        db,
        project.id,
        project_schemas.ProjectUpdate(
            xlsform_content=xlsform.getvalue(),
        ),
    )
    await db.commit()


async def convert_geojson_to_odk_csv(
    input_geojson: BytesIO,
) -> StringIO:
    """Convert GeoJSON features to ODK CSV format.

    Used for form upload media (dataset) in ODK Central.

    Args:
        input_geojson (BytesIO): GeoJSON file to convert.

    Returns:
        feature_csv (StringIO): CSV of features in XLSForm format for ODK.
    """
    parsed_geojson = parse_aoi(settings.FMTM_DB_URL, input_geojson.getvalue())

    if not parsed_geojson:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Conversion GeoJSON --> CSV failed",
        )

    csv_buffer = StringIO()
    csv_writer = csv.writer(csv_buffer)

    header = ["osm_id", "tags", "version", "changeset", "timestamp", "geometry"]
    csv_writer.writerow(header)

    features = parsed_geojson.get("features", [])
    for feature in features:
        geometry = feature.get("geometry")
        javarosa_geom = await geojson_to_javarosa_geom(geometry)

        properties = feature.get("properties", {})
        osm_id = properties.get("osm_id")
        tags = properties.get("tags")
        version = properties.get("version")
        changeset = properties.get("changeset")
        timestamp = properties.get("timestamp")

        csv_row = [osm_id, tags, version, changeset, timestamp, javarosa_geom]
        csv_writer.writerow(csv_row)

    # Reset buffer position to start to .read() works
    csv_buffer.seek(0)

    return csv_buffer


def flatten_json(data: dict, target: dict):
    """Flatten json properties to a single level.

    Removes any existing GeoJSON data from captured GPS coordinates in
    ODK submission.

    Usage:
        new_dict = {}
        flatten_json(original_dict, new_dict)
    """
    for k, v in data.items():
        if isinstance(v, dict):
            if "type" in v and "coordinates" in v:
                # GeoJSON object found, skip it
                continue
            flatten_json(v, target)
        else:
            target[k] = v


async def convert_odk_submission_json_to_geojson(
    input_json: Union[BytesIO, list],
) -> geojson.FeatureCollection:
    """Convert ODK submission JSON file to GeoJSON.

    Used for loading into QGIS.

    Args:
        input_json (BytesIO): ODK JSON submission list.

    Returns:
        geojson (BytesIO): GeoJSON format ODK submission.
    """
    if isinstance(input_json, list):
        submission_json = input_json
    else:
        submission_json = json.loads(input_json.getvalue())

    if not submission_json:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Project contains no submissions yet",
        )

    all_features = []
    for submission in submission_json:
        # Remove unnecessary keys
        keys_to_remove = ["meta", "__id", "__system"]
        for key in keys_to_remove:
            submission.pop(key)

        # Ensure no nesting of the properties (flat struct)
        data = {}
        flatten_json(submission, data)

        # Process primary geometry
        geojson_geom = await javarosa_to_geojson_geom(data.pop("xlocation", {}))

        # Identify and process additional geometries
        additional_geometries = []
        for geom_field in list(data.keys()):
            if geom_field.endswith("_geom"):
                id_field = geom_field[:-5]  # Remove "_geom" suffix
                geom_data = data.pop(geom_field, {})

                # Convert geometry
                geom = await javarosa_to_geojson_geom(geom_data)

                feature = geojson.Feature(
                    id=data.get(id_field),
                    geometry=geom,
                    properties={
                        "is_additional_geom": True,
                        "id_field": id_field,
                        "geom_field": geom_field,
                    },
                )
                additional_geometries.append(feature)

        feature = geojson.Feature(
            id=data.get("xlocation"),
            geometry=geojson_geom,
            properties=data,
        )
        all_features.append(feature)
        all_features.extend(additional_geometries)

    return geojson.FeatureCollection(features=all_features)


async def feature_geojson_to_entity_dict(
    feature: geojson.Feature,
    additional_features: bool = False,
) -> central_schemas.EntityDict:
    """Convert a single GeoJSON to an Entity dict for upload."""
    if not isinstance(feature, (dict, geojson.Feature)):
        log.error(f"Feature not in correct format: {feature}")
        raise ValueError(f"Feature not in correct format: {type(feature)}")

    geometry = feature.get("geometry", {})
    if not geometry:
        msg = "'geometry' data field is mandatory"
        log.debug(msg)
        raise ValueError(msg)

    javarosa_geom = await geojson_to_javarosa_geom(geometry)
    raw_properties = feature.get("properties", {})
    properties = {
        central_schemas.sanitize_key(key): str(
            value
        )  # NOTE all properties MUST be string values for Entities
        for key, value in raw_properties.items()
        if central_schemas.is_valid_property_name(key)
    }
    if additional_features:
        entity_label = f"Additional Feature {uuid4()}"
    else:
        properties["status"] = "unmapped"
        feature_id = feature.get("id", None)
        entity_label = f"Feature {feature_id}"

    return {
        "label": entity_label,
        "data": {"geometry": javarosa_geom, **properties},
    }


async def task_geojson_dict_to_entity_values(
    task_geojson_dict: Union[dict[int, geojson.Feature], geojson.FeatureCollection],
    additional_features: bool = False,
) -> list[central_schemas.EntityDict]:
    """Convert a dict of task GeoJSONs into data for ODK Entity upload."""
    log.debug("Converting dict of task GeoJSONs to Entity upload format")

    asyncio_tasks = []

    if additional_features:
        features = task_geojson_dict.get("features", [])
        asyncio_tasks.extend(
            feature_geojson_to_entity_dict(feature, additional_features)
            for feature in features
            if feature
        )
    else:
        for geojson_dict in task_geojson_dict.values():
            features = geojson_dict.get("features", [])
            asyncio_tasks.extend(
                feature_geojson_to_entity_dict(feature)
                for feature in features
                if feature
            )

    return await gather(*asyncio_tasks)


def _build_entity_merge_rows(
    entities_list: Optional[list[central_schemas.EntityDict]],
) -> list[dict[str, str]]:
    """Flatten EntityDict payloads into pyodk merge rows."""
    if not entities_list:
        return []

    merge_rows = []
    for entity in entities_list:
        label = entity.get("label")
        if not label:
            continue

        data = entity.get("data") or {}
        merge_rows.append({"label": label, **data})

    return merge_rows


def _collect_required_property_keys(
    properties: list[str],
    merge_rows: list[dict[str, str]],
) -> set[str]:
    """Collect all dataset property keys required by the incoming rows."""
    required_keys = set(properties)
    for row in merge_rows:
        required_keys.update(key for key in row if key != "label")
    return required_keys


def _is_property_conflict(exc: Exception) -> bool:
    """Return True for duplicate-property conflicts from pyodk requests."""
    response = getattr(exc, "response", None)
    if getattr(response, "status_code", None) == status.HTTP_409_CONFLICT:
        return True

    msg = str(exc)
    return (
        "409 Client Error" in msg
        or "Status: 409" in msg
        or '"code":409' in msg
        or 'code":409' in msg
    )


def _is_entity_version_conflict(exc: PyODKError) -> bool:
    """Return True for entity update version conflicts."""
    msg = str(exc)
    return "Status: 409" in msg and "version" in msg


def _get_existing_dataset_property_names(
    client,
    project_id: int,
    dataset_name: str,
) -> set[str]:
    """Fetch existing dataset property names, tolerating lookup failures."""
    try:
        existing_properties = client.session.get(
            f"projects/{project_id}/datasets/{dataset_name}/properties"
        )
        if existing_properties.status_code < HTTP_ERROR_STATUS_CODE:
            return _extract_dataset_property_names(existing_properties.json())
        if existing_properties.status_code != status.HTTP_404_NOT_FOUND:
            existing_properties.raise_for_status()
    except Exception as exc:
        log.warning(
            "Could not list properties for dataset '%s' in ODK project %s: %s",
            dataset_name,
            project_id,
            exc,
        )

    return set()


def _ensure_dataset_properties(
    client,
    project_id: int,
    dataset_name: str,
    required_keys: set[str],
    existing_property_names: set[str],
) -> None:
    """Create any missing dataset properties required by the incoming rows."""
    for key in sorted(required_keys):
        if key in {"__id", "__system", "label"} or key in existing_property_names:
            continue

        try:
            create_property = client.session.post(
                f"projects/{project_id}/datasets/{dataset_name}/properties",
                json={"name": key},
            )
            if create_property.status_code == status.HTTP_409_CONFLICT:
                continue
            if create_property.status_code >= HTTP_ERROR_STATUS_CODE:
                create_property.raise_for_status()
        except Exception as exc:
            if _is_property_conflict(exc):
                continue
            raise


def _index_entities_by_label(entity_table: dict | list | None) -> dict[str, dict]:
    """Map existing dataset rows by label."""
    target_rows = (
        entity_table.get("value", []) if isinstance(entity_table, dict) else []
    )
    return {
        row.get("label"): row
        for row in target_rows
        if isinstance(row, dict) and row.get("label")
    }


def _get_entity_update_data(
    source_row: dict[str, str],
    target_row: dict,
) -> dict[str, str]:
    """Build the smallest update payload needed to align an existing entity."""
    update_data = {}
    for key, value in source_row.items():
        if key == "label":
            continue

        existing_value = target_row.get(key)
        if (existing_value is None and key not in target_row) or str(value) != str(
            existing_value
        ):
            update_data[key] = value

    return update_data


def _upsert_entity_rows(
    client,
    project_id: int,
    dataset_name: str,
    merge_rows: list[dict[str, str]],
) -> None:
    """Insert new entities and minimally update existing ones by label."""
    target_by_label = _index_entities_by_label(
        client.entities.get_table(entity_list_name=dataset_name, project_id=project_id)
    )

    to_insert = []
    for source_row in merge_rows:
        label = source_row.get("label")
        if not label:
            continue

        target_row = target_by_label.get(label)
        if not target_row:
            to_insert.append(source_row)
            continue

        update_data = _get_entity_update_data(source_row, target_row)
        if not update_data:
            continue

        try:
            client.entities.update(
                uuid=target_row["__id"],
                entity_list_name=dataset_name,
                project_id=project_id,
                label=label,
                data=update_data,
                base_version=target_row["__system"]["version"],
            )
        except PyODKError as exc:
            if _is_entity_version_conflict(exc):
                log.warning(
                    "Skipping Entity update due to version conflict for "
                    "label='%s' in dataset '%s' (ODK project %s): %s",
                    label,
                    dataset_name,
                    project_id,
                    exc,
                )
                continue
            raise

    if to_insert:
        client.entities.create_many(
            data=to_insert,
            entity_list_name=dataset_name,
            project_id=project_id,
            create_source="Field-TM",
            source_size=len(to_insert),
        )


async def create_entity_list(
    odk_creds: Optional[central_schemas.ODKCentral],
    odk_id: int,
    properties: list[str],
    dataset_name: str = "features",
    entities_list: list[central_schemas.EntityDict] = None,
) -> None:
    """Create a new Entity list (dataset) in ODK and upsert entities.

    Notes on implementation:
    - Dataset creation uses the async ODK client (`osm_fieldwork.OdkCentralAsync`)
      because it is already used elsewhere and is async-friendly.
    - Entity upsert uses **official `pyodk`** (sync) via `Client.entities.merge()` to
      provide idempotent behavior on retries (insert/update; optionally delete).
    """
    log.info("Creating ODK Entity properties list")
    properties = central_schemas.entity_fields_to_list(properties)
    merge_rows = _build_entity_merge_rows(entities_list)

    if odk_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ODK project_id is missing; cannot create/merge entity lists.",
        )

    async with central_deps.get_odk_dataset(odk_creds) as odk_central:
        # Step 1: ensure dataset exists (idempotent)
        dataset_exists = False
        try:
            datasets = await odk_central.listDatasets(odk_id)
            dataset_exists = any(
                ds.get("name") == dataset_name for ds in (datasets or [])
            )
        except Exception as exc:
            log.warning(f"Could not list datasets for ODK project {odk_id}: {exc}")

        if not dataset_exists:
            await odk_central.createDataset(
                odk_id, datasetName=dataset_name, properties=properties
            )
        else:
            log.info(
                f"Dataset '{dataset_name}' already exists "
                f"for ODK project {odk_id}; will reuse it."
            )

    if not merge_rows:
        return

    async with central_deps.pyodk_client(odk_creds) as client:
        pid = int(odk_id)
        required_keys = _collect_required_property_keys(properties, merge_rows)
        existing_property_names = _get_existing_dataset_property_names(
            client, pid, dataset_name
        )
        _ensure_dataset_properties(
            client,
            pid,
            dataset_name,
            required_keys,
            existing_property_names,
        )
        _upsert_entity_rows(client, pid, dataset_name, merge_rows)


async def create_entity(
    odk_creds: Optional[central_schemas.ODKCentral],
    entity_uuid: UUID,
    odk_id: int,
    properties: list[str],
    entity: central_schemas.EntityDict,
    dataset_name: str = "features",
) -> dict:  # noqa: PLR0913
    """Create a new Entity in ODK."""
    log.info(f"Creating ODK Entity in dataset '{dataset_name}' (ODK ID: {odk_id})")
    try:
        properties = central_schemas.entity_fields_to_list(properties)

        label = entity.get("label")
        data = entity.get("data")

        if not label or not data:
            log.error("Missing required entity fields: 'label' or 'data'")
            raise ValueError("Entity must contain 'label' and 'data' fields")

        async with central_deps.pyodk_client(odk_creds) as client:
            response = client.entities.create(
                label=label,
                data=data,
                entity_list_name=dataset_name,
                project_id=odk_id,
                uuid=str(entity_uuid),  # pyodk only accepts string UUID
            )

        log.info(f"Entity '{label}' successfully created in ODK")
        return response

    except Exception as e:
        log.exception(f"Failed to create entity in ODK: {str(e)}")
        raise


async def delete_entity(
    odk_creds: central_schemas.ODKCentral,
    odk_id: int,
    entity_uuid: UUID,
    dataset_name: str = "features",
) -> None:
    """Delete an Entity in ODK."""
    log.info(f"Deleting ODK Entity in dataset '{dataset_name}' (ODK ID: {odk_id})")
    try:
        async with central_deps.pyodk_client(odk_creds) as client:
            client.entities.delete(
                uuid=str(entity_uuid),
                entity_list_name=dataset_name,
                project_id=odk_id,
            )
        log.info(f"Entity {entity_uuid} successfully deleted from ODK")

    except Exception as e:
        log.exception(f"Failed to delete entity {entity_uuid} in ODK: {str(e)}")
        raise


async def get_appuser_token(
    xform_id: str,
    project_odk_id: int,
    odk_credentials: Optional[central_schemas.ODKCentral],
):
    """Get the app user token for a specific project.

    Args:
        odk_credentials: ODK credentials for the project.
        project_odk_id: The ODK ID of the project.
        xform_id: The ID of the XForm.

    Returns:
        The app user token.
    """
    try:
        appuser_name = "fmtm_user"
        log.info(
            f"Creating ODK appuser ({appuser_name}) for ODK project ({project_odk_id})"
        )
        async with central_deps.pyodk_client(odk_credentials) as client:
            app_user_response = client.session.post(
                f"projects/{project_odk_id}/app-users",
                json={"displayName": appuser_name},
            )
            app_user_response.raise_for_status()
            app_user = app_user_response.json()
            appuser_token = app_user.get("token")
            appuser_sub = app_user.get("id")

            if not appuser_token or not appuser_sub:
                msg = "Could not generate token for app user."
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=msg,
                )

            _assign_appuser_role(
                client,
                f"projects/{project_odk_id}/assignments/2/{appuser_sub}",
                "project",
            )
            _assign_appuser_role(
                client,
                f"projects/{project_odk_id}/forms/{xform_id}/assignments/2/{appuser_sub}",
                "form",
            )

        if odk_credentials and getattr(
            odk_credentials, "external_project_instance_url", None
        ):
            odk_url = odk_credentials.external_project_instance_url
        else:
            odk_url = str(
                settings.ODK_CENTRAL_PUBLIC_URL or settings.ODK_CENTRAL_URL or ""
            ).rstrip("/")

        return f"{odk_url}/v1/key/{appuser_token}/projects/{project_odk_id}"

    except PyODKError as e:
        log.exception(f"PyODK error while creating app user token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the app user token.",
        ) from e
    except Exception as e:
        log.exception(f"An error occurred: {str(e)}", stack_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the app user token.",
        ) from e


def _assign_appuser_role(client, path: str, scope: str) -> None:
    """Assign an app-user role and validate the ODK response."""
    assignment_response = client.session.post(path)
    assignment_response.raise_for_status()
    assignment_result = assignment_response.json()
    if assignment_result.get("success"):
        return

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"Could not assign {scope} role to app user.",
    )


def _build_manager_user_email(project_odk_id: int) -> str:
    """Create the default manager email for a project."""
    return f"fmtm-manager-{project_odk_id}@example.org"


def _build_manager_user_password() -> str:
    """Generate a strong password for generated Central web users."""
    # Keep to alphanumeric for widest compatibility across Central deployments.
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(20))


def _build_manager_user_email_fallback(project_odk_id: int) -> str:
    """Create a fallback manager email variant when the primary is already taken."""
    suffix = secrets.token_hex(4)
    return f"fmtm-manager-{project_odk_id}-{suffix}@example.org"


def _get_project_manager_role_id(client) -> int:
    """Resolve the ODK Central Project Manager role id."""
    roles_response = client.session.get("roles")
    roles_response.raise_for_status()

    roles = roles_response.json() or []
    project_manager_role = next(
        (
            role
            for role in roles
            if str(role.get("name", "")).strip().lower() == "project manager"
        ),
        None,
    )
    if not project_manager_role or "id" not in project_manager_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not find 'Project Manager' role in ODK Central.",
        )

    return int(project_manager_role["id"])


def _create_manager_user(client, project_odk_id: int) -> tuple[object, str, str]:
    """Create a manager user, retrying once with a randomized email on conflict."""
    for candidate_email in (
        _build_manager_user_email(project_odk_id),
        _build_manager_user_email_fallback(project_odk_id),
    ):
        candidate_password = _build_manager_user_password()
        create_response = client.session.post(
            "users",
            json={"email": candidate_email, "password": candidate_password},
        )
        create_status = getattr(create_response, "status_code", status.HTTP_200_OK)

        if create_status < HTTP_ERROR_STATUS_CODE:
            created_user = create_response.json() or {}
            created_user_id = created_user.get("id")
            if not created_user_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="ODK Central returned no user ID after creation.",
                )
            return created_user_id, candidate_email, candidate_password

        if create_status == status.HTTP_409_CONFLICT:
            log.info(
                "Manager email %s already exists in ODK Central; "
                "trying fallback address.",
                candidate_email,
            )
            continue

        body = getattr(create_response, "text", "")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"ODK Central returned {create_status} when creating "
                f"manager user. Body: {body}"
            ),
        )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=(
            "Could not create an ODK Central manager user: "
            "both primary and fallback email addresses are already taken."
        ),
    )


def _set_manager_user_display_name(
    client,
    manager_user_id: object,
    display_name: str,
    project_odk_id: int,
) -> None:
    """Set a human-readable display name; failures are non-fatal."""
    display_name_response = client.session.patch(
        f"users/{manager_user_id}",
        json={"displayName": display_name},
    )
    if (
        getattr(display_name_response, "status_code", status.HTTP_200_OK)
        < HTTP_ERROR_STATUS_CODE
    ):
        return

    log.warning(
        "Could not set display name for manager user %s on ODK project %s.",
        manager_user_id,
        project_odk_id,
    )


def _assign_manager_user_to_project(
    client,
    project_odk_id: int,
    role_id: int,
    manager_user_id: object,
) -> None:
    """Assign the Project Manager role to the created Central user."""
    assignment_response = client.session.post(
        f"projects/{project_odk_id}/assignments/{role_id}/{manager_user_id}",
    )
    assignment_status = getattr(assignment_response, "status_code", status.HTTP_200_OK)
    if assignment_status == status.HTTP_409_CONFLICT:
        log.info(
            "Manager user %s already assigned to ODK project %s.",
            manager_user_id,
            project_odk_id,
        )
        return

    if assignment_status >= HTTP_ERROR_STATUS_CODE:
        assignment_response.raise_for_status()


async def create_project_manager_user(
    project_odk_id: int,
    project_name: str,
    odk_credentials: Optional[central_schemas.ODKCentral],
) -> tuple[str, str]:
    """Create a Central web user scoped to one project as Project Manager.

    The user is created with email + password so they can log directly into
    the ODK Central UI.  Credentials are returned once and never stored.

    ODK Central sends a welcome email on creation; a local mail-catcher
    (the 'mail' service) must be reachable in development so that delivery
    does not fail.  In production point EMAIL_HOST / EMAIL_PORT at a real
    SMTP server via environment variables.

    Returns:
        tuple[str, str]: (manager_email, manager_password)
    """
    try:
        async with central_deps.pyodk_client(odk_credentials) as client:
            role_id = _get_project_manager_role_id(client)
            display_name = f"FMTM Manager - {project_name}"
            manager_user_id, manager_email, manager_password = _create_manager_user(
                client,
                project_odk_id,
            )
            _set_manager_user_display_name(
                client,
                manager_user_id,
                display_name,
                project_odk_id,
            )
            _assign_manager_user_to_project(
                client,
                project_odk_id,
                role_id,
                manager_user_id,
            )

            log.info(
                "Created ODK Central manager user %s for project %s.",
                manager_email,
                project_odk_id,
            )
            return manager_email, manager_password

    except HTTPException:
        raise
    except Exception as e:
        log.exception(
            "Failed to create project manager user for ODK project %s.",
            project_odk_id,
            stack_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create ODK Central manager user.",
        ) from e


async def upload_form_media(
    xform_id: str,
    project_odk_id: int,
    odk_credentials: central_schemas.ODKCentral,
    media_attachments: dict[str, BytesIO],
):
    """Upload form media attachments to ODK."""
    attachment_filepaths = []

    # Write all uploaded data to temp files for upload (required by PyODK)
    # We must use TemporaryDir and preserve the uploaded file names
    with TemporaryDirectory() as temp_dir:
        for file_name, file_data in media_attachments.items():
            temp_path = Path(temp_dir) / file_name
            with open(temp_path, "wb") as temp_file:
                temp_file.write(file_data.getvalue())
            attachment_filepaths.append(temp_path)

        async with central_deps.pyodk_client(odk_credentials) as client:
            return client.forms.update(
                project_id=project_odk_id,
                form_id=xform_id,
                attachments=attachment_filepaths,
            )


async def get_form_media(
    xform_id: str,
    project_odk_id: int,
    odk_credentials: central_schemas.ODKCentral,
):
    """Get a list of form media attachments with their URLs."""
    async with central_deps.get_async_odk_form(odk_credentials) as async_odk_form:
        form_attachment_urls = await async_odk_form.getFormAttachmentUrls(
            project_odk_id,
            xform_id,
        )

    # Remove any entries where the value is None
    form_attachment_urls = {
        filename: url
        for filename, url in form_attachment_urls.items()
        if url is not None
    }

    if settings.DEBUG:
        form_attachment_urls = {
            filename: strip_presigned_url_for_local_dev(url)
            for filename, url in form_attachment_urls.items()
        }

    return form_attachment_urls


async def list_form_media(
    xform_id: str,
    project_odk_id: int,
    odk_credentials: central_schemas.ODKCentral,
) -> list[dict]:
    """Return a list of form media required for upload.

    Format:
        [
            {'name': '1731673738156.jpg', 'exists': False},
        ]
    """
    async with central_deps.get_async_odk_form(odk_credentials) as async_odk_form:
        return await async_odk_form.listFormAttachments(
            project_odk_id,
            xform_id,
        )


async def odk_credentials_test(odk_creds: central_schemas.ODKCentral):
    """Test ODK Central credentials by attempting to open a session.

    Returns status 200 if credentials are valid, otherwise raises HTTPException.
    """
    try:
        async with central_deps.get_odk_dataset(odk_creds):
            pass
        return status.HTTP_200_OK
    except HTTPException as e:
        log.error(f"ODK Central credential test failed: {e.detail}")
        raise
    except Exception as e:
        log.error(f"Unexpected error during ODK Central credential test: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while testing ODK Central credentials.",
        ) from e
