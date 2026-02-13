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

import geojson
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
from osm_fieldwork.xlsforms import xlsforms_path
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.auth.auth_deps import login_required
from app.auth.auth_schemas import AuthUser, ProjectUserDict
from app.auth.roles import mapper, project_manager
from app.central import central_crud
from app.central.central_routes import _validate_xlsform_extension
from app.central.central_schemas import ODKCentral
from app.db.database import db_conn
from app.db.enums import XLSFormType
from app.db.models import DbProject
from app.db.postgis_utils import (
    check_crs,
    featcol_keep_single_geom_type,
    geojson_to_featcol,
    merge_polygons,
)
from app.htmx.htmx_schemas import XLSFormUploadData
from app.projects import project_crud, project_schemas
from app.projects.project_schemas import ProjectUpdate
from app.projects.project_services import (
    ConflictError,
    ServiceError,
    create_project_stub,
    download_osm_data,
    finalize_odk_project,
    finalize_qfield_project,
    save_data_extract,
    save_task_areas,
    split_aoi,
)
from app.projects.project_services import (
    ValidationError as SvcValidationError,
)
from app.qfield.qfield_schemas import QFieldCloud

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
    import time

    # Generate unique map ID to avoid conflicts with previous maps
    unique_map_id = f"{map_id}-{int(time.time() * 1000)}"

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
    <div id="{unique_map_id}" style="height: {height}; width: 100%; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 15px;"></div>
    <script>
        (function() {{
            // Clean up any existing maps with the same base ID pattern
            const baseMapId = '{map_id}';
            const existingContainers = document.querySelectorAll('[id^="' + baseMapId + '-"]');
            existingContainers.forEach(function(container) {{
                if (container._leaflet_id && typeof L !== 'undefined') {{
                    try {{
                        const oldMap = L.Map.prototype.get(container._leaflet_id);
                        if (oldMap) {{
                            oldMap.remove();
                        }}
                    }} catch (e) {{
                        // Map already removed or doesn't exist
                    }}
                }}
            }});
            
            // Function to initialize the map
            function initMap() {{
                const mapContainer = document.getElementById('{unique_map_id}');
                if (!mapContainer) {{
                    setTimeout(initMap, 50);
                    return;
                }}
                
                // Check if Leaflet is loaded
                if (typeof L === 'undefined') {{
                    // Load Leaflet if not already loaded
                    if (!document.querySelector('link[href*="leaflet.css"]')) {{
                        const link = document.createElement('link');
                        link.rel = 'stylesheet';
                        link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
                        document.head.appendChild(link);
                    }}
                    if (!document.querySelector('script[src*="leaflet.js"]')) {{
                        const script = document.createElement('script');
                        script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
                        script.onload = function() {{
                            setTimeout(initMap, 100);
                        }};
                        document.head.appendChild(script);
                        return;
                    }}
                    setTimeout(initMap, 100);
                    return;
                }}
                
                // Check if container already has a map
                if (mapContainer._leaflet_id) {{
                    try {{
                        const existingMap = L.Map.prototype.get(mapContainer._leaflet_id);
                        if (existingMap) {{
                            existingMap.remove();
                        }}
                    }} catch (e) {{
                        // Ignore errors
                    }}
                }}
                
                // Small delay to ensure container is fully rendered
                setTimeout(function() {{
                    try {{
                        // Initialize Leaflet map
                        const map = L.map('{unique_map_id}').setView([0, 0], 2);
                        
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
                        
                        // Trigger resize to ensure map renders correctly
                        setTimeout(function() {{
                            map.invalidateSize();
                        }}, 100);
                    }} catch (error) {{
                        console.error('Error initializing Leaflet map:', error);
                    }}
                }}, 100);
            }}
            
            // Initialize map after HTMX swap
            if (document.getElementById('{unique_map_id}')) {{
                initMap();
            }} else {{
                // Wait for HTMX to swap content
                const initAfterSwap = function(event) {{
                    if (document.getElementById('{unique_map_id}')) {{
                        initMap();
                        document.body.removeEventListener('htmx:afterSwap', initAfterSwap);
                    }}
                }};
                document.body.addEventListener('htmx:afterSwap', initAfterSwap);
            }}
        }})();
    </script>
    """
    return map_html


@get(
    path="/",
    dependencies={"db": Provide(db_conn)},
)
async def landing(request: HTMXRequest, db: AsyncConnection) -> Template:
    """Render public landing page."""
    return HTMXTemplate(template_name="landing.html")


@get(
    path="/projects",
    dependencies={"db": Provide(db_conn)},
)
async def project_listing(request: HTMXRequest, db: AsyncConnection) -> Template:
    """Render public project listing page."""
    projects = await DbProject.all(db, limit=12) or []
    return HTMXTemplate(template_name="home.html", context={"projects": projects})


@get(
    path="/metrics",
    dependencies={"db": Provide(db_conn)},
)
async def metrics_partial(request: HTMXRequest, db: AsyncConnection) -> Template:
    """Render landing metrics partial."""
    project_count = await DbProject.count(db)
    return HTMXTemplate(
        template_name="partials/metrics.html",
        context={"project_count": project_count},
    )


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
        project_name = data.get("project_name", "").strip()
        description = data.get("description", "").strip()
        field_mapping_app = data.get("field_mapping_app", "").strip()
        hashtags_str = data.get("hashtags", "").strip()
        outline_str = data.get("outline", "").strip()

        if not outline_str:
            outline = {}
        else:
            try:
                outline = json.loads(outline_str)
            except json.JSONDecodeError:
                return Response(
                    content='<div id="form-error" style="margin-bottom: 16px; display: block;"><wa-callout variant="danger"><span id="form-error-message">Project area must be valid JSON (GeoJSON Polygon, MultiPolygon, Feature, or FeatureCollection).</span></wa-callout></div>',
                    media_type="text/html",
                    status_code=400,
                )

        hashtags = (
            [tag.strip() for tag in hashtags_str.split(",") if tag.strip()]
            if hashtags_str
            else []
        )

        project = await create_project_stub(
            db=db,
            project_name=project_name,
            field_mapping_app=field_mapping_app,
            description=description,
            outline=outline,
            hashtags=hashtags,
            user_sub=auth_user.sub,
        )
        await db.commit()

        return Response(
            content="",
            status_code=200,
            headers={"HX-Redirect": f"/htmxprojects/{project.id}"},
        )
    except SvcValidationError as e:
        message = e.message
        headers = {}
        if "Description is required" in message:
            headers.update(
                {
                    "HX-Retarget": "#description-error",
                    "HX-Reswap": "innerHTML",
                }
            )
        if "Area of Interest" in message:
            headers["HX-Trigger"] = json.dumps({"missingOutline": message})
        return Response(
            content=f'<div id="form-error" style="margin-bottom: 16px; display: block;"><wa-callout variant="danger"><span id="form-error-message">{message}</span></wa-callout></div>',
            media_type="text/html",
            status_code=400,
            headers=headers,
        )
    except ConflictError as e:
        return Response(
            content=f'<div id="form-error" style="margin-bottom: 16px; display: block;"><wa-callout variant="danger"><span id="form-error-message">{e.message}</span></wa-callout></div>',
            media_type="text/html",
            status_code=status.HTTP_409_CONFLICT,
            headers={"HX-Trigger": json.dumps({"duplicateProjectName": e.message})},
        )
    except ServiceError as e:
        return Response(
            content=f'<div id="form-error" style="margin-bottom: 16px; display: block;"><wa-callout variant="danger"><span id="form-error-message">{e.message}</span></wa-callout></div>',
            media_type="text/html",
            status_code=400,
        )
    except Exception as e:
        log.error(f"Error creating project via HTMX: {e}", exc_info=True)
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
        featcol_single_geom_type = await download_osm_data(
            db=db,
            project_id=project_id,
            osm_category=osm_category,
            geom_type=geom_type,
            centroid=centroid,
        )
        feature_count = len(featcol_single_geom_type.get("features", []))

        # Encode GeoJSON for the Accept button (don't save yet)
        geojson_str = json.dumps(featcol_single_geom_type).replace('"', "&quot;")

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

        # Return success message with embedded map preview and Accept button
        return Response(
            content=f"""<wa-callout variant="success"><span>✓ OSM data downloaded successfully! Found {feature_count} features.</span></wa-callout>
            <div id="geojson-preview-container" style="margin-top: 15px;">
                <div style="margin-bottom: 10px;">
                    <wa-callout variant="info">
                        <span>Previewing {feature_count} features on map. Review the data below. If satisfied, click "Accept Data Extract" to save. Otherwise, try downloading again with different parameters.</span>
                    </wa-callout>
                </div>
                {map_html_content}
                <form id="accept-data-extract-form" style="margin-top: 15px; display: flex; gap: 10px;">
                    <input type="hidden" name="data_extract_geojson" value='{geojson_str}' />
                    <button 
                        id="accept-data-extract-btn"
                        type="submit"
                        hx-post="/accept-data-extract-htmx?project_id={project_id}"
                        hx-target="#osm-data-status"
                        hx-swap="innerHTML"
                        hx-include="#accept-data-extract-form"
                        class="wa-button wa-button--primary"
                        style="flex: 1;"
                    >
                        Accept Data Extract
                    </button>
                </form>
            </div>""",
            media_type="text/html",
            status_code=200,
        )

    except SvcValidationError as e:
        return Response(
            content=f'<wa-callout variant="danger"><span>{e.message}</span></wa-callout>',
            media_type="text/html",
            status_code=400,
        )
    except ServiceError as e:
        return Response(
            content=f'<wa-callout variant="danger"><span>{e.message}</span></wa-callout>',
            media_type="text/html",
            status_code=500,
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

        feature_count = len(featcol_single_geom_type.get("features", []))

        # Encode GeoJSON for the Accept button (don't save yet)
        geojson_str = json.dumps(featcol_single_geom_type).replace('"', "&quot;")

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
                        <span>Previewing {feature_count} features on map. Review the data below. If satisfied, click "Accept Data Extract" to save. Otherwise, try uploading a different file.</span>
                    </wa-callout>
                </div>
                {map_html_content}
                <form id="accept-data-extract-form" style="margin-top: 15px; display: flex; gap: 10px;">
                    <input type="hidden" name="data_extract_geojson" value='{geojson_str}' />
                    <button 
                        id="accept-data-extract-btn"
                        type="submit"
                        hx-post="/accept-data-extract-htmx?project_id={project_id}"
                        hx-target="#osm-data-status"
                        hx-swap="innerHTML"
                        hx-include="#accept-data-extract-form"
                        class="wa-button wa-button--primary"
                        style="flex: 1;"
                    >
                        Accept Data Extract
                    </button>
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

        # Prepare layers for map
        geojson_layers = []

        # Add AOI outline layer (always show)
        if project.outline:
            aoi_featcol = {
                "type": "FeatureCollection",
                "features": [
                    {"type": "Feature", "geometry": project.outline, "properties": {}}
                ],
            }
            geojson_layers.append(
                {
                    "data": aoi_featcol,
                    "name": "Project AOI",
                    "color": "#d63f3f",
                    "weight": 2,
                    "opacity": 0.8,
                    "fillOpacity": 0.1,
                }
            )

        # Add data extract layer
        geojson_layers.append(
            {
                "data": geojson_data,
                "name": f"Data Extract ({feature_count} features)",
                "color": "#3388ff",
                "weight": 2,
                "opacity": 0.8,
                "fillOpacity": 0.3,
            }
        )

        # Use reusable map rendering function
        map_html_content = render_leaflet_map(
            map_id="leaflet-map-preview",
            geojson_layers=geojson_layers,
            height="500px",
            show_controls=True,
        )

        # Return HTML with Leaflet map
        map_html = f"""
        <div style="margin-top: 15px;">
            <div style="margin-bottom: 10px;">
                <wa-callout variant="info">
                    <span>Previewing {feature_count} data features on map. Review the data, then continue to the next step.</span>
                </wa-callout>
            </div>
            {map_html_content}
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
    """Save GeoJSON data extract to database (Step 2).

    Entity list creation is deferred to the final project creation step.
    This endpoint only saves the geometry data to the database.
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

        # Get project for validation
        project = await DbProject.one(db, project_id)

        # Validate that we have features
        features = geojson_data.get("features", [])
        if not features:
            return Response(
                content='<wa-callout variant="warning"><span>GeoJSON data contains no features.</span></wa-callout>',
                media_type="text/html",
                status_code=400,
            )

        # Save GeoJSON to database (entity list creation deferred to final step)
        await DbProject.update(
            db,
            project_id,
            project_schemas.ProjectUpdate(data_extract_geojson=geojson_data),
        )
        await db.commit()
        log.info(
            f"Saved data extract to database for project {project_id} (entity list creation deferred to final step)"
        )

        return Response(
            content='<wa-callout variant="success"><span>✓ Data extract successfully saved! You can now proceed to Step 3 (upload XLSForm) and then Step 4 (split tasks).</span></wa-callout><script>setTimeout(() => window.location.reload(), 2000);</script>',
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
        is_no_splitting = False

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

        # Check if NO_SPLITTING was selected (empty dict or empty features)
        if (
            not task_boundaries
            or not task_boundaries.get("features")
            or len(task_boundaries.get("features", [])) == 0
        ):
            # Check if task_areas_geojson is explicitly set to {} (NO_SPLITTING)
            if project.task_areas_geojson == {}:
                is_no_splitting = True
            else:
                # No splitting has been done yet
                return Response(
                    content='<wa-callout variant="warning"><span>No task boundaries found. Please split the project into tasks first using the "Split AOI" button above.</span></wa-callout>',
                    media_type="text/html",
                    status_code=200,  # Return 200 instead of 404 to show message
                )

        # Prepare layers for map
        geojson_layers = []

        # Add AOI outline layer (always show)
        if project.outline:
            aoi_featcol = {
                "type": "FeatureCollection",
                "features": [
                    {"type": "Feature", "geometry": project.outline, "properties": {}}
                ],
            }
            geojson_layers.append(
                {
                    "data": aoi_featcol,
                    "name": "Project AOI",
                    "color": "#d63f3f",
                    "weight": 2,
                    "opacity": 0.8,
                    "fillOpacity": 0.1,
                }
            )

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

        # Add task boundaries layer (only if splitting was done)
        if not is_no_splitting and task_boundaries and task_boundaries.get("features"):
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

        # Generate preview message
        if is_no_splitting:
            preview_message = f"Previewing whole AOI (no splitting) with {data_feature_count} data features. The entire AOI will be used as a single task."
        else:
            task_count = len(task_boundaries.get("features", []))
            preview_message = f"Previewing {task_count} task boundaries and {data_feature_count} data features together."

        return Response(
            content=f"""
            <div style="margin-top: 15px;">
                <div style="margin-bottom: 10px;">
                    <wa-callout variant="info">
                        <span>{preview_message}</span>
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
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
    project_id: int = Parameter(),
) -> Response:
    """Split AOI into tasks using selected algorithm and return preview map."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content='<wa-callout variant="danger"><span>Project not found or access denied.</span></wa-callout>',
            media_type="text/html",
            status_code=404,
        )

    try:
        # Extract form data
        log.debug(
            f"Split AOI request data keys: {list(data.keys()) if data else 'None'}"
        )
        algorithm = data.get("algorithm", "").strip() if data else ""

        try:
            no_of_buildings = int(data.get("no_of_buildings", 50)) if data else 50
        except (ValueError, TypeError):
            no_of_buildings = 50

        try:
            dimension_meters = int(data.get("dimension_meters", 100)) if data else 100
        except (ValueError, TypeError):
            dimension_meters = 100

        log.debug(
            f"Split AOI parameters: algorithm={algorithm}, no_of_buildings={no_of_buildings}, dimension_meters={dimension_meters}"
        )

        if not algorithm or algorithm == "":
            return Response(
                content='<wa-callout variant="danger"><span>Please select a splitting option.</span></wa-callout>',
                media_type="text/html",
                status_code=400,
            )

        tasks_featcol = await split_aoi(
            db=db,
            project_id=project_id,
            algorithm=algorithm,
            no_of_buildings=no_of_buildings,
            dimension_meters=dimension_meters,
        )

        if tasks_featcol == {}:
            return Response(
                content='<wa-callout variant="success"><span>✓ Task splitting is not required for this project setup.</span></wa-callout>',
                media_type="text/html",
                status_code=200,
                headers={"HX-Refresh": "true"},
            )

        task_count = len(tasks_featcol.get("features", []))

        # Store preview in a temporary location (we'll save it when user accepts)
        # For now, we'll encode it in the response and save it when Accept is clicked

        # Get project outline and data extract for map preview
        project = await DbProject.one(db, project_id)
        data_extract = project.data_extract_geojson

        # Prepare layers for map
        geojson_layers = []

        # Add AOI outline layer
        if project.outline:
            aoi_featcol = {
                "type": "FeatureCollection",
                "features": [
                    {"type": "Feature", "geometry": project.outline, "properties": {}}
                ],
            }
            geojson_layers.append(
                {
                    "data": aoi_featcol,
                    "name": "Project AOI",
                    "color": "#d63f3f",
                    "weight": 2,
                    "opacity": 0.8,
                    "fillOpacity": 0.1,
                }
            )

        # Add data extract layer if available
        if data_extract:
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

        # Encode the task areas GeoJSON for the Accept button
        tasks_geojson_str = json.dumps(tasks_featcol).replace('"', "&quot;")

        # Return success message with preview and Accept button
        data_extract_info = ""
        if data_extract:
            data_feature_count = len(data_extract.get("features", []))
            data_extract_info = f" and {data_feature_count} data features"

        return Response(
            content=f"""
            <wa-callout variant="success">
                <span>✓ AOI split successfully! Generated {task_count} task areas using {algorithm.replace("_", " ").title()}.</span>
            </wa-callout>
            <div style="margin-top: 20px;">
                <div style="margin-bottom: 10px;">
                    <wa-callout variant="info">
                        <span>Previewing {task_count} task boundaries{data_extract_info}. Review the results below. If satisfied, click "Accept Task Choices" to save. Otherwise, adjust parameters above and click "Split Again" to regenerate.</span>
                    </wa-callout>
                </div>
                {map_html_content}
                <form id="accept-split-form" style="margin-top: 20px; display: flex; gap: 10px; justify-content: center;">
                    <input type="hidden" name="tasks_geojson" value='{tasks_geojson_str}' />
                    <button 
                        id="accept-split-btn"
                        type="submit"
                        hx-post="/accept-split-htmx?project_id={project_id}"
                        hx-target="#split-status"
                        hx-swap="innerHTML"
                        hx-include="#accept-split-form"
                        class="wa-button wa-button--primary"
                        style="min-width: 200px"
                    >
                        Accept Task Choices
                    </button>
                </form>
            </div>
            """,
            media_type="text/html",
            status_code=200,
        )

    except SvcValidationError as e:
        return Response(
            content=f'<wa-callout variant="danger"><span>{e.message}</span></wa-callout>',
            media_type="text/html",
            status_code=400,
        )
    except ServiceError as e:
        return Response(
            content=f'<wa-callout variant="danger"><span>{e.message}</span></wa-callout>',
            media_type="text/html",
            status_code=500,
        )
    except Exception as e:
        log.error(f"Error splitting AOI via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=f'<wa-callout variant="danger"><span>Error: {error_msg}</span></wa-callout>',
            media_type="text/html",
            status_code=500,
        )


@post(
    path="/accept-data-extract-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def accept_data_extract_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
    project_id: int = Parameter(),
) -> Response:
    """Accept and save the data extract to the database."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content='<wa-callout variant="danger"><span>Project not found or access denied.</span></wa-callout>',
            media_type="text/html",
            status_code=404,
        )

    try:
        geojson_str = data.get("data_extract_geojson", "")
        if not geojson_str:
            log.debug(
                f"Accept data extract data keys: {list(data.keys()) if data else 'None'}"
            )
            return Response(
                content='<wa-callout variant="danger"><span>No data extract provided.</span></wa-callout>',
                media_type="text/html",
                status_code=400,
            )

        # Parse the GeoJSON
        try:
            geojson_data = json.loads(geojson_str)
        except (json.JSONDecodeError, TypeError) as e:
            log.error(
                f"Error parsing data extract GeoJSON: {e}, type: {type(geojson_str)}, value: {geojson_str[:100] if isinstance(geojson_str, str) else geojson_str}"
            )
            return Response(
                content='<wa-callout variant="danger"><span>Invalid data extract format.</span></wa-callout>',
                media_type="text/html",
                status_code=400,
            )

        feature_count = await save_data_extract(
            db=db,
            project_id=project_id,
            geojson_data=geojson_data,
        )
        log.info(
            f"Accepted and saved data extract with {feature_count} features for project {project_id}"
        )

        return Response(
            content=f'<wa-callout variant="success"><span>✓ Data extract accepted! Saved {feature_count} features. Step 2 is now complete.</span></wa-callout>',
            media_type="text/html",
            status_code=200,
            headers={"HX-Refresh": "true"},
        )

    except SvcValidationError as e:
        return Response(
            content=f'<wa-callout variant="danger"><span>{e.message}</span></wa-callout>',
            media_type="text/html",
            status_code=400,
        )
    except ServiceError as e:
        return Response(
            content=f'<wa-callout variant="danger"><span>{e.message}</span></wa-callout>',
            media_type="text/html",
            status_code=500,
        )
    except Exception as e:
        log.error(f"Error accepting data extract via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=f'<wa-callout variant="danger"><span>Error: {error_msg}</span></wa-callout>',
            media_type="text/html",
            status_code=500,
        )


