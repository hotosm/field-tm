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

import base64
from functools import lru_cache
from typing import Annotated, Any, Optional, Union

from cryptography.fernet import Fernet
from pydantic import BeforeValidator, TypeAdapter, ValidationInfo, field_validator
from pydantic.networks import HttpUrl, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

HttpUrlStr = Annotated[
    str,
    BeforeValidator(
        lambda value: str(TypeAdapter(HttpUrl).validate_python(value) if value else "")
    ),
]


class Settings(BaseSettings):
    """Main settings class, defining environment variables."""

    APP_NAME: str = "FMTM"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENCRYPTION_KEY: str = ""

    FMTM_DOMAIN: str
    FMTM_DEV_PORT: Optional[str] = "7050"

    EXTRA_CORS_ORIGINS: Optional[Union[str, list[str]]] = []

    @field_validator("EXTRA_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(
        cls,
        val: Union[str, list[str]],
        info: ValidationInfo,
    ) -> Union[list[str], str]:
        """Build and validate CORS origins list.

        By default, the provided frontend URLs are included in the origins list.
        If this variable used, the provided urls are appended to the list.
        """
        default_origins = []

        # Build default origins from env vars
        url_scheme = "http" if info.data.get("DEBUG") else "https"
        local_server_port = (
            f":{info.data.get('FMTM_DEV_PORT')}" if info.data.get("DEBUG") else ""
        )
        if frontend_domain := info.data.get("FMTM_DOMAIN"):
            default_origins = [
                f"{url_scheme}://{frontend_domain}{local_server_port}",
            ]

        if val is None:
            return default_origins

        if isinstance(val, str):
            default_origins += [i.strip() for i in val.split(",")]
            return default_origins

        elif isinstance(val, list):
            default_origins += val
            return default_origins

    API_PREFIX: str = "/"

    FMTM_DB_HOST: Optional[str] = "fmtm-db"
    FMTM_DB_USER: Optional[str] = "fmtm"
    FMTM_DB_PASSWORD: Optional[str] = "fmtm"
    FMTM_DB_NAME: Optional[str] = "fmtm"

    FMTM_DB_URL: Optional[PostgresDsn] = None

    @field_validator("FMTM_DB_URL", mode="after")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        """Build Postgres connection from environment variables."""
        if isinstance(v, str):
            return v
        pg_url = PostgresDsn.build(
            scheme="postgresql",
            username=info.data.get("FMTM_DB_USER"),
            password=info.data.get("FMTM_DB_PASSWORD"),
            host=info.data.get("FMTM_DB_HOST"),
            path=info.data.get("FMTM_DB_NAME", ""),
        )
        return pg_url

    ODK_CENTRAL_URL: Optional[HttpUrlStr] = ""
    ODK_CENTRAL_USER: Optional[str] = ""
    ODK_CENTRAL_PASSWD: Optional[str] = ""

    OSM_CLIENT_ID: str
    OSM_CLIENT_SECRET: str
    OSM_SECRET_KEY: str
    OSM_URL: HttpUrlStr = "https://www.openstreetmap.org"
    OSM_SCOPE: str = "read_prefs"
    OSM_LOGIN_REDIRECT_URI: str = "http://127.0.0.1:7051/osmauth/"

    S3_ENDPOINT: str = "http://s3:9000"
    S3_ACCESS_KEY: Optional[str] = ""
    S3_SECRET_KEY: Optional[str] = ""
    S3_BUCKET_NAME: str = "fmtm-data"
    S3_DOWNLOAD_ROOT: Optional[str] = None

    @field_validator("S3_DOWNLOAD_ROOT", mode="before")
    @classmethod
    def configure_s3_download_root(cls, v: Optional[str], info: ValidationInfo) -> str:
        """Set S3_DOWNLOAD_ROOT for S3 downloads.

        This is required, when we use a containerised S3 service.
        The S3_ENDPOINT is a docker compose service name and not
        resolvable outside of the stack.

        S3_DOWNLOAD_ROOT is equal to S3_ENDPOINT if a public S3 instance
        is used (e.g. AWS S3).
        """
        # If set manually, pass through
        if v and isinstance(v, str):
            return v

        # Externally hosted S3
        s3_endpoint = info.data.get("S3_ENDPOINT")
        if s3_endpoint and s3_endpoint.startswith("https://"):
            return s3_endpoint

        # Containerised S3
        else:
            fmtm_domain = info.data.get("FMTM_DOMAIN")
            # Local dev
            if info.data.get("DEBUG"):
                dev_port = info.data.get("FMTM_DEV_PORT")
                return f"http://s3.{fmtm_domain}:{dev_port}"
            return f"https://s3.{fmtm_domain}"

    UNDERPASS_API_URL: HttpUrlStr = "https://api-prod.raw-data.hotosm.org/v1/"
    SENTRY_DSN: Optional[str] = None

    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=".env", extra="allow"
    )


@lru_cache
def get_settings():
    """Cache settings when accessed throughout app."""
    _settings = Settings()
    if _settings.DEBUG:
        print(f"Loaded settings: {_settings.model_dump()}")
    return _settings


@lru_cache
def get_cipher_suite():
    """Cache cypher suite."""
    return Fernet(settings.ENCRYPTION_KEY)


def encrypt_value(password: str) -> str:
    """Encrypt value before going to the DB."""
    cipher_suite = get_cipher_suite()
    encrypted_password = cipher_suite.encrypt(password.encode("utf-8"))
    return base64.b64encode(encrypted_password).decode("utf-8")


def decrypt_value(db_password: str) -> str:
    """Decrypt the database value."""
    cipher_suite = get_cipher_suite()
    encrypted_password = base64.b64decode(db_password.encode("utf-8"))
    decrypted_password = cipher_suite.decrypt(encrypted_password)
    return decrypted_password.decode("utf-8")


settings = get_settings()
