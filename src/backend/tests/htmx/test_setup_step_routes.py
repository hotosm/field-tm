"""Tests for HTMX routes."""

import json
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import Mock

from litestar import Router
from litestar import status_codes as status

from app.db.models import DbProject
from app.htmx.setup_steps import (
    setup_step_extract_handlers,
    setup_step_finalize_routes,
)
from app.htmx.setup_steps.setup_step_extract_routes import (
    accept_data_extract_htmx,
    download_osm_data_htmx,
    upload_geojson_htmx,
)
from app.htmx.setup_steps.setup_step_finalize_routes import (
    add_qfc_collaborator_htmx,
    create_project_htmx,
)
from app.htmx.setup_steps.setup_step_map_layers import (
    build_split_preview_response,
    task_boundaries_layer,
)
from app.htmx.setup_steps.setup_step_responses import (
    build_finalize_error_html,
    build_odk_finalize_success_html,
    build_qfield_finalize_success_html,
    step4_completion_response,
)
from app.projects.project_services import (
    ODKFinalizeResult,
)
from app.projects.project_services import ValidationError as SvcValidationError

# We patch where project_crud is used/defined.
# htmx_routes imports `from app.projects import project_crud`
# so we patch `app.projects.project_crud.get_project_qrcode`


def test_step5_dispatch_route_is_registered():
    """The template-facing finalization endpoint must be exported to the router."""
    assert create_project_htmx in setup_step_finalize_routes.ROUTE_HANDLERS


def test_step5_finalize_routes_register_with_litestar():
    """Finalize route exports must be decorated route handlers."""
    Router(path="/", route_handlers=setup_step_finalize_routes.ROUTE_HANDLERS)


async def test_add_qfc_collaborator_escapes_success_message(monkeypatch):
    """Collaborator success feedback must not render submitted HTML."""
    project = SimpleNamespace(
        id=42,
        external_project_id="qfc-project-42",
        external_project_instance_url="https://default-qfc.example.org/projects/42",
    )
    captured = {}

    async def fake_project_one(_db, project_id):
        assert project_id == project.id
        return project

    @asynccontextmanager
    async def fake_qfield_client():
        yield object()

    async def fake_add_collaborator(_client, qfc_project_id, username, role):
        captured["qfc_project_id"] = qfc_project_id
        captured["username"] = username
        captured["role"] = role.value

    monkeypatch.setattr(
        "app.qfield.qfield_utils.settings.QFIELDCLOUD_URL",
        "https://default-qfc.example.org/api/v1/",
    )
    monkeypatch.setattr(setup_step_finalize_routes.DbProject, "one", fake_project_one)
    monkeypatch.setattr(
        setup_step_finalize_routes,
        "qfield_client",
        fake_qfield_client,
    )
    monkeypatch.setattr(
        setup_step_finalize_routes,
        "add_qfc_project_collaborator",
        fake_add_collaborator,
    )

    response = await add_qfc_collaborator_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=project.id,
        data={"qfc_username": "<img src=x onerror=alert(1)>"},
    )

    body = str(response.content)
    assert response.status_code == status.HTTP_200_OK
    assert "<img src=x onerror=alert(1)>" not in body
    assert "&lt;img src=x onerror=alert(1)&gt;" in body
    assert captured == {
        "qfc_project_id": "qfc-project-42",
        "username": "<img src=x onerror=alert(1)>",
        "role": "editor",
    }


