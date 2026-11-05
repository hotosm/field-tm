"""Tests for the ODK project finalization service workflow.

These tests exercise finalize_odk_project end-to-end with fully mocked ODK
Central interactions, verifying that manager user creation and credential
delivery work correctly through the whole chain.
"""

from contextlib import asynccontextmanager
from copy import deepcopy
from dataclasses import dataclass
from io import BytesIO
from types import SimpleNamespace
from typing import Optional
from unittest.mock import AsyncMock, patch

import pytest
from osm_fieldwork.conversion_to_xlsform import convert_to_xlsform
from osm_fieldwork.enums import NewPointCapture
from osm_fieldwork.update_xlsform import get_processed_form_options
from osm_fieldwork.xlsforms import buildings

from app.central import central_crud
from app.central.central_schemas import ODKCentral
from app.db.models import DbProject
from app.errors import (
    ServiceError,
    ValidationError,
)
from app.projects import project_services
from app.projects.odk_services import (
    ODKFinalizeResult,
    _build_feature_dataset_payload,
    finalize_odk_project,
)
from app.projects.project_services import (
    derive_simple_project_metadata,
    save_task_areas,
)
from app.projects.task_sync import (
    _build_task_entities,
    sync_odk_tasks,
)
from app.qfield.qfield_crud import _build_tasks_geojson

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_OUTLINE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [85.30, 27.71],
                        [85.30, 27.70],
                        [85.31, 27.70],
                        [85.31, 27.71],
                        [85.30, 27.71],
                    ]
                ],
            },
            "properties": {},
        }
    ],
}

SAMPLE_DATA_EXTRACT = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [85.30, 27.71],
                        [85.30, 27.70],
                        [85.31, 27.70],
                        [85.31, 27.71],
                        [85.30, 27.71],
                    ]
                ],
            },
            "properties": {"osm_id": 1, "building": "yes"},
        }
    ],
}

DUMMY_XLSFORM = b"dummy xlsform bytes"
_UNSET = object()


def _task_feature(properties: Optional[dict] = None) -> dict:
    """Build a task-area Feature with the sample polygon geometry."""
    return {
        "type": "Feature",
        "geometry": SAMPLE_OUTLINE["features"][0]["geometry"],
        "properties": properties if properties is not None else {},
    }


@dataclass
class FakeProject:
    """Minimal stand-in for DbProject used in finalize tests."""

    id: int = 1
    project_name: str = "Test Project"
    xlsform_content: bytes = DUMMY_XLSFORM
    data_extract_geojson: Optional[dict] | object = _UNSET
    outline: Optional[dict] = None
    outline_geojson: Optional[dict] | object = _UNSET
    task_areas_geojson: Optional[dict] = None
    external_project_id: Optional[int] = None
    external_project_instance_url: Optional[str] = None
    field_mapping_app: str = "ODK"
    status: str = "DRAFT"
    slug: str = "test-project"

    def __post_init__(self):
        """Set default data extract if not provided."""
        if self.data_extract_geojson is _UNSET:
            self.data_extract_geojson = SAMPLE_DATA_EXTRACT
        if self.outline_geojson is _UNSET:
            self.outline_geojson = SAMPLE_OUTLINE
        if self.outline is None and self.outline_geojson:
            features = self.outline_geojson.get("features", [])
            if features and isinstance(features[0], dict):
                self.outline = features[0].get("geometry")


# ---------------------------------------------------------------------------
# Tests: finalize_odk_project validation
# ---------------------------------------------------------------------------


async def test_finalize_odk_project_requires_xlsform(stub_project, db):
    """Finalize should reject projects without XLSForm."""
    with pytest.raises(ValidationError, match="XLSForm is required"):
        await finalize_odk_project(db, project_id=stub_project.id)


async def test_finalize_odk_project_requires_data_extract(stub_project, db):
    """Finalize should reject projects without a data extract."""
    # Give the project xlsform bytes so the xlsform check passes.
    await DbProject.update(db, stub_project.id, DbProject(xlsform_content=b"<xform/>"))
    await db.commit()

    with pytest.raises(ValidationError, match="Data extract is required"):
        await finalize_odk_project(db, project_id=stub_project.id)


