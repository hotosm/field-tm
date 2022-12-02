from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..db import database
from . import user_schemas, user_crud

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=user_schemas.UserOut)
def create_user(user: user_schemas.UserIn, db: Session = Depends(database.get_db)):
    existing_user = user_crud.get_user_by_username(db, username=user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return user_crud.create_user(db=db, user=user)

@router.get("/", response_model=List[user_schemas.UserOut])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    users = user_crud.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{id}", response_model=user_schemas.UserOut)
async def get_user_by_id(id: int, db: Session = Depends(database.get_db)):
    user = user_crud.get_user(db, user_id=id)
    if user:
        return user
    else:
        raise HTTPException(status_code=404, detail="User not found")

@router.get("/{username}", response_model=user_schemas.UserOut)
async def read_user(username: str, db: Session = Depends(database.get_db)):
    user = user_crud.get_user_by_username(db, username=username)
    if user:
        return user
    else:
        raise HTTPException(status_code=404, detail="User not found")