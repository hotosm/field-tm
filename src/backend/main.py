from typing import Union
from fastapi import FastAPI
from .users import user_routes
from .auth import login_route
from .projects import project_routes
from .db.database import SessionLocal, engine, Base

Base.metadata.create_all(bind=engine)

api = FastAPI()

api.include_router(user_routes.router)
api.include_router(login_route.router)
api.include_router(project_routes.router)

@api.get("/")
def read_root():
    return {"Hello": "Big, big World"}

@api.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}