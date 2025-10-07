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
from asyncio import gather
from datetime import datetime
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Union
from uuid import UUID, uuid4

import geojson
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from loguru import logger as log
from osm_fieldwork.OdkCentral import OdkAppUser, OdkForm, OdkProject
from osm_fieldwork.update_xlsform import append_field_mapping_fields
from psycopg import Connection
from pyodk._endpoints.entities import Entity
from pyxform.xls2xform import convert as xform_convert

from app.central import central_deps, central_schemas
from app.config import settings
from app.db.enums import DbGeomType, EntityState, HTTPStatus
from app.db.models import DbProject, DbXLSForm
from app.db.postgis_utils import (
    geojson_to_javarosa_geom,
    javarosa_to_geojson_geom,
    parse_geojson_file_to_featcol,
)
from app.projects import project_schemas
from app.s3 import strip_presigned_url_for_local_dev


def get_odk_project(odk_central: Optional[central_schemas.ODKCentralDecrypted] = None):
    """Helper function to get the OdkProject with credentials."""
    if odk_central:
        url = odk_central.odk_central_url
        user = odk_central.odk_central_user
        pw = odk_central.odk_central_password
    else:
        log.debug("ODKCentral connection variables not set in function")
        log.debug("Attempting extraction from environment variables")
        url = settings.ODK_CENTRAL_URL
        user = settings.ODK_CENTRAL_USER
        pw = (
            settings.ODK_CENTRAL_PASSWD.get_secret_value()
            if settings.ODK_CENTRAL_PASSWD
            else ""
        )

    try:
        log.debug(f"Connecting to ODKCentral: url={url} user={user}")
        project = OdkProject(url, user, pw)

    except ValueError as e:
        log.error(e)
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=(
                "ODK credentials are invalid, or may have been updated. "
                "Please update them."
            ),
        ) from e
    except Exception as e:
        log.exception(f"Error: {e}", stack_info=True)
        raise HTTPException(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Error creating project on ODK Central: {e}",
        ) from e

    return project


def get_odk_form(odk_central: central_schemas.ODKCentralDecrypted):
    """Helper function to get the OdkForm with credentials."""
    url = odk_central.odk_central_url
    user = odk_central.odk_central_user
    pw = odk_central.odk_central_password

    try:
        log.debug(f"Connecting to ODKCentral: url={url} user={user}")
        form = OdkForm(url, user, pw)
    except Exception as e:
        log.exception(f"Error: {e}", stack_info=True)
        raise HTTPException(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Error creating project on ODK Central: {e}",
        ) from e

    return form


def get_odk_app_user(odk_central: Optional[central_schemas.ODKCentralDecrypted] = None):
    """Helper function to get the OdkAppUser with credentials."""
    if odk_central:
        url = odk_central.odk_central_url
        user = odk_central.odk_central_user
        pw = odk_central.odk_central_password
    else:
        log.debug("ODKCentral connection variables not set in function")
        log.debug("Attempting extraction from environment variables")
        url = settings.ODK_CENTRAL_URL
        user = settings.ODK_CENTRAL_USER
        pw = (
            settings.ODK_CENTRAL_PASSWD.get_secret_value()
            if settings.ODK_CENTRAL_PASSWD
            else ""
        )

    try:
        log.debug(f"Connecting to ODKCentral: url={url} user={user}")
        form = OdkAppUser(url, user, pw)
    except Exception as e:
        log.exception(f"Error: {e}", stack_info=True)
        raise HTTPException(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Error creating project on ODK Central: {e}",
        ) from e

    return form


def list_odk_projects(
    odk_central: Optional[central_schemas.ODKCentralDecrypted] = None,
):
    """List all projects on a remote ODK Server."""
    project = get_odk_project(odk_central)
    return project.listProjects()


def create_odk_project(
    name: str, odk_central: Optional[central_schemas.ODKCentralDecrypted] = None
):
    """Create a project on a remote ODK Server.

    Appends Field-TM to the project name to help identify on shared servers.
    """
    project = get_odk_project(odk_central)

    try:
        log.debug(f"Attempting ODKCentral project creation: Field-TM {name}")
        result = project.createProject(f"Field-TM {name}")

        # Sometimes createProject returns a list if fails
        if isinstance(result, dict):
            if result.get("code") == 401.2:
                raise HTTPException(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    detail="Could not authenticate to odk central.",
                )

        log.debug(f"ODKCentral response: {result}")
        log.info(f"Project {name} available on the ODK Central server.")
        return result
    except Exception as e:
        log.exception(f"Error: {e}", stack_info=True)
        raise HTTPException(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Error creating project on ODK Central: {e}",
        ) from e


