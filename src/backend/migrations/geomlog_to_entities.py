"""Insert geometrylog data into odk_entities table instead."""

import asyncio
from functools import partial

from psycopg import AsyncConnection
from psycopg.rows import class_row

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


async def process_geometrylogs(db: AsyncConnection, project_id: int) -> dict:
    """Fetch geometrylog records for project."""
    sql = """
        SELECT * FROM geometrylog
        WHERE project_id = %(project_id)s;
    """
    async with db.cursor(row_factory=class_row(dict)) as cur:
        await cur.execute(sql, {"project_id": project_id})
        geomlogs = await cur.fetchall()
        processed = {}
        for geom in geomlogs:
            feature = geom.get("geojson", {})
            entity_id = feature.get("properties", {}).get("entity_id")
            status = geom.get("status")
            task_id = geom.get("task_id")
            processed.update({entity_id: {"status": status, "task_id": task_id}})
        return processed


async def insert_into_entities(
    odk_id: int, odk_creds: central_schemas.ODKCentralDecrypted, geomlog: dict
) -> bool:
    """Insert into ODK Central entities."""
    missing_entities = []
    all_success = True

    async with central_deps.pyodk_client(odk_creds) as client:
        # Fetch all entity IDs from ODK to validate against geomlog
        loop = asyncio.get_running_loop()
        odk_entities = await loop.run_in_executor(
            None,
            lambda: client.entities.list(
                project_id=odk_id, entity_list_name="features"
            ),
        )
        existing_entity_ids = {e.uuid for e in odk_entities}

        for entity_id, data in geomlog.items():
            if entity_id not in existing_entity_ids:
                print(
                    f"⚠️ WARNING: Entity ID {entity_id} from "
                    "geometrylog not found in ODK Central!"
                )
                missing_entities.append(entity_id)
                all_success = False
                continue

            geom_status = data.get("status")
            odk_status = (
                "2" if geom_status == "NEW" else "6" if geom_status == "BAD" else "0"
            )

            try:
                loop = asyncio.get_running_loop()
                update_fn = partial(
                    client.entities.update,
                    entity_id,
                    entity_list_name="features",
                    project_id=odk_id,
                    data={
                        "status": odk_status,
                        "is_new": "✅" if geom_status == "NEW" else "",
                    },
                    force=True,
                )
                await loop.run_in_executor(None, update_fn)
                print(f"✅ Updated entity {entity_id} with status {odk_status}")
            except Exception as e:
                print(f"❌ Failed to update entity {entity_id}: {e}")
                all_success = False

    return all_success


async def convert_geomlogs_to_odk_entities():
    """Convert geomlog records for project to entities."""
    all_success = False

    async with await AsyncConnection.connect(settings.FMTM_DB_URL) as db:
        projects = await fetch_projects(db)

        if not projects:
            print(f"No projects found: {projects}")
            return

        for project in projects:
            project["odk_creds"] = get_odk_creds(project)
            print(f"\n------- Project {project['id']} -------\n")

            try:
                async with central_deps.get_odk_dataset(
                    project["odk_creds"]
                ) as odk_central:
                    await odk_central.createDatasetProperty(
                        project["odkid"],
                        "is_new",
                    )
            except Exception as e:
                print(f"❌ Failed updating project ({project['id']}): {e}")
                if "409" in str(e):
                    print("It's likely the property already exists")
                else:
                    continue

            # Sleep 0.5 second between
            await asyncio.sleep(0.5)

            print(f"✅ is_new property added successfully to project {project['id']}")

            processed_geomlogs = await process_geometrylogs(db, project["id"])
            all_success = await insert_into_entities(
                project["odkid"], project["odk_creds"], processed_geomlogs
            )

        if all_success:
            async with db.cursor(row_factory=class_row(dict)) as cur:
                await cur.execute("DROP TABLE IF EXISTS geometrylog;")
                await cur.execute("DROP INDEX IF EXISTS idx_geometrylog_geojson;")
                await cur.execute("DROP ENUM public.geomstatus;")
                print("🧹 Dropped geometrylog table after successful migration.")
        else:
            print("⚠️ Not all updates succeeded, geometrylog table was NOT dropped.")


if __name__ == "__main__":
    asyncio.run(convert_geomlogs_to_odk_entities())
