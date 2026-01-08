# Copyright (c) Humanitarian OpenStreetMap Team
#
# This file is part of Field-TM.
#
#     Field-TM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Field-TM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Field-TM.  If not, see <https:#www.gnu.org/licenses/>.
#

"""HTMX routes for server-rendered HTML interactions."""

import json
import logging
from io import BytesIO
from pathlib import Path

import aiohttp
import geojson
import segno
from anyio import to_thread
from area_splitter.splitter import split_by_sql, split_by_square
from litestar import Router, get, post
from litestar import status_codes as status
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body, Parameter
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.response import Response, Template
from osm_fieldwork.conversion_to_xlsform import convert_to_xlsform
from osm_fieldwork.json_data_models import data_models_path
from osm_fieldwork.OdkCentral import OdkAppUser
from osm_fieldwork.xlsforms import xlsforms_path
from pg_nearest_city import AsyncNearestCity
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.auth.auth_deps import login_required
from app.auth.auth_schemas import AuthUser, ProjectUserDict
from app.auth.roles import mapper
from app.central import central_crud, central_deps
from app.central.central_routes import _validate_xlsform_extension
from app.central.central_schemas import ODKCentral
from app.config import settings
from app.db.database import db_conn
from app.db.enums import FieldMappingApp, ProjectStatus, TaskSplitType, XLSFormType
from app.db.languages_and_countries import countries
from app.db.models import DbProject
from app.db.postgis_utils import (
    check_crs,
    featcol_keep_single_geom_type,
    geojson_to_featcol,
    merge_polygons,
    parse_geojson_file_to_featcol,
    polygon_to_centroid,
)
from app.htmx.htmx_schemas import XLSFormUploadData
from app.projects import project_crud, project_deps, project_schemas
from app.projects.project_schemas import ProjectUpdate

log = logging.getLogger(__name__)


def render_leaflet_map(
    map_id: str,
    geojson_layers: list[dict],
    height: str = "500px",
    show_controls: bool = True,
) -> str:
    """Render a Leaflet map with one or more GeoJSON layers.

    Args:
        map_id: Unique ID for the map container div
        geojson_layers: List of dicts with keys:
            - 'data': GeoJSON FeatureCollection dict
            - 'name': Display name for the layer
            - 'color': Hex color for the layer (default: '#3388ff')
            - 'weight': Line weight (default: 2)
            - 'opacity': Line opacity (default: 0.8)
            - 'fillOpacity': Fill opacity (default: 0.3)
        height: Height of the map container
        show_controls: Whether to show layer control (if multiple layers)

    Returns:
        HTML string with Leaflet map including CSS and JS
    """
    # Escape GeoJSON for JavaScript
    escaped_layers = []
    for layer in geojson_layers:
        geojson_escaped = json.dumps(layer["data"]).replace("</script>", "<\\/script>")
        layer_config = {
            "data": geojson_escaped,
            "name": layer.get("name", "Layer"),
            "color": layer.get("color", "#3388ff"),
            "weight": layer.get("weight", 2),
            "opacity": layer.get("opacity", 0.8),
            "fillOpacity": layer.get("fillOpacity", 0.3),
        }
        escaped_layers.append(layer_config)

    layers_json = json.dumps(escaped_layers).replace("</script>", "<\\/script>")

    map_html = f"""
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <div id="{map_id}" style="height: {height}; width: 100%; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 15px;"></div>
    <script>
        (function() {{
            // Initialize Leaflet map
            const map = L.map('{map_id}').setView([0, 0], 2);
            
            // Add OpenStreetMap tile layer
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19
            }}).addTo(map);
            
            // Load and display GeoJSON layers
            const layersConfig = {layers_json};
            const layers = [];
            let allBounds = [];
            
            layersConfig.forEach(function(layerConfig, index) {{
                const geojsonData = JSON.parse(layerConfig.data);
                const geojsonLayer = L.geoJSON(geojsonData, {{
                    style: function(feature) {{
                        return {{
                            color: layerConfig.color,
                            weight: layerConfig.weight,
                            opacity: layerConfig.opacity,
                            fillOpacity: layerConfig.fillOpacity
                        }};
                    }},
                    onEachFeature: function(feature, layer) {{
                        if (feature.properties) {{
                            const props = Object.keys(feature.properties).slice(0, 5).map(k => 
                                '<strong>' + k + ':</strong> ' + feature.properties[k]
                            ).join('<br>');
                            layer.bindPopup('<strong>' + layerConfig.name + '</strong><br>' + (props || 'No properties'));
                        }}
                    }}
                }});
                
                geojsonLayer.addTo(map);
                layers.push({{name: layerConfig.name, layer: geojsonLayer}});
                
                // Collect bounds for fitting
                if (geojsonLayer.getBounds().isValid()) {{
                    allBounds.push(geojsonLayer.getBounds());
                }}
            }});
            
            // Add layer control if multiple layers and controls enabled
            if (layers.length > 1 && {str(show_controls).lower()}) {{
                const layerControl = L.control.layers({{}}, {{}});
                layers.forEach(function(l) {{
                    layerControl.addOverlay(l.layer, l.name);
                }});
                layerControl.addTo(map);
            }}
            
            // Fit map to all layer bounds
            if (allBounds.length > 0) {{
                let combinedBounds = allBounds[0];
                for (let i = 1; i < allBounds.length; i++) {{
                    combinedBounds = combinedBounds.extend(allBounds[i]);
                }}
                map.fitBounds(combinedBounds);
            }}
        }})();
    </script>
    """
    return map_html


@get(
    path="/",
    dependencies={"db": Provide(db_conn)},
)
async def home(request: HTMXRequest, db: AsyncConnection) -> Template:
    projects = await DbProject.all(db, limit=12) or []
    return HTMXTemplate(template_name="home.html", context={"projects": projects})


@get(
    path="/new",
    dependencies={"db": Provide(db_conn)},
)
async def new_project(request: HTMXRequest, db: AsyncConnection) -> Template:
    """Render the new project creation form."""
    return HTMXTemplate(template_name="new_project.html")


@get(
    path="/htmxprojects/{project_id:int}",
    dependencies={"db": Provide(db_conn)},
)
async def project_details(
    request: HTMXRequest,
    db: AsyncConnection,
    project_id: int,
) -> Template:
    """Render project details page."""
    try:
        project = await DbProject.one(db, project_id)
        return HTMXTemplate(
            template_name="project_details.html", context={"project": project}
        )
    except KeyError:
        # Project not found
        return HTMXTemplate(
            template_name="project_details.html", context={"project": None}
        )


async def _get_template_xlsform_bytes(
    form_id: int,
    db: AsyncConnection,
) -> bytes | None:
    """Get template XLSForm bytes by ID from database or osm-fieldwork.

    Returns the bytes if found, None otherwise.
    """
    # First try to get from database
    sql = """
        SELECT title, xls
        FROM template_xlsforms
        WHERE id = %(form_id)s;
    """

    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(sql, {"form_id": form_id})
        result = await cur.fetchone()

    if not result:
        return None

    # If XLSForm bytes exist in database, return them
    if result.get("xls"):
        return result["xls"]

    # If not in database, try to get from osm-fieldwork by title
    form_title = result.get("title")
    if form_title:
        try:
            # Map title to XLSFormType enum value
            form_type = None
            for xls_type in XLSFormType:
                if xls_type.value == form_title:
                    form_type = xls_type
                    break

            if form_type:
                form_filename = form_type.name
                form_path = f"{xlsforms_path}/{form_filename}.yaml"
                xlsx_bytes = convert_to_xlsform(str(form_path))
                if xlsx_bytes:
                    return xlsx_bytes
        except Exception as e:
            log.error(f"Error converting YAML to XLSForm: {e}", exc_info=True)

    return None


