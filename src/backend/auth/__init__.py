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
    osm_url=config_env["osm_url"],
    client_id=config_env["osm_client_id"],
    client_secret=config_env["osm_client_secret"],
    secret_key=config_env["osm_secret_key"],
    login_redirect_uri=config_env["osm_login_redirect_uri"],
    scope=config_env["osm_scope"],
)


def login_required(access_token: str = Header(...)):
    return osm_auth.deserialize_access_token(access_token)
