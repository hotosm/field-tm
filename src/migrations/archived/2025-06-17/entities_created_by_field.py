"""Update ODK entities to have created_at property.

Prefil created_at='svcfmtm' based on is_new field being set.
"""

"""Insert geometrylog data into odk_entities table instead."""

import asyncio
from functools import partial

from psycopg import AsyncConnection
from psycopg.rows import class_row, scalar_row

from app.central import central_deps, central_schemas
from app.config import settings


def get_odk_creds(project: dict) -> central_schemas.ODKCentralDecrypted:
    """Retrieve ODK credentials from project, organisation, or environment."""
    for key_prefix in ["", "org_"]:
        odk_url = project.get(f"{key_prefix}odk_central_url")
        odk_user = project.get(f"{key_prefix}odk_central_user")
        odk_pass = project.get(f"{key_prefix}odk_central_password")

        if all([odk_url, odk_user, odk_pass]):
            return central_schemas.ODKCentralDecrypted(
                odk_central_url=odk_url,
                odk_central_user=odk_user,
                odk_central_password=odk_pass,
            )

    # Fallback to environment variables
    return central_schemas.ODKCentral(
        odk_central_url=settings.ODK_CENTRAL_URL,
        odk_central_user=settings.ODK_CENTRAL_USER,
        odk_central_password=settings.ODK_CENTRAL_PASSWD.get_secret_value(),
    )


async def fetch_projects(db: AsyncConnection) -> list[dict]:
    """Fetch projects plus odk creds."""
    sql = """
        SELECT p.id, p.odkid, p.created_at,
               p.odk_central_url, p.odk_central_user, p.odk_central_password,
               p_org.odk_central_url as org_odk_central_url,
               p_org.odk_central_user as org_odk_central_user,
               p_org.odk_central_password as org_odk_central_password
        FROM projects p
        LEFT JOIN organisations p_org ON p.organisation_id = p_org.id;
    """
    async with db.cursor(row_factory=class_row(dict)) as cur:
        await cur.execute(sql)
        return await cur.fetchall()


async def process_entities(
    odk_id: int, odk_creds: central_schemas.ODKCentralDecrypted, svc_user_sub,
) -> bool:
    """Insert values into ODK Central entities."""
    all_success = True

    async with central_deps.pyodk_client(odk_creds) as client:
        # Fetch all entity IDs from ODK to validate against geomlog
        loop = asyncio.get_running_loop()
        get_entity_fn = partial(
            client.entities.get_table,
            project_id=odk_id,
            entity_list_name="features",
        )
        try:
            odk_entities = await loop.run_in_executor(None, get_entity_fn)
        except Exception as e:
            if "404" in str(e):
                print(f"⚠️ Entities endpoint not found for project {odk_id}, skipping...")
                return True  # skip if project not found.
            raise
        new_feat_entity_ids = {e.get("__id") for e in odk_entities.get("value", {}) if e.get("is_new") == "✅"}

        for entity_id in new_feat_entity_ids:
            try:
                loop = asyncio.get_running_loop()
                update_fn = partial(
                    client.entities.update,
                    entity_id,
                    entity_list_name="features",
                    project_id=odk_id,
                    data={
                        "created_by": svc_user_sub,
                    },
                    force=True,
                )
                await loop.run_in_executor(None, update_fn)
                print(f"✅ Updated entity {entity_id} with is_new=✅")
            except Exception as e:
                print(f"❌ Failed to update entity {entity_id}: {e}")
                all_success = False

    return all_success


async def update_entity_properties():
    """Update is_new --> created_by property."""
    all_success = False

    async with await AsyncConnection.connect(settings.FMTM_DB_URL) as db:
        projects = await fetch_projects(db)

        if not projects:
            print(f"No projects found: {projects}")
            return

        async with db.cursor(row_factory=scalar_row) as cur:
            # Create the created_by field if it doesn't exist
            await cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='odk_entities' AND column_name='created_by'
                    ) THEN
                        ALTER TABLE odk_entities ADD COLUMN created_by character varying;
                    END IF;
                END$$;
            """)

            # Set svcfmtm as the default created_by user, as we can't find out this info now
            await cur.execute("SELECT sub FROM users WHERE username = 'svcfmtm';")
            svc_user_sub = await cur.fetchone()

            # Update odk_entities where is_new is TRUE
            await cur.execute("""
                UPDATE odk_entities
                SET created_by = %s
                WHERE is_new = TRUE;
            """, (svc_user_sub,))

        for project in projects:
            project["odk_creds"] = get_odk_creds(project)
            print(f"\n------- Project {project['id']} -------\n")

            # NOTE We add the new property created_by, but it's not actually
            # NOTE possible as of 2025-05-29 to delete entity properties!
            # NOTE For the small number of projects made since adding this
            # NOTE property, it will just have to remain a zombie property
            try:
                async with central_deps.get_odk_dataset(
                    project["odk_creds"]
                ) as odk_central:
                    await odk_central.createDatasetProperty(
                        project["odkid"],
                        "created_by",
                    )
            except Exception as e:
                print(f"❌ Failed updating project ({project['id']}): {e}")
                if "409" in str(e):
                    print("It's likely the property already exists")
                else:
                    continue

            # Sleep 0.5 second between
            await asyncio.sleep(0.5)

            print(f"✅ created_by property added successfully to project {project['id']}")

            # Always attempt to insert data into entities regardless of field existence
            project_success = await process_entities(
                project["odkid"], project["odk_creds"], svc_user_sub
            )
            all_success = all_success or project_success

        if all_success:
            async with db.cursor() as cur:
                await cur.execute("ALTER TABLE odk_entities DROP COLUMN IF EXISTS is_new;")
                print("🧹 Dropped is_new field from table odk_entities after successful migration.")
        else:
            print("⚠️ Not all updates succeeded, is_new field was NOT dropped.")


if __name__ == "__main__":
    asyncio.run(update_entity_properties())
