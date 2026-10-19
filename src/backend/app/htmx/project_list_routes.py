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

"""Project listing HTMX routes."""

from urllib.parse import urlencode

from litestar import get
from litestar.di import Provide
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.response import Template
from psycopg import AsyncConnection

from app.auth.auth_deps import get_optional_auth_user
from app.config import AuthProvider, settings
from app.db.database import db_conn
from app.db.enums import ProjectStatus
from app.db.models import DbProject

PAGE_SIZE = 12
PROJECT_SORT_OPTIONS = {
    "newest",
    "oldest",
    "name_asc",
    "name_desc",
}


def _create_project_href(auth_user: object | None) -> str:
    """Return the correct create-project target for the current auth state."""
    if settings.AUTH_PROVIDER == AuthProvider.DISABLED or auth_user is not None:
        return "/new"
    return "/login?return_to=%2Fnew"


def _parse_page(raw: str | None) -> int:
    try:
        return max(int(raw or 1), 1)
    except ValueError:
        return 1


def _page_href(filters: dict[str, str], page: int) -> str:
    params = {key: value for key, value in filters.items() if value}
    if page > 1:
        params["page"] = str(page)
    return f"/projects?{urlencode(params)}" if params else "/projects"


@get(
    path="/projects",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(get_optional_auth_user),
    },
)
async def project_listing(
    request: HTMXRequest, db: AsyncConnection, auth_user: object | None
) -> Template:
    """Render public project listing page."""
    status_param = request.query_params.get("status")
    search_query = (request.query_params.get("search") or "").strip()
    sort_param = request.query_params.get("sort") or "newest"
    selected_status = None
    selected_sort = sort_param if sort_param in PROJECT_SORT_OPTIONS else "newest"

    if status_param:
        try:
            selected_status = ProjectStatus(status_param.upper())
        except ValueError:
            selected_status = None

    page = _parse_page(request.query_params.get("page"))
    # Fetch one extra row to know whether a next page exists.
    projects = (
        await DbProject.all(
            db,
            skip=(page - 1) * PAGE_SIZE,
            limit=PAGE_SIZE + 1,
            status=selected_status,
            search=search_query or None,
            sort_by=selected_sort,
        )
        or []
    )
    has_next = len(projects) > PAGE_SIZE
    filters = {
        "status": selected_status.value if selected_status else "",
        "search": search_query,
        "sort": selected_sort,
    }
    return HTMXTemplate(
        template_name="home.html",
        context={
            "projects": projects[:PAGE_SIZE],
            "page": page,
            "prev_href": _page_href(filters, page - 1) if page > 1 else None,
            "next_href": _page_href(filters, page + 1) if has_next else None,
            "selected_status": selected_status.value if selected_status else "",
            "search_query": search_query,
            "selected_sort": selected_sort,
            "create_project_href": _create_project_href(auth_user),
        },
    )
