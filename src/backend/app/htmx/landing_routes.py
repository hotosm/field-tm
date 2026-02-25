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

from litestar import get
from litestar.di import Provide
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.response import Template
from psycopg import AsyncConnection

from app.db.database import db_conn


@get(
    path="/",
    dependencies={"db": Provide(db_conn)},
)
async def landing(request: HTMXRequest, db: AsyncConnection) -> Template:
    """Render public landing page."""
    return HTMXTemplate(template_name="landing.html")


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
                    SELECT COUNT(DISTINCT country)
                    FROM users
                    WHERE country IS NOT NULL
                      AND TRIM(country) <> ''
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
