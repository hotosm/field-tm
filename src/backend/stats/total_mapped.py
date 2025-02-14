"""For each project get: ID, location, total features, total features mapped.

Also include a project count per country at the end.
"""

import asyncio
import os
from typing import List, Optional
from collections import defaultdict

import httpx
from pydantic import BaseModel

# Access from the same machine: http://localhost:7052
# Access from the docker container: http://localhost:8000
# Access from another container on same docker network: http://api:8000
API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN", None)
headers = {"access-token": API_TOKEN} if API_TOKEN else None

SURVEY_SUBMITTED = 2


class EntityProperties(BaseModel):
    task_id: Optional[int] = None
    osm_id: Optional[int] = None
    tags: Optional[str] = None
    version: Optional[str] = None
    changeset: Optional[str] = None
    timestamp: Optional[str] = None
    status: Optional[int] = None


class ProjectDetails(BaseModel):
    id: int
    location_str: Optional[str]


async def fetch_projects(client: httpx.AsyncClient) -> List[ProjectDetails]:
    url = f"{API_BASE_URL}/projects"
    response = await client.get(url, headers=headers)
    response.raise_for_status()
    return [ProjectDetails(**proj) for proj in response.json()]


async def fetch_entities(
    client: httpx.AsyncClient, project_id: int
) -> List[EntityProperties]:
    url = f"{API_BASE_URL}/projects/{project_id}/entities/statuses"
    response = await client.get(url, headers=headers)
    response.raise_for_status()
    return [EntityProperties(**entity) for entity in response.json()]


async def process_project(client: httpx.AsyncClient, project: ProjectDetails):
    entities = await fetch_entities(client, project.id)
    total_features = len(entities)
    mapped_features = sum(1 for entity in entities if entity.status == SURVEY_SUBMITTED)

    return {
        "project_id": project.id,
        "total_features": total_features,
        "mapped_features": mapped_features,
        "location_str": project.location_str,
    }


async def main():
    print(f"Connecting to server: {API_BASE_URL}")
    async with httpx.AsyncClient() as client:
        projects = await fetch_projects(client)
        if not projects:
            print("No projects found.")
            return

        all_project_details = await asyncio.gather(
            *(process_project(client, proj) for proj in projects)
        )

    project_count_per_country = defaultdict(int)

    print("\nFMTM Stats")
    print("----------\n")
    for project_details in all_project_details:
        print(project_details)

        # Group projects by country
        if not project_details.get("location_str"):
            # Skip if no location string
            continue
        _, country = project_details["location_str"].rsplit(",", 1)  # Extract country
        project_count_per_country[country.strip()] += 1

    print("--------------------------\n")
    print(f"Project count per country:\n")
    for country, count in project_count_per_country.items():
        print(f"{country}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