async def delete_odk_project(
    project_id: int, odk_central: Optional[central_schemas.ODKCentralDecrypted] = None
):
    """Delete a project from a remote ODK Server."""
    # FIXME: when a project is deleted from Central, we have to update the
    # odkid in the projects table
    try:
        project = get_odk_project(odk_central)
        result = project.deleteProject(project_id)
        log.info(f"Project {project_id} has been deleted from the ODK Central server.")
        return result
    except Exception:
        return "Could not delete project from central odk"


def create_odk_xform(
    odk_id: int,
    xform_data: BytesIO,
    odk_credentials: central_schemas.ODKCentralDecrypted,
) -> None:
    """Create an XForm on a remote ODK Central server.

    Args:
        odk_id (str): Project ID for ODK Central.
        xform_data (BytesIO): XForm data to set.
        odk_credentials (ODKCentralDecrypted): Creds for ODK Central.

    Returns: None
    """
    try:
        xform = get_odk_form(odk_credentials)
    except Exception as e:
        log.exception(f"Error: {e}", stack_info=True)
        raise HTTPException(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            detail={"message": "Connection failed to odk central"},
        ) from e

    xform.createForm(odk_id, xform_data, publish=True)


def list_submissions(
    project_id: int, odk_central: Optional[central_schemas.ODKCentralDecrypted] = None
):
    """List all submissions for a project, aggregated from associated users."""
    project = get_odk_project(odk_central)
    xform = get_odk_form(odk_central)
    submissions = list()
    for user in project.listAppUsers(project_id):
        for subm in xform.listSubmissions(project_id, user["displayName"]):
            submissions.append(subm)

    return submissions


async def get_form_list(db: Connection) -> list:
    """Returns the list of {id:title} for XLSForms in the database."""
    try:
        return await DbXLSForm.all(db)
    except Exception as e:
        log.exception(f"Error: {e}", stack_info=True)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
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
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg
        ) from e


def get_project_form_xml(
    odk_creds: central_schemas.ODKCentralDecrypted, odkid: int, odk_form_id: str
) -> str:
    """Get the XForm from ODK Central as raw XML."""
    xform = get_odk_form(odk_creds)
    return xform.getXml(odkid, odk_form_id)


async def append_fields_to_user_xlsform(
    xlsform: BytesIO,
    form_name: str = "buildings",
    new_geom_type: Optional[DbGeomType] = DbGeomType.POLYGON,
    need_verification_fields: bool = True,
    mandatory_photo_upload: bool = False,
    use_odk_collect: bool = False,
) -> tuple[str, BytesIO]:
    """Helper to return the intermediate XLSForm prior to convert."""
    log.debug("Appending mandatory Field-TM fields to XLSForm")
    return await append_field_mapping_fields(
        xlsform,
        form_name=form_name,
        new_geom_type=new_geom_type,
        need_verification_fields=need_verification_fields,
        mandatory_photo_upload=mandatory_photo_upload,
        use_odk_collect=use_odk_collect,
    )


async def validate_and_update_user_xlsform(
    xlsform: BytesIO,
    form_name: str = "buildings",
    new_geom_type: Optional[DbGeomType] = DbGeomType.POLYGON,
    need_verification_fields: bool = True,
    mandatory_photo_upload: bool = False,
    use_odk_collect: bool = False,
) -> BytesIO:
    """Wrapper to append mandatory fields and validate user uploaded XLSForm."""
    xform_id, updated_file_bytes = await append_fields_to_user_xlsform(
        xlsform,
        form_name=form_name,
        new_geom_type=new_geom_type,
        need_verification_fields=need_verification_fields,
        mandatory_photo_upload=mandatory_photo_upload,
        use_odk_collect=use_odk_collect,
    )

    # Validate and return the form
    log.debug("Validating uploaded XLS form")
    return await read_and_test_xform(updated_file_bytes)


async def update_odk_central_xform(
    xform_id: str,
    odk_id: int,
    xlsform: BytesIO,
    # osm_category: str,
    odk_credentials: central_schemas.ODKCentralDecrypted,
) -> None:
    """Update and publish the XForm for a project.

    Args:
        xform_id (str): The UUID of the existing XForm in ODK Central.
        odk_id (int): ODK Central form ID.
        xlsform (UploadFile): XForm data.
        odk_credentials (central_schemas.ODKCentralDecrypted): ODK Central creds.

    Returns: None
    """
    xform_bytesio = await read_and_test_xform(xlsform)

    xform_obj = get_odk_form(odk_credentials)

    # NOTE calling createForm for an existing form will update it
    xform_obj.createForm(
        odk_id,
        xform_bytesio,
        # NOTE this variable is incorrectly named and should be form_id
        form_name=xform_id,
    )
    # The draft form must be published after upload
    # NOTE we can't directly publish existing forms
    # in createForm and need 2 steps
    xform_obj.publishForm(odk_id, xform_id)


