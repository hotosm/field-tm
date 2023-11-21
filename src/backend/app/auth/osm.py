import os
from typing import Optional

from fastapi import Header
from osm_login_python.core import Auth
from pydantic import BaseModel

from ..config import settings

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


def login_required(access_token: str = Header(...)):
    osm_auth = init_osm_auth()
    return osm_auth.deserialize_access_token(access_token)