@pytest.mark.asyncio
async def test_finalize_odk_project_allows_collect_new_data_only_mode():
    """Finalize should allow an explicitly empty FeatureCollection extract."""
    project = FakeProject(
        data_extract_geojson={"type": "FeatureCollection", "features": []},
        external_project_id=None,
    )

    fake_db = AsyncMock()
    fake_db.commit = AsyncMock()

    async def fake_create_odk_project(name, creds):
        return {"id": 42}

    async def fake_feature_geojson_to_entity_dict(feature, **kwargs):
        return {"label": "Task 1", "data": {"geometry": "geom"}}

    async def fake_read_and_test_xform(xlsform_bytes):
        return BytesIO(b"<xform/>")

    async def fake_create_odk_xform(*args, **kwargs):
        pass

    async def fake_generate_project_files(db, project_id, odk_credentials=None):
        return True

    async def fake_create_project_manager_user(
        project_odk_id, project_name, odk_credentials
    ):
        return ("field-tm-manager-42@fieldtm.org", "SecurePass12345abcde")

    mock_create_entity_list = AsyncMock()

    creds = ODKCentral(
        external_project_instance_url="https://central.example.org",
        external_project_username="admin@example.org",
        external_project_password="secret",
    )

    with (
        patch(
            "app.db.models.DbProject.one",
            return_value=project,
        ),
        patch(
            "app.db.models.DbProject.update",
            new_callable=AsyncMock,
        ),
        patch(
            "app.central.central_crud.create_odk_project",
            side_effect=fake_create_odk_project,
        ),
        patch(
            "app.central.central_crud.create_entity_list",
            mock_create_entity_list,
        ),
        patch(
            "app.central.central_crud.feature_geojson_to_entity_dict",
            side_effect=fake_feature_geojson_to_entity_dict,
        ),
        patch(
            "app.central.central_crud.read_and_test_xform",
            side_effect=fake_read_and_test_xform,
        ),
        patch(
            "app.central.central_crud.create_odk_xform",
            side_effect=fake_create_odk_xform,
        ),
        patch(
            "app.projects.project_crud.generate_project_files",
            side_effect=fake_generate_project_files,
        ),
        patch(
            "app.central.central_crud.create_project_manager_user",
            side_effect=fake_create_project_manager_user,
        ),
    ):
        result = await finalize_odk_project(
            db=fake_db,
            project_id=1,
            custom_odk_creds=creds,
        )

    assert isinstance(result, ODKFinalizeResult)
    assert result.odk_url == "https://central.example.org/#/projects/42"
    assert mock_create_entity_list.await_count == 2

    features_call = mock_create_entity_list.await_args_list[0]
    assert features_call.kwargs["dataset_name"] == "features"
    assert features_call.kwargs["entities_list"] == []


async def test_finalize_odk_project_requires_odk_credentials(stub_project, db):
    """Finalize should reject when no ODK credentials are available."""
    # Set xlsform + data_extract so we reach the ODK credentials check.
    await DbProject.update(
        db,
        stub_project.id,
        DbProject(
            xlsform_content=b"<xform/>",
            data_extract_geojson={"type": "FeatureCollection", "features": []},
        ),
    )
    await db.commit()

    with (
        patch("app.projects.odk_services.settings") as mock_settings,
        pytest.raises(ValidationError, match="ODK Central credentials"),
    ):
        mock_settings.ODK_CENTRAL_URL = ""
        mock_settings.ODK_CENTRAL_USER = ""
        await finalize_odk_project(db, project_id=stub_project.id)


@pytest.mark.asyncio
async def test_finalize_odk_project_returns_manager_credentials():
    """Full finalize flow should return ODK URL + manager credentials."""
    project = FakeProject(external_project_id=None)

    fake_db = AsyncMock()
    fake_db.commit = AsyncMock()

    # Mock ODK project creation
    async def fake_create_odk_project(name, creds):
        return {"id": 42}

    # Mock entity list creation
    async def fake_create_entity_list(*args, **kwargs):
        pass

    # Mock task geojson to entity values
    async def fake_task_geojson_dict_to_entity_values(geojson, **kwargs):
        return [
            {
                "label": "Feature 1",
                "data": {
                    "geometry": "geom",
                    "osm_id": "1",
                    "building": "yes",
                },
            }
        ]

    # Mock feature geojson to entity dict
    async def fake_feature_geojson_to_entity_dict(feature, **kwargs):
        return {
            "label": "Task 1",
            "data": {"geometry": "geom"},
        }

    # Mock XLSForm reading
    async def fake_read_and_test_xform(xlsform_bytes):
        return BytesIO(b"<xform/>")

    # Mock XForm upload
    async def fake_create_odk_xform(*args, **kwargs):
        pass

    # Mock generate_project_files
    async def fake_generate_project_files(db, project_id, odk_credentials=None):
        return True

    # Mock manager user creation
    async def fake_create_project_manager_user(
        project_odk_id, project_name, odk_credentials
    ):
        return ("field-tm-manager-42@fieldtm.org", "SecurePass12345abcde")

    creds = ODKCentral(
        external_project_instance_url="https://central.example.org",
        external_project_username="admin@example.org",
        external_project_password="secret",
    )

    with (
        patch(
            "app.db.models.DbProject.one",
            return_value=project,
        ),
        patch(
            "app.db.models.DbProject.update",
            new_callable=AsyncMock,
        ),
        patch(
            "app.central.central_crud.create_odk_project",
            side_effect=fake_create_odk_project,
        ),
        patch(
            "app.central.central_crud.create_entity_list",
            side_effect=fake_create_entity_list,
        ),
        patch(
            "app.central.central_crud.task_geojson_dict_to_entity_values",
            side_effect=fake_task_geojson_dict_to_entity_values,
        ),
        patch(
            "app.central.central_crud.feature_geojson_to_entity_dict",
            side_effect=fake_feature_geojson_to_entity_dict,
        ),
        patch(
            "app.central.central_crud.read_and_test_xform",
            side_effect=fake_read_and_test_xform,
        ),
        patch(
            "app.central.central_crud.create_odk_xform",
            side_effect=fake_create_odk_xform,
        ),
        patch(
            "app.projects.project_crud.generate_project_files",
            side_effect=fake_generate_project_files,
        ),
        patch(
            "app.central.central_crud.create_project_manager_user",
            side_effect=fake_create_project_manager_user,
        ),
    ):
        result = await finalize_odk_project(
            db=fake_db,
            project_id=1,
            custom_odk_creds=creds,
        )

    assert isinstance(result, ODKFinalizeResult)
    assert result.odk_url == "https://central.example.org/#/projects/42"
    assert result.manager_username == "field-tm-manager-42@fieldtm.org"
    assert result.manager_password == "SecurePass12345abcde"


