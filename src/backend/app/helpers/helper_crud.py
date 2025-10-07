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
"""Logic for helper routes."""

from email.message import EmailMessage

from aiosmtplib import SMTP, SMTPException
from fastapi.exceptions import HTTPException
from loguru import logger as log
from markdown import markdown

from app.config import settings
from app.db.enums import HTTPStatus


async def send_email(
    user_emails: list[str],
    title: str,
    message_content: str,
):
    """Send an email to a list of email addresses."""
    if not settings.emails_enabled:
        raise HTTPException(
            status_code=HTTPStatus.NOT_IMPLEMENTED,
            detail="An SMTP server has not been configured.",
        )

    message = EmailMessage()
    # NOTE isn't no longer possible to have different login user & FROM header
    message["From"] = settings.SMTP_USER
    message["Subject"] = title
    message.set_content(message_content)
    html_content = markdown(message_content)
    message.add_alternative(html_content, subtype="html")

    smtp_client = SMTP(
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD.get_secret_value(),
        # start_tls=None,  # by default, the connection is upgraded by server
    )

    log.debug(f"Sending email to {', '.join(user_emails)}")
    try:
        async with smtp_client:
            recipient_errors, response = await smtp_client.send_message(
                message, recipients=user_emails
            )

            if recipient_errors:
                log.error(f"Some recipients were refused: {recipient_errors}")

            return response
    except SMTPException as e:
        log.error(e)
        log.error(f"Failed to send email to {', '.join(user_emails)}")
        raise