@get(
    "/template-xlsform/{form_id:int}",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
)
async def get_template_xlsform(
    form_id: int,
    db: AsyncConnection,
) -> Response:
    """Get template XLSForm bytes by ID from database or osm-fieldwork."""
    xlsx_bytes = await _get_template_xlsform_bytes(form_id, db)

    if not xlsx_bytes:
        return Response(
            content="Template XLSForm not found",
            status_code=404,
        )

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=template_{form_id}.xlsx"
        },
    )


@get("/static/images/{filename:str}")
async def serve_static_image(filename: str) -> Response:
    """Serve static image files."""
    static_dir = Path(__file__).parent.parent / "static" / "images"
    file_path = static_dir / filename

    # Security: only allow SVG files and ensure no path traversal
    if (
        not filename.endswith(".svg")
        or ".." in filename
        or "/" in filename
        or "\\" in filename
    ):
        return Response(
            content="Forbidden",
            status_code=403,
        )

    if not file_path.exists():
        return Response(
            content="Not Found",
            status_code=404,
        )

    with open(file_path, "rb") as f:
        content = f.read()

    return Response(
        content=content,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=3600"},
    )


# Individual route handlers for favicon and icons
async def _serve_icon_file(filename: str, media_type: str) -> Response:
    """Helper to serve icon files."""
    icons_dir = Path(__file__).parent.parent / "static" / "icons"
    file_path = icons_dir / filename

    # Handle favicon.ico - try .png if .ico doesn't exist
    if filename == "favicon.ico" and not file_path.exists():
        file_path = icons_dir / "favicon.png"
        if not file_path.exists():
            return Response(
                content="Not Found",
                status_code=404,
            )
        media_type = "image/png"
    else:
        if not file_path.exists():
            return Response(
                content="Not Found",
                status_code=404,
            )

    with open(file_path, "rb") as f:
        content = f.read()

    return Response(
        content=content,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=86400"},  # Cache for 1 day
    )


@get("/favicon.ico")
async def serve_favicon_ico() -> Response:
    """Serve favicon.ico."""
    return await _serve_icon_file("favicon.ico", "image/x-icon")


@get("/favicon.png")
async def serve_favicon_png() -> Response:
    """Serve favicon.png."""
    return await _serve_icon_file("favicon.png", "image/png")


@get("/favicon.svg")
async def serve_favicon_svg() -> Response:
    """Serve favicon.svg."""
    return await _serve_icon_file("favicon.svg", "image/svg+xml")


@get("/apple-touch-icon-180x180.png")
async def serve_apple_touch_icon() -> Response:
    """Serve apple-touch-icon-180x180.png."""
    return await _serve_icon_file("apple-touch-icon-180x180.png", "image/png")


@get("/maskable-icon-512x512.png")
async def serve_maskable_icon() -> Response:
    """Serve maskable-icon-512x512.png."""
    return await _serve_icon_file("maskable-icon-512x512.png", "image/png")


@get("/pwa-192x192.png")
async def serve_pwa_192() -> Response:
    """Serve pwa-192x192.png."""
    return await _serve_icon_file("pwa-192x192.png", "image/png")


@get("/pwa-512x512.png")
async def serve_pwa_512() -> Response:
    """Serve pwa-512x512.png."""
    return await _serve_icon_file("pwa-512x512.png", "image/png")


@get("/pwa-64x64.png")
async def serve_pwa_64() -> Response:
    """Serve pwa-64x64.png."""
    return await _serve_icon_file("pwa-64x64.png", "image/png")


@post(
    path="/projects/create",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
)
async def create_project_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    auth_user: AuthUser,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    """Create a project via HTMX form submission."""
    try:
        # Extract form data
        project_name = data.get("project_name", "").strip()
        description = data.get("description", "").strip() or None
        field_mapping_app = data.get("field_mapping_app", "").strip()
        hashtags_str = data.get("hashtags", "").strip()
        outline_str = data.get("outline", "").strip()

        # Validate required fields
        if not project_name:
            return Response(
                content='<div id="form-error" style="margin-bottom: 16px; display: block;"><wa-callout variant="danger"><span id="form-error-message">Project name is required.</span></wa-callout></div>',
                media_type="text/html",
                status_code=400,
            )

        if not description or not description.strip():
            return Response(
                content='<div id="form-error" style="margin-bottom: 16px; display: block;"><wa-callout variant="danger"><span id="form-error-message">Description is required.</span></wa-callout></div>',
                media_type="text/html",
                status_code=400,
                headers={
                    "HX-Retarget": "#description-error",
                    "HX-Reswap": "innerHTML",
                },
            )

        if not field_mapping_app:
            return Response(
                content='<div id="form-error" style="margin-bottom: 16px; display: block;"><wa-callout variant="danger"><span id="form-error-message">Field Mapping App is required.</span></wa-callout></div>',
                media_type="text/html",
                status_code=400,
            )

        if not outline_str:
            error_msg = "You must draw or upload an Area of Interest (AOI) on the map before submitting."
            return Response(
                content=f'<div id="form-error" style="margin-bottom: 16px; display: block;"><wa-callout variant="danger"><span id="form-error-message">{error_msg}</span></wa-callout></div>',
                media_type="text/html",
                status_code=400,
                headers={
                    "HX-Trigger": json.dumps({"missingOutline": error_msg}),
                },
            )

        # Parse outline GeoJSON
        try:
            outline = json.loads(outline_str)
        except json.JSONDecodeError:
            return Response(
                content='<div id="form-error" style="margin-bottom: 16px; display: block;"><wa-callout variant="danger"><span id="form-error-message">Project area must be valid JSON (GeoJSON Polygon, MultiPolygon, Feature, or FeatureCollection).</span></wa-callout></div>',
                media_type="text/html",
                status_code=400,
            )

        # Parse hashtags
        hashtags = []
        if hashtags_str:
            hashtags = [tag.strip() for tag in hashtags_str.split(",") if tag.strip()]

        # Create StubProjectIn object
        project_data = project_schemas.StubProjectIn(
            project_name=project_name,
            field_mapping_app=field_mapping_app,
            description=description.strip(),
            outline=outline,
            hashtags=hashtags,
            merge=True,
        )

        # Remove merge field as it is not in database
        if hasattr(project_data, "merge"):
            delattr(project_data, "merge")
        project_data.status = ProjectStatus.DRAFT

        # Check for duplicate project name before creating
        exists = await project_deps.project_name_does_not_already_exist(
            db, project_data.project_name
        )
        if exists:
            error_msg = f"Project with name '{project_data.project_name}' already exists. Please choose a different name."
            return Response(
                content=f'<div id="form-error" style="margin-bottom: 16px; display: block;"><wa-callout variant="danger"><span id="form-error-message">{error_msg}</span></wa-callout></div>',
                media_type="text/html",
                status_code=status.HTTP_409_CONFLICT,
                headers={
                    "HX-Trigger": json.dumps({"duplicateProjectName": error_msg}),
                },
            )

        # Get the location_str via reverse geocode
        try:
            # Get outline dict - StubProjectIn.outline is a Pydantic model, so use model_dump()
            outline_dict = project_data.outline.model_dump()
            async with AsyncNearestCity(db) as geocoder:
                # polygon_to_centroid can handle Polygon, MultiPolygon, Feature, or FeatureCollection
                centroid = await polygon_to_centroid(outline_dict)
                latitude, longitude = centroid.y, centroid.x
                location = await geocoder.query(latitude, longitude)
                # Convert to two letter country code --> full name
                if location:
                    country_full_name = (
                        countries.get(location.country, location.country)
                        if location.country
                        else None
                    )
                    if location.city and country_full_name:
                        project_data.location_str = (
                            f"{location.city}, {country_full_name}"
                        )
                    elif location.city:
                        project_data.location_str = location.city
                    elif country_full_name:
                        project_data.location_str = country_full_name
                    else:
                        project_data.location_str = None
                    log.info(
                        f"Geocoded location for project {project_data.project_name}: {project_data.location_str}"
                    )
                else:
                    project_data.location_str = None
                    log.warning(
                        f"Could not geocode location for project {project_data.project_name} at {latitude}, {longitude}"
                    )
        except Exception as e:
            log.error(
                f"Error getting location for project {project_data.project_name}: {e}",
                exc_info=True,
            )
            project_data.location_str = None

        # Create the project in the Field-TM DB
        project_data.created_by_sub = auth_user.sub
        try:
            project = await DbProject.create(db, project_data)
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error creating project via HTMX: {e}")
            raise HTTPException(
                status_code=422,
                detail="Project creation failed.",
            ) from e

        # Return HTMX redirect response
        return Response(
            content="",
            status_code=200,
            headers={
                "HX-Redirect": f"/htmxprojects/{project.id}",
            },
        )

    except HTTPException as e:
        error_msg = (
            str(e.detail)
            if hasattr(e, "detail")
            else "Project creation failed. Please check your inputs and try again."
        )
        return Response(
            content=f'<div id="form-error" style="margin-bottom: 16px; display: block;"><wa-callout variant="danger"><span id="form-error-message">{error_msg}</span></wa-callout></div>',
            media_type="text/html",
            status_code=e.status_code,
        )
    except Exception as e:
        log.error(f"Error creating project via HTMX: {e}")
        return Response(
            content='<div id="form-error" style="margin-bottom: 16px; display: block;"><wa-callout variant="danger"><span id="form-error-message">An unexpected error occurred. Please try again.</span></wa-callout></div>',
            media_type="text/html",
            status_code=500,
        )


