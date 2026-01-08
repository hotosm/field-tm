"""Litestar application entrypoint (renamed from litestar_app.py)."""

import json
import logging
from pathlib import Path

from litestar import Litestar, Request, Response, Router, get
from litestar import status_codes as status
from litestar.config.cors import CORSConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.di import Provide
from litestar.exceptions import HTTPException, ValidationException
from litestar.logging import LoggingConfig
from litestar.openapi import OpenAPIConfig
from litestar.plugins.htmx import HTMXPlugin
from litestar.plugins.pydantic import PydanticPlugin
from litestar.status_codes import HTTP_422_UNPROCESSABLE_ENTITY
from litestar.template.config import TemplateConfig
from osm_fieldwork.xlsforms import xlsforms_path
from pg_nearest_city import AsyncNearestCity
from psycopg import AsyncConnection
from psycopg.rows import tuple_row

from app.__version__ import __version__
from app.auth.auth_deps import login_required
from app.config import MonitoringTypes, settings
from app.db.database import close_db_connection_pool, db_conn, get_db_connection_pool
from app.db.models import DbUser
from app.monitoring import (
    add_endpoint_profiler,
    instrument_app_otel,
    set_otel_tracer,
    set_sentry_otel_tracer,
)
from app.projects.project_crud import read_and_insert_xlsforms

log = logging.getLogger(__name__)


async def server_init(server: Litestar) -> None:
    """Actions on server startup.

    This sets up:
    - XLSForm templates in the db.
    - Database entries for reverse geocoding.
    """
    log.debug("Starting up Litestar server")

    async with server.state.db_pool.connection() as conn:
        log.debug("Reading XLSForms from DB")
        await read_and_insert_xlsforms(conn, xlsforms_path)
        log.debug("Initialising reverse geocoding database")
        async with AsyncNearestCity(conn):
            pass


async def create_local_admin_user(server: Litestar) -> None:
    """Init admin user on application startup."""
    admin_user = DbUser(
        sub="osm|1",
        username="localadmin",
        is_admin=True,
        name="Admin",
        email_address="admin@fmtm.dev",
    )
    async with server.state.db_pool.connection() as conn:
        log.debug(f"Creating admin user {admin_user.username}")
        await DbUser.create(conn, admin_user, ignore_conflict=True)


def _custom_validation_exception_handler(
    request: Request, exc: ValidationException
) -> Response:
    """Custom handler to return 422 with FastAPI-compatible format for validation errors.

    NOTE this is a temporary FastAPI compatibility handler.
    NOTE if we use HTMX, this is no longer required
    """
    # Transform Litestar's validation errors to FastAPI format
    detail = []

    if exc.extra:
        for error in exc.extra:
            # Litestar uses 'message' and 'key', we need to transform to FastAPI format
            field_key = error.get("key", "unknown")
            message = error.get("message", "")

            # Extract the expected values from the message if it's an enum error
            # Message format: "Input should be 'VALUE1', 'VALUE2' or 'VALUE3'"
            ctx = {}
            if "Input should be" in message:
                # Extract everything after "Input should be "
                expected = message.replace("Input should be ", "")
                ctx["expected"] = expected

            detail.append(
                {
                    "type": error.get("type", "value_error"),
                    "loc": [field_key],  # Use the field key as location
                    "msg": message,
                    "input": error.get("input"),
                    "ctx": ctx,
                }
            )

    # If no errors in exc.extra, create a generic error
    if not detail:
        detail.append(
            {
                "type": "validation_error",
                "loc": ["body"],
                "msg": str(exc.detail) if exc.detail else "Validation failed",
                "input": None,
                "ctx": {},
            }
        )

    return Response(
        content={
            "detail": detail,
        },
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
    )


def _build_cors_config() -> CORSConfig:
    """Configure CORS for server."""
    cors_config = CORSConfig(
        allow_origins=settings.EXTRA_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )
    return cors_config


