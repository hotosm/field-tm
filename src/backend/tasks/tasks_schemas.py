from pydantic import BaseModel

from ..models.enums import TaskStatus

class TaskBase(BaseModel):
    id: int
    project_id: int
    project_task_index: int
    project_task_name: str
    outline_json: str
    initial_feature_count: int
    task_status: TaskStatus

    class Config:
        orm_mode = True

class Task(TaskBase):
    geometry_geojson: str 
    pass

class TaskOut(TaskBase):
    pass

class TaskDetails(TaskBase):
    pass