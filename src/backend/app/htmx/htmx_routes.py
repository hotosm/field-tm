"""HTMX router composition."""

from litestar import Router

from app.htmx.basemap.basemap_routes import ROUTE_HANDLERS as BASEMAP_HANDLERS
from app.htmx.landing_routes import landing, login_page, metrics_partial
from app.htmx.project_create.project_create_page_routes import (
    ROUTE_HANDLERS as PROJECT_CREATE_PAGE_HANDLERS,
)
from app.htmx.project_create.project_create_submit_routes import (
    ROUTE_HANDLERS as PROJECT_CREATE_SUBMIT_HANDLERS,
)
from app.htmx.project_create.project_create_xlsform_routes import (
    ROUTE_HANDLERS as PROJECT_CREATE_XLSFORM_HANDLERS,
)
from app.htmx.project_detail_routes import (
    add_qfc_collaborators_htmx,
    delete_project_htmx,
    export_project_geojson_htmx,
    project_details,
    project_qrcode_htmx,
    qfc_collaborator_form_htmx,
)
from app.htmx.project_list_routes import project_listing
from app.htmx.qfc_admin.qfc_admin_routes import ROUTE_HANDLERS as QFC_ADMIN_HANDLERS
from app.htmx.setup_steps.setup_step_extract_routes import (
    ROUTE_HANDLERS as SETUP_STEP_EXTRACT_HANDLERS,
)
from app.htmx.setup_steps.setup_step_finalize_routes import (
    ROUTE_HANDLERS as SETUP_STEP_FINALIZE_HANDLERS,
)
from app.htmx.setup_steps.setup_step_split_routes import (
    ROUTE_HANDLERS as SETUP_STEP_SPLIT_HANDLERS,
)
from app.htmx.setup_steps.setup_step_validate_routes import (
    ROUTE_HANDLERS as SETUP_STEP_VALIDATE_HANDLERS,
)
from app.htmx.static_routes import (
    serve_apple_touch_icon,
    serve_favicon_ico,
    serve_favicon_png,
    serve_favicon_svg,
    serve_maskable_icon,
    serve_pwa_64,
    serve_pwa_192,
    serve_pwa_512,
    serve_static_css,
    serve_static_image,
    serve_static_js,
)

htmx_router = Router(
    path="/",
    tags=["htmx"],
    route_handlers=[
        serve_favicon_png,
        serve_favicon_svg,
        serve_favicon_ico,
        serve_apple_touch_icon,
        serve_maskable_icon,
        serve_pwa_192,
        serve_pwa_512,
        serve_pwa_64,
        landing,
        login_page,
        project_listing,
        metrics_partial,
        *PROJECT_CREATE_PAGE_HANDLERS,
        project_details,
        delete_project_htmx,
        *PROJECT_CREATE_SUBMIT_HANDLERS,
        serve_static_css,
        serve_static_js,
        serve_static_image,
        *PROJECT_CREATE_XLSFORM_HANDLERS,
        *SETUP_STEP_EXTRACT_HANDLERS,
        *SETUP_STEP_SPLIT_HANDLERS,
        *SETUP_STEP_FINALIZE_HANDLERS,
        project_qrcode_htmx,
        qfc_collaborator_form_htmx,
        add_qfc_collaborators_htmx,
        export_project_geojson_htmx,
        *SETUP_STEP_VALIDATE_HANDLERS,
        *QFC_ADMIN_HANDLERS,
        *BASEMAP_HANDLERS,
    ],
)
