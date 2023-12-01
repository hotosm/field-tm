# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Entrypoint for FastAPI app."""

import logging
import sys
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from loguru import logger as log
from osm_fieldwork.xlsforms import xlsforms_path

from app.__version__ import __version__
from app.auth import auth_routes
from app.central import central_routes
from app.config import settings
from app.db.database import get_db
from app.organization import organization_routes
from app.projects import project_routes
from app.projects.project_crud import read_xlsforms
from app.submission import submission_routes
from app.tasks import tasks_routes
from app.users import user_routes

# Add sentry tracing only in prod
if not settings.DEBUG:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI startup/shutdown event."""
    log.debug("Starting up FastAPI server.")
    log.debug("Reading XLSForms from DB.")
    await read_xlsforms(next(get_db()), xlsforms_path)

    yield

    # Shutdown events
    log.debug("Shutting down FastAPI server.")


def get_application() -> FastAPI:
    """Get the FastAPI app instance, with settings."""
    _app = FastAPI(
        title=settings.APP_NAME,
        description="HOTOSM Field Tasking Manager",
        version=__version__,
        license_info={
            "name": "GPL-3.0-only",
            "url": "https://raw.githubusercontent.com/hotosm/fmtm/main/LICENSE",
        },
        debug=settings.DEBUG,
        lifespan=lifespan,
        root_path=settings.API_PREFIX,
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
    _app.include_router(tasks_routes.router)
    _app.include_router(central_routes.router)
    _app.include_router(auth_routes.router)
    _app.include_router(submission_routes.router)
    _app.include_router(organization_routes.router)

    return _app


class InterceptHandler(logging.Handler):
    """Intercept python standard lib logging."""

    def emit(self, record):
        """Retrieve context where the logging call occurred.

        This happens to be in the 6th frame upward.
        """
        logger_opt = log.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelno, record.getMessage())


def get_logger():
    """Override FastAPI logger with custom loguru."""
    # Hook all other loggers into ours
    logger_name_list = [name for name in logging.root.manager.loggerDict]
    for logger_name in logger_name_list:
        logging.getLogger(logger_name).setLevel(10)
        logging.getLogger(logger_name).handlers = []
        if logger_name == "sqlalchemy":
            # Don't hook sqlalchemy, very verbose
            continue
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

    log.add(
        "/opt/logs/create_project.json",
        level=settings.LOG_LEVEL,
        enqueue=True,
        serialize=True,
        rotation="00:00",
        retention="10 days",
        filter=lambda record: record["extra"].get("task") == "create_project",
    )


api = get_application()


# Add endpoint profiler to check for bottlenecks
if settings.DEBUG:
    from pyinstrument import Profiler

    @api.middleware("http")
    async def profile_request(request: Request, call_next):
        """Calculate the execution time for routes."""
        profiling = request.query_params.get("profile", False)
        if profiling:
            profiler = Profiler(interval=0.001, async_mode="enabled")
            profiler.start()
            await call_next(request)
            profiler.stop()
            return HTMLResponse(profiler.output_html())
        else:
            return await call_next(request)


@api.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Exception handler for more descriptive logging."""
    errors = []
    for error in exc.errors():
        # TODO Handle this properly
        if error["msg"] in ["Invalid input", "field required"]:
            status_code = 422  # Unprocessable Entity
        else:
            status_code = 400  # Bad Request
        errors.append(
            {
                "loc": error["loc"],
                "msg": error["msg"],
                "error": error["msg"] + str([x for x in error["loc"]]),
            }
        )
    return JSONResponse(status_code=status_code, content={"errors": errors})


@api.get("/")
async def home():
    """Redirect home to docs."""
    return RedirectResponse("/docs")
