"""Template and upload helpers for project-create HTMX routes."""

# ruff: noqa: D103

import logging
from io import BytesIO
from pathlib import Path

from litestar import status_codes as status
from litestar.exceptions import HTTPException
from litestar.response import Response
from osm_fieldwork.conversion_to_xlsform import convert_to_xlsform
from osm_fieldwork.xlsforms import xlsforms_path
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.db.enums import XLSFormType
from app.htmx.htmx_schemas import XLSFormUploadData
from app.i18n import _

from ..htmx_helpers import callout as _callout

log = logging.getLogger(__name__)


def template_form_type_from_title(form_title: str | None) -> XLSFormType | None:
    if not form_title:
        return None
    return next(
        (xls_type for xls_type in XLSFormType if xls_type.value == form_title),
        None,
    )


async def get_template_xlsform_bytes(form_id: int, db: AsyncConnection) -> bytes | None:
    sql = """
        SELECT title, xls
        FROM template_xlsforms
        WHERE id = %(form_id)s;
    """

    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(sql, {"form_id": form_id})
        result = await cur.fetchone()

    if not result:
        return None

    if result.get("xls"):
        return result["xls"]

    form_type = template_form_type_from_title(result.get("title"))
    if not form_type:
        return None

    try:
        form_path = f"{xlsforms_path}/{form_type.name}.yaml"
        xlsx_bytes = convert_to_xlsform(str(form_path))
        if xlsx_bytes:
            return xlsx_bytes
    except Exception as e:
        log.error(f"Error converting YAML to XLSForm: {e}", exc_info=True)

    return None


async def get_default_buildings_template_bytes(db: AsyncConnection) -> bytes | None:
    sql = """
        SELECT id
        FROM template_xlsforms
        WHERE title = %(title)s
        ORDER BY id
        LIMIT 1;
    """

    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(sql, {"title": XLSFormType.buildings.value})
        result = await cur.fetchone()

    if result and result.get("id") is not None:
        xlsx_bytes = await get_template_xlsform_bytes(int(result["id"]), db)
        if xlsx_bytes:
            return xlsx_bytes

    try:
        fallback_path = f"{xlsforms_path}/{XLSFormType.buildings.name}.yaml"
        return convert_to_xlsform(fallback_path)
    except Exception as e:
        log.error(
            "Error converting default OSM Buildings YAML to XLSForm: %s",
            e,
            exc_info=True,
        )
        return None


async def validate_xlsform_extension(data: XLSFormUploadData) -> BytesIO:
    filename = Path(data.filename or "")
    file_ext = filename.suffix.lower()

    if file_ext not in [".xls", ".xlsx"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_("Provide a valid .xls or .xlsx file"),
        )

    return BytesIO(await data.read())


async def resolve_uploaded_xlsform_bytes(
    data: XLSFormUploadData,
    db: AsyncConnection,
) -> tuple[BytesIO | None, Response | None]:
    template_form_id_str = str(data.template_form_id) if data.template_form_id else ""
    if template_form_id_str:
        template_bytes = await get_template_xlsform_bytes(int(template_form_id_str), db)
        if not template_bytes:
            return None, Response(
                content=_callout("danger", _("Failed to load template form.")),
                media_type="text/html",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return BytesIO(template_bytes), None

    if not data.xlsform:
        return None, Response(
            content=_callout("danger", _("Please select a form or upload a file.")),
            media_type="text/html",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return await validate_xlsform_extension(data.xlsform), None