@post(
    path="/upload-xlsform-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def upload_xlsform_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    data: XLSFormUploadData = Body(media_type=RequestEncodingType.MULTI_PART),
    project_id: int = Parameter(),
) -> Response:
    """Upload XLSForm via HTMX form submission."""
    project = current_user.get("project")
    if not project:
        return Response(
            content='<wa-callout variant="danger"><span>Project not found.</span></wa-callout>',
            media_type="text/html",
            status_code=404,
        )

    # Verify project_id matches the user's project for security
    if project.id != project_id:
        return Response(
            content='<wa-callout variant="danger"><span>Project ID mismatch. You do not have access to this project.</span></wa-callout>',
            media_type="text/html",
            status_code=403,
        )

    # Use project.id from current_user (more secure)
    project_id = project.id

    # Extract form fields from schema with defaults
    xlsform_file = data.xlsform
    need_verification_fields = data.need_verification_fields or "true"
    mandatory_photo_upload = data.mandatory_photo_upload or "false"
    use_odk_collect = data.use_odk_collect or "false"
    default_language = data.default_language or "english"
    template_form_id = data.template_form_id or ""

    # Get form configuration options (convert string to bool)
    need_verification_fields_bool = (
        need_verification_fields.lower() == "true"
        if isinstance(need_verification_fields, str)
        else bool(need_verification_fields)
    )
    mandatory_photo_upload_bool = (
        mandatory_photo_upload.lower() == "true"
        if isinstance(mandatory_photo_upload, str)
        else bool(mandatory_photo_upload)
    )
    use_odk_collect_bool = (
        use_odk_collect.lower() == "true"
        if isinstance(use_odk_collect, str)
        else bool(use_odk_collect)
    )
    template_form_id_str = str(template_form_id) if template_form_id else ""

    try:
        # Handle template form selection
        if template_form_id_str:
            # Fetch template form bytes
            template_bytes = await _get_template_xlsform_bytes(
                int(template_form_id_str),
                db,
            )
            if not template_bytes:
                return Response(
                    content='<wa-callout variant="danger"><span>Failed to load template form.</span></wa-callout>',
                    media_type="text/html",
                    status_code=404,
                )

            # Create BytesIO from template bytes (template files are already validated)
            xlsform_bytes = BytesIO(template_bytes)
        else:
            # Handle custom file upload
            if not xlsform_file:
                return Response(
                    content='<wa-callout variant="danger"><span>Please select a form or upload a file.</span></wa-callout>',
                    media_type="text/html",
                    status_code=400,
                )
            # Validate and read file bytes
            xlsform_bytes = await _validate_xlsform_extension(xlsform_file)

        # Call the existing upload endpoint logic
        form_name = f"FMTM_Project_{project.id}"

        # Validate and process the form
        await central_crud.validate_and_update_user_xlsform(
            xlsform=xlsform_bytes,
            form_name=form_name,
            need_verification_fields=need_verification_fields_bool,
            mandatory_photo_upload=mandatory_photo_upload_bool,
            default_language=default_language,
            use_odk_collect=use_odk_collect_bool,
        )

        xform_id, project_xlsform = await central_crud.append_fields_to_user_xlsform(
            xlsform=xlsform_bytes,
            form_name=form_name,
            need_verification_fields=need_verification_fields_bool,
            mandatory_photo_upload=mandatory_photo_upload_bool,
            default_language=default_language,
            use_odk_collect=use_odk_collect_bool,
        )

        # Write XLS form content to db
        project_xlsform.seek(0)
        xlsform_db_bytes = project_xlsform.getvalue()
        if len(xlsform_db_bytes) == 0 or not xform_id:
            return Response(
                content='<wa-callout variant="danger"><span>There was an error modifying the XLSForm!</span></wa-callout>',
                media_type="text/html",
                status_code=422,
            )

        log.debug(
            f"Setting project XLSForm db data for xFormId: {xform_id}, bytes length: {len(xlsform_db_bytes)}"
        )
        await DbProject.update(
            db,
            project_id,
            ProjectUpdate(xlsform_content=xlsform_db_bytes),
        )
        await db.commit()
        log.debug(f"Successfully saved XLSForm to database for project {project_id}")

        # Return success response with HTMX redirect
        return Response(
            content='<wa-callout variant="success"><span>✓ Form validated and uploaded successfully! Reloading page...</span></wa-callout>',
            media_type="text/html",
            status_code=200,
            headers={
                "HX-Refresh": "true",  # Reload the page to show updated state
            },
        )

    except Exception as e:
        log.error(f"Error uploading XLSForm via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=f'<wa-callout variant="danger"><span>Error: {error_msg}</span></wa-callout>',
            media_type="text/html",
            status_code=500,
        )


