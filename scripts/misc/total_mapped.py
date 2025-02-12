import os
import httpx
import asyncio
from pydantic import BaseModel
from typing import List, Optional

# API_BASE_URL = "http://localhost:7052"
API_BASE_URL = os.getenv("API_URL", "http://localhost:7052")
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
    response = await client.get(url)
    response.raise_for_status()
    return [ProjectDetails(id=proj["id"], location_str=proj["location_str"]) for proj in response.json()]

async def fetch_entities(client: httpx.AsyncClient, project_id: int) -> List[EntityProperties]:
    url = f"{API_BASE_URL}/projects/{project_id}/entities/statuses"
    response = await client.get(url)
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
    async with httpx.AsyncClient() as client:
        projects = await fetch_projects(client)
        if not projects:
            print("No projects found.")
            return
        
        results = await asyncio.gather(*(process_project(client, proj) for proj in projects))
    
    for result in results:
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
