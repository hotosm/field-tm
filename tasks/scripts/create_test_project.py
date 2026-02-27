"""Create a test ODK buildings project via the external JSON API.

Run inside the api container:
    docker compose exec -T api python3 - < tasks/scripts/create_test_project.py

The script:
  1. Ensures a local admin user + API key exist (via direct DB access).
  2. Looks up the buildings XLSForm template ID (via direct DB access).
  3. Calls POST http://localhost:8000/api/v1/projects with all parameters in
     one request and prints the resulting URLs and credentials.
"""

import asyncio
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from secrets import token_urlsafe
from uuid import uuid4

import psycopg

from app.auth.auth_schemas import AuthUser
from app.config import settings
from app.db.models import DbTemplateXLSForm
from app.users.user_crud import get_or_create_user

# Small AOI in Kathmandu, Nepal - suitable for a quick buildings test
AOI_OUTLINE = {
    "type": "Polygon",
    "coordinates": [[
        [85.299989110, 27.7140080437],
        [85.299989110, 27.7108923499],
        [85.304783157, 27.7108923499],
        [85.304783157, 27.7140080437],
        [85.299989110, 27.7140080437],
    ]],
}

API_BASE = "http://localhost:8000/api/v1"


async def _get_or_create_api_key(db) -> str:
    """Return a plain-text API key, creating one if none exist for localadmin."""
    test_user = await get_or_create_user(
        db,
        AuthUser(sub="osm|1", username="localadmin", is_admin=True),
    )
    await db.commit()

    # Ensure the api_keys table exists (may not exist in dev before migrations)
    async with db.cursor() as cur:
        await cur.execute(
            """
            CREATE TABLE IF NOT EXISTS public.api_keys (
                id SERIAL PRIMARY KEY,
                user_sub character varying NOT NULL
                    REFERENCES public.users(sub) ON DELETE CASCADE,
                key_hash character varying NOT NULL UNIQUE,
                name character varying,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                last_used_at TIMESTAMPTZ,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
            """
        )
    await db.commit()

    # Reuse an existing key if one exists
    async with db.cursor() as cur:
        await cur.execute(
            "SELECT key_hash FROM api_keys WHERE user_sub = %s AND is_active LIMIT 1",
            (test_user.sub,),
        )
        row = await cur.fetchone()

    if row:
        # We stored the hash, not the plain key — create a fresh one instead
        pass

    # Generate a new key
    plain_key = token_urlsafe(32)
    key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
    async with db.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO api_keys (user_sub, key_hash, name)
            VALUES (%s, %s, %s)
            ON CONFLICT (key_hash) DO NOTHING
            """,
            (test_user.sub, key_hash, "test-script-key"),
        )
    await db.commit()
    return plain_key


async def _get_buildings_template_id(db) -> int:
    """Return the database ID of the buildings XLSForm template."""
    templates = await DbTemplateXLSForm.all(db)
    buildings_id = next(
        (t["id"] for t in (templates or []) if "building" in t["title"].lower()),
        None,
    )
    if not buildings_id:
        print("ERROR: Buildings template not found in database!", flush=True)
        sys.exit(1)
    return buildings_id


def _post_json(url: str, payload: dict, api_key: str) -> dict:
    """Send a POST request with JSON body and return parsed JSON response."""
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-API-KEY": api_key,
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


async def main():
    async with await psycopg.AsyncConnection.connect(
        settings.FMTM_DB_URL, autocommit=False
    ) as db:
        print("Setting up local admin user and API key...", flush=True)
        api_key = await _get_or_create_api_key(db)

        print("Looking up buildings XLSForm template...", flush=True)
        template_id = await _get_buildings_template_id(db)

    odk_tunnel_url = os.getenv("ODK_CENTRAL_TUNNEL_URL", "").rstrip("/")
    odk_username = settings.ODK_CENTRAL_USER
    odk_password = (
        settings.ODK_CENTRAL_PASSWD.get_secret_value()
        if settings.ODK_CENTRAL_PASSWD
        else None
    )

    print("Creating project via API (this may take ~60s)...", flush=True)
    payload = {
        "project_name": f"{uuid4()}",
        "field_mapping_app": "ODK",
        "description": "Auto-created test project for ODK Collect testing",
        "outline": AOI_OUTLINE,
        "hashtags": ["#test"],
        # XLSForm
        "template_form_id": template_id,
        "need_verification_fields": True,
        "mandatory_photo_upload": False,
        "use_odk_collect": True,
        "default_language": "english",
        # Data extract — download OSM buildings
        "osm_category": "OSM Buildings",
        "geom_type": "POLYGON",
        "centroid": False,
        # Task splitting
        "algorithm": "DIVIDE_BY_SQUARE",
        "no_of_buildings": 10,
        "dimension_meters": 100,
        "include_roads": True,
        "include_rivers": True,
        "include_railways": True,
        "include_aeroways": True,
    }

    # For mobile testing, force ODK project setup to use the externally reachable
    # tunnel URL rather than internal docker service URLs.
    if odk_tunnel_url and odk_username and odk_password:
        payload.update(
            {
                "external_project_instance_url": odk_tunnel_url,
                "external_project_username": odk_username,
                "external_project_password": odk_password,
            }
        )
        print(f"Using external ODK URL: {odk_tunnel_url}", flush=True)
    else:
        print(
            "No external ODK tunnel URL provided; using server default ODK settings.",
            flush=True,
        )

    try:
        result = _post_json(f"{API_BASE}/projects", payload, api_key)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        print(f"ERROR {exc.code}: {body}", flush=True)
        sys.exit(1)

    fmtm_domain = settings.FMTM_DOMAIN or "fmtm.localhost"
    fmtm_port = f":{settings.FMTM_DEV_PORT}" if settings.FMTM_DEV_PORT else ""
    scheme = "http" if "localhost" in fmtm_domain else "https"

    project_url = result.get("fmtm_url") or (
        f"{scheme}://{fmtm_domain}{fmtm_port}/projects/{result.get('project_id', 'n/a')}"
    )

    print("", flush=True)
    print("=" * 60, flush=True)
    print("Test project created successfully!", flush=True)
    print(f"FieldTM URL:      {project_url}", flush=True)
    print(f"ODK Central:      {result.get('downstream_url', 'n/a')}", flush=True)
    print(f"Manager username: {result.get('manager_username', 'n/a')}", flush=True)
    print(f"Manager password: {result.get('manager_password', 'n/a')}", flush=True)
    print("=" * 60, flush=True)
    print(
        "Open the FieldTM URL, view the QR code, then scan with ODK Collect.",
        flush=True,
    )


asyncio.run(main())
