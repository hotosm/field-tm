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

"""Config file for Pydantic and FastAPI, using environment variables."""

import logging
from functools import lru_cache
from typing import Any, Optional, Union

from pydantic import AnyUrl, BaseSettings, PostgresDsn, validator

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Main settings class, defining environment variables."""

    APP_NAME: str = "FMTM"
    DEBUG: bool = False
    LOG_LEVEL: str = "DEBUG"

    URL_SCHEME: Optional[str]
    FRONTEND_MAIN_URL: Optional[str]
    FRONTEND_MAP_URL: Optional[str]

    EXTRA_CORS_ORIGINS: Optional[Union[str, list[AnyUrl]]]

    @validator("EXTRA_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(
        cls, val: Union[str, list[AnyUrl]], values: dict
    ) -> list[str]:
        """Build and validate CORS origins list.

        By default, the provided frontend URLs are included in the origins list.
        If this variable used, the provided urls are appended to the list.
        """
        default_origins = []

        # Build default origins from env vars
        url_scheme = values.get("URL_SCHEME")
        main_url = values.get("FRONTEND_MAIN_URL")
        map_url = values.get("FRONTEND_MAP_URL")
        if url_scheme and main_url and map_url:
            default_origins = [
                f"{url_scheme}://{main_url}",
                f"{url_scheme}://{map_url}",
            ]

        if val is None:
            return default_origins

        if isinstance(val, str):
            default_origins += [i.strip() for i in val.split(",")]
            return default_origins

        elif isinstance(val, list):
            default_origins += val
            return default_origins

        raise ValueError(f"Not a valid CORS origin list: {val}")

    API_PREFIX: Optional[str] = "/"

    FMTM_DB_HOST: Optional[str] = "fmtm-db"
    FMTM_DB_USER: Optional[str] = "fmtm"
    FMTM_DB_PASSWORD: Optional[str] = "fmtm"
    FMTM_DB_NAME: Optional[str] = "fmtm"

    FMTM_DB_URL: Optional[PostgresDsn]

    @validator("FMTM_DB_URL", pre=True)
    def assemble_db_connection(cls, v: str, values: dict[str, Any]) -> Any:
        """Build Postgres connection from environment variables."""
        if isinstance(v, str):
            return v
        if not (user := values.get("FMTM_DB_USER")):
            raise ValueError("FMTM_DB_USER is not present in the environment")
        if not (password := values.get("FMTM_DB_PASSWORD")):
            raise ValueError("FMTM_DB_PASSWORD is not present in the environment")
        if not (host := values.get("FMTM_DB_HOST")):
            raise ValueError("FMTM_DB_HOST is not present in the environment")
        return PostgresDsn.build(
            scheme="postgresql",
            user=user,
            password=password,
            host=host,
            path=f"/{values.get('FMTM_DB_NAME') or ''}",
        )

    ODK_CENTRAL_URL: AnyUrl
    ODK_CENTRAL_USER: str
    ODK_CENTRAL_PASSWD: str

    OSM_CLIENT_ID: str
    OSM_CLIENT_SECRET: str
    OSM_URL: AnyUrl
    OSM_SCOPE: str
    OSM_LOGIN_REDIRECT_URI: AnyUrl
    OSM_SECRET_KEY: str
    OAUTHLIB_INSECURE_TRANSPORT: Optional[str] = 1

    class Config:
        """Pydantic settings config."""

        case_sensitive = True
        env_file = ".env"


@lru_cache
def get_settings():
    """Cache settings, for calling in multiple modules."""
    _settings = Settings()
    # logger.info(f"Loaded settings: {_settings.dict()}")
    return _settings


settings = get_settings()
