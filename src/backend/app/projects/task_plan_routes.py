"""Task planner API: the only integration surface with the planner app.

GET is open to anyone who can view the project (the read-only task map);
PUT needs a project manager.
"""

from typing import Any

from litestar import Router, get, put
from litestar import status_codes as status
from litestar.di import Provide
from litestar.exceptions import HTTPException
from psycopg import AsyncConnection

from app.auth.auth_deps import get_optional_auth_user, login_required
from app.auth.auth_schemas import ProjectUserDict
from app.auth.roles import check_access, project_manager, viewable_project
from app.db.database import db_conn
from app.db.enums import ProjectRole
from app.db.models import DbProject
from app.projects.project_services import ServiceError
from app.projects.task_plan import save_task_plan


def _featcol_or_none(value: object) -> dict | None:
    """Return a non-empty FeatureCollection, else None."""
    if isinstance(value, dict) and value.get("features"):
        return value
    return None


@get(
    "/{project_id:int}/planner-input",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(get_optional_auth_user),
        "project": Provide(viewable_project),
    },
)
async def planner_input(
    db: AsyncConnection, project: DbProject, auth_user: object | None = None
) -> dict:
    """Project area, data extract (managers only) and current task plan."""
    is_manager = auth_user is not None and bool(
        await check_access(
            auth_user, db, project_id=project.id, role=ProjectRole.PROJECT_MANAGER
        )
    )
    return {
        "project": {
            "id": project.id,
            "name": project.project_name,
            "field_mapping_app": getattr(
                project.field_mapping_app, "value", project.field_mapping_app
            ),
        },
        "aoi": project.outline,
        "features": _featcol_or_none(project.data_extract_geojson)
        if is_manager
        else None,
        "task_plan": _featcol_or_none(project.task_areas_geojson),
    }


@put(
    "/{project_id:int}/task-plan",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
    request_max_body_size=50 * 1024 * 1024,
)
async def put_task_plan(
    db: AsyncConnection,
    project_id: int,
    current_user: ProjectUserDict,
    data: Any,  # noqa: ANN401 (validated by clean_task_plan)
) -> dict:
    """Validate and save the task plan. Published projects need a re-sync."""
    try:
        task_count = await save_task_plan(db, project_id, data)
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        ) from e
    return {"task_count": task_count}


task_plan_router = Router(
    path="/api/v1/projects",
    tags=["api"],
    route_handlers=[planner_input, put_task_plan],
)
