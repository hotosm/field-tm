"""Read-only project API for other HOT tools (e.g. Portal)."""

from litestar import Router, get
from litestar.di import Provide
from psycopg import AsyncConnection

from app.auth.auth_deps import get_optional_auth_user, get_user_sub, login_required
from app.auth.roles import viewable_project
from app.db.database import db_conn
from app.db.models import DbProject


def project_summary(project: DbProject) -> dict:
    """Minimal public project metadata."""
    return {
        "id": project.id,
        "name": project.project_name,
        "field_mapping_app": project.field_mapping_app,
        "status": project.status,
        "visibility": project.visibility,
        "location_str": project.location_str,
        "centroid": project.centroid,
    }


@get(
    "/mine",
    dependencies={"db": Provide(db_conn), "auth_user": Provide(login_required)},
)
async def my_projects(db: AsyncConnection, auth_user: object) -> list[dict]:
    """Projects the current user created or has a role on."""
    projects = await DbProject.all(db, user_sub=get_user_sub(auth_user)) or []
    return [project_summary(project) for project in projects]


@get(
    "/{project_id:int}",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(get_optional_auth_user),
        "project": Provide(viewable_project),
    },
)
async def project_detail(project: DbProject) -> dict:
    """A single project's summary."""
    return project_summary(project)


project_router = Router(
    path="/api/v1/projects",
    tags=["api"],
    route_handlers=[my_projects, project_detail],
)
