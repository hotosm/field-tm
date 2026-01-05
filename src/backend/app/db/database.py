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

"""Config for the Field-TM database connection."""

import logging
from collections.abc import AsyncGenerator
from typing import cast

from litestar import Litestar
from litestar.datastructures import State
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

from app.config import settings

log = logging.getLogger(__name__)


async def get_db_connection_pool(server: Litestar) -> AsyncConnectionPool:
    """Get the connection pool for psycopg.

    NOTE the pool connection is opened in the Litestar server startup (lifespan).
    """
    log.debug(
        "Creating database connection pool: "
        f"{settings.FMTM_DB_USER}@{settings.FMTM_DB_HOST}"
    )

    pool = getattr(server.state, "db_pool", None)

    if pool is None or pool.closed:
        if pool is not None:
            log.debug("Existing DB pool is closed; creating a new one")

        pool = AsyncConnectionPool(
            conninfo=settings.FMTM_DB_URL,
            min_size=1,
            max_size=10,  # max 10 concurrent DB connections (less than max_connections)
            timeout=30.0,  # how long to wait if all connections are busy
            open=False,
        )
        server.state.db_pool = pool
        await pool.open()
        log.debug("Database connection pool opened")

    return cast(AsyncConnectionPool, pool)


async def close_db_connection_pool(server: Litestar) -> None:
    """Close the psycopg connection pool."""
    pool = getattr(server.state, "db_pool", None)
    if pool and not pool.closed:
        await cast("AsyncConnectionPool", server.state.db_pool).close()
        log.debug("Database connection pool closed")


async def db_conn(state: State) -> AsyncGenerator[AsyncConnection, None]:
    """Get a connection from the psycopg pool.

    This is an async generator that yields a connection and returns it to the pool
    when the request handler completes.
    """
    db_pool = cast(AsyncConnectionPool, state.db_pool)
    async with db_pool.connection() as conn:
        yield conn