@pytest.mark.asyncio
async def test_finalize_odk_project_persists_custom_odk_credentials():
    """Finalize should persist custom ODK URL + username + encrypted password source."""
    project = FakeProject(external_project_id=None)

    fake_db = AsyncMock()
    fake_db.commit = AsyncMock()

    async def fake_create_odk_project(name, creds):
        return {"id": 42}

    async def fake_create_entity_list(*args, **kwargs):
        pass

    async def fake_task_geojson_dict_to_entity_values(geojson, **kwargs):
        return [
            {
                "label": "Feature 1",
                "data": {"geometry": "geom", "osm_id": "1", "building": "yes"},
            }
        ]

    async def fake_feature_geojson_to_entity_dict(feature, **kwargs):
        return {"label": "Task 1", "data": {"geometry": "geom"}}

    async def fake_read_and_test_xform(xlsform_bytes):
        return BytesIO(b"<xform/>")

    async def fake_create_odk_xform(*args, **kwargs):
        pass

    async def fake_generate_project_files(db, project_id, odk_credentials=None):
        return True

    async def fake_create_project_manager_user(
        project_odk_id, project_name, odk_credentials
    ):
        return ("field-tm-manager-42@fieldtm.org", "SecurePass12345abcde")

    mock_update = AsyncMock()

    creds = ODKCentral(
        external_project_instance_url="https://example-odk.trycloudflare.com",
        external_project_username="admin@example.org",
        external_project_password="secret",
    )

    with (
        patch(
            "app.db.models.DbProject.one",
            return_value=project,
        ),
        patch(
            "app.db.models.DbProject.update",
            mock_update,
        ),
        patch(
            "app.central.central_crud.create_odk_project",
            side_effect=fake_create_odk_project,
        ),
        patch(
            "app.central.central_crud.create_entity_list",
            side_effect=fake_create_entity_list,
        ),
        patch(
            "app.central.central_crud.task_geojson_dict_to_entity_values",
            side_effect=fake_task_geojson_dict_to_entity_values,
        ),
        patch(
            "app.central.central_crud.feature_geojson_to_entity_dict",
            side_effect=fake_feature_geojson_to_entity_dict,
        ),
        patch(
            "app.central.central_crud.read_and_test_xform",
            side_effect=fake_read_and_test_xform,
        ),
        patch(
            "app.central.central_crud.create_odk_xform",
            side_effect=fake_create_odk_xform,
        ),
        patch(
            "app.projects.project_crud.generate_project_files",
            side_effect=fake_generate_project_files,
        ),
        patch(
            "app.central.central_crud.create_project_manager_user",
            side_effect=fake_create_project_manager_user,
        ),
    ):
        await finalize_odk_project(
            db=fake_db,
            project_id=1,
            custom_odk_creds=creds,
        )

    payloads = [call.args[2] for call in mock_update.await_args_list]
    assert any(
        payload.external_project_instance_url == "https://example-odk.trycloudflare.com"
        and payload.external_project_username == "admin@example.org"
        and payload.external_project_password == "secret"
        for payload in payloads
    )


@pytest.mark.asyncio
async def test_finalize_odk_project_prefers_public_url_for_manager_link():
    """Use public ODK URL for returned manager link when using env credentials."""
    project = FakeProject(
        external_project_id=42,
        external_project_instance_url="http://central:8383",
    )

    fake_db = AsyncMock()
    fake_db.commit = AsyncMock()

    async def fake_create_entity_list(*args, **kwargs):
        pass

    async def fake_task_geojson_dict_to_entity_values(geojson, **kwargs):
        return [
            {
                "label": "Feature 1",
                "data": {"geometry": "geom", "osm_id": "1", "building": "yes"},
            }
        ]

    async def fake_feature_geojson_to_entity_dict(feature, **kwargs):
        return {"label": "Task 1", "data": {"geometry": "geom"}}

    async def fake_read_and_test_xform(xlsform_bytes):
        return BytesIO(b"<xform/>")

    async def fake_create_odk_xform(*args, **kwargs):
        pass

    async def fake_generate_project_files(db, project_id, odk_credentials=None):
        return True

    async def fake_create_project_manager_user(
        project_odk_id, project_name, odk_credentials
    ):
        return ("field-tm-manager-42@fieldtm.org", "SecurePass12345abcde")

    with (
        patch(
            "app.db.models.DbProject.one",
            return_value=project,
        ),
        patch(
            "app.db.models.DbProject.update",
            new_callable=AsyncMock,
        ),
        patch(
            "app.central.central_crud.create_entity_list",
            side_effect=fake_create_entity_list,
        ),
        patch(
            "app.central.central_crud.task_geojson_dict_to_entity_values",
            side_effect=fake_task_geojson_dict_to_entity_values,
        ),
        patch(
            "app.central.central_crud.feature_geojson_to_entity_dict",
            side_effect=fake_feature_geojson_to_entity_dict,
        ),
        patch(
            "app.central.central_crud.read_and_test_xform",
            side_effect=fake_read_and_test_xform,
        ),
        patch(
            "app.central.central_crud.create_odk_xform",
            side_effect=fake_create_odk_xform,
        ),
        patch(
            "app.projects.project_crud.generate_project_files",
            side_effect=fake_generate_project_files,
        ),
        patch(
            "app.central.central_crud.create_project_manager_user",
            side_effect=fake_create_project_manager_user,
        ),
        patch("app.projects.odk_services.settings") as mock_settings,
    ):
        mock_settings.ODK_CENTRAL_URL = "http://central:8383"
        mock_settings.ODK_CENTRAL_PUBLIC_URL = "http://odk.field.localhost:7050"
        mock_settings.ODK_CENTRAL_USER = "admin@example.org"

        result = await finalize_odk_project(
            db=fake_db,
            project_id=1,
            custom_odk_creds=None,
        )

    assert result.odk_url == "http://odk.field.localhost:7050/#/projects/42"
    assert result.manager_username == "field-tm-manager-42@fieldtm.org"
    assert result.manager_password == "SecurePass12345abcde"


