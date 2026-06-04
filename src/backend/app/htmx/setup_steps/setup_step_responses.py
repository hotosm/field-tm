"""Shared response builders for setup-step HTMX routes."""

# ruff: noqa: D103

import json
from typing import TYPE_CHECKING

from litestar import status_codes as status
from litestar.response import Response, Template

from app.db.models import DbProject
from app.i18n import _
from app.projects.project_services import (
    ODKFinalizeResult,
    QFieldFinalizeResult,
    ServiceError,
)
from app.projects.project_services import ValidationError as SvcValidationError

from ..htmx_helpers import callout as _callout

if TYPE_CHECKING:
    from app.auth.auth_schemas import ProjectUserDict


def _hx_trigger_header(
    event: str, payload: dict[str, object] | None = None
) -> dict[str, str]:
    trigger_payload: dict[str, object] = {event: payload or {}}
    return {"HX-Trigger": json.dumps(trigger_payload)}


def hx_redirect_response(
    location: str,
    *,
    status_code: int = status.HTTP_200_OK,
    header_name: str = "HX-Redirect",
    headers: dict[str, str] | None = None,
) -> Response:
    response_headers = {header_name: location}
    if headers:
        response_headers.update(headers)
    return Response(
        content="",
        media_type="text/html",
        status_code=status_code,
        headers=response_headers,
    )


def hx_trigger_response(
    content: str,
    *,
    event: str,
    payload: dict[str, object] | None = None,
    status_code: int = status.HTTP_200_OK,
    media_type: str = "text/html",
) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        status_code=status_code,
        headers=_hx_trigger_header(event, payload),
    )


def unexpected_error_response(message: str | None = None) -> Response:
    error_msg = message or unexpected_error_message()
    return html_error_response(
        _("Error: %(error_msg)s") % {"error_msg": error_msg},
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def authorized_project_or_response(
    current_user: "ProjectUserDict", project_id: int
) -> tuple["DbProject | None", Response | None]:
    project = current_user.get("project")
    if not project or project.id != project_id:
        return None, project_not_found_response()
    return project, None


def unexpected_error_message() -> str:
    return _("An unexpected error occurred")


def project_not_found_response() -> Response:
    return Response(
        content=_callout("danger", _("Project not found or access denied.")),
        media_type="text/html",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def html_error_response(message: str, status_code: int) -> Response:
    return Response(
        content=_callout("danger", message),
        media_type="text/html",
        status_code=status_code,
        headers={"Vary": "HX-Request"},
    )


def json_error_response(message: str, status_code: int) -> Response:
    return Response(
        content=json.dumps({"error": message}),
        media_type="application/json",
        status_code=status_code,
        headers={"Vary": "HX-Request"},
    )


def service_error_response(error: ServiceError) -> Response:
    status_code = (
        status.HTTP_400_BAD_REQUEST
        if isinstance(error, SvcValidationError)
        else status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    return Response(
        content=_callout("danger", error.message),
        media_type="text/html",
        status_code=status_code,
        headers={"Vary": "HX-Request"},
    )


def _format_technical_error_details(raw_details: object) -> str:
    if raw_details is None:
        return ""
    if isinstance(raw_details, (dict, list)):
        return json.dumps(raw_details, indent=2, ensure_ascii=False)

    raw_text = str(raw_details).strip()
    if not raw_text:
        return ""

    try:
        parsed = json.loads(raw_text)
    except (json.JSONDecodeError, TypeError):
        return raw_text

    if isinstance(parsed, (dict, list)):
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    return raw_text


def _is_technical_error_text(error_text: str) -> bool:
    stripped = error_text.strip()
    if not stripped:
        return False
    if stripped.startswith("{") or stripped.startswith("["):
        return True
    return any(marker in stripped for marker in ('"detail"', '"error"', "'detail'"))


def build_finalize_error_html(raw_error: object) -> Template:
    technical_details = _format_technical_error_details(raw_error)
    generic_message = _(
        "Project finalisation failed. Please check your settings and try again. "
        "If it continues, send the technical details below to your instance "
        "administrator or support team."
    )

    if technical_details and not _is_technical_error_text(technical_details):
        user_message = technical_details
    else:
        user_message = generic_message

    return Template(
        template_name="partials/project_details/fragments/finalize_error.html",
        context={
            "user_message": user_message,
            "technical_details": technical_details or "",
        },
        media_type="text/html",
        status_code=status.HTTP_200_OK,
    )


def finalize_error_response(raw_error: object, status_code: int) -> Response:
    template = build_finalize_error_html(raw_error)
    template.status_code = status_code
    template.headers = {"Vary": "HX-Request"}
    return template


def build_odk_finalize_success_html(
    result: ODKFinalizeResult, *, project_id: int | None = None
) -> Template:
    payload: dict[str, object] = {"provider": "ODK"}
    if project_id is not None:
        payload["projectId"] = project_id
    return Template(
        template_name="partials/project_details/fragments/finalize_success_odk.html",
        context={"result": result},
        media_type="text/html",
        status_code=status.HTTP_200_OK,
        headers={
            "Vary": "HX-Request",
            **_hx_trigger_header("project-setup:finalize-complete", payload),
        },
    )


def build_qfield_finalize_success_html(
    result: QFieldFinalizeResult, *, project_id: int | None = None
) -> Template:
    payload: dict[str, object] = {"provider": "QField"}
    if project_id is not None:
        payload["projectId"] = project_id
    return Template(
        template_name="partials/project_details/fragments/finalize_success_qfield.html",
        context={
            "result": result,
            "project_id": project_id,
        },
        media_type="text/html",
        status_code=status.HTTP_200_OK,
        headers={
            "Vary": "HX-Request",
            **_hx_trigger_header("project-setup:finalize-complete", payload),
        },
    )


def build_data_extract_preview_response(
    *,
    status_message: str,
    preview_message: str,
    map_html_content: str,
    project_id: int,
) -> Template:
    return Template(
        template_name="partials/project_details/fragments/data_extract_preview.html",
        context={
            "status_variant": "success",
            "status_message": status_message,
            "preview_message": preview_message,
            "map_html_content": map_html_content,
            "project_id": project_id,
        },
        media_type="text/html",
        status_code=status.HTTP_200_OK,
        headers={"Vary": "HX-Request"},
    )


def is_fragment_mode(mode: str | None) -> bool:
    return (mode or "").strip().lower() == "fragment"


def step4_completion_response(
    *,
    request: object,
    project_id: int,
    message: str,
    mode: str | None,
    project: "DbProject | None" = None,
) -> Response:
    trigger_payload = {
        "projectId": project_id,
        "step": 4,
        "nextStep": 5,
        "code": "step4_complete",
        "message": message,
    }
    if not is_fragment_mode(mode):
        return Response(
            content=_callout("success", message),
            media_type="text/html",
            status_code=status.HTTP_200_OK,
            headers=_hx_trigger_header("project-setup:step4-complete", trigger_payload),
        )

    return Template(
        template_name="partials/project_details/setup_steps.html",
        context={"project": project},
        media_type="text/html",
        status_code=status.HTTP_200_OK,
        headers={
            "Vary": "HX-Request",
            **_hx_trigger_header("project-setup:step4-complete", trigger_payload),
        },
    )
