"""Minimal HTTP service for QFieldCloud user management.

Runs inside a container using the qfield-app image (same Django environment)
so it can use the ORM directly to create users.

Exposes a single endpoint:
    POST /create-user  { "username": "...", "password": "...", "email": "..." }
    → 201  { "status": "created" }
    → 200  { "status": "exists" }
    → 400/500  { "error": "..." }
"""

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "qfieldcloud.settings")

import django  # noqa: E402

django.setup()

from qfieldcloud.core.models import Person  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
log = logging.getLogger(__name__)

PORT = 8001


class UserMgmtHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        log.info("%s - %s", self.address_string(), format % args)

    def do_POST(self):
        if self.path != "/create-user":
            self._send_json(404, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
        except Exception:
            self._send_json(400, {"error": "invalid JSON body"})
            return

        username = (body.get("username") or "").strip()
        password = (body.get("password") or "").strip()
        email = (body.get("email") or f"{username}@noreply.local").strip()

        if not username or not password:
            self._send_json(400, {"error": "username and password are required"})
            return

        try:
            existing_user = Person.objects.filter(username=username).first()
            if existing_user:
                existing_user.email = email
                existing_user.has_accepted_tos = True
                existing_user.set_password(password)
                existing_user.save(
                    update_fields=["email", "has_accepted_tos", "password"]
                )
                log.info("Updated QFieldCloud user '%s'", username)
                self._send_json(200, {"status": "updated"})
                return

            Person.objects.create_user(
                username=username,
                email=email,
                password=password,
                has_accepted_tos=True,
            )
            log.info("Created QFieldCloud user '%s'", username)
            self._send_json(201, {"status": "created"})

        except Exception as exc:
            log.error("Error creating user '%s': %s", username, exc)
            self._send_json(500, {"error": str(exc)})

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), UserMgmtHandler)
    log.info("QFieldCloud user management service listening on port %d", PORT)
    server.serve_forever()
