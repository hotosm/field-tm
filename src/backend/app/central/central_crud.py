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

import logging
import re
import secrets
import string
from asyncio import gather, to_thread
from contextlib import suppress
from io import BytesIO
from typing import Optional, Union
from uuid import uuid4

import pandas as pd
from litestar import status_codes as status
from osm_fieldwork.enums import NewPointCapture
from osm_fieldwork.update_xlsform import append_field_mapping_fields
from psycopg import AsyncConnection
from pyodk.errors import PyODKError
from pyxform.xls2xform import convert as xform_convert
from requests import RequestException

from app.central import central_deps, central_schemas
from app.config import settings
from app.db.enums import DbGeomType
from app.db.models import DbTemplateXLSForm
from app.errors import (
    ServiceError,
    UnprocessableError,
    ValidationError,
)
from app.helpers.geometry_utils import (
    geojson_to_javarosa_geom,
)
from app.i18n import _

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
                raise ServiceError(detail)
            result = response.json()

        log.debug(f"ODK Central response: {result}")
        log.info(f"Project {name} available on the ODK Central server.")
        return result
    except Exception as e:
        log.exception(f"Error: {e}", stack_info=True)
        raise ServiceError(
            _("Error creating project on ODK Central: %(error)s") % {"error": e}
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
    """Create an XForm on a remote ODK Central server."""
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
        raise ServiceError(
            _("Failed to upload form to ODK Central: %(error)s") % {"error": e}
        ) from e


async def update_odk_xform(
    odk_id: int,
    xform_id: str,
    xform_data: BytesIO,
    odk_credentials: Optional[central_schemas.ODKCentral],
) -> None:
    """Publish a new version of an existing XForm on ODK Central."""
    try:
        async with central_deps.pyodk_client(odk_credentials) as client:
            client.forms.update(
                form_id=xform_id,
                project_id=odk_id,
                definition=xform_data.getvalue().decode("utf-8"),
            )
    except Exception as e:
        log.exception(f"Error: {e}", stack_info=True)
        raise ServiceError(
            _("Failed to update form in ODK Central: %(error)s") % {"error": e}
        ) from e


async def get_form_list(db: AsyncConnection) -> list:
    """Returns the list of {id:title} for XLSForms in the database."""
    try:
        return await DbTemplateXLSForm.all(db)
    except Exception as e:
        log.exception(f"Error: {e}", stack_info=True)
        raise ServiceError(str(e)) from e


# Lists Field-TM injects during the merge - users don't have to define
# these themselves, so don't fail validation when the survey references them.
_INJECTED_CHOICE_LISTS = frozenset({"yes_no", "mapping_mode", "digitisation_problem"})
_SELECT_TYPE_RE = re.compile(r"^\s*(select_one|select_multiple)\s+(\S+)")


def _missing_choice_lists(
    types: list, available_lists: set[str]
) -> list[tuple[int, str]]:
    """Return (row, list_name) for select questions using undefined lists."""
    invalid = []
    for offset, type_value in enumerate(types):
        match = None if pd.isna(type_value) else _SELECT_TYPE_RE.match(str(type_value))
        # select_one_from_file references a CSV (has a "."), not a choices list
        if (
            match
            and "." not in match.group(2)
            and match.group(2) not in available_lists
        ):
            # +2: header row is row 1, dataframe is 0-indexed
            invalid.append((offset + 2, match.group(2)))
    return invalid


def _validate_user_xlsform_choices(xlsform: BytesIO) -> None:
    """Reject select_one/select_multiple references missing from the choices sheet.

    Raises UnprocessableError with the original survey row numbers. Skips
    select_one_from_file (CSV references) and rewinds xlsform before returning.
    """
    try:
        xlsform.seek(0)
        sheets = pd.read_excel(xlsform, sheet_name=None, engine="calamine")
    except Exception as exc:
        raise UnprocessableError(
            _("Could not read XLSForm file: %(error)s") % {"error": exc}
        ) from exc
    finally:
        xlsform.seek(0)

    survey_df = sheets.get("survey")
    if survey_df is None or "type" not in survey_df.columns:
        return

    choices_df = sheets.get("choices")
    available_lists: set[str] = set(_INJECTED_CHOICE_LISTS)
    if choices_df is not None and "list_name" in choices_df.columns:
        available_lists.update(
            str(value)
            for value in choices_df["list_name"].dropna().tolist()
            if str(value).strip()
        )

    invalid = _missing_choice_lists(survey_df["type"].tolist(), available_lists)
    if not invalid:
        return

    parts = ", ".join(f"row {row} references list '{name}'" for row, name in invalid)
    raise UnprocessableError(
        _(
            "XLSForm has select questions referencing lists that aren't "
            "defined in the choices sheet: %(rows)s. Check your survey "
            "and choices sheets."
        )
        % {"rows": parts}
    )


async def read_and_test_xform(input_data: BytesIO) -> None:
    """Validate an XForm and return its XML in a BytesIO buffer."""
    try:
        log.debug(
            f"Parsing XLSForm --> XML data: input type {type(input_data)} | "
            f"data length {input_data.getbuffer().nbytes}"
        )
        # NOTE pyxform.xls2xform.convert returns a ConvertResult object
        return BytesIO(xform_convert(input_data).xform.encode("utf-8"))
    except Exception as e:
        log.exception(f"Error: {e}", stack_info=True)
        msg = _("XLSForm is invalid: %(error)s") % {"error": e}
        raise UnprocessableError(msg) from e


async def append_fields_to_user_xlsform(  # noqa: PLR0913
    xlsform: BytesIO,
    form_name: str = "buildings",
    new_geom_type: Optional[DbGeomType] = DbGeomType.POINT,
    need_verification_fields: bool = True,
    include_photo_upload: bool = True,
    mandatory_photo_upload: bool = False,
    default_language: str | None = None,
    use_odk_collect: bool = False,
    *,
    new_point_capture: NewPointCapture = NewPointCapture.MAP,
    form_id: str | None = None,
) -> tuple[str, BytesIO]:
    """Helper to return the intermediate XLSForm prior to convert."""
    log.debug("Appending mandatory Field-TM fields to XLSForm")
    return await append_field_mapping_fields(
        xlsform,
        form_name=form_name,
        new_geom_type=new_geom_type,
        new_point_capture=new_point_capture,
        need_verification_fields=need_verification_fields,
        include_photo_upload=include_photo_upload,
        mandatory_photo_upload=mandatory_photo_upload,
        default_language=default_language,
        use_odk_collect=use_odk_collect,
        form_id=form_id,
    )


async def validate_and_update_user_xlsform(  # noqa: PLR0913
    xlsform: BytesIO,
    default_language: str | None = None,
    form_name: str = "buildings",
    new_geom_type: Optional[DbGeomType] = DbGeomType.POINT,
    need_verification_fields: bool = True,
    include_photo_upload: bool = True,
    mandatory_photo_upload: bool = False,
    use_odk_collect: bool = False,
    *,
    new_point_capture: NewPointCapture = NewPointCapture.MAP,
    form_id: str | None = None,
) -> BytesIO:
    """Wrapper to append mandatory fields and validate user uploaded XLSForm."""
    # Validate before merging to report row numbers from the original upload.
    _validate_user_xlsform_choices(xlsform)

    xform_id, updated_file_bytes = await append_fields_to_user_xlsform(
        xlsform,
        form_name=form_name,
        new_geom_type=new_geom_type,
        new_point_capture=new_point_capture,
        need_verification_fields=need_verification_fields,
        include_photo_upload=include_photo_upload,
        mandatory_photo_upload=mandatory_photo_upload,
        default_language=default_language,
        use_odk_collect=use_odk_collect,
        form_id=form_id,
    )

    log.debug("Validating uploaded XLS form")
    return await read_and_test_xform(updated_file_bytes)


def flatten_json(data: dict, target: dict):
    """Flatten submission properties into target, skipping GeoJSON GPS data."""
    for k, v in data.items():
        if isinstance(v, dict):
            if "type" in v and "coordinates" in v:
                continue
            flatten_json(v, target)
        else:
            target[k] = v


async def feature_geojson_to_entity_dict(
    feature: dict,
    additional_features: bool = False,
) -> central_schemas.EntityDict:
    """Convert a single GeoJSON to an Entity dict for upload."""
    if not isinstance(feature, dict):
        log.error(f"Feature not in correct format: {feature}")
        raise ValueError(f"Feature not in correct format: {type(feature)}")

    geometry = feature.get("geometry", {})
    if not geometry:
        msg = _("'geometry' data field is mandatory")
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
        feature_id = feature.get("id")
        entity_label = f"Feature {feature_id}"

    return {
        "label": entity_label,
        "data": {"geometry": javarosa_geom, **properties},
    }


async def task_geojson_dict_to_entity_values(
    task_geojson_dict: Union[dict[int, dict], dict],
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
    keep_existing: frozenset[str] = frozenset(),
) -> dict[str, str]:
    """Build the smallest update payload needed to align an existing entity."""
    update_data = {}
    for key, value in source_row.items():
        if key == "label" or (key in keep_existing and key in target_row):
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
    target_by_label: dict[str, dict],
    keep_existing: frozenset[str] = frozenset(),
) -> None:
    """Insert new entities and minimally update existing ones by label."""
    to_insert = []
    for source_row in merge_rows:
        label = source_row.get("label")
        if not label:
            continue

        target_row = target_by_label.get(label)
        if not target_row:
            to_insert.append(source_row)
            continue

        update_data = _get_entity_update_data(source_row, target_row, keep_existing)
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