@post(
    path="/accept-split-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def accept_split_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
    project_id: int = Parameter(),
) -> Response:
    """Accept and save the task split results to the database."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content='<wa-callout variant="danger"><span>Project not found or access denied.</span></wa-callout>',
            media_type="text/html",
            status_code=404,
        )

    try:
        # Get task areas GeoJSON from form data (hx-vals sends it as form data)
        tasks_geojson_str = data.get("tasks_geojson", "")
        if not tasks_geojson_str:
            log.debug(
                f"Accept split data keys: {list(data.keys()) if data else 'None'}"
            )
            return Response(
                content='<wa-callout variant="danger"><span>No task areas data provided.</span></wa-callout>',
                media_type="text/html",
                status_code=400,
            )

        # Parse the GeoJSON
        try:
            tasks_geojson = json.loads(tasks_geojson_str)
        except (json.JSONDecodeError, TypeError) as e:
            log.error(
                f"Error parsing task areas GeoJSON: {e}, type: {type(tasks_geojson_str)}, value: {tasks_geojson_str[:100] if isinstance(tasks_geojson_str, str) else tasks_geojson_str}"
            )
            return Response(
                content='<wa-callout variant="danger"><span>Invalid task areas data format.</span></wa-callout>',
                media_type="text/html",
                status_code=400,
            )

        task_count = await save_task_areas(
            db=db,
            project_id=project_id,
            tasks_geojson=tasks_geojson,
        )
        is_empty_task_areas = tasks_geojson == {}

        log.info(
            f"Accepted and saved task areas for project {project_id} (empty: {is_empty_task_areas}, count: {task_count})"
        )

        if is_empty_task_areas:
            success_message = '<wa-callout variant="success"><span>✓ Split tasks saved successfully</span></wa-callout>'
        else:
            success_message = '<wa-callout variant="success"><span>✓ Split tasks saved successfully</span></wa-callout>'

        return Response(
            content=success_message,
            media_type="text/html",
            status_code=200,
            headers={"HX-Refresh": "true"},
        )

    except SvcValidationError as e:
        return Response(
            content=f'<wa-callout variant="danger"><span>{e.message}</span></wa-callout>',
            media_type="text/html",
            status_code=400,
        )
    except ServiceError as e:
        return Response(
            content=f'<wa-callout variant="danger"><span>{e.message}</span></wa-callout>',
            media_type="text/html",
            status_code=500,
        )
    except Exception as e:
        log.error(f"Error accepting split via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=f'<wa-callout variant="danger"><span>Error: {error_msg}</span></wa-callout>',
            media_type="text/html",
            status_code=500,
        )


@post(
    path="/create-project-odk-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def create_project_odk_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    project_id: int = Parameter(),
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    """Final step: Create project in ODK Central with all data (entity lists, forms, task boundaries)."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content='<wa-callout variant="danger"><span>Project not found or access denied.</span></wa-callout>',
            media_type="text/html",
            status_code=404,
        )

    try:
        custom_odk_creds = None
        external_url = data.get("external_project_instance_url", "").strip()
        external_username = data.get("external_project_username", "").strip()
        external_password = data.get("external_project_password", "").strip()

        any_custom = any([external_url, external_username, external_password])
        all_custom = all([external_url, external_username, external_password])

        if any_custom and not all_custom:
            return Response(
                content=(
                    '<wa-callout variant="warning"><span>'
                    "Provide ODK URL, username, and password (all 3), or leave them all blank to use server defaults."
                    "</span></wa-callout>"
                ),
                media_type="text/html",
                status_code=400,
            )

        if all_custom:
            custom_odk_creds = ODKCentral(
                external_project_instance_url=external_url,
                external_project_username=external_username,
                external_project_password=external_password,
            )

        odk_url = await finalize_odk_project(
            db=db, project_id=project_id, custom_odk_creds=custom_odk_creds
        )

        return Response(
            content=f'<wa-callout variant="success"><span>✓ Project successfully created in ODK Central! <a href="{odk_url}" target="_blank">View Project in ODK</a></span></wa-callout>',
            media_type="text/html",
            status_code=200,
            headers={"HX-Refresh": "true"},
        )
    except SvcValidationError as e:
        return Response(
            content=f'<wa-callout variant="danger"><span>{e.message}</span></wa-callout>',
            media_type="text/html",
            status_code=400,
        )
    except ServiceError as e:
        return Response(
            content=f'<wa-callout variant="danger"><span>{e.message}</span></wa-callout>',
            media_type="text/html",
            status_code=500,
        )
    except Exception as e:
        log.error(f"Error creating ODK project via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=f'<wa-callout variant="danger"><span>Error: {error_msg}</span></wa-callout>',
            media_type="text/html",
            status_code=500,
        )