@post(
    path="/download-osm-data-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def download_osm_data_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    project_id: int = Parameter(),
    osm_category: str = Parameter(default="buildings"),
    geom_type: str = Parameter(default="POLYGON"),
    centroid: bool = Parameter(default=False),
) -> Response:
    """Download OSM data extract via HTMX and store GeoJSON in database."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content='<wa-callout variant="danger"><span>Project not found or access denied.</span></wa-callout>',
            media_type="text/html",
            status_code=404,
        )

    try:
        # Get project outline
        outline = project.outline
        if not outline:
            return Response(
                content='<wa-callout variant="danger"><span>Project outline not found.</span></wa-callout>',
                media_type="text/html",
                status_code=400,
            )

        # Convert outline to FeatureCollection format
        aoi_featcol = {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "geometry": outline, "properties": {}}],
        }

        # Get extract config
        try:
            osm_category_enum = XLSFormType[osm_category.lower()]
        except (KeyError, AttributeError):
            osm_category_enum = XLSFormType.buildings

        config_filename = osm_category_enum.name
        data_model = f"{data_models_path}/{config_filename}.json"

        with open(data_model, encoding="utf-8") as f:
            config_data = json.load(f)

        geom_type_lower = geom_type.lower()
        data_config = {
            ("polygon", False): ["ways_poly"],
            ("point", True): ["ways_poly", "nodes"],
            ("point", False): ["nodes"],
            ("polyline", False): ["ways_line"],
        }

        config_data["from"] = data_config.get((geom_type_lower, centroid))
        if geom_type_lower == "polyline":
            geom_type_lower = "line"

        # Generate data extract
        result = await project_crud.generate_data_extract(
            project.id,
            aoi_featcol,
            geom_type_lower,
            config_data,
            centroid,
            True,
        )

        # Download GeoJSON from URL
        download_url = result.data.get("download_url")
        if not download_url:
            return Response(
                content='<wa-callout variant="danger"><span>Failed to get download URL from data extract.</span></wa-callout>',
                media_type="text/html",
                status_code=500,
            )

        # Download and parse GeoJSON
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as response:
                if not response.ok:
                    return Response(
                        content='<wa-callout variant="danger"><span>Failed to download GeoJSON from extract URL.</span></wa-callout>',
                        media_type="text/html",
                        status_code=500,
                    )
                # Read as text first (handles binary/octet-stream content type)
                text_content = await response.text()
                try:
                    geojson_data = json.loads(text_content)
                except json.JSONDecodeError:
                    return Response(
                        content='<wa-callout variant="danger"><span>Failed to parse GeoJSON data from download.</span></wa-callout>',
                        media_type="text/html",
                        status_code=500,
                    )

        # Validate and clean GeoJSON
        featcol = parse_geojson_file_to_featcol(json.dumps(geojson_data))
        featcol_single_geom_type = featcol_keep_single_geom_type(featcol)

        if not featcol_single_geom_type:
            return Response(
                content='<wa-callout variant="danger"><span>Could not process GeoJSON data.</span></wa-callout>',
                media_type="text/html",
                status_code=422,
            )

        await check_crs(featcol_single_geom_type)

        # Don't save to database yet - only save after successful ODK upload
        # Store in hidden input for submission
        feature_count = len(featcol_single_geom_type.get("features", []))
        geojson_json = (
            json.dumps(featcol_single_geom_type)
            .replace("'", "&#39;")
            .replace('"', "&quot;")
        )

        # Automatically show preview after successful download
        # Get the project again to check field_mapping_app for button text
        project = await DbProject.one(db, project_id)
        app_name = "QField"
        if project.field_mapping_app:
            app_str = str(project.field_mapping_app).lower()
            if "odk" in app_str:
                app_name = "ODK"

        # Use reusable map rendering function
        map_html_content = render_leaflet_map(
            map_id="leaflet-map-download",
            geojson_layers=[
                {
                    "data": featcol_single_geom_type,
                    "name": "Data Extract",
                    "color": "#3388ff",
                    "weight": 2,
                    "opacity": 0.8,
                    "fillOpacity": 0.3,
                }
            ],
            height="500px",
            show_controls=False,
        )

        # Return success message with embedded map preview
        return Response(
            content=f"""<wa-callout variant="success"><span>✓ OSM data downloaded successfully! Found {feature_count} features.</span></wa-callout>
            <div id="geojson-preview-container" style="margin-top: 15px;">
                <div style="margin-bottom: 10px;">
                    <wa-callout variant="info">
                        <span>Previewing {feature_count} features on map. Review the data, then submit to {app_name} when ready.</span>
                    </wa-callout>
                </div>
                {map_html_content}
                <form id="submit-data-extract-form" style="margin-top: 15px;">
                    <input type="hidden" name="geojson-data" value='{geojson_json}' />
                    <div style="display: flex; gap: 10px;">
                        <button 
                            id="submit-data-extract-btn" 
                            hx-post="/submit-geojson-data-extract-htmx?project_id={project_id}"
                            hx-target="#submit-status"
                            hx-swap="innerHTML"
                            hx-include="#submit-data-extract-form"
                            class="wa-button wa-button--primary"
                            style="flex: 1;"
                        >
                            Upload Data Extract to {app_name}
                        </button>
                    </div>
                    <div id="submit-status" style="margin-top: 10px;"></div>
                </form>
            </div>""",
            media_type="text/html",
            status_code=200,
        )

    except Exception as e:
        log.error(f"Error downloading OSM data via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=f'<wa-callout variant="danger"><span>Error: {error_msg}</span></wa-callout>',
            media_type="text/html",
            status_code=500,
        )


@post(
    path="/upload-geojson-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def upload_geojson_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
    project_id: int = Parameter(),
) -> Response:
    """Upload custom GeoJSON file via HTMX and store in database."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content='<wa-callout variant="danger"><span>Project not found or access denied.</span></wa-callout>',
            media_type="text/html",
            status_code=404,
        )

    try:
        # Read and validate file
        file_content = await data.read()

        # Validate file extension
        if not data.filename.lower().endswith((".geojson", ".json")):
            return Response(
                content='<wa-callout variant="danger"><span>Invalid file type. Please upload a .geojson or .json file.</span></wa-callout>',
                media_type="text/html",
                status_code=400,
            )

        # Parse and validate GeoJSON using the same logic as validate-geojson endpoint
        # First, parse the file content to get the raw GeoJSON
        try:
            geojson_input = json.loads(file_content)
        except json.JSONDecodeError as e:
            return Response(
                content=f'<wa-callout variant="danger"><span>Invalid JSON format: {str(e)}. Please ensure the file contains valid JSON.</span></wa-callout>',
                media_type="text/html",
                status_code=400,
            )

        # Convert to FeatureCollection and normalize (same as validate-geojson)
        # This handles Feature, FeatureCollection, or Geometry types
        featcol = geojson_to_featcol(geojson_input)

        # Check if we have any features
        if not featcol.get("features", []):
            return Response(
                content='<wa-callout variant="danger"><span>No valid geometries found in GeoJSON.</span></wa-callout>',
                media_type="text/html",
                status_code=422,
            )

        # Validate CRS (same as validate-geojson)
        await check_crs(featcol)

        # For data extracts, keep single geometry type (points, lines, or polygons)
        # Unlike validate-geojson which filters to polygons only for AOI
        featcol_single_geom_type = featcol_keep_single_geom_type(featcol)

        if not featcol_single_geom_type or not featcol_single_geom_type.get(
            "features", []
        ):
            return Response(
                content='<wa-callout variant="danger"><span>Could not process GeoJSON. Please ensure it contains features with a single geometry type (all points, all lines, or all polygons).</span></wa-callout>',
                media_type="text/html",
                status_code=422,
            )

        # Don't save to database yet - only save after successful ODK upload
        # Store in hidden input for submission
        feature_count = len(featcol_single_geom_type.get("features", []))
        geojson_json = (
            json.dumps(featcol_single_geom_type)
            .replace("'", "&#39;")
            .replace('"', "&quot;")
        )

        # Get project to determine app name
        project = await DbProject.one(db, project_id)
        app_name = "QField"
        if project.field_mapping_app:
            app_str = str(project.field_mapping_app).lower()
            if "odk" in app_str:
                app_name = "ODK"

        # Use reusable map rendering function
        map_html_content = render_leaflet_map(
            map_id="leaflet-map-upload",
            geojson_layers=[
                {
                    "data": featcol_single_geom_type,
                    "name": "Data Extract",
                    "color": "#3388ff",
                    "weight": 2,
                    "opacity": 0.8,
                    "fillOpacity": 0.3,
                }
            ],
            height="500px",
            show_controls=False,
        )

        return Response(
            content=f"""<wa-callout variant="success"><span>✓ GeoJSON uploaded successfully! Found {feature_count} features.</span></wa-callout>
            <div id="geojson-preview-container" style="margin-top: 15px;">
                <div style="margin-bottom: 10px;">
                    <wa-callout variant="info">
                        <span>Previewing {feature_count} features on map. Review the data, then submit to {app_name} when ready.</span>
                    </wa-callout>
                </div>
                {map_html_content}
                <form id="submit-data-extract-form" style="margin-top: 15px;">
                    <input type="hidden" name="geojson-data" value='{geojson_json}' />
                    <div style="display: flex; gap: 10px;">
                        <button 
                            id="submit-data-extract-btn" 
                            hx-post="/submit-geojson-data-extract-htmx?project_id={project_id}"
                            hx-target="#submit-status"
                            hx-swap="innerHTML"
                            hx-include="#submit-data-extract-form"
                            class="wa-button wa-button--primary"
                            style="flex: 1;"
                        >
                            Upload Data Extract to {app_name}
                        </button>
                    </div>
                    <div id="submit-status" style="margin-top: 10px;"></div>
                </form>
            </div>""",
            media_type="text/html",
            status_code=200,
        )

    except Exception as e:
        log.error(f"Error uploading GeoJSON via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=f'<wa-callout variant="danger"><span>Error: {error_msg}</span></wa-callout>',
            media_type="text/html",
            status_code=500,
        )


