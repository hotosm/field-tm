import os
from typing import Union

from dotenv import dotenv_values
from fastapi import Header
from osm_login_python.core import Auth
from pydantic import BaseModel

# Python Environment Variable setup required on System or .env file
config_env = {
    **dotenv_values(".env"),  # load local file development variables
    **os.environ,  # override loaded values with system environment variables
}

# Access the variable like below
# print(config_env["VAR_NAME"])


class AuthUser(BaseModel):
    id: int
    username: str
    img_url: Union[str, None]


# config plan
osm_auth = Auth(
    osm_url=config_env["OSM_URL"],
    client_id=config_env["OSM_CLIENT_ID"],
    client_secret=config_env["OSM_CLIENT_SECRET"],
    secret_key=config_env["OSM_SECRET_KEY"],
    login_redirect_uri=config_env["OSM_LOGIN_REDIRECT_URI"],
    scope=config_env["OSM_SCOPE"],
)


def login_required(access_token: str = Header(...)):
    return osm_auth.deserialize_access_token(access_token)
