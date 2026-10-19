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
"""Routes to help with common processes in the Field-TM workflow (Litestar)."""

import logging

from litestar import Response, Router, get
from litestar import status_codes as status
from litestar.exceptions import HTTPException
from osm_fieldwork.conversion_to_xlsform import convert_to_xlsform
from osm_fieldwork.xlsforms import xlsforms_path

from app.db.enums import XLSFormType
from app.i18n import _

log = logging.getLogger(__name__)


@get(
    "/download-template-xlsform",
)
async def download_template(
    form_type: XLSFormType,
) -> Response[bytes]:
    """Download example XLSForm from Field-TM."""
    form_filename = XLSFormType(form_type).name
    form_path = f"{xlsforms_path}/{form_filename}.yaml"
    xlsx_bytes = convert_to_xlsform(str(form_path))
    if xlsx_bytes:
        return Response(
            content=xlsx_bytes,
            media_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            headers={
                "Content-Disposition": f"attachment; filename={form_filename}.xlsx"
            },
            status_code=status.HTTP_200_OK,
        )
    msg = _("Failed to convert YAML form to XLSForm.")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=msg,
    )


helper_router = Router(
    path="/api/v1/helpers",
    tags=["api"],
    route_handlers=[download_template],
)
