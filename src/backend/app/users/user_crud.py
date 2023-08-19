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
from typing import List

from sqlalchemy.orm import Session

from ..db import db_models
from . import user_schemas

# --------------
# ---- CRUD ----
# --------------


def get_users(db: Session, skip: int = 0, limit: int = 100):
    db_users = db.query(db_models.DbUser).offset(skip).limit(limit).all()
    return convert_to_app_user(db_users) if db_users else []


def get_user(db: Session, user_id: int, db_obj: bool = False):
    db_user = db.query(db_models.DbUser).filter(db_models.DbUser.id == user_id).first()
    if db_obj:
        return db_user
    return convert_to_app_user(db_user)


def get_user_by_username(db: Session, username: str):
    db_user = (
        db.query(db_models.DbUser).filter(db_models.DbUser.username == username).first()
    )
    return convert_to_app_user(db_user)


# --------------------
# ---- CONVERTERS ----
# --------------------


# TODO: write tests for these
def convert_to_app_user(db_user: db_models.DbUser):
    if db_user:
        app_user: user_schemas.User = db_user
        return app_user
    else:
        return None


def convert_to_app_users(db_users: List[db_models.DbUser]):
    if db_users and len(db_users) > 0:
        app_users = []
        for user in db_users:
            if user:
                app_users.append(convert_to_app_user(user))
        app_users_without_nones = [i for i in app_users if i is not None]
        return app_users_without_nones
    else:
        return []


def get_user_role_by_user_id(db: Session, user_id: int):
    db_user_role = (
        db.query(db_models.DbUserRoles)
        .filter(db_models.DbUserRoles.user_id == user_id)
        .first()
    )
    if db_user_role:
        return db_user_role.role.value
    return None


async def create_user_roles(user_role: user_schemas.UserRoles, db: Session):
    db_user_role = db_models.DbUserRoles(
        user_id=user_role.user_id,
        role=user_role.role,
        organization_id=user_role.organization_id,
        project_id=user_role.project_id,
    )

    db.add(db_user_role)
    db.commit()
    db.refresh(db_user_role)
    return db_user_role


def get_user_by_id(db: Session, user_id: int):
    db_user = db.query(db_models.DbUser).filter(db_models.DbUser.id == user_id).first()
    return db_user
