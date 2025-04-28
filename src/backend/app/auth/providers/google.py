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

"""Core logic for Google OAuth."""

from time import time

from fastapi import Request, Response
from fastapi.exceptions import HTTPException
from loguru import logger as log
from requests_oauthlib import OAuth2Session

from app.auth.auth_logic import (
    create_jwt_tokens,
    set_cookies,
)
from app.config import settings
from app.db.enums import HTTPStatus, UserRole


class GoogleAuth:
    """Main class for Google login."""

    def __init__(
        self,
        authorization_url,
        token_url,
        client_id,
        client_secret,
        login_redirect_uri,
        scope,
    ):
        """Set object params and get OAuth2 session."""
        self.authorization_url = authorization_url
        self.token_url = token_url
        self.client_secret = client_secret
        self.oauth = OAuth2Session(
            client_id,
            redirect_uri=login_redirect_uri,
            scope=scope,
        )

    def login(self) -> str:
        """Generate login URL from Google session.

        Provides a login URL using the session created by Google
        client id and redirect uri supplied.

        Returns:
            str: The login URL for Google OAuth
        """
        login_url, _ = self.oauth.authorization_url(self.authorization_url)
        return {"login_url": login_url}

    def callback(self, callback_url: str) -> dict:
        """Performs token exchange between Google and the callback website.

        Args:
            callback_url (str): Absolute URL should be passed which
                is caught from login_redirect_uri.

        Returns:
            dict: User data retrieved from Google API
        """
        self.oauth.fetch_token(
            self.token_url,
            authorization_response=callback_url,
            client_secret=self.client_secret,
        )

        user_api_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        resp = self.oauth.get(user_api_url)
        if resp.status_code != 200:
            raise ValueError("Invalid response from Google")

        data = resp.json()

        # Map Google user data to our expected format
        user_data = {
            "id": data.get("id"),
            "username": data.get("email").split("@")[0],
            "email": data.get("email"),
            "profile_img": data.get("picture"),
            "role": UserRole.MAPPER.name,
        }

        return user_data


async def init_google_auth():
    """Initialize Auth object for Google login."""
    required_settings = [
        settings.GOOGLE_CLIENT_ID,
        settings.GOOGLE_CLIENT_SECRET,
        settings.google_login_redirect_uri,
    ]
    if not all(required_settings):
        raise HTTPException(
            status_code=HTTPStatus.NOT_IMPLEMENTED,
            detail="Google authentication is not enabled.",
        )

    return GoogleAuth(
        authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://www.googleapis.com/oauth2/v4/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET.get_secret_value(),
        login_redirect_uri=settings.google_login_redirect_uri,
        scope=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
    )


async def handle_google_callback(request: Request, google_auth: GoogleAuth):
    """Handle Google callback in OAuth flow.

    Args:
        request: The GET request.
        google_auth: The GoogleAuth object.

    Returns:
        Response: A response including cookies that will be set in-browser.
    """
    log.debug(f"Google callback url requested: {request.url}")

    # Enforce https callback url
    callback_url = str(request.url).replace("http://", "https://")

    try:
        user_data = google_auth.callback(callback_url)

        jwt_payload = {
            "sub": f"google|{user_data['id']}",
            "aud": settings.FMTM_DOMAIN,
            "iat": int(time()),
            "exp": int(time()) + 86400,
            "username": user_data["username"],
            "email": user_data.get("email"),
            "picture": user_data.get("profile_img"),
            "role": UserRole.MAPPER.name,
        }
    except Exception as e:
        raise ValueError(f"Invalid Google token: {e}") from e

    fmtm_token, refresh_token = create_jwt_tokens(jwt_payload)
    response = Response(status_code=HTTPStatus.OK)
    response_plus_cookies = set_cookies(response, fmtm_token, refresh_token)

    return response_plus_cookies
