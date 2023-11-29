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

"""Auth routes, using OSM OAuth2 endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from loguru import logger as log
from sqlalchemy.orm import Session

from ..db import database
from ..db.db_models import DbUser
from ..users import user_crud
from .osm import AuthUser, init_osm_auth, login_required

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)


@router.get("/osm_login/")
async def login_url(request: Request, osm_auth=Depends(init_osm_auth)):
    """Get Login URL for OSM Oauth Application.

    The application must be registered on openstreetmap.org.
    Open the download url returned to get access_token.

    Args:
        request: The GET request.
        osm_auth: The Auth object from osm-login-python.

    Returns:
        login_url (string): URL to authorize user in OSM.
            Includes URL params: client_id, redirect_uri, permission scope.
    """
    login_url = osm_auth.login()
    log.debug(f"Login URL returned: {login_url}")
    return JSONResponse(content=login_url, status_code=200)


@router.get("/callback/")
async def callback(request: Request, osm_auth=Depends(init_osm_auth)):
    """Performs token exchange between OpenStreetMap and Export tool API.

    Core will use Oauth secret key from configuration while deserializing token,
    provides access token that can be used for authorized endpoints.

    Args:
        request: The GET request.
        osm_auth: The Auth object from osm-login-python.

    Returns:
        access_token(string): The access token provided by the login URL request.
    """
    log.debug(f"Callback url requested: {request.url}")

    # Enforce https callback url
    callback_url = str(request.url).replace("http://", "https://")

    access_token = osm_auth.callback(callback_url)

    log.debug(f"Access token returned: {access_token}")
    return JSONResponse(content={"access_token": access_token}, status_code=200)


@router.get("/me/", response_model=AuthUser)
async def my_data(
    db: Session = Depends(database.get_db),
    user_data: AuthUser = Depends(login_required),
):
    """Read access token and get user details from OSM.

    Args:
        db: The db session.
        user_data: User data provided by osm-login-python Auth.

    Returns:
        user_data(dict): The dict of user data.
    """
    # Save user info in User table
    user = await user_crud.get_user_by_id(db, user_data["id"])
    if not user:
        user_by_username = await user_crud.get_user_by_username(
            db, user_data["username"]
        )
        if user_by_username:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"User with this username {user_data['username']} already exists. "
                    "Please contact the administrator."
                ),
            )

        # Add user to database
        db_user = DbUser(id=user_data["id"], username=user_data["username"])
        db.add(db_user)
        db.commit()

    return JSONResponse(content={"user_data": user_data}, status_code=200)
