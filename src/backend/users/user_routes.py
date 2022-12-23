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
        raise HTTPException(
            status_code=400, detail="Username already registered")
    return user_crud.create_user(db=db, user=user)


@router.get("/", response_model=List[user_schemas.UserOut])
def get_users(username: str = "", skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    users = user_crud.get_users(db, skip=skip, limit=limit)
    return users
    # TODO error thrown when no users are in db


@router.get("/{id}", response_model=user_schemas.UserOut)
async def get_user_by_id(id: int, db: Session = Depends(database.get_db)):
    user = user_crud.get_user(db, user_id=id)
    if user:
        return user
    else:
        raise HTTPException(status_code=404, detail="User not found")
