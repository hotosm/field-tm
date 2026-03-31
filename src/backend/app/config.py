# Copyright (c) Humanitarian OpenStreetMap Team
#
# This file is part of Field-TM.
#
#     Field-TM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Field-TM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Field-TM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Config file for Pydantic and LiteStar, using environment variables."""

import base64
import os
from enum import Enum
from functools import lru_cache
from typing import Annotated, Optional, Union
from urllib.parse import urlsplit

from cryptography.fernet import Fernet
from pydantic import (
    BeforeValidator,
    Field,
    SecretStr,
    TypeAdapter,
    ValidationInfo,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic.networks import HttpUrl, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

# NOTE this validator also appends a trailing slash to a URL
HttpUrlStr = Annotated[
    str,
    BeforeValidator(
        lambda value: str(TypeAdapter(HttpUrl).validate_python(value) if value else "")
    ),
]


class AuthProvider(str, Enum):
    """Authentication provider options."""

    BUNDLED = "bundled"  # self-hosted Hanko via contrib/login (default)
    DISABLED = "disabled"  # no authentication - public access only
    HOTOSM = "hotosm"  # centralised HOT login at login.hotosm.org
    CUSTOM = "custom"  # user-supplied HANKO_API_URL / LOGIN_URL


class MonitoringTypes(str, Enum):
    """Configuration options for monitoring."""

    NONE = ""
    SENTRY = "sentry"
    OPENOBSERVE = "openobserve"


class OtelSettings(BaseSettings):
    """Inherited OpenTelemetry specific settings (monitoring).

    These mostly set environment variables set by the OTEL SDK.
    """

    FTM_DOMAIN: Optional[str] = Field(exclude=True)
    LOG_LEVEL: Optional[str] = Field(exclude=True)
    ODK_CENTRAL_URL: Optional[str] = Field(exclude=True)

    @computed_field
    @property
    def otel_log_level(self) -> Optional[str]:
        """Set OpenTelemetry log level."""
        log_level = "info"
        if self.LOG_LEVEL:
            log_level = self.LOG_LEVEL.lower()
            # NOTE setting to DEBUG makes very verbose for every library
            # os.environ["OTEL_LOG_LEVEL"] = log_level
            os.environ["OTEL_LOG_LEVEL"] = "info"
        return log_level

    @computed_field
    @property
    def otel_service_name(self) -> Optional[HttpUrlStr]:
        """Set OpenTelemetry service name for traces."""
        service_name = "unknown"
        if self.FTM_DOMAIN:
            # Return domain with underscores
            service_name = self.FTM_DOMAIN.replace(".", "_")
            # Export to environment for OTEL instrumentation
            os.environ["OTEL_SERVICE_NAME"] = service_name
        return service_name

    @computed_field
    @property
    def otel_python_excluded_urls(self) -> Optional[str]:
        """Set excluded URLs for Python instrumentation."""
        endpoints = "__lbheartbeat__,docs,openapi.json,robots.txt,^/static/.*"
        os.environ["OTEL_PYTHON_EXCLUDED_URLS"] = endpoints
        # Add extra endpoints ignored by for requests
        # NOTE we add ODK Central session auth endpoint here
        if self.ODK_CENTRAL_URL:
            os.environ["OTEL_PYTHON_REQUESTS_EXCLUDED_URLS"] = (
                f"{endpoints}{self.ODK_CENTRAL_URL}/v1/sessions"
            )
        return endpoints

    @computed_field
    @property
    def otel_python_log_correlation(self) -> Optional[str]:
        """Set log correlation for OpenTelemetry Python spans."""
        value = "true"
        os.environ["OTEL_PYTHON_LOG_CORRELATION"] = value
        return value


class SentrySettings(OtelSettings):
    """Optional Sentry OpenTelemetry specific settings (monitoring)."""

    SENTRY_DSN: HttpUrlStr


class OpenObserveSettings(OtelSettings):
    """Optional OpenTelemetry specific settings (monitoring)."""

    OTEL_ENDPOINT: HttpUrlStr = Field(exclude=True)
    OTEL_AUTH_TOKEN: Optional[SecretStr] = Field(exclude=True)

    @computed_field
    @property
    def otel_exporter_otpl_endpoint(self) -> Optional[HttpUrlStr]:
        """Set endpoint for OpenTelemetry."""
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = str(self.OTEL_ENDPOINT)
        return self.OTEL_ENDPOINT

    @computed_field
    @property
    def otel_exporter_otlp_headers(self) -> Optional[str]:
        """Set headers for OpenTelemetry collector service."""
        if not self.OTEL_AUTH_TOKEN:
            return None
        # NOTE auth token must be URL encoded, i.e. space=%20
        auth_header = f"Authorization=Basic%20{self.OTEL_AUTH_TOKEN.get_secret_value()}"
        os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = auth_header
        return auth_header


class Settings(BaseSettings):
    """Main settings defining environment variables."""

    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=".env", extra="allow"
    )

    FTM_DOMAIN: str
    FTM_DEV_PORT: Optional[str] = None
    APP_NAME: str = "Field-TM"
    DEBUG: bool = False
    # Auth provider - controls which Hanko instance and login page are used.
    #   bundled  - self-hosted Hanko via `just start login` (default)
    #   disabled - no authentication, public access only
    #   hotosm   - centralised HOT login (auto-configures HANKO_API_URL + LOGIN_URL)
    #   custom   - bring your own Hanko; set HANKO_API_URL + LOGIN_URL explicitly
    AUTH_PROVIDER: AuthProvider = AuthProvider.BUNDLED
    # Only used directly for AUTH_PROVIDER=custom. For bundled/hotosm these are
    # auto-configured by the model validator below.
    # contrib/login/compose.yaml injects HANKO_PUBLIC_URL for bundled local dev.
    HANKO_API_URL: Optional[str] = None
    HANKO_PUBLIC_URL: Optional[str] = None
    LOGIN_URL: Optional[str] = None

    @model_validator(mode="after")
    def _apply_auth_provider(self) -> "Settings":
        """Auto-configure auth fields based on AUTH_PROVIDER."""
        if self.AUTH_PROVIDER == AuthProvider.DISABLED:
            object.__setattr__(self, "HANKO_API_URL", None)
            object.__setattr__(self, "HANKO_PUBLIC_URL", None)
            object.__setattr__(self, "LOGIN_URL", None)
        elif self.AUTH_PROVIDER == AuthProvider.HOTOSM:
            object.__setattr__(self, "HANKO_API_URL", "https://login.hotosm.org")
            object.__setattr__(self, "LOGIN_URL", "https://login.hotosm.org/app")
        elif self.AUTH_PROVIDER == AuthProvider.BUNDLED:
            if not self.HANKO_API_URL:
                object.__setattr__(self, "HANKO_API_URL", "http://hanko:8000")
        elif self.AUTH_PROVIDER == AuthProvider.CUSTOM:
            if not self.HANKO_API_URL:
                raise ValueError("HANKO_API_URL must be set when AUTH_PROVIDER=custom")
        return self

    LOG_LEVEL: str = "INFO"
    PYODK_LOG_LEVEL: str = "CRITICAL"
    ENCRYPTION_KEY: SecretStr
    # NOTE HS384 is used for simplicity of implementation and compatibility with
    # existing Fernet based database value encryption
    JWT_ENCRYPTION_ALGORITHM: str = "HS384"

    EXTRA_CORS_ORIGINS: Optional[str | list[str]] = None

    @field_validator("EXTRA_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(
        cls,
        extra_origins: Optional[Union[str, list[str]]],
        info: ValidationInfo,
    ) -> list[str]:
        """Build and validate CORS origins list."""
        # Initialize default origins
        default_origins = ["https://xlsform-editor.field.hotosm.org"]

        # Handle localhost/testing scenario
        domain = info.data.get("FTM_DOMAIN", "field.localhost")
        dev_port = info.data.get("FTM_DEV_PORT")
        # NOTE field-tm.dev.test is used as the Playwright test domain
        if "localhost" in domain or "field-tm.dev.test" in domain:
            local_server_port = (
                f":{dev_port}"
                if dev_port and dev_port.lower() not in ("0", "no", "false")
                else ""
            )
            # Manager frontend via proxy
            default_origins.append(f"http://{domain}{local_server_port}")
            # Manager frontend direct port access
            default_origins.append("http://localhost:7051")
            # we also include next port, in case already bound by docker
            default_origins.append("http://localhost:7052")
            # we also include next port, in case already bound by docker
            default_origins.append("http://localhost:7058")
        else:
            # Add the main Field-TM frontend domain
            default_origins.append(f"https://{domain}")

        # Process `extra_origins` if provided
        if isinstance(extra_origins, str):
            # Split by comma and strip whitespace
            extra_origins_list = [
                i.strip() for i in extra_origins.split(",") if i.strip()
            ]
            default_origins.extend(extra_origins_list)
        elif isinstance(extra_origins, list):
            default_origins.extend(extra_origins)

        # Ensure uniqueness and return (remove dups)
        return list(dict.fromkeys(default_origins))

    FTM_DB_HOST: Optional[str] = "fieldtm-db"
    FTM_DB_USER: Optional[str] = "fieldtm"
    FTM_DB_PASSWORD: Optional[SecretStr] = SecretStr("fieldtm")
    FTM_DB_NAME: Optional[str] = "fieldtm"

    FTM_DB_URL: Optional[str] = None

    @field_validator("FTM_DB_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> str:
        """Build Postgres connection from environment variables."""
        if v and isinstance(v, str):
            return v
        pg_url = PostgresDsn.build(
            scheme="postgresql",
            username=info.data.get("FTM_DB_USER"),
            password=info.data.get("FTM_DB_PASSWORD").get_secret_value(),
            host=info.data.get("FTM_DB_HOST"),
            path=info.data.get("FTM_DB_NAME", ""),
        )
        return pg_url.unicode_string()

    # ODK
    ODK_CENTRAL_URL: Optional[HttpUrlStr] = ""
    ODK_CENTRAL_PUBLIC_URL: Optional[HttpUrlStr] = ""
    ODK_CENTRAL_USER: Optional[str] = ""
    ODK_CENTRAL_PASSWD: Optional[SecretStr] = ""

    # QField
    QFIELDCLOUD_URL: Optional[str] = ""
    QFIELDCLOUD_USER: Optional[str] = ""
    QFIELDCLOUD_PASSWORD: Optional[SecretStr] = ""
    QFIELDCLOUD_PROJECT_OWNER: Optional[str] = ""
    QFIELDCLOUD_QGIS_URL: str = "http://qfield-qgis:8080"

    @field_validator("QFIELDCLOUD_URL", mode="after")
    @classmethod
    def append_qfc_api_path(cls, value: Optional[str]) -> Optional[str]:
        """Normalise QFieldCloud URL to always end with /api/v1/.

        Users provide the base domain (e.g. https://qfc.example.com) and the
        API path is appended automatically, consistent with how ODK_CENTRAL_URL
        is handled (where /v1 is appended by the PyODK library).
        """
        if not value:
            return value
        parsed = urlsplit(value.strip())
        if parsed.scheme and parsed.netloc:
            base = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
        else:
            base = value.split("/api/v1")[0].rstrip("/")
        return f"{base}/api/v1/"

    OSM_CLIENT_ID: str
    OSM_CLIENT_SECRET: SecretStr
    # NOTE www is required for now
    # https://github.com/openstreetmap/operations/issues/951#issuecomment-1748717154
    OSM_URL: HttpUrlStr = "https://www.openstreetmap.org"
    OSM_SCOPE: list[str] = ["read_prefs", "send_messages"]
    OSM_SECRET_KEY: SecretStr

    @computed_field
    @property
    def manager_osm_login_redirect_uri(self) -> str:
        """The constructed OSM redirect URL for manager frontend.

        Must be set in the OAuth2 config for the openstreetmap profile.
        """
        if self.DEBUG:
            uri = "http://127.0.0.1:7051/osmauth"
        else:
            uri = f"https://{self.FTM_DOMAIN}/osmauth"
        return uri

    RAW_DATA_API_URL: HttpUrlStr = "https://api-prod.raw-data.hotosm.org/v1"
    RAW_DATA_API_AUTH_TOKEN: Optional[SecretStr] = None

    @field_validator("RAW_DATA_API_AUTH_TOKEN", mode="before")
    @classmethod
    def set_raw_data_api_auth_none(cls, v: Optional[str]) -> Optional[str]:
        """Set RAW_DATA_API_AUTH_TOKEN to None if set to empty string.

        This variable is used by HOTOSM to track raw-data-api usage.
        It is not required if running your own instance.
        """
        if v == "":
            return None
        return v

    MONITORING: Optional[MonitoringTypes] = None

    @computed_field
    @property
    def monitoring_config(self) -> Optional[OpenObserveSettings | SentrySettings]:
        """Get the monitoring configuration."""
        if self.MONITORING == MonitoringTypes.SENTRY:
            return SentrySettings()
        elif self.MONITORING == MonitoringTypes.OPENOBSERVE:
            return OpenObserveSettings()
        return None


@lru_cache
def get_settings():
    """Cache settings when accessed throughout app."""
    _settings = Settings()
    # NOTE hotosm-auth reads these via AuthConfig.from_env() during app startup,
    # so they must be set here.  Skip when auth is disabled.
    if _settings.HANKO_API_URL:
        os.environ["HANKO_API_URL"] = _settings.HANKO_API_URL
    os.environ["COOKIE_SECRET"] = _settings.ENCRYPTION_KEY.get_secret_value()

    if _settings.DEBUG:
        # Enable detailed Python async debugger
        # os.environ["PYTHONASYNCIODEBUG"] = "1"
        print(f"Loaded settings: {_settings.model_dump()}")
    return _settings


@lru_cache
def get_cipher_suite():
    """Cache cypher suite."""
    # Fernet is used by cryptography as a simple and effective default
    # it enforces a 32 char secret.
    #
    # In the future we could migrate this to HS384 encryption, which we also
    # use for our JWT signing. Ideally this needs 48 characters, but for now
    # we are stuck at 32 char to maintain support with Fernet (reuse the same key).
    #
    # However this would require a migration for all existing instances of Field-TM.
    return Fernet(settings.ENCRYPTION_KEY.get_secret_value())


def encrypt_value(password: Union[str, HttpUrlStr]) -> str:
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