@pytest.mark.asyncio
async def test_finalize_odk_project_generate_files_failure():
    """Finalize should raise ServiceError when project file generation fails."""
    project = FakeProject(external_project_id=99)

    fake_db = AsyncMock()
    fake_db.commit = AsyncMock()

    async def fake_create_entity_list(*args, **kwargs):
        pass

    async def fake_task_geojson_dict_to_entity_values(geojson, **kwargs):
        return [
            {
                "label": "Feature 1",
                "data": {"geometry": "g", "osm_id": "1", "building": "yes"},
            }
        ]

    async def fake_read_and_test_xform(xlsform_bytes):
        return BytesIO(b"<xform/>")

    async def fake_create_odk_xform(*args, **kwargs):
        pass

    async def fake_generate_project_files(db, project_id, odk_credentials=None):
        return False  # Signal failure

    creds = ODKCentral(
        external_project_instance_url="https://central.example.org",
        external_project_username="admin@example.org",
        external_project_password="secret",
    )

    with (
        patch(
            "app.db.models.DbProject.one",
            return_value=project,
        ),
        patch(
            "app.db.models.DbProject.update",
            new_callable=AsyncMock,
        ),
        patch(
            "app.central.central_crud.create_entity_list",
            side_effect=fake_create_entity_list,
        ),
        patch(
            "app.central.central_crud.task_geojson_dict_to_entity_values",
            side_effect=fake_task_geojson_dict_to_entity_values,
        ),
        patch(
            "app.central.central_crud.read_and_test_xform",
            side_effect=fake_read_and_test_xform,
        ),
        patch(
            "app.central.central_crud.create_odk_xform",
            side_effect=fake_create_odk_xform,
        ),
        patch(
            "app.projects.project_crud.generate_project_files",
            side_effect=fake_generate_project_files,
        ),
    ):
        with pytest.raises(ServiceError, match="Failed to generate project files"):
            await finalize_odk_project(
                db=fake_db,
                project_id=1,
                custom_odk_creds=creds,
            )


@pytest.mark.asyncio
async def test_finalize_odk_project_manager_user_failure_raises_service_error():
    """Finalize should raise ServiceError when manager user creation fails."""
    project = FakeProject(external_project_id=99)

    fake_db = AsyncMock()
    fake_db.commit = AsyncMock()

    async def fake_create_entity_list(*args, **kwargs):
        pass

    async def fake_task_geojson_dict_to_entity_values(geojson, **kwargs):
        return [
            {
                "label": "Feature 1",
                "data": {"geometry": "g", "osm_id": "1", "building": "yes"},
            }
        ]

    async def fake_feature_geojson_to_entity_dict(feature, **kwargs):
        return {"label": "Task 1", "data": {"geometry": "geom"}}

    async def fake_read_and_test_xform(xlsform_bytes):
        return BytesIO(b"<xform/>")

    async def fake_create_odk_xform(*args, **kwargs):
        pass

    async def fake_generate_project_files(db, project_id, odk_credentials=None):
        return True

    async def fake_create_project_manager_user(*args, **kwargs):
        raise Exception("central user-create failed")

    creds = ODKCentral(
        external_project_instance_url="https://central.example.org",
        external_project_username="admin@example.org",
        external_project_password="secret",
    )

    with (
        patch(
            "app.db.models.DbProject.one",
            return_value=project,
        ),
        patch(
            "app.db.models.DbProject.update",
            new_callable=AsyncMock,
        ),
        patch(
            "app.central.central_crud.create_entity_list",
            side_effect=fake_create_entity_list,
        ),
        patch(
            "app.central.central_crud.task_geojson_dict_to_entity_values",
            side_effect=fake_task_geojson_dict_to_entity_values,
        ),
        patch(
            "app.central.central_crud.feature_geojson_to_entity_dict",
            side_effect=fake_feature_geojson_to_entity_dict,
        ),
        patch(
            "app.central.central_crud.read_and_test_xform",
            side_effect=fake_read_and_test_xform,
        ),
        patch(
            "app.central.central_crud.create_odk_xform",
            side_effect=fake_create_odk_xform,
        ),
        patch(
            "app.projects.project_crud.generate_project_files",
            side_effect=fake_generate_project_files,
        ),
        patch(
            "app.central.central_crud.create_project_manager_user",
            side_effect=fake_create_project_manager_user,
        ),
    ):
        with pytest.raises(
            ServiceError, match="Failed to create ODK Central manager user"
        ):
            await finalize_odk_project(
                db=fake_db,
                project_id=1,
                custom_odk_creds=creds,
            )


