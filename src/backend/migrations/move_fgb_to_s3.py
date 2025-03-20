"""Migrate remote raw data api fgb url to fmtm s3 server."""

import asyncio
from io import BytesIO
from typing import List, Tuple

import aiohttp
from psycopg import AsyncConnection

from app.config import settings
from app.s3 import add_obj_to_bucket


async def get_all_existing_fgb_urls() -> List[Tuple[int, int, str]]:
    """Fetches all existing FGB (FlatGeobuf) URLs from the database.

    Returns:
        List[Tuple[int, int, str]]: A list of tuples containing
        - project_id
        - organization_id
        - data_extract_url.
    """
    async with await AsyncConnection.connect(
        settings.FMTM_DB_URL.unicode_string()
    ) as db:
        async with db.cursor() as cur:
            sql = """
                SELECT
                    id,
                    organisation_id AS org_id,
                    data_extract_url
                FROM projects
                WHERE
                    data_extract_url
                LIKE '%production-raw-data-api%';
                -- find the remote fgb url
            """
            await cur.execute(sql)
            results = await cur.fetchall()
    return results


async def read_and_upload_fgb_data() -> None:
    """Reads FGB data from existing URLs and uploads it to the S3 bucket.

    Raises:
        aiohttp.ClientError: If there is an issue with the HTTP request.
        Exception: If there is an issue with uploading to S3 or updating the database.
    """
    project_fgb_urls = await get_all_existing_fgb_urls()

    for project_id, org_id, fgb_url in project_fgb_urls:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(fgb_url) as response:
                    response.raise_for_status()
                    fgb_data = await response.read()

            await upload_fgb_data_to_s3(project_id, org_id, fgb_data)
            print(f"Successfully uploaded FGB data for project {project_id} to S3.")

        except aiohttp.ClientError as e:
            print(
                f"Failed to fetch FGB data from {fgb_url} for project {project_id}: {e}"
            )
        except Exception as e:
            print(f"Error processing project {project_id}: {e}")


async def upload_fgb_data_to_s3(project_id: int, org_id: int, fgb_data: bytes) -> str:
    """Uploads FGB data to the S3 bucket and updates the database with the new URL.

    Args:
        project_id (int): The ID of the project.
        org_id (int): The ID of the organization.
        fgb_data (bytes): The FGB data to upload.

    Returns:
        str: The full S3 URL of the uploaded FGB file.
    """
    fgb_obj = BytesIO(fgb_data)
    s3_fgb_path = f"{org_id}/{project_id}/data_extract.fgb"

    # Upload to S3
    add_obj_to_bucket(
        bucket_name=settings.S3_BUCKET_NAME,
        file_obj=fgb_obj,
        s3_path=s3_fgb_path,
        content_type="application/octet-stream",
    )

    s3_fgb_full_url = (
        f"{settings.S3_DOWNLOAD_ROOT}/{settings.S3_BUCKET_NAME}/{s3_fgb_path}"
    )

    # Update the database with the new URL
    async with await AsyncConnection.connect(
        settings.FMTM_DB_URL.unicode_string()
    ) as db:
        async with db.cursor() as cur:
            sql = """
                UPDATE projects
                SET data_extract_url = %(s3_url)s
                WHERE id = %(project_id)s;
            """
            await cur.execute(
                sql, {"s3_url": s3_fgb_full_url, "project_id": project_id}
            )
            await db.commit()

    return s3_fgb_full_url


async def main() -> None:
    """Main function to execute the FGB data migration process."""
    try:
        await read_and_upload_fgb_data()
        print("FGB data migration completed successfully.")
    except Exception as e:
        print(f"An error occurred during FGB data migration: {e}")


if __name__ == "__main__":
    asyncio.run(main())
