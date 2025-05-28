"""Upload basemaps on the filesystem to the connected S3 bucket."""

import asyncio
from pathlib import Path

from dotenv import load_dotenv
from psycopg import AsyncConnection

from app.config import settings
from app.db.models import DbBackgroundTask, DbBasemap, DbProject
from app.projects.project_schemas import BasemapOut, BasemapUpdate
from app.s3 import add_file_to_bucket

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")


async def upload_basemap_file(
    project_id: int, org_id: int, basemap: DbBasemap, filepath: str
) -> str:
    """Upload the file to S3 and cleanup the file after."""
    try:
        basemap_out = BasemapOut(
            **basemap.model_dump(exclude={"url"}),
            url=filepath,
        )
        basemap_s3_path = (
            f"{org_id}/{project_id}/basemaps/{basemap_out.id}.{basemap_out.format}"
        )
        print(f"Uploading basemap to S3 path: {basemap_s3_path}")
        add_file_to_bucket(
            settings.S3_BUCKET_NAME,
            basemap_s3_path,
            filepath,
            content_type=basemap_out.mimetype,
        )
        basemap_external_s3_url = (
            f"{settings.S3_DOWNLOAD_ROOT}/{settings.S3_BUCKET_NAME}/{basemap_s3_path}"
        )
        print(f"Upload of basemap to S3 complete: {basemap_external_s3_url}")
        # Delete file on disk
        Path(filepath).unlink(missing_ok=True)

        return basemap_external_s3_url
    except Exception as e:
        print(f"Error uploading basemap file: {e}")
        raise


async def basemap_files_to_s3():
    """Upload basemap file & update the DbBasemap.url field."""
    async with await AsyncConnection.connect(
        settings.FMTM_DB_URL,
    ) as db:
        try:
            projects = await DbProject.all(db)
            if not projects:
                print("No projects found.")
                return

            for project in projects:
                print("")
                print("--------------------------")
                print(f"------- Project {project.id} -------")
                print("--------------------------")
                print("")
                basemaps = await DbBasemap.all(db, project.id)
                if not basemaps:
                    print("No basemaps found for upload.")
                    continue

                for index, basemap in enumerate(basemaps):
                    status = basemap.status
                    filepath = basemap.url

                    if status == "FAILED":
                        print(
                            f"({index}) Cleanup / remove FAILED "
                            f"basemap creation ({basemap.id})"
                        )
                        await DbBasemap.delete(db, basemap.id)
                        if not basemap.background_task_id:
                            continue

                        print(
                            f"Also removing related DbBackgroundTask entry "
                            f"({basemap.background_task_id})"
                        )
                        await DbBackgroundTask.delete(db, basemap.background_task_id)
                        continue

                    if filepath and filepath.startswith("http"):
                        print(
                            f"({index}) Basemap already uploaded "
                            f"({basemap.id}): {basemap.url}"
                        )
                        continue

                    elif not filepath or not Path(filepath).exists():
                        print(
                            f"({index}) File does not exist or invalid "
                            f"filepath for basemap ({basemap.id}): {basemap.url}"
                        )
                        continue

                    try:
                        new_s3_path = await upload_basemap_file(
                            project.id,
                            project.organisation_id,
                            basemap,
                            filepath,
                        )
                        await DbBasemap.update(
                            db,
                            basemap.id,
                            BasemapUpdate(url=new_s3_path),
                        )
                        print(
                            f"({index}) Basemap {basemap.id} "
                            f"URL updated to {new_s3_path}"
                        )
                    except Exception as e:
                        print(
                            f"Failed to process basemap {basemap.id} "
                            f"for project {project.id}: {e}"
                        )
        except Exception as e:
            print(f"Error in basemap_files_to_s3: {e}")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(basemap_files_to_s3())
    loop.close()