async def update_project_xlsform(
    db: Connection,
    project: DbProject,
    xlsform: BytesIO,
    xform_id: str,
):
    """Update both the ODK Central and FieldTM XLSForm."""
    # Update ODK Central form data
    await update_odk_central_xform(
        xform_id,
        project.odkid,
        xlsform,
        project.odk_credentials,
    )
    form_xml = await run_in_threadpool(
        get_project_form_xml,
        project.odk_credentials,
        project.odkid,
        xform_id,
    )

    await DbProject.update(
        db,
        project.id,
        project_schemas.ProjectUpdate(
            xlsform_content=xlsform.getvalue(),
            odk_form_xml=form_xml,
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
    parsed_geojson = parse_geojson_file_to_featcol(input_geojson.getvalue())

    if not parsed_geojson:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
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
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
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
        properties["status"] = "0"
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


async def create_entity_list(
    odk_creds: central_schemas.ODKCentralDecrypted,
    odk_id: int,
    properties: list[str],
    dataset_name: str = "features",
    entities_list: list[central_schemas.EntityDict] = None,
) -> None:
    """Create a new Entity list in ODK."""
    log.info("Creating ODK Entity properties list")
    properties = central_schemas.entity_fields_to_list(properties)

    async with central_deps.get_odk_dataset(odk_creds) as odk_central:
        # Step 1: create the Entity list, with properties
        await odk_central.createDataset(
            odk_id, datasetName=dataset_name, properties=properties
        )
        # Step 2: populate the Entities
        if entities_list:
            log.debug(f"Creating project ODK entities for dataset: {dataset_name}")
            await odk_central.createEntities(
                odk_id,
                dataset_name,
                entities_list,
            )


async def create_entity(
    odk_creds: central_schemas.ODKCentralDecrypted,
    entity_uuid: UUID,
    odk_id: int,
    properties: list[str],
    entity: central_schemas.EntityDict,
    dataset_name: str = "features",
) -> Entity:
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
    odk_creds: central_schemas.ODKCentralDecrypted,
    odk_id: int,
    entity_uuid: UUID,
    dataset_name: str = "features",
) -> bool:
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


async def get_entities_geojson(
    odk_creds: central_schemas.ODKCentralDecrypted,
    odk_id: int,
    dataset_name: str = "features",
    minimal: Optional[bool] = False,
) -> geojson.FeatureCollection:
    """Get the Entity details for a dataset / Entity list.

    Uses the OData endpoint from ODK Central.

    Currently it is not possible to filter via OData filters on custom params.
    TODO in the future filter by task_id via the URL,
    instead of returning all and filtering.

    Response GeoJSON format:
    {
        "type": "FeatureCollection",
        "features": [
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [xxx]
            },
            "id": uuid_of_entity,
            "properties": {
                "updated_at": "2024-04-11T18:23:30.787Z",
                "project_id": "1",
                "task_id": "1",
                "osm_id": "2",
                "tags": "xxx",
                "version": "1",
                "changeset": "1",
                "timestamp": "2024-12-20",
                "status": "LOCKED_FOR_MAPPING"
            }
        ]
    }


    Response GeoJSON format, minimal:
    {
        "type": "FeatureCollection",
        "features": [
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [xxx]
            },
            "id": uuid_of_entity,
            "properties": {
                "osm_id": "0044554",
                "updated_at": "2024-04-11T18:23:30.787Z",
                "status": "LOCKED_FOR_MAPPING"
            }
        ]
    }

    Args:
        odk_creds (ODKCentralDecrypted): ODK credentials for a project.
        odk_id (str): The project ID in ODK Central.
        dataset_name (str): The dataset / Entity list name in ODK Central.
        minimal (bool): Remove all fields apart from id, updated_at, and status.

    Returns:
        dict: Entity data in OData JSON format.
    """
    async with central_deps.get_odk_dataset(odk_creds) as odk_central:
        entities = await odk_central.getEntityData(
            odk_id,
            dataset_name,
            url_params="$select=__id, __system/updatedAt, geometry, osm_id, status"
            if minimal
            else None,
        )

    all_features = []
    for entity in entities:
        flattened_dict = {}
        flatten_json(entity, flattened_dict)

        javarosa_geom = flattened_dict.pop("geometry") or ""
        geojson_geom = await javarosa_to_geojson_geom(javarosa_geom)

        feature = geojson.Feature(
            geometry=geojson_geom,
            id=flattened_dict.pop("__id"),
            properties=flattened_dict,
        )
        all_features.append(feature)

    return geojson.FeatureCollection(features=all_features)


async def get_entities_data(
    odk_creds: central_schemas.ODKCentralDecrypted,
    odk_id: int,
    dataset_name: str = "features",
    fields: str = (
        "__system/updatedAt, osm_id, status, task_id, submission_ids, "
        "geometry, created_by"
    ),
    filter_date: Optional[datetime] = None,
) -> list:
    """Get all the entity mapping statuses.

    No geometries are included.

    Args:
        odk_creds (ODKCentralDecrypted): ODK credentials for a project.
        odk_id (str): The project ID in ODK Central.
        dataset_name (str): The dataset / Entity list name in ODK Central.
        fields (str): Extra fields to include in $select filter.
            __id is included by default.
        filter_date (datetime): Filter entities last updated after this date.

    Returns:
        list: JSON list containing Entity info. If updated_at is included,
            the format is string 2022-01-31T23:59:59.999Z.
    """
    try:
        url_params = f"$select=__id{',' if fields else ''} {fields}"

        filters = []
        if filter_date:
            filters.append(f"__system/updatedAt gt {filter_date}")
        if filters:
            url_params += f"&$filter={' and '.join(filters)}"
        async with central_deps.get_odk_dataset(odk_creds) as odk_central:
            entities = await odk_central.getEntityData(
                odk_id,
                dataset_name,
                url_params=url_params,
            )
    except Exception as e:
        log.exception(f"Error: {e}", stack_info=True)
        msg = f"Getting entity data failed for ODK project ({odk_id})"
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=msg,
        ) from e

    all_entities = []
    for entity in entities:
        flattened_dict = {}
        flatten_json(entity, flattened_dict)

        # Rename '__id' to 'id'
        flattened_dict["id"] = flattened_dict.pop("__id")

        all_entities.append(flattened_dict)

    return all_entities