async def test_add_qfc_collaborator_escapes_httpexception_error(monkeypatch):
    """Error-path messages from the QFC SDK must not render submitted HTML."""
    from litestar.exceptions import HTTPException

    project = SimpleNamespace(
        id=44,
        external_project_id="qfc-project-44",
        external_project_instance_url="https://default-qfc.example.org/projects/44",
    )

    async def fake_project_one(_db, project_id):
        assert project_id == project.id
        return project

    @asynccontextmanager
    async def fake_qfield_client():
        yield object()

    async def fake_add_collaborator(_client, _qfc_project_id, _username, _role):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QFC user '<script>alert(1)</script>' not found.",
        )

    monkeypatch.setattr(
        "app.qfield.qfield_utils.settings.QFIELDCLOUD_URL",
        "https://default-qfc.example.org/api/v1/",
    )
    monkeypatch.setattr(setup_step_finalize_routes.DbProject, "one", fake_project_one)
    monkeypatch.setattr(
        setup_step_finalize_routes,
        "qfield_client",
        fake_qfield_client,
    )
    monkeypatch.setattr(
        setup_step_finalize_routes,
        "add_qfc_project_collaborator",
        fake_add_collaborator,
    )

    response = await add_qfc_collaborator_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=project.id,
        data={"qfc_username": "alice"},
    )

    body = str(response.content)
    assert response.status_code == status.HTTP_200_OK
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in body


