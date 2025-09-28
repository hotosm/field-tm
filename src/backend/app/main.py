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
"""Entrypoint for FastAPI app."""

import json
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, AsyncIterator

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response
from loguru import logger as log
from osm_fieldwork.xlsforms import xlsforms_path
from pg_nearest_city import AsyncNearestCity
from psycopg import Connection

from app.__version__ import __version__
from app.auth import auth_routes
from app.central import central_routes
from app.config import MonitoringTypes, settings
from app.db.database import db_conn, get_db_connection_pool
from app.db.enums import HTTPStatus
from app.helpers import helper_routes
from app.integrations import integration_routes
from app.monitoring import (
    add_endpoint_profiler,
    instrument_app_otel,
    set_otel_tracer,
    set_sentry_otel_tracer,
)
from app.organisations import organisation_routes
from app.organisations.organisation_crud import init_admin_org
from app.projects import project_routes
from app.projects.project_crud import read_and_insert_xlsforms
from app.qfield import qfield_routes
from app.submissions import submission_routes
from app.tasks import task_routes
from app.users import user_routes


def get_api() -> FastAPI:
    """Return the FastAPI app, configured for the environment.

    Add endpoint profiler or monitoring setup based on environment.
    """
    api = get_application()

    # Add endpoint profiler to check for bottlenecks
    if settings.DEBUG:
        add_endpoint_profiler(api)

    # Add monitoring if flag set
    if settings.MONITORING == MonitoringTypes.SENTRY:
        log.info("Adding Sentry OpenTelemetry monitoring config")
        set_sentry_otel_tracer(settings.monitoring_config.SENTRY_DSN)
        instrument_app_otel(api)
    elif settings.MONITORING == MonitoringTypes.OPENOBSERVE:
        log.info("Adding OpenObserve OpenTelemetry monitoring config")
        set_otel_tracer(api, settings.monitoring_config.otel_exporter_otpl_endpoint)
        # set_otel_logger(settings.monitoring_config.otel_exporter_otpl_endpoint)
        instrument_app_otel(api)

    return api


@asynccontextmanager
async def lifespan(
    app: FastAPI,  # dead: disable
) -> AsyncIterator[None]:
    """FastAPI startup/shutdown event."""
    log.debug("Starting up FastAPI server.")

    # Create a pooled db connection and make available in lifespan state
    # https://asgi.readthedocs.io/en/latest/specs/lifespan.html#lifespan-state
    # NOTE to use within a request (this is wrapped in database.py already):
    # from typing import cast
    # db_pool = cast(AsyncConnectionPool, request.state.db_pool)
    # async with db_pool.connection() as conn:
    db_pool = get_db_connection_pool()
    await db_pool.open()

    async with db_pool.connection() as conn:
        log.debug("Initialising admin org and user in DB.")
        await init_admin_org(conn)
        log.debug("Reading XLSForms from DB.")
        await read_and_insert_xlsforms(conn, xlsforms_path)
        log.debug("Initialising reverse geocoding database")
        async with AsyncNearestCity(conn):
            pass

    yield {"db_pool": db_pool}

    # Shutdown events
    log.debug("Shutting down FastAPI server.")
    await db_pool.close()


def get_application() -> FastAPI:
    """Get the FastAPI app instance, with settings."""
    _app = FastAPI(
        title=settings.APP_NAME,
        description="HOTOSM Field Tasking Manager",
        version=__version__,
        license_info={
            "name": "AGPL-3.0-only",
            "url": "https://raw.githubusercontent.com/hotosm/field-tm/main/LICENSE.md",
        },
        debug=settings.DEBUG,
        lifespan=lifespan,
        root_path=settings.API_PREFIX,
        # NOTE REST APIs should not have trailing slashes
        redirect_slashes=False,
    )

    # Set custom logger
    _app.logger = get_logger()

    _app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.EXTRA_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )

    _app.include_router(user_routes.router)
    _app.include_router(project_routes.router)
    _app.include_router(task_routes.router)
    _app.include_router(central_routes.router)
    _app.include_router(qfield_routes.router)
    _app.include_router(auth_routes.router)
    _app.include_router(submission_routes.router)
    _app.include_router(organisation_routes.router)
    _app.include_router(integration_routes.router)
    _app.include_router(helper_routes.router)

    return _app


class InterceptHandler(logging.Handler):
    """Intercept python standard lib logging."""

    def emit(self, record):
        """Retrieve context where the logging call occurred.

        This happens to be in the 6th frame upward.
        """
        logger_opt = log.opt(depth=6, exception=record.exc_info)
        logger_opt.log(logging.getLevelName(record.levelno), record.getMessage())


def get_logger():
    """Override FastAPI logger with custom loguru."""
    # Hook all other loggers into ours
    logger_name_list = [name for name in logging.root.manager.loggerDict]
    for logger_name in logger_name_list:
        logging.getLogger(logger_name).setLevel(settings.LOG_LEVEL)
        logging.getLogger(logger_name).handlers = []
        if settings.LOG_LEVEL != "DEBUG" and logger_name == "urllib3":
            # Don't hook urllib3 in prod, as it's called on each OTEL trace
            continue
        if logger_name == "pyodk._utils.config":
            # Set pyodk logger level to CRITICAL to avoid noise
            logging.getLogger("pyodk._utils.config").setLevel(settings.PYODK_LOG_LEVEL)
        if "." not in logger_name:
            logging.getLogger(logger_name).addHandler(InterceptHandler())

    log.remove()
    log.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} "
            "| {name}:{function}:{line} | {message}"
        ),
        enqueue=True,  # Run async / non-blocking
        colorize=True,
        backtrace=True,  # More detailed tracebacks
        catch=True,  # Prevent app crashes
    )

    # Only log to file in production
    if not settings.DEBUG:
        log.add(
            "/opt/logs/fmtm.json",
            level=settings.LOG_LEVEL,
            enqueue=True,
            serialize=True,  # JSON format
            rotation="00:00",  # New file at midnight
            retention="10 days",
            # format=log_json_format, # JSON format func
        )


api = get_api()


@api.get("/")
async def home():
    """Redirect home to docs."""
    return RedirectResponse("/docs")


@api.get("/__version__")
async def deployment_details():
    """Mozilla Dockerflow Spec: source, version, commit, and link to CI build."""
    details = {}

    version_path = Path("/opt/version.json")
    if version_path.exists():
        with open(version_path) as version_file:
            details = json.load(version_file)
    commit = details.get("commit", "commit key was not found in file!")
    build = details.get("build", "build key was not found in file!")

    return JSONResponse(
        status_code=HTTPStatus.OK,
        content={
            "source": "https://github.com/hotosm/field-tm",
            "version": __version__,
            "commit": commit or "/app/version.json not found",
            "build": build or "/app/version.json not found",
        },
    )


@api.get("/__heartbeat__")
async def heartbeat_plus_db(db: Annotated[Connection, Depends(db_conn)]):
    """Heartbeat that checks that API and DB are both up and running."""
    try:
        async with db.cursor() as cur:
            await cur.execute("SELECT 1")
        return Response(status_code=HTTPStatus.OK)
    except Exception as e:
        log.warning(e)
        log.warning("Server failed __heartbeat__ database connection check")
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, content={"error": str(e)}
        )


@api.get("/__lbheartbeat__")
async def simple_heartbeat():
    """Simple ping/pong API response."""
    return Response(status_code=HTTPStatus.OK)
