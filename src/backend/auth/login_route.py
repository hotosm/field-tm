from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..users import user_schemas, user_crud
from ..db import database

router = APIRouter(
    prefix="/login",
    tags=["login"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=user_schemas.UserOut)
def login(user: user_schemas.UserIn, db: Session = Depends(database.get_db)):
    return user_crud.verify_user(db, user)
