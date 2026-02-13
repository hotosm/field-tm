"""HTMX router composition."""

from litestar import Router

from app.htmx.landing_routes import landing, metrics_partial
from app.htmx.project_create_routes import (
    create_project_htmx,
    get_template_xlsform,
    new_project,
    upload_xlsform_htmx,
)
from app.htmx.project_detail_routes import project_details, project_qrcode_htmx
from app.htmx.project_list_routes import project_listing
from app.htmx.setup_step_routes import (
    accept_data_extract_htmx,
    accept_split_htmx,
    create_project_odk_htmx,
    create_project_qfield_htmx,
    download_osm_data_htmx,
    preview_geojson_htmx,
    preview_tasks_and_data_htmx,
    skip_task_split_htmx,
    split_aoi_htmx,
    submit_geojson_data_extract_htmx,
    upload_geojson_htmx,
    validate_geojson,
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
    serve_static_image,
)

htmx_router = Router(
    path="/",
    tags=["htmx"],
    route_handlers=[
        serve_favicon_ico,
        serve_favicon_png,
        serve_favicon_svg,
        serve_apple_touch_icon,
        serve_maskable_icon,
        serve_pwa_192,
        serve_pwa_512,
        serve_pwa_64,
        landing,
        project_listing,
        metrics_partial,
        new_project,
        project_details,
        create_project_htmx,
        serve_static_image,
        get_template_xlsform,
        upload_xlsform_htmx,
        download_osm_data_htmx,
        upload_geojson_htmx,
        preview_geojson_htmx,
        submit_geojson_data_extract_htmx,
        preview_tasks_and_data_htmx,
        skip_task_split_htmx,
        split_aoi_htmx,
        accept_data_extract_htmx,
        accept_split_htmx,
        create_project_odk_htmx,
        create_project_qfield_htmx,
        project_qrcode_htmx,
        validate_geojson,
    ],
)
