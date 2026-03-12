"""Create a test QField buildings project via the external JSON API.

Run inside the api container:
    docker compose exec -T api python3 - < tasks/scripts/create_qfield_test_project.py

The script:
  1. Ensures a local admin user + API key exist (via direct DB access).
  2. Looks up the buildings XLSForm template ID (via direct DB access).
  3. Calls POST http://localhost:8000/api/v1/projects with all parameters in
     one request and prints the resulting URLs and credentials.
"""

import asyncio
import hashlib
import json
import sys
import urllib.error
import urllib.request
from secrets import token_urlsafe
from uuid import uuid4

import psycopg

from app.auth.auth_schemas import AuthUser
from app.config import settings
from app.db.models import DbTemplateXLSForm
from app.auth.user_crud import get_or_create_user

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
        AuthUser(sub="custom|1", username="localadmin", is_admin=True),
    )
    await db.commit()

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
        settings.FTM_DB_URL, autocommit=False
    ) as db:
        print("Setting up local admin user and API key...", flush=True)
        api_key = await _get_or_create_api_key(db)

        print("Looking up buildings XLSForm template...", flush=True)
        template_id = await _get_buildings_template_id(db)

    print("Creating QField project via API (this may take ~60s)...", flush=True)
    payload = {
        "project_name": f"{uuid4()}",
        "field_mapping_app": "QField",
        "description": "Auto-created test project for QField testing",
        "outline": AOI_OUTLINE,
        "hashtags": ["#test"],
        # XLSForm
        "template_form_id": template_id,
        "need_verification_fields": True,
        "mandatory_photo_upload": False,
        "use_odk_collect": False,
        "default_language": "english",
        # Data extract - download OSM buildings
        "osm_category": "buildings",
        "geom_type": "POLYGON",
        "centroid": False,
        # Task splitting
        "algorithm": "DIVIDE_BY_SQUARE",
        "dimension_meters": 100,
    }

    try:
        result = _post_json(f"{API_BASE}/projects", payload, api_key)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        print(f"ERROR {exc.code}: {body}", flush=True)
        sys.exit(1)

    ftm_domain = settings.FTM_DOMAIN or "field.localhost"
    ftm_port = f":{settings.FTM_DEV_PORT}" if settings.FTM_DEV_PORT else ""
    scheme = "http" if "localhost" in ftm_domain else "https"

    project_url = result.get("ftm_url") or (
        f"{scheme}://{ftm_domain}{ftm_port}/projects/{result.get('project_id', 'n/a')}"
    )

    print("", flush=True)
    print("=" * 60, flush=True)
    print("Test QField project created successfully!", flush=True)
    print(f"FieldTM URL:           {project_url}", flush=True)
    print(f"QFieldCloud URL:       {result.get('downstream_url', 'n/a')}", flush=True)
    print(f"Manager username:      {result.get('manager_username', 'n/a')}", flush=True)
    print(f"Manager password:      {result.get('manager_password', 'n/a')}", flush=True)
    print("=" * 60, flush=True)
    print(
        "Open the FieldTM URL, view the QR code, then scan with QField.\n"
        "Mapper credentials are shown below the QR code.",
        flush=True,
    )


asyncio.run(main())