@get(
    path="/preview-geojson-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def preview_geojson_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    project_id: int = Parameter(),
) -> Response:
    """Preview GeoJSON data extract in Leaflet map via HTMX."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content='<wa-callout variant="danger"><span>Project not found or access denied.</span></wa-callout>',
            media_type="text/html",
            status_code=404,
        )

    try:
        # Get stored GeoJSON
        project = await DbProject.one(db, project_id)
        geojson_data = project.data_extract_geojson

        if not geojson_data:
            return Response(
                content='<wa-callout variant="warning"><span>No GeoJSON data found. Please download OSM data or upload a GeoJSON file first.</span></wa-callout>',
                media_type="text/html",
                status_code=404,
            )

        feature_count = len(geojson_data.get("features", []))
        geojson_json = json.dumps(geojson_data)

        # Determine app name for button
        app_name = "QField"
        if project.field_mapping_app:
            app_str = str(project.field_mapping_app).lower()
            if "odk" in app_str:
                app_name = "ODK"

        # Use reusable map rendering function
        map_html_content = render_leaflet_map(
            map_id="leaflet-map-preview",
            geojson_layers=[
                {
                    "data": geojson_data,
                    "name": "Data Extract",
                    "color": "#3388ff",
                    "weight": 2,
                    "opacity": 0.8,
                    "fillOpacity": 0.3,
                }
            ],
            height="500px",
            show_controls=False,
        )

        # Return HTML with Leaflet map
        map_html = f"""
        <div id="geojson-preview-container" style="margin-top: 15px;">
            <div style="margin-bottom: 10px;">
                <wa-callout variant="info">
                    <span>Previewing {feature_count} features on map. Review the data, then submit to ODK/QField when ready.</span>
                </wa-callout>
            </div>
            {map_html_content}
            <div style="display: flex; gap: 10px; margin-top: 15px;">
                <button 
                    id="submit-data-extract-btn" 
                    hx-post="/submit-geojson-data-extract-htmx?project_id={project_id}"
                    hx-target="#submit-status"
                    hx-swap="innerHTML"
                    class="wa-button wa-button--primary"
                    style="flex: 1;"
                >
                    Upload Data Extract to {app_name}
                </button>
            </div>
            <div id="submit-status" style="margin-top: 10px;"></div>
        </div>
        """

        return Response(
            content=map_html,
            media_type="text/html",
            status_code=200,
        )

    except Exception as e:
        log.error(f"Error previewing GeoJSON via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=f'<wa-callout variant="danger"><span>Error: {error_msg}</span></wa-callout>',
            media_type="text/html",
            status_code=500,
        )


@post(
    path="/submit-geojson-data-extract-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def submit_geojson_data_extract_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
    project_id: int = Parameter(),
) -> Response:
    """Submit GeoJSON data extract to ODK/QField as entity list/layer (Step 2).

    This only creates the entity list in ODK or uploads to QField project.
    Full project submission happens in Step 4.
    """
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content='<wa-callout variant="danger"><span>Project not found or access denied.</span></wa-callout>',
            media_type="text/html",
            status_code=404,
        )

    try:
        # Get GeoJSON from request body (passed from download/upload endpoints)
        # or fall back to database if not in request (for backwards compatibility)
        geojson_data = None

        log.debug(
            f"Submit data extract request received. Keys in data: {list(data.keys()) if data else 'None'}"
        )

        if "geojson-data" in data:
            # Get from request body (new flow - not saved to DB yet)
            try:
                geojson_str = data["geojson-data"]
                log.debug(
                    f"Received geojson-data, length: {len(geojson_str) if geojson_str else 0}"
                )
                geojson_data = json.loads(geojson_str)
                log.debug(
                    f"Successfully parsed GeoJSON with {len(geojson_data.get('features', []))} features"
                )
            except json.JSONDecodeError as e:
                log.error(f"Failed to parse GeoJSON from request: {e}")
                return Response(
                    content='<wa-callout variant="danger"><span>Invalid GeoJSON data in request. Please try uploading again.</span></wa-callout>',
                    media_type="text/html",
                    status_code=400,
                )
            except (TypeError, KeyError) as e:
                log.error(f"Error accessing geojson-data from request: {e}")
                return Response(
                    content='<wa-callout variant="danger"><span>Error reading GeoJSON data from request.</span></wa-callout>',
                    media_type="text/html",
                    status_code=400,
                )
        else:
            # Fall back to database (backwards compatibility)
            log.debug("No geojson-data in request, falling back to database")
            project_db = await DbProject.one(db, project_id)
            geojson_data = project_db.data_extract_geojson

        if not geojson_data:
            return Response(
                content='<wa-callout variant="warning"><span>No GeoJSON data found. Please download OSM data or upload a GeoJSON file first.</span></wa-callout>',
                media_type="text/html",
                status_code=404,
            )

        # Get project for other fields
        project = await DbProject.one(db, project_id)

        # Determine field mapping app
        field_mapping_app = project.field_mapping_app
        app_name = "QField"
        is_odk = False
        if field_mapping_app:
            app_str = str(field_mapping_app).lower()
            if "odk" in app_str:
                app_name = "ODK"
                is_odk = True

        # ODK credentials not stored on project, use None to fall back to env vars
        project_odk_creds = None

        # For ODK: Create project if it doesn't exist, then create entity list
        if is_odk:
            project_odk_id = project.external_project_id
            if not project_odk_id:
                # Create ODK project if it doesn't exist
                odk_project = await to_thread.run_sync(
                    central_crud.create_odk_project,
                    project.project_name,
                    project_odk_creds,
                )
                project_odk_id = odk_project["id"]
                # Update project with ODK project ID
                await DbProject.update(
                    db,
                    project_id,
                    project_schemas.ProjectUpdate(external_project_id=project_odk_id),
                )
                await db.commit()
                log.info(
                    f"Created ODK project {project_odk_id} for Field-TM project {project_id}"
                )

        # Extract properties from first feature
        features = geojson_data.get("features", [])
        if not features:
            return Response(
                content='<wa-callout variant="warning"><span>GeoJSON data contains no features.</span></wa-callout>',
                media_type="text/html",
                status_code=400,
            )

        first_feature = features[0]
        entity_properties = list(first_feature.get("properties", {}).keys())

        # Add default style properties if not present
        for field in ["created_by", "fill", "marker-color", "stroke", "stroke-width"]:
            if field not in entity_properties:
                entity_properties.append(field)

        if app_name == "ODK":
            # Create entity list in ODK Central
            entities_list = await central_crud.task_geojson_dict_to_entity_values(
                geojson_data, additional_features=True
            )

            default_style = {
                "fill": "#1a1a1a",
                "marker-color": "#1a1a1a",
                "stroke": "#000000",
                "stroke-width": "6",
            }

            for entity in entities_list:
                data = entity["data"]
                for key, value in default_style.items():
                    data.setdefault(key, value)

            log.debug("Creating ODK entity list 'features' from data extract")
            expected_entity_count = len(entities_list)

            await central_crud.create_entity_list(
                project_odk_creds,
                project_odk_id,
                properties=entity_properties,
                dataset_name="features",
                entities_list=entities_list,
            )

            # Verify that entities were actually created in ODK
            # This ensures we can guarantee the upload succeeded
            async with central_deps.get_odk_dataset(project_odk_creds) as odk_central:
                actual_entity_count = await odk_central.getEntityCount(
                    project_odk_id, "features"
                )

            if actual_entity_count != expected_entity_count:
                error_msg = (
                    f"Upload verification failed: Expected {expected_entity_count} entities "
                    f"but only {actual_entity_count} were found in ODK. "
                    "The data extract may not have been fully uploaded."
                )
                log.error(error_msg)
                return Response(
                    content=f'<wa-callout variant="danger"><span>{error_msg}</span></wa-callout>',
                    media_type="text/html",
                    status_code=500,
                )

            log.info(
                f"Verified {actual_entity_count} entities successfully uploaded to ODK "
                f"for project {project_id}"
            )

            # Only save to database AFTER successful ODK upload and verification
            await DbProject.update(
                db,
                project_id,
                project_schemas.ProjectUpdate(data_extract_geojson=geojson_data),
            )
            await db.commit()
            log.info(
                f"Saved data extract to database for project {project_id} after successful ODK upload"
            )
        else:
            # For QField, we would upload to QField project here
            # This is a placeholder - QField upload logic would go here
            log.debug("QField data extract upload not yet implemented")
            return Response(
                content='<wa-callout variant="info"><span>QField data extract upload will be implemented in a future update.</span></wa-callout>',
                media_type="text/html",
                status_code=200,
            )

        return Response(
            content=f'<wa-callout variant="success"><span>✓ Data extract successfully uploaded to {app_name}! You can now proceed to Step 3 (task splitting) or Step 4 (final submission).</span></wa-callout><script>setTimeout(() => window.location.reload(), 2000);</script>',
            media_type="text/html",
            status_code=200,
            headers={"HX-Refresh": "true"},
        )

    except Exception as e:
        log.error(
            f"Error submitting GeoJSON data extract to ODK/QField via HTMX: {e}",
            exc_info=True,
        )
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=f'<wa-callout variant="danger"><span>Error: {error_msg}</span></wa-callout>',
            media_type="text/html",
            status_code=500,
        )


@get(
    path="/preview-tasks-and-data-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def preview_tasks_and_data_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    project_id: int = Parameter(),
) -> Response:
    """Preview task boundaries and data extract together on a Leaflet map via HTMX."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content='<wa-callout variant="danger"><span>Project not found or access denied.</span></wa-callout>',
            media_type="text/html",
            status_code=404,
        )

    try:
        # Get stored GeoJSON data extract
        project = await DbProject.one(db, project_id)
        data_extract = project.data_extract_geojson

        if not data_extract:
            return Response(
                content='<wa-callout variant="warning"><span>No data extract found. Please download OSM data or upload a GeoJSON file first.</span></wa-callout>',
                media_type="text/html",
                status_code=404,
            )

        # Get task boundaries
        task_boundaries_json = await project_crud.get_task_geometry(db, project_id)
        task_boundaries = None
        if task_boundaries_json:
            if isinstance(task_boundaries_json, str):
                try:
                    task_boundaries = json.loads(task_boundaries_json)
                except json.JSONDecodeError:
                    log.warning(
                        f"Failed to parse task boundaries JSON for project {project_id}"
                    )
            elif isinstance(task_boundaries_json, dict):
                task_boundaries = task_boundaries_json

        if not task_boundaries or not task_boundaries.get("features"):
            return Response(
                content='<wa-callout variant="warning"><span>No task boundaries found. Please split the project into tasks first using the "Split AOI" button above.</span></wa-callout>',
                media_type="text/html",
                status_code=200,  # Return 200 instead of 404 to show message
            )

        # Prepare layers for map
        geojson_layers = []

        # Add data extract layer
        data_feature_count = len(data_extract.get("features", []))
        geojson_layers.append(
            {
                "data": data_extract,
                "name": f"Data Extract ({data_feature_count} features)",
                "color": "#3388ff",
                "weight": 2,
                "opacity": 0.8,
                "fillOpacity": 0.3,
            }
        )

        # Add task boundaries layer
        task_count = len(task_boundaries.get("features", []))
        geojson_layers.append(
            {
                "data": task_boundaries,
                "name": f"Task Boundaries ({task_count} tasks)",
                "color": "#ff7800",
                "weight": 3,
                "opacity": 1.0,
                "fillOpacity": 0.1,
            }
        )

        # Use reusable map rendering function
        map_html_content = render_leaflet_map(
            map_id="leaflet-map-tasks-and-data",
            geojson_layers=geojson_layers,
            height="600px",
            show_controls=True,
        )

        return Response(
            content=f"""
            <div style="margin-top: 15px;">
                <div style="margin-bottom: 10px;">
                    <wa-callout variant="info">
                        <span>Previewing {task_count} task boundaries and {data_feature_count} data features together.</span>
                    </wa-callout>
                </div>
                {map_html_content}
            </div>
            """,
            media_type="text/html",
            status_code=200,
        )

    except Exception as e:
        log.error(
            f"Error previewing tasks and data extract via HTMX: {e}", exc_info=True
        )
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=f'<wa-callout variant="danger"><span>Error: {error_msg}</span></wa-callout>',
            media_type="text/html",
            status_code=500,
        )


