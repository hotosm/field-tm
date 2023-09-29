import os
from typing import Union

from fastapi import Header
from osm_login_python.core import Auth
from pydantic import BaseModel

from ..config import settings

if settings.DEBUG:
    # Required as callback url is http during dev
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


class AuthUser(BaseModel):
    """A Pydantic model representing an authenticated user.

    Attributes:
        id (int): The ID of the user.
        username (str): The username of the user.
        img_url (Union[str, None]): The URL of the user's profile image, or None if not provided.
    """

    id: int
    username: str
    img_url: Union[str, None]


def init_osm_auth():
    """Initialize an instance of the Auth class from the osm_login_python.core module.

    Returns:
        An instance of the Auth class.
    """
    return Auth(
        osm_url=settings.OSM_URL,
        client_id=settings.OSM_CLIENT_ID,
        client_secret=settings.OSM_CLIENT_SECRET,
        secret_key=settings.OSM_SECRET_KEY,
        login_redirect_uri=settings.OSM_LOGIN_REDIRECT_URI,
        scope=settings.OSM_SCOPE,
    )


def login_required(access_token: str = Header(...)):
    """A dependency that deserializes an access token from the request header.

    Args:
        access_token (str, optional): The access token from the request header. Injected by FastAPI.

    Returns:
        The result of deserializing the access token.
    """
    osm_auth = init_osm_auth()
    return osm_auth.deserialize_access_token(access_token)
