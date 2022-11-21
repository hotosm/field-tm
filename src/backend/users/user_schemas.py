from pydantic import BaseModel

class UserBase(BaseModel):
    username: str

class UserIn(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

class UserOut(UserBase):
    id: int

    class Config:
        orm_mode = True

class LoginResult(BaseModel):
    user: UserOut
        