@post(
    path="/skip-task-split-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def skip_task_split_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    project_id: int = Parameter(),
) -> Response:
    """Skip task splitting and use the whole AOI as a single task."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content='<wa-callout variant="danger"><span>Project not found or access denied.</span></wa-callout>',
            media_type="text/html",
            status_code=404,
        )

    try:
        # Get project with outline
        project = await DbProject.one(db, project_id)

        if not project.outline:
            return Response(
                content='<wa-callout variant="danger"><span>Project outline not found. Cannot skip task splitting.</span></wa-callout>',
                media_type="text/html",
                status_code=400,
            )

        # For ODK: Don't create task_boundaries dataset (it will be None/empty)
        # For QField: Don't create temp table (it won't exist)
        # The project generation will handle this by using the whole AOI

        # Store empty dict {} to indicate task splitting was skipped
        await DbProject.update(
            db,
            project_id,
            project_schemas.ProjectUpdate(task_areas_geojson={}),
        )
        await db.commit()

        log.info(
            f"Task splitting skipped for project {project_id}. Will use whole AOI as single task."
        )

        return Response(
            content='<wa-callout variant="success"><span>✓ Task splitting skipped. The whole AOI will be used as a single task. You can proceed to Step 4.</span></wa-callout>',
            media_type="text/html",
            status_code=200,
            headers={"HX-Refresh": "true"},
        )

    except Exception as e:
        log.error(f"Error skipping task split via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=f'<wa-callout variant="danger"><span>Error: {error_msg}</span></wa-callout>',
            media_type="text/html",
            status_code=500,
        )


@post(
    path="/split-aoi-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def split_aoi_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    project_id: int = Parameter(),
    algorithm: str = Parameter(default="TASK_SPLITTING_ALGORITHM"),
    no_of_buildings: int = Parameter(default=50),
    dimension_meters: int = Parameter(default=100),
) -> Response:
    """Split AOI into tasks using selected algorithm and upload to ODK/QField."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content='<wa-callout variant="danger"><span>Project not found or access denied.</span></wa-callout>',
            media_type="text/html",
            status_code=404,
        )

    try:
        # Get project with outline
        project = await DbProject.one(db, project_id)

        if not project.outline:
            return Response(
                content='<wa-callout variant="danger"><span>Project outline not found. Cannot split AOI.</span></wa-callout>',
                media_type="text/html",
                status_code=400,
            )

        # Convert outline to FeatureCollection
        aoi_featcol = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": project.outline, "properties": {}}
            ],
        }

        # Get data extract if available
        parsed_extract = project.data_extract_geojson

        # Validate algorithm type
        try:
            algorithm_enum = TaskSplitType(algorithm)
        except ValueError:
            return Response(
                content=f'<wa-callout variant="danger"><span>Invalid algorithm type: {algorithm}</span></wa-callout>',
                media_type="text/html",
                status_code=400,
            )

        # Perform splitting based on algorithm
        log.info(f"Splitting AOI for project {project_id} using algorithm: {algorithm}")

        if algorithm_enum == TaskSplitType.TASK_SPLITTING_ALGORITHM:
            # Use split_by_sql (average buildings per task)
            if not parsed_extract:
                return Response(
                    content='<wa-callout variant="warning"><span>Data extract required for task splitting algorithm. Please download OSM data or upload GeoJSON first.</span></wa-callout>',
                    media_type="text/html",
                    status_code=400,
                )

            # split_by_sql signature: (aoi, db, num_buildings, outfile=None, osm_extract=None)
            features = await to_thread.run_sync(
                split_by_sql,
                aoi_featcol,
                settings.FMTM_DB_URL,
                no_of_buildings,
                None,  # outfile - we don't want to write to file
                parsed_extract,  # osm_extract
            )
        elif algorithm_enum == TaskSplitType.DIVIDE_ON_SQUARE:
            # Use split_by_square (grid-based)
            # split_by_square signature: (aoi, db, meters=100, osm_extract=None, outfile=None)
            features = await to_thread.run_sync(
                split_by_square,
                aoi_featcol,
                settings.FMTM_DB_URL,
                dimension_meters,
                parsed_extract,  # osm_extract (can be None)
                None,  # outfile - we don't want to write to file
            )
        else:
            return Response(
                content=f'<wa-callout variant="danger"><span>Algorithm {algorithm} not yet implemented in HTMX interface.</span></wa-callout>',
                media_type="text/html",
                status_code=400,
            )

        if not features or not features.get("features"):
            return Response(
                content='<wa-callout variant="warning"><span>No task areas generated. Please try different parameters.</span></wa-callout>',
                media_type="text/html",
                status_code=400,
            )

        # Upload task boundaries to ODK/QField
        tasks_featcol = features
        await check_crs(tasks_featcol)

        # Upload to ODK or QField
        if project.field_mapping_app == FieldMappingApp.ODK:
            project_odk_id = project.external_project_id
            if not project_odk_id:
                # Create ODK project if it doesn't exist
                odk_project = await to_thread.run_sync(
                    central_crud.create_odk_project,
                    project.project_name,
                    None,  # Use env vars for credentials
                )
                project_odk_id = odk_project["id"]
                await DbProject.update(
                    db,
                    project_id,
                    project_schemas.ProjectUpdate(external_project_id=project_odk_id),
                )
                await db.commit()

            # Convert task boundaries to entities
            task_entities = []
            for idx, feature in enumerate(tasks_featcol.get("features", [])):
                if feature.get("geometry"):
                    entity_dict = await central_crud.feature_geojson_to_entity_dict(
                        feature, additional_features=True
                    )
                    entity_dict["label"] = f"Task {idx + 1}"
                    if "data" in entity_dict:
                        # Only keep geometry and task_id properties for task boundaries
                        # Filter out any other properties that might cause issues
                        entity_data = {"geometry": entity_dict["data"]["geometry"]}
                        entity_data["task_id"] = str(idx + 1)
                        entity_dict["data"] = entity_data
                    task_entities.append(entity_dict)

            # Create ODKCentral credentials from environment variables
            # ODK credentials not stored on project, use env vars
            project_odk_creds = ODKCentral(
                external_project_instance_url=settings.ODK_CENTRAL_URL,
                external_project_username=settings.ODK_CENTRAL_USER,
                external_project_password=settings.ODK_CENTRAL_PASSWD.get_secret_value()
                if settings.ODK_CENTRAL_PASSWD
                else "",
            )

            try:
                async with central_deps.get_odk_dataset(
                    project_odk_creds
                ) as odk_central:
                    datasets = await odk_central.listDatasets(project_odk_id)
                    if any(ds.get("name") == "task_boundaries" for ds in datasets):
                        log.info(
                            "Task boundaries dataset already exists, will be replaced"
                        )
            except Exception as e:
                log.warning(f"Could not check existing datasets: {e}")

            await central_crud.create_entity_list(
                project_odk_creds,
                project_odk_id,
                properties=["geometry", "task_id"],
                dataset_name="task_boundaries",
                entities_list=task_entities,
            )
            log.info(
                f"Uploaded {len(task_entities)} task boundaries to ODK Central for project {project_id}"
            )
        elif project.field_mapping_app == FieldMappingApp.QFIELD:
            # For QField, store in temp table
            async with db.cursor() as cur:
                await cur.execute(f"""
                    DROP TABLE IF EXISTS temp_task_boundaries_{project_id} CASCADE;
                """)
                await cur.execute(f"""
                    CREATE TEMP TABLE temp_task_boundaries_{project_id} (
                        task_index INTEGER,
                        outline GEOMETRY(POLYGON, 4326)
                    );
                """)
                for idx, feature in enumerate(tasks_featcol.get("features", [])):
                    if feature.get("geometry"):
                        geom_json = json.dumps(feature["geometry"])
                        await cur.execute(
                            f"""
                            INSERT INTO temp_task_boundaries_{project_id} (task_index, outline)
                            VALUES (%s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));
                            """,
                            (idx + 1, geom_json),
                        )
                await db.commit()
            log.info(
                f"Stored {len(tasks_featcol.get('features', []))} task boundaries in temp table for QField project {project_id}"
            )

        # Store task boundaries GeoJSON in database (for both ODK and QField)
        await DbProject.update(
            db,
            project_id,
            project_schemas.ProjectUpdate(task_areas_geojson=tasks_featcol),
        )
        await db.commit()

        task_count = len(tasks_featcol.get("features", []))

        # Auto-preview: Get data extract and show map
        data_extract = project.data_extract_geojson
        if data_extract:
            # Prepare layers for map
            geojson_layers = []

            # Add data extract layer
            data_feature_count = len(data_extract.get("features", []))
            geojson_layers.append(
                {
                    "data": data_extract,
                    "name": f"Data Extract ({data_feature_count} features)",
                    "color": "#3388ff",
                    "weight": 2,
                    "opacity": 0.8,
                    "fillOpacity": 0.3,
                }
            )

            # Add task boundaries layer
            geojson_layers.append(
                {
                    "data": tasks_featcol,
                    "name": f"Task Boundaries ({task_count} tasks)",
                    "color": "#ff7800",
                    "weight": 3,
                    "opacity": 1.0,
                    "fillOpacity": 0.1,
                }
            )

            map_html_content = render_leaflet_map(
                map_id="leaflet-map-split-preview",
                geojson_layers=geojson_layers,
                height="600px",
                show_controls=True,
            )

            preview_html = f"""
            <div style="margin-top: 15px;">
                <div style="margin-bottom: 10px;">
                    <wa-callout variant="info">
                        <span>Previewing {task_count} task boundaries and {data_feature_count} data features together.</span>
                    </wa-callout>
                </div>
                {map_html_content}
            </div>
            """
        else:
            preview_html = ""

        # Return success message in split-status, and preview will be moved to preview container
        return Response(
            content=f"""
            <wa-callout variant="success">
                <span>✓ AOI split successfully! Generated {task_count} task areas using {algorithm.replace("_", " ").title()}.</span>
            </wa-callout>
            <div id="split-preview-wrapper" style="display: none;">{preview_html}</div>
            """,
            media_type="text/html",
            status_code=200,
            headers={"HX-Refresh": "true"},
        )

    except Exception as e:
        log.error(f"Error splitting AOI via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=f'<wa-callout variant="danger"><span>Error: {error_msg}</span></wa-callout>',
            media_type="text/html",
            status_code=500,
        )


