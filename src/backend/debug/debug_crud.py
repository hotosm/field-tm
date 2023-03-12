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

from fastapi import UploadFile
from fastapi.logger import logger as log

from ..central.central_crud import create_odk_project
from ..db import database
from ..projects.project_crud import (
    create_project_with_project_info,
    update_project_with_zip,
)
from ..projects.project_schemas import BETAProjectUpload, ProjectInfo
from ..test_data import test_data_path
from ..users.user_crud import create_user, get_user_by_username
from ..users.user_schemas import User, UserIn


def load_test_data_as_test_user() -> None:
    """Load in the test data .zip files to the API."""
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
            f"Updating project {name} with boundaries "
            f"and QR codes from zip {test_zips[index]}"
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
