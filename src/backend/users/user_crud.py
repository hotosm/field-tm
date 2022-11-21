from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import db_models
from . import user_schemas

def get_users(db: Session, skip: int = 0, limit: int = 100):
    db_users = db.query(db_models.DbUser).offset(skip).limit(limit).all()
    return convert_to_app_user(db_users)

def get_user(db: Session, user_id: int):
    db_user = db.query(db_models.DbUser).filter(db_models.DbUser.id == user_id).first()
    return convert_to_app_user(db_user)

def get_user_by_username(db: Session, username: str):
    db_user = db.query(db_models.DbUser).filter(db_models.DbUser.username == username).first()
    return convert_to_app_user(db_user)

def create_user(db: Session, user: user_schemas.UserIn):
    if user:
        db_user = db_models.DbUser(username=user.username, password=hash_password(user.password))
        db.add(db_user)
        db.commit()
        db.refresh(db_user) # now contains generated id etc.

        return convert_to_app_user(db_user)

    return Exception('No user passed in')

def hash_password(password: str):
    return password

def unhash_password(hashed_password: str):
    return hashed_password

def verify_user(db: Session, questionable_user: user_schemas.UserIn):
    db_user = get_user_by_username(db, questionable_user.username)
    if db_user:
        if unhash_password(db_user.password) == questionable_user.password:
            return convert_to_app_user(db_user)
        else:
            raise HTTPException(status_code=400, detail="Incorrect password.")
    else:
        raise HTTPException(status_code=400, detail="Username not registered.")

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
        return app_users
    else:
        return None


