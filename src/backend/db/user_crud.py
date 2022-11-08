from sqlalchemy.orm import Session
from . import db_models
from ..models import schemas

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(db_models.DbUser).offset(skip).limit(limit).all()

def get_user(db: Session, user_id: int):
    return db.query(db_models.DbUser).filter(db_models.DbUser.uid == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(db_models.DbUser).filter(db_models.DbUser.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password + "notreally"
    db_user = db_models.DbUser(username=user.username, password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user) # now contains generated uid etc.
    return db_user