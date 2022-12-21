from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session

from ..db import database
from . import tasks_schemas, tasks_crud

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=tasks_schemas.TaskDetails)
async def read_tasks(user_id: int = None, task_id: int = None, skip: int = 0, limit: int = 1000, db: Session = Depends(database.get_db)):
    tasks = tasks_crud.get_tasks(db, user_id, task_id, skip, limit)
    if tasks:
        return tasks
    else:
        raise HTTPException(status_code=404, detail="Tasks not found")