@pytest.mark.asyncio
async def test_build_feature_dataset_payload_allows_empty_data_extract_features():
    """Collect-new-data mode should generate an empty features dataset payload."""
    project = FakeProject(
        data_extract_geojson={"type": "FeatureCollection", "features": []}
    )

    entity_properties, entities_list = await _build_feature_dataset_payload(
        project_id=1,
        project=project,
    )

    assert entity_properties == []
    assert entities_list == []


# ---------------------------------------------------------------------------
# Tests: stable task_id stamping and task entity building
# ---------------------------------------------------------------------------


async def test_save_task_areas_stamps_missing_task_ids(stub_project, db):
    """Saving task areas should stamp sequential ids onto unstamped features."""
    tasks_geojson = {
        "type": "FeatureCollection",
        "features": [_task_feature(), _task_feature(), _task_feature()],
    }

    task_count = await save_task_areas(db, stub_project.id, tasks_geojson)

    assert task_count == 3
    updated_project = await DbProject.one(db, stub_project.id)
    stored_ids = [
        feature["properties"]["task_id"]
        for feature in updated_project.task_areas_geojson["features"]
    ]
    assert stored_ids == [1, 2, 3]


async def test_save_task_areas_preserves_existing_ids_and_avoids_collisions(
    stub_project, db
):
    """Existing task ids must stay untouched; stamped ids skip used values."""
    tasks_geojson = {
        "type": "FeatureCollection",
        "features": [
            _task_feature(properties={"task_id": 2}),
            _task_feature(),
            _task_feature(properties={"task_id": 1}),
            _task_feature(),
        ],
    }

    await save_task_areas(db, stub_project.id, tasks_geojson)

    updated_project = await DbProject.one(db, stub_project.id)
    stored_ids = [
        feature["properties"]["task_id"]
        for feature in updated_project.task_areas_geojson["features"]
    ]
    assert stored_ids == [2, 3, 1, 4]


async def test_save_task_areas_restamps_duplicate_and_invalid_ids(stub_project, db):
    """Duplicate, malformed, or digit-string ids must persist as unique ints."""
    tasks_geojson = {
        "type": "FeatureCollection",
        "features": [
            _task_feature(properties={"task_id": 2}),
            _task_feature(properties={"task_id": 2}),
            _task_feature(properties={"task_id": "3"}),
            _task_feature(properties={"task_id": "abc"}),
            _task_feature(properties={"task_id": 0}),
        ],
    }

    await save_task_areas(db, stub_project.id, tasks_geojson)

    updated_project = await DbProject.one(db, stub_project.id)
    stored_ids = [
        feature["properties"]["task_id"]
        for feature in updated_project.task_areas_geojson["features"]
    ]
    assert stored_ids == [2, 1, 3, 4, 5]
    assert all(isinstance(task_id, int) for task_id in stored_ids)


async def test_save_task_areas_rejects_invalid_data_format(stub_project, db):
    """Non-dict task areas payloads should be rejected before persisting."""
    with pytest.raises(ValidationError, match="Invalid task areas data format"):
        await save_task_areas(db, stub_project.id, ["not", "a", "dict"])


@pytest.mark.asyncio
async def test_build_task_entities_uses_stored_task_ids():
    """Entity labels and data must come from stored task_id, not position."""
    project = FakeProject(
        task_areas_geojson={
            "type": "FeatureCollection",
            "features": [
                _task_feature(properties={"task_id": 7}),
                _task_feature(properties={"task_id": 3}),
            ],
        }
    )

    async def fake_feature_geojson_to_entity_dict(feature, **kwargs):
        return {"label": "", "data": {"geometry": "geom"}}

    with patch(
        "app.central.central_crud.feature_geojson_to_entity_dict",
        side_effect=fake_feature_geojson_to_entity_dict,
    ):
        task_entities = await _build_task_entities(project)

    assert [entity["label"] for entity in task_entities] == ["Task 7", "Task 3"]
    assert [entity["data"]["task_id"] for entity in task_entities] == ["7", "3"]