def entity_to_flat_dict(
    entity: dict,
    odk_id: int,
    entity_uuid: str,
    dataset_name: str = "features",
) -> dict:
    """Convert returned Entity from ODK Central to flattened dict."""
    if not entity:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=(
                f"Entity ({entity_uuid}) not found in ODK project ({odk_id}) "
                f"and dataset ({dataset_name})"
            ),
        )

    # Remove dataReceived if present to avoid conflict with currentVersion
    current_version = entity.get("currentVersion")
    if isinstance(current_version, dict):
        current_version.pop("dataReceived", None)

    flattened_dict = {}
    flatten_json(entity, flattened_dict)

    # Rename 'uuid' to 'id'
    flattened_dict["id"] = flattened_dict.pop("uuid")

    return flattened_dict


async def get_entity_mapping_status(
    odk_creds: central_schemas.ODKCentralDecrypted,
    odk_id: int,
    entity_uuid: str,
    dataset_name: str = "features",
) -> dict:
    """Get an single entity mapping status.

    No geometries are included.

    Args:
        odk_creds (ODKCentralDecrypted): ODK credentials for a project.
        odk_id (str): The project ID in ODK Central.
        dataset_name (str): The dataset / Entity list name in ODK Central.
        entity_uuid (str): The unique entity UUID for ODK Central.

    Returns:
        dict: JSON containing Entity: id, status, updated_at.
            updated_at is in string format 2022-01-31T23:59:59.999Z.
    """
    async with central_deps.get_odk_dataset(odk_creds) as odk_central:
        entity = await odk_central.getEntity(
            odk_id,
            dataset_name,
            entity_uuid,
        )
    return entity_to_flat_dict(entity, odk_id, entity_uuid, dataset_name)


async def update_entity_mapping_status(
    odk_creds: central_schemas.ODKCentralDecrypted,
    odk_id: int,
    entity_uuid: str,
    label: str,
    status: EntityState,
    submission_ids: Optional[str] = None,
    dataset_name: str = "features",
) -> dict:
    """Update the Entity mapping status.

    This includes both the 'label' and 'status' data field.

    Args:
        odk_creds (ODKCentralDecrypted): ODK credentials for a project.
        odk_id (str): The project ID in ODK Central.
        entity_uuid (str): The unique entity UUID for ODK Central.
        label (str): New label, with emoji prepended for status.
        status (EntityState): New EntityState to assign, in string form.
        submission_ids (str): UUID (instanceID) of each submission.
        dataset_name (str): Override the default dataset / Entity list name 'features'.

    Returns:
        dict: All Entity data in OData JSON format.
    """
    async with central_deps.pyodk_client(odk_creds) as client:
        updated_entity = client.entities.update(
            entity_uuid,
            entity_list_name=dataset_name,
            project_id=odk_id,
            label=label,
            data={"status": status, "submission_ids": submission_ids}
            if submission_ids
            else {
                "status": status,
            },
            # We don't know the current entity version, so we need this
            force=True,
        )
        entity_dict = updated_entity.model_dump()
    return entity_to_flat_dict(entity_dict, odk_id, entity_uuid, dataset_name)