async def test_add_qfc_collaborator_blocks_custom_qfc_instance(monkeypatch):
    """Post-finalize collaborator add must not target the default QFC by mistake."""
    project = SimpleNamespace(
        id=43,
        external_project_id="custom-project-43",
        external_project_instance_url="https://custom-qfc.example.org/projects/43",
    )
    add_collaborator = Mock()

    async def fake_project_one(_db, project_id):
        assert project_id == project.id
        return project

    monkeypatch.setattr(
        "app.qfield.qfield_utils.settings.QFIELDCLOUD_URL",
        "https://default-qfc.example.org/api/v1/",
    )
    monkeypatch.setattr(setup_step_finalize_routes.DbProject, "one", fake_project_one)
    monkeypatch.setattr(
        setup_step_finalize_routes,
        "add_qfc_project_collaborator",
        add_collaborator,
    )

    response = await add_qfc_collaborator_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=project.id,
        data={"qfc_username": "alice"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "custom QFieldCloud instance" in str(response.content)
    add_collaborator.assert_not_called()


async def test_project_setup_shows_step1_advanced_config_toggle(client, stub_project):
    """Draft setup should show a basic-first Step 1 with advanced config."""
    response = await client.get(
        f"/projects/{stub_project.id}",
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "Choose Your Survey Form" in response.text
    assert "Continue" in response.text
    assert "More options" in response.text
    assert response.text.index("Form language") < response.text.index("Form questions")


async def test_project_setup_shows_step2_advanced_config_options(client, db, project):
    """Step 2 should expose custom data paths only under advanced config."""
    await DbProject.update(
        db,
        project.id,
        DbProject(xlsform_content=b"test xlsform"),
    )
    await db.commit()

    response = await client.get(
        f"/projects/{project.id}",
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "Use OSM data" in response.text
    assert "Start with empty map" in response.text
    assert "upload your own map file (GeoJSON)" in response.text
    assert response.text.index("data-advanced-config-toggle") < response.text.index(
        'id="osm-data-status"'
    )


async def test_project_setup_hides_step2_actions_when_data_extract_is_complete(
    client, db, project
):
    """Completed Step 2 should collapse actions and focus user on Step 3."""
    await DbProject.update(
        db,
        project.id,
        DbProject(
            xlsform_content=b"test xlsform",
            data_extract_geojson={"type": "FeatureCollection", "features": []},
        ),
    )
    await db.commit()

    response = await client.get(
        f"/projects/{project.id}",
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "Data extract ready" in response.text
    assert 'id="download-osm-data-btn"' not in response.text
    assert 'id="collect-new-data-btn"' not in response.text
    assert 'id="upload-geojson-btn"' not in response.text
    assert 'id="preview-data-extract-btn"' not in response.text


async def test_collect_new_data_only_htmx_sets_empty_feature_collection(
    client, db, project
):
    """Collect-new-data option should persist an empty FeatureCollection."""
    response = await client.post(
        f"/collect-new-data-only-htmx?project_id={project.id}",
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    hx_trigger = json.loads(response.headers.get("HX-Trigger", "{}"))
    trigger_payload = hx_trigger.get("project-setup:step3-complete")
    assert trigger_payload is not None
    assert trigger_payload["projectId"] == project.id
    assert trigger_payload["step"] == 3
    assert trigger_payload["nextStep"] == 4
    assert trigger_payload["code"] == "collect_new_data_enabled"
    assert "Collect-new-data mode selected" in response.text
    assert "Task splitting is skipped" in response.text

    updated_project = await DbProject.one(db, project.id)
    assert updated_project.data_extract_geojson == {
        "type": "FeatureCollection",
        "features": [],
    }
    assert updated_project.task_areas_geojson == {}


async def test_download_osm_data_htmx_returns_requested_no_data_message(monkeypatch):
    """No-feature validation errors should surface the requested OSM no-data copy."""
    project = Mock(id=42)

    async def fake_download_osm_data(**_kwargs):
        raise SvcValidationError(
            "No data found in OSM. Please continue with the Collect New "
            "Data Only option."
        )

    monkeypatch.setattr(
        setup_step_extract_handlers,
        "download_osm_data",
        fake_download_osm_data,
    )

    response = await download_osm_data_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=project.id,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        "No data found in OSM. Please continue with the Collect New Data Only option."
        in str(response.content)
    )


async def test_upload_geojson_htmx_accepts_multipolygon_with_utf8_tags(monkeypatch):
    """Upload should accept OSM-style GeoJSON properties including UTF-8 tags."""
    uploaded_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [
                            [
                                [85.3000, 27.7140],
                                [85.3000, 27.7130],
                                [85.3010, 27.7130],
                                [85.3010, 27.7140],
                                [85.3000, 27.7140],
                            ]
                        ]
                    ],
                },
                "properties": {
                    "osm_id": 24691221,
                    "tags": {
                        "name": "पुष्पलाल पथ ;स्वयम्भु मार्ग",
                        "name:en": "Pushpalal Path;Swoyambhu Marg",
                    },
                },
            }
        ],
    }
    uploaded_bytes = json.dumps(uploaded_geojson, ensure_ascii=False).encode("utf-8")
    captured: dict = {}
    project = Mock(id=42)

    def fake_parse_aoi(_db_url, input_geojson, merge=True):
        captured["payload"] = input_geojson
        captured["merge"] = merge
        return uploaded_geojson

    async def fake_check_crs(_featcol):
        return None

    class FakeUploadFile:
        filename = "osm-export.geojson"

        async def read(self):
            return uploaded_bytes

    monkeypatch.setattr(setup_step_extract_handlers, "parse_aoi", fake_parse_aoi)
    monkeypatch.setattr(setup_step_extract_handlers, "check_crs", fake_check_crs)

    response = await upload_geojson_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        data=FakeUploadFile(),
        project_id=project.id,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.template_name.endswith("data_extract_preview.html")
    assert response.context["status_variant"] == "success"
    assert (
        "GeoJSON uploaded successfully! Found 1 features."
        in response.context["status_message"]
    )
    assert "Accept Data Extract" in response.context["preview_message"]
    assert captured["payload"] == uploaded_bytes
    assert captured["merge"] is False


async def test_accept_data_extract_htmx_decodes_html_escaped_geojson(monkeypatch):
    """Accept-data route should tolerate HTML-escaped JSON form values."""
    saved: dict = {}
    project = Mock(id=42)
    escaped_geojson = (
        '{&quot;type&quot;: "FeatureCollection", '
        '&quot;features&quot;: [{&quot;type&quot;: "Feature", '
        "&quot;geometry&quot;: null, &quot;properties&quot;: {}}]}"
    )
    feature_collection = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "geometry": None, "properties": {}}],
    }

    async def fake_save_data_extract(*, db, project_id, geojson_data):
        saved["db"] = db
        saved["project_id"] = project_id
        saved["geojson_data"] = geojson_data
        return len(geojson_data["features"])

    monkeypatch.setattr(
        "app.htmx.setup_steps.setup_step_extract_handlers.save_data_extract",
        fake_save_data_extract,
    )

    response = await accept_data_extract_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        data={"data_extract_geojson": escaped_geojson},
        project_id=project.id,
    )

    assert response.status_code == status.HTTP_200_OK
    hx_trigger = json.loads(response.headers.get("HX-Trigger", "{}"))
    trigger_payload = hx_trigger.get("project-setup:step3-complete")
    assert trigger_payload is not None
    assert trigger_payload["projectId"] == project.id
    assert saved["project_id"] == project.id
    assert saved["geojson_data"] == feature_collection