def _get_logging_config() -> LoggingConfig:
    """Configure server logging config."""
    logging_config = LoggingConfig(
        root={"level": settings.LOG_LEVEL, "handlers": ["queue_listener"]},
        formatters={
            "standard": {
                "format": "%(asctime)s.%(msecs)03d | %(levelname)-8s | "
                "%(name)s:%(funcName)s:%(lineno)d | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        log_exceptions="always",
    )
    return logging_config


def configure_root_router() -> Router:
    """The top level root router."""

    @get("/__version__")
    async def deployment_details() -> dict[str, str]:
        """Provide deployment metadata."""
        details: dict[str, str] = {}
        version_path = Path("/opt/version.json")
        if version_path.exists():
            with open(version_path) as version_file:
                details = json.load(version_file)
        commit = details.get("commit", "commit key was not found in file!")
        build = details.get("build", "build key was not found in file!")

        return {
            "source": "https://github.com/hotosm/field-tm",
            "version": __version__,
            "commit": commit or "/app/version.json not found",
            "build": build or "/app/version.json not found",
        }

    @get(
        "/__lbheartbeat__",
        status_code=status.HTTP_200_OK,
    )
    async def simple_heartbeat() -> None:
        """Simple load balancer heartbeat."""
        return None

    @get(
        "/__heartbeat__",
        dependencies={
            "current_user": Provide(login_required),
            "db": Provide(db_conn),
        },
        status_code=status.HTTP_200_OK,
    )
    async def heartbeat_plus_db(db: AsyncConnection) -> None:
        """Heartbeat that checks that API and DB are both up and running."""
        try:
            async with db.cursor(row_factory=tuple_row) as cur:
                await cur.execute("SELECT 1")
            return None
        except Exception as exc:
            log.warning(exc)
            log.warning("Server failed __heartbeat__ database connection check")
            return HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not connect to database",
            )

    return Router(
        path="/",
        tags=["root"],
        route_handlers=[
            deployment_details,
            simple_heartbeat,
            heartbeat_plus_db,
        ],
    )


def create_app() -> Litestar:
    """Configure Litestar app main router."""
    root_router = configure_root_router()
    # Import routers after logger / settings to avoid circular imports
    from app.auth.auth_routes import auth_router
    from app.central.central_routes import central_router
    from app.helpers.helper_routes import helper_router
    from app.htmx.htmx_routes import htmx_router
    from app.projects.project_routes import project_router
    from app.qfield.qfield_routes import qfield_router
    from app.users.user_routes import user_router

    app = Litestar(
        route_handlers=[
            root_router,
            project_router,
            auth_router,
            user_router,
            qfield_router,
            helper_router,
            central_router,
            htmx_router,
        ],
        plugins=[PydanticPlugin(), HTMXPlugin()],
        on_startup=[get_db_connection_pool, server_init, create_local_admin_user],
        on_shutdown=[close_db_connection_pool],
        cors_config=_build_cors_config(),
        openapi_config=OpenAPIConfig(title="Field-TM", version=__version__),
        logging_config=_get_logging_config(),
        exception_handlers={ValidationException: _custom_validation_exception_handler},
        template_config=TemplateConfig(
            directory=Path(__file__).parent / "templates",
            engine=JinjaTemplateEngine,
        ),
        debug=settings.DEBUG,
    )

    # Monitoring / tracing configuration
    if settings.DEBUG:
        add_endpoint_profiler(app)

    if settings.MONITORING == MonitoringTypes.SENTRY:
        log.info("Adding Sentry OpenTelemetry monitoring config")
        set_sentry_otel_tracer(settings.monitoring_config.SENTRY_DSN)
        instrument_app_otel(app)
    elif settings.MONITORING == MonitoringTypes.OPENOBSERVE:
        log.info("Adding OpenObserve OpenTelemetry monitoring config")
        set_otel_tracer(app, settings.monitoring_config.otel_exporter_otpl_endpoint)
        instrument_app_otel(app)

    return app


api = create_app()