@pytest.mark.asyncio
async def test_build_task_entities_include_assignments_and_colour():
    """Task entities carry assignments; the colour styles the task."""
    project = FakeProject(
        task_areas_geojson={
            "type": "FeatureCollection",
            "features": [
                _task_feature(
                    properties={
                        "task_id": 2,
                        "assigned_group": "team-a",
                        "assigned_to": "Chomba",
                        "comment": "Start Monday",
                        "colour": "#d63f3f",
                    }
                ),
                _task_feature(properties={"task_id": 3}),
            ],
        }
    )

    async def fake_feature_geojson_to_entity_dict(feature, **kwargs):
        return {"label": "", "data": {"geometry": "geom"}}

    with patch(
        "app.central.central_crud.feature_geojson_to_entity_dict",
        side_effect=fake_feature_geojson_to_entity_dict,
    ):
        assigned, plain = await _build_task_entities(project)

    assert assigned["data"] == {
        "geometry": "geom",
        "task_id": "2",
        "status": "ready",
        "assigned_group": "team-a",
        "assigned_to": "Chomba",
        "comment": "Start Monday",
        "colour": "#d63f3f",
        "fill": "#d63f3f33",
        "stroke": "#d63f3f",
        "stroke-width": "3",
    }
    assert plain["data"]["assigned_to"] == ""
    assert plain["data"]["stroke"] == "#3388ff"


@pytest.mark.asyncio
async def test_sync_odk_tasks_keeps_field_status():
    """Re-sync upserts task entities without resetting their status."""
    project = FakeProject(
        task_areas_geojson={
            "type": "FeatureCollection",
            "features": [_task_feature(properties={"task_id": 1})],
        }
    )

    async def fake_feature_geojson_to_entity_dict(feature, **kwargs):
        return {"label": "", "data": {"geometry": "geom"}}

    with (
        patch(
            "app.central.central_crud.feature_geojson_to_entity_dict",
            side_effect=fake_feature_geojson_to_entity_dict,
        ),
        patch(
            "app.central.central_crud.create_entity_list",
            new_callable=AsyncMock,
        ) as mock_create,
    ):
        await sync_odk_tasks(project, None, 17)

    kwargs = mock_create.await_args.kwargs
    assert mock_create.await_args.args == (None, 17)
    assert kwargs["dataset_name"] == "tasks"
    assert kwargs["keep_existing"] == frozenset({"status"})
    assert "assigned_to" in kwargs["properties"]


def test_entity_update_skips_kept_properties():
    """Kept properties are only written when the entity lacks them."""
    source = {"label": "Task 1", "status": "ready", "assigned_to": "Bo"}
    target = {"status": "mapped", "assigned_to": "Al"}

    update = central_crud._get_entity_update_data(
        source, target, keep_existing=frozenset({"status"})
    )

    assert update == {"assigned_to": "Bo"}


@pytest.mark.asyncio
async def test_build_task_entities_stamps_legacy_rows_in_memory():
    """Features saved before id stamping get in-memory ids matching position."""
    project = FakeProject(
        task_areas_geojson={
            "type": "FeatureCollection",
            "features": [_task_feature(), _task_feature()],
        }
    )

    async def fake_feature_geojson_to_entity_dict(feature, **kwargs):
        return {"label": "", "data": {"geometry": "geom"}}

    with patch(
        "app.central.central_crud.feature_geojson_to_entity_dict",
        side_effect=fake_feature_geojson_to_entity_dict,
    ):
        task_entities = await _build_task_entities(project)

    assert [entity["label"] for entity in task_entities] == ["Task 1", "Task 2"]
    assert [entity["data"]["task_id"] for entity in task_entities] == ["1", "2"]


@pytest.mark.asyncio
async def test_build_task_entities_agrees_with_qfield_builder_on_mixed_ids():
    """Both export builders must derive identical ids from the same fixture."""
    featcol = {
        "type": "FeatureCollection",
        "features": [
            _task_feature(),
            _task_feature(properties={"task_id": 1}),
            _task_feature(properties={"task_id": 4}),
            _task_feature(),
        ],
    }

    qfield_project = SimpleNamespace(task_areas_geojson=deepcopy(featcol), outline=None)
    qfield_ids = [
        feature["properties"]["task_id"]
        for feature in _build_tasks_geojson(qfield_project)["features"]
    ]

    odk_project = FakeProject(task_areas_geojson=deepcopy(featcol))

    async def fake_feature_geojson_to_entity_dict(feature, **kwargs):
        return {"label": "", "data": {"geometry": "geom"}}

    with patch(
        "app.central.central_crud.feature_geojson_to_entity_dict",
        side_effect=fake_feature_geojson_to_entity_dict,
    ):
        task_entities = await _build_task_entities(odk_project)
    odk_ids = [int(entity["data"]["task_id"]) for entity in task_entities]

    assert qfield_ids == [2, 1, 4, 3]
    assert odk_ids == qfield_ids


@pytest.mark.asyncio
async def test_build_task_entities_outline_fallback_stays_task_one():
    """The single-task outline fallback must keep its canonical task id 1."""
    project = FakeProject(task_areas_geojson=None)

    async def fake_feature_geojson_to_entity_dict(feature, **kwargs):
        return {"label": "", "data": {"geometry": "geom"}}

    with patch(
        "app.central.central_crud.feature_geojson_to_entity_dict",
        side_effect=fake_feature_geojson_to_entity_dict,
    ):
        task_entities = await _build_task_entities(project)

    assert len(task_entities) == 1
    assert task_entities[0]["label"] == "Task 1"
    assert task_entities[0]["data"]["task_id"] == "1"


