from pydantic import BaseModel
from typing import List

from ..users.user_schemas import User
from ..models.enums import ProjectStatus
from ..models import gis_schemas

class ProjectInfo(BaseModel):
    locale: str
    name: str
    short_description: str
    description: str
    instructions: str
    per_task_instructions: str

    class Config:
        orm_mode = True

class BETAProjectUpload(BaseModel):
    author: User 
    project_info: ProjectInfo

class ProjectBase(BaseModel):
    id: int
    author: User 
    default_locale: str
    project_info: List[ProjectInfo]
    status: ProjectStatus
    outline: gis_schemas.FmtmPolygon = None

    class Config:
        orm_mode = True

class Project(ProjectBase):
    pass

class ProjectOut(ProjectBase):
    pass