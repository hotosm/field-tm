"""Add dataset properties for all projects."""

import asyncio
from time import sleep

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
    """Fetch all projects (no date filter)."""
    sql = """
        SELECT p.id, p.odkid,
               p.odk_central_url, p.odk_central_user, p.odk_central_password,
               p_org.odk_central_url as org_odk_central_url,
               p_org.odk_central_user as org_odk_central_user,
               p_org.odk_central_password as org_odk_central_password
        FROM projects p
        LEFT JOIN organisations p_org ON p.organisation_id = p_org.id
        WHERE p.odkid = 258;
    """
    async with db.cursor(row_factory=class_row(dict)) as cur:
        await cur.execute(sql)
        return await cur.fetchall()


async def add_properties():
    """Add dataset properties to all projects."""
    async with await AsyncConnection.connect(settings.FMTM_DB_URL) as db:
        projects = await fetch_projects(db)

        if not projects:
            print(f"No projects found: {projects}")
            return

        properties_to_add = ["fill", "marker-color", "stroke", "stroke-width"]

        for project in projects:
            project["odk_creds"] = get_odk_creds(project)
            print(f"\n------- Project {project['id']} -------\n")

            try:
                async with central_deps.get_odk_dataset(project["odk_creds"]) as odk_central:
                    for prop in properties_to_add:
                        try:
                            await odk_central.createDatasetProperty(project["odkid"], prop)
                            print(f"✅ Property '{prop}' added successfully.")
                        except Exception as e:
                            print(f"⚠️ Failed adding property '{prop}' for project {project['id']}: {e}")
                            print("If 409 conflict, it's likely the property already exists")
                            print("If 400 conflict, check the project ODK credentials")
                            continue

            except Exception as e:
                print(f"Failed updating project ({project['id']}): {e}")
                continue

            # Sleep 0.5 second between projects
            sleep(0.5)


if __name__ == "__main__":
    asyncio.run(add_properties())
