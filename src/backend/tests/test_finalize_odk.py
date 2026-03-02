"""Tests for the ODK project finalization service workflow.

These tests exercise finalize_odk_project end-to-end with fully mocked ODK
Central interactions, verifying that manager user creation and credential
delivery work correctly through the whole chain.
"""

from contextlib import asynccontextmanager
from dataclasses import dataclass
from io import BytesIO
from typing import Optional
from unittest.mock import AsyncMock, patch

import pytest

from app.central.central_schemas import ODKCentral
from app.projects.project_services import (
    ODKFinalizeResult,
    ServiceError,
    ValidationError,
    finalize_odk_project,
)

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


@pytest.mark.asyncio
async def test_finalize_odk_project_requires_xlsform():
    """Finalize should reject projects without XLSForm."""
    project = FakeProject(xlsform_content=b"")

    fake_db = AsyncMock()

    with (
        patch(
            "app.projects.project_services.DbProject.one",
            return_value=project,
        ),
        pytest.raises(ValidationError, match="XLSForm is required"),
    ):
        await finalize_odk_project(fake_db, project_id=1)


@pytest.mark.asyncio
async def test_finalize_odk_project_requires_data_extract():
    """Finalize should reject projects without a data extract."""
    project = FakeProject(data_extract_geojson=None)

    fake_db = AsyncMock()

    with (
        patch(
            "app.projects.project_services.DbProject.one",
            return_value=project,
        ),
        pytest.raises(ValidationError, match="Data extract is required"),
    ):
        await finalize_odk_project(fake_db, project_id=1)


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
        return ("fmtm-manager-42@example.org", "SecurePass12345abcde")

    @asynccontextmanager
    async def fake_get_odk_dataset(_):
        class FakeDataset:
            async def listDatasets(self, odk_id):  # noqa: N802
                return []

        yield FakeDataset()

    mock_create_entity_list = AsyncMock()

    creds = ODKCentral(
        external_project_instance_url="https://central.example.org",
        external_project_username="admin@example.org",
        external_project_password="secret",
    )

    with (
        patch(
            "app.projects.project_services.DbProject.one",
            return_value=project,
        ),
        patch(
            "app.projects.project_services.DbProject.update",
            new_callable=AsyncMock,
        ),
        patch(
            "app.projects.project_services.central_crud.create_odk_project",
            side_effect=fake_create_odk_project,
        ),
        patch(
            "app.projects.project_services.central_crud.create_entity_list",
            mock_create_entity_list,
        ),
        patch(
            "app.projects.project_services.central_crud.feature_geojson_to_entity_dict",
            side_effect=fake_feature_geojson_to_entity_dict,
        ),
        patch(
            "app.projects.project_services.central_crud.read_and_test_xform",
            side_effect=fake_read_and_test_xform,
        ),
        patch(
            "app.projects.project_services.central_crud.create_odk_xform",
            side_effect=fake_create_odk_xform,
        ),
        patch(
            "app.projects.project_services.project_crud.generate_project_files",
            side_effect=fake_generate_project_files,
        ),
        patch(
            "app.projects.project_services.central_crud.create_project_manager_user",
            side_effect=fake_create_project_manager_user,
        ),
        patch(
            "app.projects.project_services.central_deps.get_odk_dataset",
            fake_get_odk_dataset,
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


@pytest.mark.asyncio
async def test_finalize_odk_project_requires_odk_credentials():
    """Finalize should reject when no ODK credentials are available."""
    project = FakeProject()

    fake_db = AsyncMock()

    with (
        patch(
            "app.projects.project_services.DbProject.one",
            return_value=project,
        ),
        patch("app.projects.project_services.settings") as mock_settings,
    ):
        mock_settings.ODK_CENTRAL_URL = ""
        mock_settings.ODK_CENTRAL_USER = ""

        with pytest.raises(ValidationError, match="ODK Central credentials"):
            await finalize_odk_project(fake_db, project_id=1)


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
        return ("fmtm-manager-42@example.org", "SecurePass12345abcde")

    # Mock dataset check
    @asynccontextmanager
    async def fake_get_odk_dataset(_):
        class FakeDataset:
            async def listDatasets(self, odk_id):  # noqa: N802
                return []

        yield FakeDataset()

    creds = ODKCentral(
        external_project_instance_url="https://central.example.org",
        external_project_username="admin@example.org",
        external_project_password="secret",
    )

    with (
        patch(
            "app.projects.project_services.DbProject.one",
            return_value=project,
        ),
        patch(
            "app.projects.project_services.DbProject.update",
            new_callable=AsyncMock,
        ),
        patch(
            "app.projects.project_services.central_crud.create_odk_project",
            side_effect=fake_create_odk_project,
        ),
        patch(
            "app.projects.project_services.central_crud.create_entity_list",
            side_effect=fake_create_entity_list,
        ),
        patch(
            "app.projects.project_services.central_crud.task_geojson_dict_to_entity_values",
            side_effect=fake_task_geojson_dict_to_entity_values,
        ),
        patch(
            "app.projects.project_services.central_crud.feature_geojson_to_entity_dict",
            side_effect=fake_feature_geojson_to_entity_dict,
        ),
        patch(
            "app.projects.project_services.central_crud.read_and_test_xform",
            side_effect=fake_read_and_test_xform,
        ),
        patch(
            "app.projects.project_services.central_crud.create_odk_xform",
            side_effect=fake_create_odk_xform,
        ),
        patch(
            "app.projects.project_services.project_crud.generate_project_files",
            side_effect=fake_generate_project_files,
        ),
        patch(
            "app.projects.project_services.central_crud.create_project_manager_user",
            side_effect=fake_create_project_manager_user,
        ),
        patch(
            "app.projects.project_services.central_deps.get_odk_dataset",
            fake_get_odk_dataset,
        ),
    ):
        result = await finalize_odk_project(
            db=fake_db,
            project_id=1,
            custom_odk_creds=creds,
        )

    assert isinstance(result, ODKFinalizeResult)
    assert result.odk_url == "https://central.example.org/#/projects/42"
    assert result.manager_username == "fmtm-manager-42@example.org"
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
        return ("fmtm-manager-42@example.org", "SecurePass12345abcde")

    @asynccontextmanager
    async def fake_get_odk_dataset(_):
        class FakeDataset:
            async def listDatasets(self, odk_id):  # noqa: N802
                return []

        yield FakeDataset()

    mock_update = AsyncMock()

    creds = ODKCentral(
        external_project_instance_url="https://example-odk.trycloudflare.com",
        external_project_username="admin@example.org",
        external_project_password="secret",
    )

    with (
        patch(
            "app.projects.project_services.DbProject.one",
            return_value=project,
        ),
        patch(
            "app.projects.project_services.DbProject.update",
            mock_update,
        ),
        patch(
            "app.projects.project_services.central_crud.create_odk_project",
            side_effect=fake_create_odk_project,
        ),
        patch(
            "app.projects.project_services.central_crud.create_entity_list",
            side_effect=fake_create_entity_list,
        ),
        patch(
            "app.projects.project_services.central_crud.task_geojson_dict_to_entity_values",
            side_effect=fake_task_geojson_dict_to_entity_values,
        ),
        patch(
            "app.projects.project_services.central_crud.feature_geojson_to_entity_dict",
            side_effect=fake_feature_geojson_to_entity_dict,
        ),
        patch(
            "app.projects.project_services.central_crud.read_and_test_xform",
            side_effect=fake_read_and_test_xform,
        ),
        patch(
            "app.projects.project_services.central_crud.create_odk_xform",
            side_effect=fake_create_odk_xform,
        ),
        patch(
            "app.projects.project_services.project_crud.generate_project_files",
            side_effect=fake_generate_project_files,
        ),
        patch(
            "app.projects.project_services.central_crud.create_project_manager_user",
            side_effect=fake_create_project_manager_user,
        ),
        patch(
            "app.projects.project_services.central_deps.get_odk_dataset",
            fake_get_odk_dataset,
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
        return ("fmtm-manager-42@example.org", "SecurePass12345abcde")

    @asynccontextmanager
    async def fake_get_odk_dataset(_):
        class FakeDataset:
            async def listDatasets(self, odk_id):  # noqa: N802
                return []

        yield FakeDataset()

    with (
        patch(
            "app.projects.project_services.DbProject.one",
            return_value=project,
        ),
        patch(
            "app.projects.project_services.DbProject.update",
            new_callable=AsyncMock,
        ),
        patch(
            "app.projects.project_services.central_crud.create_entity_list",
            side_effect=fake_create_entity_list,
        ),
        patch(
            "app.projects.project_services.central_crud.task_geojson_dict_to_entity_values",
            side_effect=fake_task_geojson_dict_to_entity_values,
        ),
        patch(
            "app.projects.project_services.central_crud.feature_geojson_to_entity_dict",
            side_effect=fake_feature_geojson_to_entity_dict,
        ),
        patch(
            "app.projects.project_services.central_crud.read_and_test_xform",
            side_effect=fake_read_and_test_xform,
        ),
        patch(
            "app.projects.project_services.central_crud.create_odk_xform",
            side_effect=fake_create_odk_xform,
        ),
        patch(
            "app.projects.project_services.project_crud.generate_project_files",
            side_effect=fake_generate_project_files,
        ),
        patch(
            "app.projects.project_services.central_crud.create_project_manager_user",
            side_effect=fake_create_project_manager_user,
        ),
        patch(
            "app.projects.project_services.central_deps.get_odk_dataset",
            fake_get_odk_dataset,
        ),
        patch("app.projects.project_services.settings") as mock_settings,
    ):
        mock_settings.ODK_CENTRAL_URL = "http://central:8383"
        mock_settings.ODK_CENTRAL_PUBLIC_URL = "http://odk.fmtm.localhost:7050"
        mock_settings.ODK_CENTRAL_USER = "admin@example.org"

        result = await finalize_odk_project(
            db=fake_db,
            project_id=1,
            custom_odk_creds=None,
        )

    assert result.odk_url == "http://odk.fmtm.localhost:7050/#/projects/42"
    assert result.manager_username == "fmtm-manager-42@example.org"
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

    @asynccontextmanager
    async def fake_get_odk_dataset(_):
        class FakeDataset:
            async def listDatasets(self, odk_id):  # noqa: N802
                return []

        yield FakeDataset()

    creds = ODKCentral(
        external_project_instance_url="https://central.example.org",
        external_project_username="admin@example.org",
        external_project_password="secret",
    )

    with (
        patch(
            "app.projects.project_services.DbProject.one",
            return_value=project,
        ),
        patch(
            "app.projects.project_services.DbProject.update",
            new_callable=AsyncMock,
        ),
        patch(
            "app.projects.project_services.central_crud.create_entity_list",
            side_effect=fake_create_entity_list,
        ),
        patch(
            "app.projects.project_services.central_crud.task_geojson_dict_to_entity_values",
            side_effect=fake_task_geojson_dict_to_entity_values,
        ),
        patch(
            "app.projects.project_services.central_crud.read_and_test_xform",
            side_effect=fake_read_and_test_xform,
        ),
        patch(
            "app.projects.project_services.central_crud.create_odk_xform",
            side_effect=fake_create_odk_xform,
        ),
        patch(
            "app.projects.project_services.project_crud.generate_project_files",
            side_effect=fake_generate_project_files,
        ),
        patch(
            "app.projects.project_services.central_deps.get_odk_dataset",
            fake_get_odk_dataset,
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

    @asynccontextmanager
    async def fake_get_odk_dataset(_):
        class FakeDataset:
            async def listDatasets(self, odk_id):  # noqa: N802
                return []

        yield FakeDataset()

    creds = ODKCentral(
        external_project_instance_url="https://central.example.org",
        external_project_username="admin@example.org",
        external_project_password="secret",
    )

    with (
        patch(
            "app.projects.project_services.DbProject.one",
            return_value=project,
        ),
        patch(
            "app.projects.project_services.DbProject.update",
            new_callable=AsyncMock,
        ),
        patch(
            "app.projects.project_services.central_crud.create_entity_list",
            side_effect=fake_create_entity_list,
        ),
        patch(
            "app.projects.project_services.central_crud.task_geojson_dict_to_entity_values",
            side_effect=fake_task_geojson_dict_to_entity_values,
        ),
        patch(
            "app.projects.project_services.central_crud.feature_geojson_to_entity_dict",
            side_effect=fake_feature_geojson_to_entity_dict,
        ),
        patch(
            "app.projects.project_services.central_crud.read_and_test_xform",
            side_effect=fake_read_and_test_xform,
        ),
        patch(
            "app.projects.project_services.central_crud.create_odk_xform",
            side_effect=fake_create_odk_xform,
        ),
        patch(
            "app.projects.project_services.project_crud.generate_project_files",
            side_effect=fake_generate_project_files,
        ),
        patch(
            "app.projects.project_services.central_crud.create_project_manager_user",
            side_effect=fake_create_project_manager_user,
        ),
        patch(
            "app.projects.project_services.central_deps.get_odk_dataset",
            fake_get_odk_dataset,
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
    from app.projects.project_services import _build_feature_dataset_payload

    project = FakeProject(
        data_extract_geojson={"type": "FeatureCollection", "features": []}
    )

    entity_properties, entities_list = await _build_feature_dataset_payload(
        project_id=1,
        project=project,
    )

    assert entity_properties == []
    assert entities_list == []