def test_task_boundaries_layer_uses_translated_popup_labels():
    """Task boundary popups should show translated labels without layer name."""
    layer = task_boundaries_layer(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": None,
                    "properties": {"task_id": 3, "building_count": 14},
                }
            ],
        }
    )

    assert layer["popup_options"]["showLayerName"] is False
    assert layer["popup_options"]["propertyLabels"] == {
        "task_id": "Task ID",
        "building_count": "Building Count",
    }
    assert layer["popup_options"]["propertyOrder"] == ["task_id", "building_count"]


def test_build_odk_finalize_success_html_includes_manager_credentials():
    """ODK finalize helper should return template context with manager credentials."""
    result = ODKFinalizeResult(
        odk_url="https://central.example.org/#/projects/17",
        manager_username="field-tm-manager@fieldtm.org",
        manager_password="StrongPass123!",
    )

    response_template = build_odk_finalize_success_html(result, project_id=17)

    assert response_template.template_name.endswith("finalize_success_odk.html")
    hx_trigger = json.loads(response_template.headers.get("HX-Trigger", "{}"))
    trigger_payload = hx_trigger.get("project-setup:finalize-complete")
    assert trigger_payload is not None
    assert trigger_payload["projectId"] == 17
    assert response_template.context["result"].manager_username == (
        "field-tm-manager@fieldtm.org"
    )
    assert response_template.context["result"].manager_password == "StrongPass123!"


def test_build_odk_finalize_success_html_does_not_render_qr_markup():
    """ODK finalize helper should use ODK success fragment, not QField QR fragment."""
    result = ODKFinalizeResult(
        odk_url="https://central.example.org/#/projects/17",
        manager_username="field-tm-manager@fieldtm.org",
        manager_password="StrongPass123!",
    )

    response_template = build_odk_finalize_success_html(result)

    assert response_template.template_name.endswith("finalize_success_odk.html")
    assert not response_template.template_name.endswith("finalize_success_qfield.html")
    hx_trigger = json.loads(response_template.headers.get("HX-Trigger", "{}"))
    trigger_payload = hx_trigger.get("project-setup:finalize-complete")
    assert trigger_payload is not None
    assert trigger_payload["provider"] == "ODK"


def test_build_qfield_finalize_success_html_emits_finalize_event():
    """QField finalize helper should emit explicit finalize-complete trigger."""
    result = SimpleNamespace(
        qfield_url="https://app.qfield.cloud/projects/99",
        manager_username="manager@fieldtm.org",
        manager_password="Pass123!",
    )

    response_template = build_qfield_finalize_success_html(result, project_id=99)

    assert response_template.template_name.endswith("finalize_success_qfield.html")
    hx_trigger = json.loads(response_template.headers.get("HX-Trigger", "{}"))
    trigger_payload = hx_trigger.get("project-setup:finalize-complete")
    assert trigger_payload is not None
    assert trigger_payload["provider"] == "QField"
    assert trigger_payload["projectId"] == 99


