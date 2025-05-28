"""Add dataset property submission ID for old projects."""

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
    """Fetch projects created after a certain date."""
    sql = """
        SELECT p.id, p.odkid, p.created_at,
               p.odk_central_url, p.odk_central_user, p.odk_central_password,
               p_org.odk_central_url as org_odk_central_url,
               p_org.odk_central_user as org_odk_central_user,
               p_org.odk_central_password as org_odk_central_password
        FROM projects p
        LEFT JOIN organisations p_org ON p.organisation_id = p_org.id
        WHERE p.created_at < '2025-01-24 00:00:00.000+00:00'::timestamptz;
    """
    async with db.cursor(row_factory=class_row(dict)) as cur:
        await cur.execute(sql)
        return await cur.fetchall()


async def add_submission_id():
    """Add dataset property for all projects."""
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
                        "submission_ids",
                    )
            except Exception as e:
                print(f"Failed updating project ({project['id']}): {e}")
                print("If 409 conflict, it's likely the property already exists")
                print("If 400 conflict, the project odk credentials may be incorrect")
                continue

            # Sleep 0.5 second between
            sleep(0.5)

            print("✅ Submission ID property added successfully.")


if __name__ == "__main__":
    asyncio.run(add_submission_id())
