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
import bcrypt
from typing import List

from fastapi import HTTPException
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


def create_user(db: Session, user: user_schemas.UserIn):
    if user:
        db_user = db_models.DbUser(
            username=user.username, password=hash_password(user.password)
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)  # now contains generated id etc.

        return convert_to_app_user(db_user)

    return Exception("No user passed in")


# ---------------------------
# ---- SUPPORT FUNCTIONS ----
# ---------------------------


def hash_password(password: str):
    '''
        Hashing the password using bcrypt
    '''
    hashed_password_encoded = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
    hashed_password = hashed_password_encoded.decode("utf8")
    return hashed_password


def verify_password(user_password, hashed_password):
    '''
        This function takes the password user entered and the hashed password in the db
        and check if they matches.
    '''
    is_valid = bcrypt.checkpw(user_password.encode('utf8'), 
                              hashed_password.encode('utf8'))
    return is_valid


def unhash_password(hashed_password: str):
    return hashed_password


def verify_user(db: Session, questionable_user: user_schemas.UserIn):
    db_user = get_user_by_username(db, questionable_user.username)
    if db_user:
        if verify_password(questionable_user.password, db_user.password):
            return {'id':db_user.id, 
                    'name':db_user.username,
                    'role':db_user.role
                    }

        else:
            raise HTTPException(status_code=400, detail="Incorrect password.")
    else:
        raise HTTPException(status_code=400, detail="Username not registered.")


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