@post(
    path="/create-project-qfield-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def create_project_qfield_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    project_id: int = Parameter(),
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    """Final step: Create project in QField with all data."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content='<wa-callout variant="danger"><span>Project not found or access denied.</span></wa-callout>',
            media_type="text/html",
            status_code=404,
        )

    try:
        custom_qfield_creds = None
        qfield_url_param = data.get("qfield_cloud_url", "").strip()
        qfield_user = data.get("qfield_cloud_user", "").strip()
        qfield_password = data.get("qfield_cloud_password", "").strip()

        if qfield_url_param and qfield_user and qfield_password:
            custom_qfield_creds = QFieldCloud(
                qfield_cloud_url=qfield_url_param,
                qfield_cloud_user=qfield_user,
                qfield_cloud_password=qfield_password,
            )
        qfield_url = await finalize_qfield_project(
            db=db, project_id=project_id, custom_qfield_creds=custom_qfield_creds
        )

        return Response(
            content=f'<wa-callout variant="success"><span>✓ Project successfully created in QField! <a href="{qfield_url}" target="_blank">View Project in QField</a></span></wa-callout>',
            media_type="text/html",
            status_code=200,
            headers={"HX-Refresh": "true"},
        )
    except SvcValidationError as e:
        return Response(
            content=f'<wa-callout variant="danger"><span>{e.message}</span></wa-callout>',
            media_type="text/html",
            status_code=400,
        )
    except ServiceError as e:
        return Response(
            content=f'<wa-callout variant="danger"><span>{e.message}</span></wa-callout>',
            media_type="text/html",
            status_code=500,
        )
    except Exception as e:
        log.error(f"Error creating QField project via HTMX: {e}", exc_info=True)
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
    },
)
async def project_qrcode_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    project_id: int = Parameter(),
    username: str = Parameter(default="fieldtm_user"),
) -> Response:
    """Generate and return QR code for a published project."""
    try:
        project = await DbProject.one(db, project_id)
    except KeyError:
        return Response(
            content='<wa-callout variant="danger"><span>Project not found.</span></wa-callout>',
            media_type="text/html",
            status_code=404,
        )

    try:
        # Use CRUD function to generate QR code
        qr_code_data_url = await project_crud.get_project_qrcode(
            db, project_id, username
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

    except HTTPException as e:
        error_msg = str(e.detail) if hasattr(e, "detail") else str(e)
        return Response(
            content=f'<wa-callout variant="danger"><span>Error: {error_msg}</span></wa-callout>',
            media_type="text/html",
            status_code=e.status_code,
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
        project_qrcode_htmx,
        validate_geojson,
        accept_data_extract_htmx,
        create_project_odk_htmx,
    ],
)
