from fastapi import APIRouter, Depends, HTTPException

# from ..dependencies import get_token_header

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


fake_items_db = {"plumbus": {"name": "Plumbus"}, "gun": {"name": "Portal Gun"}}


@router.get("/")
async def read_projects():
    return fake_items_db


@router.get("/{project_id}")
async def read_project(project_id: str):
    if project_id not in fake_items_db:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"name": fake_items_db[project_id]["name"], "item_id": project_id}


@router.put(
    "/{project_id}",
    responses={403: {"description": "Operation forbidden"}},
)
async def update_item(project_id: str):
    if project_id != "plumbus":
        raise HTTPException(
            status_code=403, detail="You can only update the item: plumbus"
        )
    return {"project_id": project_id, "name": "The great Plumbus"}