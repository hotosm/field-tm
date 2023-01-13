from typing import Union

from fastapi import Header
from osm_login_python.core import Auth
from pydantic import BaseModel
from src.config import config  # read from the config


class AuthUser(BaseModel):
    id: int
    username: str
    img_url: Union[str, None]


# config plan
osm_auth = Auth(
    osm_url=config.get("OAUTH", "url"),
    client_id=config.get("OAUTH", "client_id"),
    client_secret=config.get("OAUTH", "client_secret"),
    secret_key=config.get("OAUTH", "secret_key"),
    login_redirect_uri=config.get("OAUTH", "login_redirect_uri"),
    scope=config.get("OAUTH", "scope"),
)


def login_required(access_token: str = Header(...)):
    return osm_auth.deserialize_access_token(access_token)
