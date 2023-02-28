# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
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


import os
import sys
import logging

from typing import Union

from fastapi import FastAPI
from fastapi.logger import logger as fastapi_logger
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .__version__ import __version__
from .config import settings
from .auth import routers as auth_routers
from .db.database import Base, engine
from .projects import project_routes
from .tasks import tasks_routes
from .users import user_routes
from .debug import debug_routes
from .central import central_routes

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

gunicorn_error_logger = logging.getLogger("gunicorn.error")
gunicorn_logger = logging.getLogger("gunicorn")
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.handlers = gunicorn_error_logger.handlers

fastapi_logger.handlers = gunicorn_error_logger.handlers

logger = logging.getLogger(__name__)


def get_application() -> FastAPI:

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
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _app.include_router(user_routes.router)
    _app.include_router(project_routes.router)
    _app.include_router(tasks_routes.router)
    _app.include_router(debug_routes.router)
    _app.include_router(central_routes.router)
    _app.include_router(auth_routers.router)

    return _app


api = get_application()


@api.on_event("startup")
async def startup_event():
    """Commands to run on server startup."""
    logger.debug("Starting up FastAPI server.")
    logger.debug("Connecting to DB with SQLAlchemy")
    Base.metadata.create_all(bind=engine)


@api.on_event("shutdown")
async def shutdown_event():
    """Commands to run on server shutdown."""
    logger.debug("Shutting down FastAPI server.")


@api.get("/")
def read_root():
    logger.info("logging from the root logger")
    return {"Hello": "Big, big World"}


@api.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@api.get("/images/{image_filename}")
def get_images(image_filename: str):
    path = f"./backend/images/{image_filename}"
    return FileResponse(path)
