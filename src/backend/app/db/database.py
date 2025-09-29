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

from typing import cast

from fastapi import Request
from loguru import logger as log
from psycopg import Connection
from psycopg_pool import AsyncConnectionPool

from app.config import settings


def get_db_connection_pool() -> AsyncConnectionPool:
    """Get the connection pool for psycopg.

    NOTE the pool connection is opened in the FastAPI server startup (lifespan).
    """
    log.debug(
        "Creating database connection pool: "
        f"{settings.FMTM_DB_USER}@{settings.FMTM_DB_HOST}"
    )
    return AsyncConnectionPool(
        conninfo=settings.FMTM_DB_URL,
        open=False,
        min_size=1,
        max_size=10,  # max 10 concurrent DB connections (less than max_connections)
        timeout=30.0,  # how long to wait if all connections are busy
    )


async def db_conn(request: Request) -> Connection:
    """Get a connection from the psycopg pool.

    Info on connections vs cursors:
    https://www.psycopg.org/psycopg3/docs/advanced/async.html

    Here we are getting a connection from the pool, which will be returned
    after the session ends / endpoint finishes processing.

    In summary:
    - Connection is created on endpoint call.
    - Cursors are used to execute commands throughout endpoint.
      Note it is possible to create multiple cursors from the connection,
      but all will be executed in the same db 'transaction'.
    - Connection is closed on endpoint finish.

    -----------------------------------
    To use the connection in endpoints:
    -----------------------------------

    @app.get("/something")
    async def do_stuff(db = Depends(db_conn)):
        async with db.cursor() as cursor:
            await cursor.execute("SELECT * FROM items")
            result = await cursor.fetchall()
            return result

    -----------------------------------
    Additionally, the connection could be passed through to a function to
    utilise the Pydantic model serialisation on the cursor:
    -----------------------------------

    from psycopg.rows import class_row
    async def get_user_by_id(db: Connection, id: int):
        async with db.cursor(row_factory=class_row(User)) as cur:
            await cur.execute(
                '''
                SELECT id, first_name, last_name, dob
                FROM (VALUES
                    (1, 'John', 'Doe', '2000-01-01'::date),
                    (2, 'Jane', 'White', NULL)
                ) AS data (id, first_name, last_name, dob)
                WHERE id = %(id)s;
                ''',
                {"id": id},
            )
            obj = await cur.fetchone()

            # reveal_type(obj) would return 'Optional[User]' here

            if not obj:
                raise KeyError(f"user {id} not found")

            # reveal_type(obj) would return 'User' here

            return obj
    """
    db_pool = cast(AsyncConnectionPool, request.state.db_pool)
    async with db_pool.connection() as conn:
        yield conn
