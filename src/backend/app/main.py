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
import os
import sys
from typing import Union

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from osm_fieldwork.xlsforms import xlsforms_path
from osm_fieldwork.xlsforms import xlsforms_path

from .__version__ import __version__
from .auth import auth_routes
from .central import central_routes
from .config import settings
from .db.database import Base, engine, get_db
from .debug import debug_routes
from .projects import project_routes
from .projects.project_crud import read_xlsforms
from .submission import submission_routes
from .tasks import tasks_routes
from .users import user_routes
from .organization import organization_routes

# Env variables
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = settings.OAUTHLIB_INSECURE_TRANSPORT

# Logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=(
        "%(asctime)s.%(msecs)03d [%(levelname)s] "
        "%(name)s | %(funcName)s:%(lineno)d | %(message)s"
    ),
    datefmt="%y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


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
    )

    _app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.EXTRA_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _app.include_router(user_routes.router)
    _app.include_router(project_routes.router)
    _app.include_router(tasks_routes.router)
    _app.include_router(central_routes.router)
    _app.include_router(auth_routes.router)
    _app.include_router(submission_routes.router)
    _app.include_router(organization_routes.router)

    if settings.DEBUG:
        _app.include_router(debug_routes.router)

    return _app


api = get_application()


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


@api.on_event("startup")
async def startup_event():
    """Commands to run on server startup."""
    logger.debug("Starting up FastAPI server.")
    logger.debug("Connecting to DB with SQLAlchemy")
    Base.metadata.create_all(bind=engine)

    # Read in XLSForms
    read_xlsforms(next(get_db()), xlsforms_path)


@api.on_event("shutdown")
async def shutdown_event():
    """Commands to run on server shutdown."""
    logger.debug("Shutting down FastAPI server.")


@api.get("/")
def home():
    """Redirect home to docs."""
    return RedirectResponse("/docs")


@api.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    """Get item IDs."""
    return {"item_id": item_id, "q": q}


@api.get("/images/{image_filename}")
def get_images(image_filename: str):
    """Download image files."""
    path = f"./app/images/{image_filename}"
    return FileResponse(path)
