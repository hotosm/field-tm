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

"""Auth methods related to OSM OAuth2."""

import os
from typing import Optional

from fastapi import Header, HTTPException, Request
from loguru import logger as log
from osm_login_python.core import Auth
from pydantic import BaseModel

from app.config import settings

if settings.DEBUG:
    # Required as callback url is http during dev
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


class AuthUser(BaseModel):
    id: int
    username: str
    img_url: Optional[str]


def init_osm_auth():
    return Auth(
        osm_url=settings.OSM_URL,
        client_id=settings.OSM_CLIENT_ID,
        client_secret=settings.OSM_CLIENT_SECRET,
        secret_key=settings.OSM_SECRET_KEY,
        login_redirect_uri=settings.OSM_LOGIN_REDIRECT_URI,
        scope=settings.OSM_SCOPE,
    )


def login_required(request: Request, access_token: str = Header(None)):
    osm_auth = init_osm_auth()

    # Attempt extract from cookie if access token not passed
    if not access_token:
        cookie_name = settings.FMTM_DOMAIN.replace(".", "_")
        log.debug(f"Extracting token from cookie {cookie_name}")
        access_token = request.cookies.get(cookie_name)

    if not access_token:
        raise HTTPException(status_code=401, detail="No access token provided")

    return osm_auth.deserialize_access_token(access_token)
