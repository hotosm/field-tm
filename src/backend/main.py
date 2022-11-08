from typing import Union
from fastapi import FastAPI
from .routes import users, projects
from .db import db_models
from .db.database import SessionLocal, engine, Base

Base.metadata.create_all(bind=engine)

api = FastAPI()

api.include_router(users.router)
# api.include_router(projects.router)

@api.get("/")
def read_root():
    return {"Hello": "Big, big World"}



@api.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}