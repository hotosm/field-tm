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

"""Landing page and metrics HTMX routes."""

from urllib.parse import urlsplit, urlunsplit

from litestar import get
from litestar.di import Provide
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.response import Template
from psycopg import AsyncConnection

from app.auth.auth_deps import get_optional_auth_user
from app.db.database import db_conn
from app.htmx.project_list_routes import create_project_href


def _safe_return_path(return_to: str | None, host: str | None) -> str:
    """Reduce return_to to a same-origin path, to avoid open redirects.

    Callers pass either a path (``/new``) or, from the hotosm-auth header
    button, the full page URL. Anything pointing at another host becomes ``/``.
    """
    if not return_to:
        return "/"
    parts = urlsplit(return_to)
    if parts.netloc and parts.netloc != host:
        return "/"
    path = parts.path or "/"
    # Reject scheme-relative ("//evil.com") or backslash tricks after reduction.
    if not path.startswith("/") or path.startswith("//") or "\\" in path:
        return "/"
    return urlunsplit(("", "", path, parts.query, parts.fragment))


@get(path="/login")
async def login_page(request: HTMXRequest) -> Template:
    """Render the login page.

    For bundled (self-hosted) Hanko this embeds the login form directly; for
    other providers it redirects to the external login app.
    """
    return_to = _safe_return_path(
        request.query_params.get("return_to"), request.headers.get("host")
    )
    return HTMXTemplate(
        template_name="login.html",
        context={"return_to": return_to},
    )


@get(
    path="/",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(get_optional_auth_user),
    },
)
async def landing(
    request: HTMXRequest, db: AsyncConnection, auth_user: object | None
) -> Template:
    """Render public landing page."""
    return HTMXTemplate(
        template_name="landing.html",
        context={"create_project_href": create_project_href(auth_user)},
    )


@get(
    path="/metrics",
    dependencies={"db": Provide(db_conn)},
)
async def metrics_partial(request: HTMXRequest, db: AsyncConnection) -> Template:
    """Render landing metrics partial."""
    async with db.cursor() as cur:
        await cur.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM projects) AS project_count,
                (SELECT COUNT(*) FROM users) AS user_count,
                (
                    SELECT COALESCE(
                        SUM(
                            CASE
                                WHEN data_extract_geojson IS NULL THEN 0
                                WHEN jsonb_typeof(
                                    data_extract_geojson -> 'features'
                                ) = 'array'
                                    THEN jsonb_array_length(
                                        data_extract_geojson -> 'features'
                                    )
                                ELSE 0
                            END
                        ),
                        0
                    )
                    FROM projects
                ) AS mapped_features_count,
                (
                    SELECT COUNT(DISTINCT project_country)
                    FROM (
                        SELECT NULLIF(
                            BTRIM(REGEXP_REPLACE(location_str, '^.*,', '')),
                            ''
                        ) AS project_country
                        FROM projects
                        WHERE location_str IS NOT NULL
                    ) AS normalized_project_locations
                    WHERE project_country IS NOT NULL
                ) AS countries_covered;
            """
        )
        metrics_row = await cur.fetchone()

    project_count, user_count, mapped_features_count, countries_covered = (
        metrics_row if metrics_row else (0, 0, 0, 0)
    )

    return HTMXTemplate(
        template_name="partials/metrics.html",
        context={
            "project_count": int(project_count),
            "user_count": int(user_count),
            "mapped_features_count": int(mapped_features_count),
            "countries_covered": int(countries_covered),
        },
    )
