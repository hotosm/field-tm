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

from litestar import get
from litestar.di import Provide
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.response import Template
from psycopg import AsyncConnection

from app.db.database import db_conn
from app.db.models import DbProject


@get(
    path="/htmxprojects",
    dependencies={"db": Provide(db_conn)},
)
async def project_listing(request: HTMXRequest, db: AsyncConnection) -> Template:
    """Render public project listing page."""
    projects = await DbProject.all(db, limit=12) or []
    return HTMXTemplate(template_name="home.html", context={"projects": projects})