def _delete_missing_entities(
    client,
    project_id: int,
    dataset_name: str,
    merge_rows: list[dict[str, str]],
    target_by_label: dict[str, dict],
) -> None:
    """Delete entities whose label is not in the incoming rows."""
    keep = {row["label"] for row in merge_rows}
    for label, row in target_by_label.items():
        if label not in keep:
            client.entities.delete(
                uuid=row["__id"], entity_list_name=dataset_name, project_id=project_id
            )


def _sync_entity_list(  # noqa: PLR0913
    client,
    project_id: int,
    dataset_name: str,
    properties: list[str],
    merge_rows: list[dict[str, str]],
    keep_existing: frozenset[str],
    delete_missing: bool,
) -> None:
    """Ensure the dataset and its properties exist, then upsert entity rows."""
    existing = {ds.name for ds in client.entity_lists.list(project_id=project_id)}
    if dataset_name not in existing:
        log.info(f"Creating dataset '{dataset_name}' for ODK project {project_id}")
        client.entity_lists.create(entity_list_name=dataset_name, project_id=project_id)

    _ensure_dataset_properties(
        client,
        project_id,
        dataset_name,
        _collect_required_property_keys(properties, merge_rows),
        _get_existing_dataset_property_names(client, project_id, dataset_name),
    )
    if not merge_rows and not delete_missing:
        return

    target_by_label = _index_entities_by_label(
        client.entities.get_table(entity_list_name=dataset_name, project_id=project_id)
    )
    _upsert_entity_rows(
        client, project_id, dataset_name, merge_rows, target_by_label, keep_existing
    )
    if delete_missing:
        _delete_missing_entities(
            client, project_id, dataset_name, merge_rows, target_by_label
        )


