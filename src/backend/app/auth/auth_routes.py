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

from fastapi import APIRouter, Depends, Request
from fastapi.logger import logger as log
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..db.db_models import DbUser
from ..db import database
from ..users import user_crud, user_schemas
from .osm import AuthUser, init_osm_auth, login_required

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)


@router.post("/login/")
def login(user: user_schemas.UserIn, db: Session = Depends(database.get_db)):
    """The Login API allows users to authenticate themselves with the application.
    Username and password are passed and users information is obtained in the response.
    """
    return user_crud.verify_user(db, user)


@router.get("/osm_login/")
def login_url(request: Request, osm_auth=Depends(init_osm_auth)):
    """Generate Login URL for authentication using OAuth2 Application registered with OpenStreetMap.
    Click on the download url returned to get access_token.

    Parameters: None

    Returns:
    -------
    - login_url (string) - URL to authorize user to the application via. Openstreetmap
        OAuth2 with client_id, redirect_uri, and permission scope as query_string parameters
    """
    login_url = osm_auth.login()
    log.debug(f"Login URL returned: {login_url}")
    return JSONResponse(content=login_url, status_code=200)


@router.get("/callback/")
def callback(request: Request, osm_auth=Depends(init_osm_auth)):
    """Performs token exchange between OpenStreetMap and Export tool API.

    Core will use Oauth secret key from configuration while deserializing token,
    provides access token that can be used for authorized endpoints.

    Parameters: None

    Returns:
    -------
    - access_token (string)
    """
    access_token = osm_auth.callback(str(request.url))
    log.debug(f"Access token returned: {access_token}")
    print(access_token, 'access_token')
    return JSONResponse(content={"access_token": access_token}, status_code=200)


@router.get("/me/", response_model=AuthUser)
def my_data(user_data: AuthUser = Depends(login_required)):
    """Read the access token and provide  user details from OSM user's API endpoint,
    also integrated with underpass .

    Parameters:None

    Returns: user_data
    """

    # Save user info in User table
    db_user = DbUser(id=user_data['id'], username=user_data['username'])
    db_user.commit()

    return JSONResponse(content={"user_data": user_data}, status_code=200)