@pytest.mark.asyncio
async def test_build_task_entities_requires_outline_when_no_task_areas():
    """Missing both task areas and outline should fail with a clear error."""
    project = FakeProject(task_areas_geojson=None, outline_geojson=None)

    with pytest.raises(ValidationError, match="Project outline is missing"):
        await _build_task_entities(project)


@pytest.mark.asyncio
async def test_derive_simple_project_metadata_uses_lon_lat_order_for_nearest_city():
    """Nearest-city lookup must pass coordinates as (lon, lat)."""
    outline = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [85.30, 27.71],
                            [85.30, 27.70],
                            [85.31, 27.70],
                            [85.31, 27.71],
                            [85.30, 27.71],
                        ]
                    ],
                },
                "properties": {},
            }
        ],
    }

    class CapturingNearestCity:
        def __init__(self, _db):
            self.calls = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def query(self, lon, lat):
            self.calls.append((lon, lat))
            return SimpleNamespace(city="Kathmandu", country="NP")

    geocoder = CapturingNearestCity(None)

    with (
        patch(
            "app.projects.project_services.parse_aoi",
            return_value=outline,
        ),
        patch(
            "app.projects.project_services.polygon_to_centroid",
            new=AsyncMock(return_value=SimpleNamespace(x=85.305, y=27.705)),
        ),
        patch(
            "app.projects.project_services.AsyncNearestCity",
            return_value=geocoder,
        ),
    ):
        (
            project_name,
            _description,
            hashtags,
            location_str,
        ) = await derive_simple_project_metadata(db=AsyncMock(), outline=outline)

    assert geocoder.calls == [(85.305, 27.705)]
    assert project_name == "Kathmandu OSM Buildings"
    assert hashtags == ["osm", "buildings", "simple"]
    assert location_str == "Kathmandu, Nepal"


@pytest.mark.asyncio
async def test_derive_simple_project_metadata_falls_back_when_nearest_city_fails():
    """Nearest-city errors should fall back to a deterministic project name."""
    outline = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [85.30, 27.71],
                            [85.30, 27.70],
                            [85.31, 27.70],
                            [85.31, 27.71],
                            [85.30, 27.71],
                        ]
                    ],
                },
                "properties": {},
            }
        ],
    }

    class RaisingNearestCity:
        def __init__(self, _db):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def query(self, lon, lat):
            raise RuntimeError("pg_nearest_city unavailable")

    with (
        patch(
            "app.projects.project_services.parse_aoi",
            return_value=outline,
        ),
        patch(
            "app.projects.project_services.polygon_to_centroid",
            new=AsyncMock(return_value=SimpleNamespace(x=85.305, y=27.705)),
        ),
        patch(
            "app.projects.project_services.AsyncNearestCity",
            new=RaisingNearestCity,
        ),
    ):
        (
            project_name,
            description,
            hashtags,
            location_str,
        ) = await derive_simple_project_metadata(db=AsyncMock(), outline=outline)

    assert project_name == "Area 27.7050_85.3050 OSM Buildings"
    assert "simplified workflow" in description.lower()
    assert hashtags == ["osm", "buildings", "simple"]
    assert location_str is None


@pytest.mark.asyncio
async def test_derive_simple_project_metadata_uses_translated_fallback_strings():
    """Fallback simple-project strings should use gettext-backed text."""
    outline = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [85.30, 27.71],
                            [85.30, 27.70],
                            [85.31, 27.70],
                            [85.31, 27.71],
                            [85.30, 27.71],
                        ]
                    ],
                },
                "properties": {},
            }
        ],
    }

    class RaisingNearestCity:
        def __init__(self, _db):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def query(self, lon, lat):
            raise RuntimeError("pg_nearest_city unavailable")

    translations = {
        (
            "This project was created with a simplified workflow in FieldTM "
            "and is made to collect building data to enhance OpenStreetMap."
        ): "Descripcion traducida",
        "Area {latitude:.4f}_{longitude:.4f}": "Zona {latitude:.4f}_{longitude:.4f}",
        "{location} OSM Buildings": "{location} Edificios OSM",
    }

    with (
        patch(
            "app.projects.project_services.parse_aoi",
            return_value=outline,
        ),
        patch(
            "app.projects.project_services.polygon_to_centroid",
            new=AsyncMock(return_value=SimpleNamespace(x=85.305, y=27.705)),
        ),
        patch(
            "app.projects.project_services.AsyncNearestCity",
            new=RaisingNearestCity,
        ),
        patch.object(
            project_services,
            "_",
            side_effect=lambda message: translations.get(message, message),
        ),
    ):
        (
            project_name,
            description,
            hashtags,
            location_str,
        ) = await derive_simple_project_metadata(db=AsyncMock(), outline=outline)

    assert project_name == "Zona 27.7050_85.3050 Edificios OSM"
    assert description == "Descripcion traducida"
    assert hashtags == ["osm", "buildings", "simple"]
    assert location_str is None


def _fake_entities(rows: list[dict]) -> SimpleNamespace:
    """Fake pyodk `client.entities`, recording writes in `calls`."""
    calls = {"updated": [], "created": [], "deleted": []}
    return SimpleNamespace(
        calls=calls,
        get_table=lambda **_: {"value": rows},
        update=lambda uuid, data, **_: calls["updated"].append((uuid, data)),
        create_many=lambda data, **_: calls["created"].extend(data),
        delete=lambda uuid, **_: calls["deleted"].append(uuid),
    )