async def create_entity_list(  # noqa: PLR0913
    odk_creds: Optional[central_schemas.ODKCentral],
    odk_id: int,
    properties: list[str],
    dataset_name: str = "features",
    entities_list: list[central_schemas.EntityDict] = None,
    keep_existing: frozenset[str] = frozenset(),
    delete_missing: bool = False,
) -> None:
    """Create an Entity list (dataset) in ODK if needed and upsert entities.

    Properties in `keep_existing` are only set on new entities.
    With `delete_missing`, entities not in `entities_list` are deleted.
    """
    if odk_id is None:
        raise ValidationError(
            _("ODK project_id is missing; cannot create/merge entity lists.")
        )

    properties = central_schemas.entity_fields_to_list(properties)
    merge_rows = _build_entity_merge_rows(entities_list)
    async with central_deps.pyodk_client(odk_creds) as client:
        await to_thread(
            _sync_entity_list,
            client,
            int(odk_id),
            dataset_name,
            properties,
            merge_rows,
            keep_existing,
            delete_missing,
        )


async def get_submissions(
    odk_creds: Optional[central_schemas.ODKCentral], project_odk_id: int
) -> list[dict]:
    """All submissions of the project's survey form, with repeats expanded."""
    async with central_deps.pyodk_client(odk_creds) as client:
        forms = client.forms.list(project_id=project_odk_id)
        if not forms:
            return []
        table = client.submissions.get_table(
            form_id=forms[0].xmlFormId, project_id=project_odk_id, expand="*"
        )
    return table.get("value", [])


