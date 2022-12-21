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
        



