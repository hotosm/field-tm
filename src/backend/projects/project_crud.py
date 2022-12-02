from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import db_models
from . import project_schemas

# --------------
# ---- CRUD ----
# --------------

def get_projects(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    if user_id:
        db_projects = db.query(db_models.DbProject).filter(db_models.DbProject.author_id == user_id).offset(skip).limit(limit).all()
    else:
        db_projects = db.query(db_models.DbProject).offset(skip).limit(limit).all()
    return convert_to_app_projects(db_projects)

def get_project_by_id(db:Session, project_id: int):
    db_project = db.query(db_models.DbProject).filter(db_models.DbProject.id == project_id).first()
    return db_project
    # return convert_to_app_project(db_project)

def create_project_with_project_info(db: Session, project_metadata: project_schemas.BETAProjectUpload):
    # TODO: get this from authenticated user
    user = project_metadata.author
    project_info_1 = project_metadata.project_info
    
    # verify data coming in
    if not user:
        return Exception('No user passed in')
    if not project_info_1:
        return Exception('No project info passed in')
    
    # create new project
    db_project = db_models.DbProject(
        author_id = user.id,
        default_locale = project_info_1.locale,
    )

    db.add(db_project)
    db.commit()
    db.refresh(db_project) # now contains generated id etc.

    # add project info (project id needed to create project info)
    db_project_info = db_models.DbProjectInfo(
        project_id = db_project.id,
        locale = project_info_1.locale,
        name = project_info_1.name,
        short_description = project_info_1.short_description,
        description = project_info_1.description,
        instructions = project_info_1.instructions,
        project_id_str = f'{db_project.id}',
        per_task_instructions = project_info_1.per_task_instructions
    )
    db_project.project_info = [db_project_info]
    db.commit()
    db.refresh(db_project)

    return convert_to_app_project(db_project)


# --------------------
# ---- CONVERTERS ----
# --------------------

# TODO: write tests for these

def convert_to_db_info(app_project_info: project_schemas.ProjectInfo):
    if app_project_info:
        db_project_info = db_models.DbProjectInfo(

        )
    else:
        return None

def convert_to_app_project(db_project: db_models.DbProject):
    if db_project:
        app_project: project_schemas.Project = db_project
        return app_project
    else:
        return None

def convert_to_app_projects(db_projects: List[db_models.DbProject]):
    if db_projects and len(db_projects) > 0:
        app_projects = []
        for project in db_projects:
            if project:
                app_projects.append(convert_to_app_project(project))
        return app_projects
    else:
        return []