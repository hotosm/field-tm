# Copyright (c) 2023 Humanitarian OpenStreetMap Team
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

from fastapi import APIRouter, Depends, UploadFile
from fastapi.logger import logger as log

from ..central.central_crud import create_odk_project

# from ..odkconvert.make_data_extract import PostgresClient, OverpassClient
from ..db import database
from ..debug import debug_schemas
from ..projects.project_crud import (
    create_project_with_project_info,
    update_project_with_zip,
)
from ..projects.project_schemas import BETAProjectUpload, ProjectInfo
from ..test_data import test_data_path
from ..users.user_crud import create_user, get_user_by_username
from ..users.user_schemas import User, UserIn

router = APIRouter(
    prefix="/debug",
    tags=["debug"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)

#
# These are temporary debugging endpoints so it's possible to
# call directly into the backend support code. As that code is
# more developed, then these will be called by other endpoints,
# and not directly.
#


@router.get("/", response_model=debug_schemas.DebugOut)
async def debug():
    return {"message": "Hello World!"}
    # raise HTTPException(status_code=404, detail="Tasks not found")


@router.get("/basemap")
def make_basemap():
    """Make a basemap of satellite imagery."""
    log.info("/debug/basemap Unimplemented!")
    return {"message": "Hello World from /debug/basemap"}


@router.get("/makecsv")
def do_odk2csv():
    """Convert the submissions data into a CSV file."""
    log.info("/debug/do_odk2csv is Unimplemented!")
    return {"message": "Hello World from /debug/makecsv"}


@router.get("/load-test-data")
def load_test_data_as_test_user():
    """Load the test data zips into the API.

    This endpoint should only be available during debugging, and is
    useful for first load.

    A user with credentials test:test is created, and 5 projects are generated.
    Zips containing task and QR codes are then uploaded for each project.

    "Coulibistrie": "resilience"
    "Dos_D_Ane": "resilience"
    "Naivasha": "buildings"
    "Stonetown2": "buildings"
    "Vulamba": "buildings"
    """
    log.info("/load-test-data called")
    db = next(database.get_db())
    user = UserIn(username="test", password="test")

    # Create user
    log.debug(f"Checking for existing user: {user}")
    test_user = get_user_by_username(db, username=user.username)
    if not test_user:
        log.debug(f"Creating user: {user}")
        test_user = create_user(db, user)
        log.debug("User generated")

    user_id = test_user.id
    log.debug(f"Test user ID: {user_id}")

    # Create projects
    test_metadata = {
        "Coulibistrie": "resilience",
        "Dos_D_Ane": "resilience",
        "Naivasha": "buildings",
        "Stonetown2": "buildings",
        "Vulamba": "buildings",
    }
    test_names = test_metadata.keys()
    test_zips = [f"{test_data_path}/{name}.zip" for name in test_names]

    for index, name in enumerate(test_names):
        project_obj = BETAProjectUpload(
            author=User(username="test", id=user_id),
            project_info=ProjectInfo(
                locale="en",
                name=name,
                short_description=f"Test{index}: {name}",
                description=f"Test{index}: {name}",
                instructions="No instructions",
                per_task_instructions="No per task instructions",
            ),
            city=name,
            country="Unknown",
        )
        log.debug(f"Creating ODKCentral project for: {project_obj}")
        odkproject = create_odk_project(project_obj.project_info.name)
        log.debug("Submitting project to API")
        new_project = create_project_with_project_info(
            db, project_obj, odkproject["id"]
        )

        log.debug(
            f"Updating project {name} with boundaries and QR codes from zip {test_zips[index]}"
        )
        with open(test_zips[index], "rb") as file_data:
            upload_file = UploadFile(
                filename=f"{name}.zip",
                file=file_data,
                content_type="application/zip",
            )
            log.debug(upload_file)
            update_project_with_zip(
                db, new_project.id, name, test_metadata[name], upload_file
            )
        log.debug(f"Zip file upload complete for project {name}")

    return {"message": "Test data upload successful"}
