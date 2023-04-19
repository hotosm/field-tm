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

from sqlalchemy.orm import Session
from ..central.central_crud import xform
from ..projects import project_crud
from ..central.central_crud import project

def get_submission_of_project(
        db: Session,
        project_id: int,
        task_id: int = None
        ):
    """ 
        Gets the submission of project.
        This function takes project_id and task_id as a parameter.
        If task_id is provided, it returns all the submission made to that particular task, else all the submission made in the projects are returned.
    """

    project_info = project_crud.get_project_by_id(db, project_id)
    odkid = project_info.odkid
    project_name = project_info.project_name_prefix
    form_category = project_info.xform_title
    project_tasks = project_info.tasks

    # If task id is not provided, submission for all the task are listed
    if task_id is None:
        task_list = []
        for x in project_tasks:
            task_list.append(x.id)

        data = []
        for id in task_list:

            # XML Form Id is a combination or project_name, category and task_id
            xml_form_id = f'{project_name}_{form_category}_{id}'.split('_')[2]

            submission_list = xform.listSubmissions(odkid, xml_form_id)
            if isinstance(submission_list,list):
                for submission in submission_list:
                    # App User Id is a combination of project_name, category and task_id 
                    # Need to access from api
                    submission['submitted_by'] = f'{project_name}_{form_category}_{id}'
                    data.append(submission)
        return data
    
    else:
        # If task_id is provided, submission made to this particular task is returned.
        xml_form_id = f'{project_name}_{form_category}_{task_id}'.split('_')[2]
        submission_list = xform.listSubmissions(odkid, xml_form_id)
        for x in submission_list:
            x['submitted_by'] = f'{project_name}_{form_category}_{task_id}'
        return submission_list


def get_forms_of_project(
        db : Session,
        project_id: int
    ):
    project_info = project_crud.get_project_by_id(db, project_id)
    odkid = project_info.odkid

    result = project.listForms(odkid)
    return result


def list_app_users_or_project(
        db : Session,
        project_id: int
    ):
    project_info = project_crud.get_project_by_id(db, project_id)
    odkid = project_info.odkid
    result = project.listAppUsers(odkid)
    return result
