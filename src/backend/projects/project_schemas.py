from pydantic import BaseModel
from typing import List, Any
from shapely.geometry import shape

from ..users.user_schemas import User
from ..models.enums import ProjectStatus, ProjectPriority
from ..tasks import tasks_schemas

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
    city: str
    country: str

class ProjectSummary(BaseModel):
    id: int
    priority: ProjectPriority
    title: str 
    location_str: str
    description: str 
    num_contributors: int
    org_icon: bytes 

class ProjectBase(BaseModel):
    id: int
    author: User 
    default_locale: str
    project_info: List[ProjectInfo]
    status: ProjectStatus
    outline_json: str = None
    project_tasks: List[tasks_schemas.Task] = None

    class Config:
        orm_mode = True

class Project(ProjectBase):
    pass

class ProjectOut(ProjectBase):
    pass