# FIXME replace osm_fieldwork.CSVDump with osm_fieldwork.ODKParsers
# def convert_csv(
#     filespec: str,
#     data: bytes,
# ):
#     """Convert ODK CSV to OSM XML and GeoJson."""
#     csvin = CSVDump("/xforms.yaml")

#     osmoutfile = f"{filespec}.osm"
#     csvin.createOSM(osmoutfile)

#     jsonoutfile = f"{filespec}.geojson"
#     csvin.createGeoJson(jsonoutfile)

#     if len(data) == 0:
#         log.debug("Parsing csv file %r" % filespec)
#         # The yaml file is in the package files for osm_fieldwork
#         data = csvin.parse(filespec)
#     else:
#         csvdata = csvin.parse(filespec, data)
#         for entry in csvdata:
#             log.debug(f"Parsing csv data {entry}")
#             if len(data) <= 1:
#                 continue
#             feature = csvin.createEntry(entry)
#             # Sometimes bad entries, usually from debugging XForm design, sneak in
#             if len(feature) > 0:
#                 if "tags" not in feature:
#                     log.warning("Bad record! %r" % feature)
#                 else:
#                     if "lat" not in feature["attrs"]:
#                         import epdb

#                         epdb.st()
#                     csvin.writeOSM(feature)
#                     # This GeoJson file has all the data values
#                     csvin.writeGeoJson(feature)
#                     pass

#     csvin.finishOSM()
#     csvin.finishGeoJson()

#     return True


async def get_appuser_token(
    xform_id: str,
    project_odk_id: int,
    odk_credentials: central_schemas.ODKCentralDecrypted,
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
        appuser = get_odk_app_user(odk_credentials)
        odk_project = get_odk_project(odk_credentials)
        odk_app_user = odk_project.listAppUsers(project_odk_id)
        log.debug(f"Current project appusers in ODK: {odk_app_user}")

        # delete if app_user already exists
        if odk_app_user:
            app_user_sub = odk_app_user[0].get("id")
            log.debug(f"Removing existing appuser: {app_user_sub}")
            appuser.delete(project_odk_id, app_user_sub)

        # create new app_user
        appuser_name = "fmtm_user"
        log.info(
            f"Creating ODK appuser ({appuser_name}) for ODK project ({project_odk_id})"
        )
        appuser_json = appuser.create(project_odk_id, appuser_name)
        appuser_token = appuser_json.get("token")
        appuser_sub = appuser_json.get("id")

        odk_url = odk_credentials.odk_central_url

        # Update the user role for the created xform
        log.info("Updating XForm role for appuser in ODK Central")
        response = appuser.updateRole(
            projectId=project_odk_id,
            xform=xform_id,
            actorId=appuser_sub,
        )
        if not response.ok:
            try:
                json_data = response.json()
                log.error(f"Error updating XForm role {json_data}")
            except json.decoder.JSONDecodeError:
                log.error(
                    "Could not parse response json during appuser update. "
                    f"status_code={response.status_code}"
                )
            finally:
                msg = f"Failed to update appuser for formId: ({xform_id})"
                log.error(msg)
                raise HTTPException(
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg
                ) from None
        return f"{odk_url}/v1/key/{appuser_token}/projects/{project_odk_id}"

    except Exception as e:
        log.exception(f"An error occurred: {str(e)}", stack_info=True)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the app user token.",
        ) from e


async def upload_form_media(
    xform_id: str,
    project_odk_id: int,
    odk_credentials: central_schemas.ODKCentralDecrypted,
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
    odk_credentials: central_schemas.ODKCentralDecrypted,
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
    odk_credentials: central_schemas.ODKCentralDecrypted,
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
        return HTTPStatus.OK
    except HTTPException as e:
        log.error(f"ODK Central credential test failed: {e.detail}")
        raise
    except Exception as e:
        log.error(f"Unexpected error during ODK Central credential test: {str(e)}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Unexpected error while testing ODK Central credentials.",
        ) from e