@get(
    path="/project-qrcode-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def project_qrcode_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    project_id: int = Parameter(),
) -> Response:
    """Generate and return QR code for a published project."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content='<wa-callout variant="danger"><span>Project not found or access denied.</span></wa-callout>',
            media_type="text/html",
            status_code=404,
        )

    try:
        # Get fresh project data
        project = await DbProject.one(db, project_id)

        if not project.project_name:
            return Response(
                content='<wa-callout variant="danger"><span>Project name not found.</span></wa-callout>',
                media_type="text/html",
                status_code=400,
            )

        qr_code_data_url = None

        if project.field_mapping_app == FieldMappingApp.ODK:
            # For ODK, generate QR code using appuser token
            if not project.external_project_id:
                return Response(
                    content='<wa-callout variant="danger"><span>ODK project ID not found.</span></wa-callout>',
                    media_type="text/html",
                    status_code=400,
                )

            # Get ODK credentials (use None to fall back to env vars)
            project_odk_creds = project.get_odk_credentials()
            if project_odk_creds is None:
                odk_central = ODKCentral(
                    external_project_instance_url=settings.ODK_CENTRAL_URL,
                    external_project_username=settings.ODK_CENTRAL_USER,
                    external_project_password=settings.ODK_CENTRAL_PASSWD.get_secret_value()
                    if settings.ODK_CENTRAL_PASSWD
                    else "",
                )
            else:
                odk_central = project_odk_creds

            # Get appuser token from ODK Central
            from app.central.central_crud import get_odk_app_user, get_odk_project

            appuser = get_odk_app_user(odk_central)
            odk_project = get_odk_project(odk_central)
            appusers = odk_project.listAppUsers(project.external_project_id)

            if not appusers:
                return Response(
                    content='<wa-callout variant="danger"><span>No appuser found for this ODK project.</span></wa-callout>',
                    media_type="text/html",
                    status_code=400,
                )

            appuser_token = appusers[0].get("token")
            if not appuser_token:
                return Response(
                    content='<wa-callout variant="danger"><span>Appuser token not found.</span></wa-callout>',
                    media_type="text/html",
                    status_code=400,
                )

            # Generate QR code using OdkAppUser.createQRCode
            appuser_obj = OdkAppUser(
                odk_central.external_project_instance_url,
                odk_central.external_project_username,
                odk_central.external_project_password,
            )
            osm_username = (
                auth_user.username if hasattr(auth_user, "username") else "fieldtm_user"
            )
            qrcode = appuser_obj.createQRCode(
                odk_id=project.external_project_id,
                project_name=project.project_name,
                appuser_token=appuser_token,
                basemap="osm",
                osm_username=osm_username,
            )
            # Convert to base64 data URL
            qr_code_data_url = qrcode.png_data_uri(scale=5)

        elif project.field_mapping_app == FieldMappingApp.QFIELD:
            # For QField, generate QR code with qfield://cloud?project=ID
            if not project.external_project_id:
                return Response(
                    content='<wa-callout variant="danger"><span>QField project ID not found.</span></wa-callout>',
                    media_type="text/html",
                    status_code=400,
                )

            qfield_url = f"qfield://cloud?project={project.external_project_id}"
            qrcode = segno.make(qfield_url, micro=False)
            qr_code_data_url = qrcode.png_data_uri(scale=6)

        if not qr_code_data_url:
            return Response(
                content='<wa-callout variant="danger"><span>Failed to generate QR code.</span></wa-callout>',
                media_type="text/html",
                status_code=500,
            )

        app_name = (
            project.field_mapping_app.value
            if hasattr(project.field_mapping_app, "value")
            else str(project.field_mapping_app)
        )

        html_content = f"""
        <div style="text-align: center; padding: 20px; background-color: #f9f9f9; border-radius: 8px; margin-top: 20px;">
            <h3 style="color: #333; margin-bottom: 15px;">Scan QR Code to Access Project</h3>
            <p style="color: #666; margin-bottom: 20px;">Use {app_name} to scan this QR code and load the project</p>
            <div style="display: inline-block; padding: 15px; background-color: white; border-radius: 8px; margin-bottom: 15px;">
                <img src="{qr_code_data_url}" alt="Project QR Code" style="max-width: 300px; height: auto;" />
            </div>
            <div>
                <wa-button 
                    onclick="downloadQRCode('{qr_code_data_url}', '{project.project_name}_{app_name}_{project_id}')"
                    variant="default"
                >
                    Download QR Code
                </wa-button>
            </div>
        </div>
        <script>
            function downloadQRCode(dataUrl, filename) {{
                const link = document.createElement('a');
                link.href = dataUrl;
                link.download = filename + '.png';
                link.click();
            }}
        </script>
        """

        return Response(
            content=html_content,
            media_type="text/html",
            status_code=200,
        )

    except Exception as e:
        log.error(f"Error generating QR code via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=f'<wa-callout variant="danger"><span>Error: {error_msg}</span></wa-callout>',
            media_type="text/html",
            status_code=500,
        )


# TODO Luke replace the logic here with geojson-aoi-parser
@post(
    path="/validate-geojson",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
)
async def validate_geojson(
    request: HTMXRequest,
    db: AsyncConnection,
    auth_user: AuthUser,
    data: dict = Body(media_type=RequestEncodingType.JSON),
) -> Response:
    """Validate and normalize GeoJSON for project area upload.

    Accepts GeoJSON (Feature, FeatureCollection, or Geometry) and returns
    a normalized, optionally merged single polygon FeatureCollection suitable for use
    as a project area of interest (AOI).

    Args:
        data: Request body containing:
            - geojson: The GeoJSON to validate and normalize
            - merge_geometries: Optional boolean to merge geometries using convex hull
    """
    try:
        geojson_input = data.get("geojson")
        merge_geometries = data.get("merge_geometries", False)

        if not geojson_input:
            return Response(
                content=json.dumps({"error": "GeoJSON is required"}),
                media_type="application/json",
                status_code=400,
            )

        # Convert to FeatureCollection and normalize
        featcol = geojson_to_featcol(geojson_input)

        # Check if we have any features
        if not featcol.get("features", []):
            return Response(
                content=json.dumps({"error": "No valid geometries found in GeoJSON"}),
                media_type="application/json",
                status_code=422,
            )

        # Validate CRS
        await check_crs(featcol)

        # Keep only polygons (filter out points and linestrings)
        # For project AOI, we want polygons
        polygon_features = [
            f
            for f in featcol.get("features", [])
            if f.get("geometry", {}).get("type") in ("Polygon", "MultiPolygon")
        ]

        if not polygon_features:
            return Response(
                content=json.dumps(
                    {
                        "error": "No polygon geometries found. Project area must be a polygon."
                    }
                ),
                media_type="application/json",
                status_code=422,
            )

        # Create FeatureCollection with only polygons
        polygon_featcol = geojson.FeatureCollection(features=polygon_features)

        if merge_geometries:
            # TODO: Implement convex hull logic for multipolygons
            # When merge_geometries is True, use convex hull to merge any multipolygon
            # geometries into a single polygon. This should:
            # 1. Detect if there are MultiPolygon geometries
            # 2. Apply convex hull to create a single bounding polygon
            # 3. Merge all polygons (including single polygons) into one
            # For now, use the existing merge_polygons function
            merged_featcol = merge_polygons(
                polygon_featcol, merge=True, dissolve_polygon=False
            )
        else:
            # Don't merge, just return normalized polygons
            merged_featcol = polygon_featcol

        # Return normalized GeoJSON
        # If single feature, return it directly; otherwise return FeatureCollection
        result_geojson = (
            merged_featcol["features"][0]
            if len(merged_featcol.get("features", [])) == 1
            else merged_featcol
        )

        return Response(
            content=json.dumps({"geojson": result_geojson}),
            media_type="application/json",
            status_code=200,
        )

    except HTTPException as e:
        # Convert HTTP exceptions to JSON format
        return Response(
            content=json.dumps({"error": e.detail}),
            media_type="application/json",
            status_code=e.status_code,
        )
    except Exception as e:
        log.error(f"Error validating GeoJSON: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=json.dumps({"error": error_msg}),
            media_type="application/json",
            status_code=500,
        )


htmx_router = Router(
    path="/",
    tags=["htmx"],
    route_handlers=[
        # Icon routes first to avoid conflicts
        serve_favicon_ico,
        serve_favicon_png,
        serve_favicon_svg,
        serve_apple_touch_icon,
        serve_maskable_icon,
        serve_pwa_192,
        serve_pwa_512,
        serve_pwa_64,
        # Other routes
        home,
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
        project_qrcode_htmx,
        validate_geojson,
    ],
)