def test_build_qfield_finalize_success_hides_custom_instance_collaborator_form(
    monkeypatch,
):
    """Custom QFC projects must not show a form that posts to default creds."""
    monkeypatch.setattr(
        "app.qfield.qfield_utils.settings.QFIELDCLOUD_URL",
        "https://default-qfc.example.org/api/v1/",
    )
    result = SimpleNamespace(
        qfield_url="https://custom-qfc.example.org/projects/99",
        manager_username="manager@fieldtm.org",
        manager_password="Pass123!",
    )

    response_template = build_qfield_finalize_success_html(result, project_id=99)

    assert response_template.context["show_collaborator_form"] is False


def test_build_qfield_finalize_success_shows_default_instance_collaborator_form(
    monkeypatch,
):
    """Default-instance QFC projects must surface the collaborator form."""
    monkeypatch.setattr(
        "app.qfield.qfield_utils.settings.QFIELDCLOUD_URL",
        "https://default-qfc.example.org/api/v1/",
    )
    result = SimpleNamespace(
        qfield_url="https://default-qfc.example.org/projects/100",
        manager_username="manager@fieldtm.org",
        manager_password="Pass123!",
    )

    response_template = build_qfield_finalize_success_html(result, project_id=100)

    assert response_template.context["show_collaborator_form"] is True
    assert response_template.context["project_id"] == 100


def test_build_split_preview_response_emits_step4_preview_event(monkeypatch):
    """Split preview helper should emit explicit step4-preview-ready trigger."""
    monkeypatch.setattr(
        "app.htmx.setup_steps.setup_step_map_layers.render_leaflet_map",
        lambda **_kwargs: "<div id='leaflet-map-split-preview'></div>",
    )

    project = SimpleNamespace(
        outline={
            "type": "Polygon",
            "coordinates": [
                [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0], [1.0, 0.0], [0.0, 0.0]]
            ],
        }
    )
    tasks_featcol = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[0.0, 0.0], [0.0, 0.5], [0.5, 0.5], [0.5, 0.0], [0.0, 0.0]]
                    ],
                },
                "properties": {"task_id": 1, "building_count": 5},
            }
        ],
    }
    data_extract = {"type": "FeatureCollection", "features": []}

    response_template = build_split_preview_response(
        project_id=44,
        algorithm="TOTAL_TASKS",
        tasks_featcol=tasks_featcol,
        data_extract=data_extract,
        project=project,
    )

    hx_trigger = json.loads(response_template.headers.get("HX-Trigger", "{}"))
    trigger_payload = hx_trigger.get("project-setup:step4-preview-ready")
    assert trigger_payload is not None
    assert trigger_payload["projectId"] == 44
    assert trigger_payload["taskCount"] == 1


def test_step4_completion_response_uses_explicit_project_id_in_trigger():
    """Step4 completion helper should emit provided project id in trigger payload."""
    request = Mock()
    request.template_context = {}

    response = step4_completion_response(
        request=request,
        project_id=77,
        message="done",
        mode="refresh",
    )

    hx_trigger = json.loads(response.headers.get("HX-Trigger", "{}"))
    trigger_payload = hx_trigger.get("project-setup:step4-complete")
    assert trigger_payload is not None
    assert trigger_payload["projectId"] == 77
    assert trigger_payload["step"] == 4
    assert trigger_payload["nextStep"] == 5


def test_build_finalize_error_html_prefers_friendly_text_for_plain_errors():
    """Plain-text errors should remain user-facing and include raw details."""
    response_template = build_finalize_error_html("Could not connect to ODK Central.")

    assert response_template.template_name.endswith("finalize_error.html")
    assert (
        response_template.context["user_message"] == "Could not connect to ODK Central."
    )
    assert (
        response_template.context["technical_details"]
        == "Could not connect to ODK Central."
    )


def test_build_finalize_error_html_uses_generic_text_for_json_payload():
    """Structured payloads should show a generic user-facing message."""
    response_template = build_finalize_error_html(
        '{"detail":"{"error":"invalid credentials"}"}'
    )

    assert response_template.template_name.endswith("finalize_error.html")
    assert "Project finalisation failed." in response_template.context["user_message"]
    assert '"detail"' in response_template.context["technical_details"]