def _fake_pyodk_client(entities):
    client = SimpleNamespace(
        entities=entities,
        entity_lists=SimpleNamespace(
            list=lambda **_: [SimpleNamespace(name="tasks")],
            create=lambda **_: pytest.fail("dataset exists"),
        ),
        session=SimpleNamespace(
            get=lambda _path: SimpleNamespace(status_code=200, json=list),
            post=lambda *_a, **_k: SimpleNamespace(status_code=201),
        ),
    )

    @asynccontextmanager
    async def fake(_creds):
        yield client

    return fake


def _odk_row(task_id: int, status: str = "mapped") -> dict:
    return {
        "__id": f"uuid-{task_id}",
        "__system": {"version": 1},
        "label": f"Task {task_id}",
        "geometry": "old",
        "task_id": str(task_id),
        "status": status,
        "assigned_to": "",
    }


@pytest.mark.parametrize(("reset", "status"), [(False, None), (True, "ready")])
async def test_sync_odk_tasks_updates_or_resets_and_deletes(reset, status):
    """Re-sync updates task 1, adds task 3, deletes task 2; reset sets status."""
    project = FakeProject(
        task_areas_geojson={
            "type": "FeatureCollection",
            "features": [
                _task_feature(properties={"task_id": 1, "assigned_to": "Bo"}),
                _task_feature(properties={"task_id": 3}),
            ],
        }
    )
    entities = _fake_entities([_odk_row(1), _odk_row(2)])

    async def fake_feature_geojson_to_entity_dict(feature, **kwargs):
        return {"label": "", "data": {"geometry": "old"}}

    with (
        patch(
            "app.central.central_crud.feature_geojson_to_entity_dict",
            side_effect=fake_feature_geojson_to_entity_dict,
        ),
        patch(
            "app.central.central_crud.central_deps.pyodk_client",
            _fake_pyodk_client(entities),
        ),
    ):
        await sync_odk_tasks(project, None, 17, reset=reset)

    [(uuid, update)] = entities.calls["updated"]
    assert uuid == "uuid-1"
    assert update["assigned_to"] == "Bo"
    assert update.get("status") == status
    assert [row["label"] for row in entities.calls["created"]] == ["Task 3"]
    assert entities.calls["deleted"] == ["uuid-2"]


# ---------------------------------------------------------------------------
# Updating the form of a published project
# ---------------------------------------------------------------------------


async def _build_processed_form(**options) -> bytes:
    _, form = await central_crud.append_fields_to_user_xlsform(
        BytesIO(convert_to_xlsform(str(buildings))),
        form_name="FTM_Project_1",
        use_odk_collect=True,
        form_id="published-form-id",
        **options,
    )
    return form.getvalue()


async def test_update_odk_project_form_keeps_id_and_options():
    """A new upload keeps the published form ID and the project's form options."""
    project = DbProject(
        id=1,
        external_project_id=5,
        xlsform_content=await _build_processed_form(include_photo_upload=False),
    )
    upload = BytesIO(convert_to_xlsform(str(buildings)))

    with (
        patch.object(central_crud, "update_odk_xform", AsyncMock()) as update_xform,
        patch.object(DbProject, "update", AsyncMock()) as update_db,
    ):
        await project_services.update_odk_project_form(AsyncMock(), project, upload)

    odk_id, form_id, xform, _ = update_xform.await_args.args
    assert (odk_id, form_id) == (5, "published-form-id")
    assert 'id="published-form-id"' in xform.getvalue().decode()
    assert "survey_photos" not in xform.getvalue().decode()
    stored = update_db.await_args.args[2].xlsform_content
    assert get_processed_form_options(stored)["form_id"] == "published-form-id"


async def test_update_odk_project_form_keeps_new_point_capture():
    """A published GPS capture form stays GPS capture after a form update."""
    project = DbProject(
        id=1,
        external_project_id=5,
        xlsform_content=await _build_processed_form(
            new_point_capture=NewPointCapture.GPS
        ),
    )
    upload = BytesIO(convert_to_xlsform(str(buildings)))

    with (
        patch.object(central_crud, "update_odk_xform", AsyncMock()),
        patch.object(DbProject, "update", AsyncMock()) as update_db,
    ):
        await project_services.update_odk_project_form(AsyncMock(), project, upload)

    stored = update_db.await_args.args[2].xlsform_content
    assert get_processed_form_options(stored)["new_point_capture"] == (
        NewPointCapture.GPS
    )


async def test_update_odk_project_form_keeps_stored_form_if_central_fails():
    """Field-TM's copy must keep matching ODK when publishing fails."""
    project = DbProject(
        id=1,
        external_project_id=5,
        xlsform_content=await _build_processed_form(),
    )
    upload = BytesIO(convert_to_xlsform(str(buildings)))

    with (
        patch.object(
            central_crud,
            "update_odk_xform",
            AsyncMock(side_effect=ServiceError("Central said no")),
        ),
        patch.object(DbProject, "update", AsyncMock()) as update_db,
        pytest.raises(ServiceError),
    ):
        await project_services.update_odk_project_form(AsyncMock(), project, upload)

    update_db.assert_not_awaited()