async def get_appuser_token(
    xform_id: str,
    project_odk_id: int,
    odk_credentials: Optional[central_schemas.ODKCentral],
):
    """Get the app user token for a project and XForm."""
    try:
        appuser_name = "fieldtm_user"
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
                msg = _("Could not generate token for app user.")
                raise UnprocessableError(msg)

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
        raise ServiceError(
            _("An error occurred while creating the app user token.")
        ) from e
    except Exception as e:
        log.exception(f"An error occurred: {str(e)}", stack_info=True)
        raise ServiceError(
            _("An error occurred while creating the app user token.")
        ) from e


def _assign_appuser_role(client, path: str, scope: str) -> None:
    """Assign an app-user role and validate the ODK response."""
    assignment_response = client.session.post(path)
    assignment_response.raise_for_status()
    assignment_result = assignment_response.json()
    if assignment_result.get("success"):
        return

    raise UnprocessableError(
        _("Could not assign %(scope)s role to app user.") % {"scope": scope}
    )


def _build_manager_user_email(project_odk_id: int) -> str:
    """Create the default manager email for a project."""
    return f"field-tm-manager-{project_odk_id}@fieldtm.org"


def _build_manager_user_password() -> str:
    """Generate a strong password for generated Central web users."""
    # Keep to alphanumeric for widest compatibility across Central deployments.
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(20))


def _build_manager_user_email_fallback(project_odk_id: int) -> str:
    """Create a fallback manager email variant when the primary is already taken."""
    suffix = secrets.token_hex(4)
    return f"field-tm-manager-{project_odk_id}-{suffix}@fieldtm.org"


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
        raise ServiceError(_("Could not find 'Project Manager' role in ODK Central."))

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
                raise ServiceError(_("ODK Central returned no user ID after creation."))
            return created_user_id, candidate_email, candidate_password

        if create_status == status.HTTP_409_CONFLICT:
            log.info(
                "Manager email %s already exists in ODK Central; "
                "trying fallback address.",
                candidate_email,
            )
            continue

        body = getattr(create_response, "text", "")
        raise ServiceError(
            f"ODK Central returned {create_status} when creating "
            f"manager user. Body: {body}"
        )

    raise ServiceError(
        "Could not create an ODK Central manager user: "
        "both primary and fallback email addresses are already taken."
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
    """Create a Central Project Manager and return (email, password).

    Credentials are returned once, without storage. Central sends a welcome
    email, so a reachable mail-catcher (development) or SMTP server is required.
    """
    try:
        async with central_deps.pyodk_client(odk_credentials) as client:
            role_id = _get_project_manager_role_id(client)
            display_name = f"Field-TM Manager - {project_name}"
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

    except ServiceError:
        raise
    except Exception as e:
        log.exception(
            "Failed to create project manager user for ODK project %s.",
            project_odk_id,
            stack_info=True,
        )
        raise ServiceError(_("Failed to create ODK Central manager user.")) from e


async def odk_credentials_test(odk_creds: central_schemas.ODKCentral):
    """Test ODK Central credentials by attempting to open a session.

    Returns status 200 if credentials are valid, otherwise raises ServiceError.
    """
    try:
        async with central_deps.pyodk_client(odk_creds):
            pass
        return status.HTTP_200_OK
    except PyODKError as e:
        log.error(f"ODK Central credential test failed: {e}")
        raise ValidationError(
            _("ODK credentials are invalid, or may have changed.")
        ) from e
    except RequestException as e:
        log.error(f"ODK Central credential test failed: {e}")
        raise ValidationError(
            _("Failed to connect to Central. Is the URL valid?")
        ) from e
    except Exception as e:
        log.error(f"Unexpected error during ODK Central credential test: {str(e)}")
        raise ServiceError(
            _("Unexpected error while testing ODK Central credentials.")
        ) from e
