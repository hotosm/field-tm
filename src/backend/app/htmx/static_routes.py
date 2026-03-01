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

"""Static asset HTMX routes (favicon, icons, images)."""

from pathlib import Path

from litestar import get
from litestar.response import Response


@get("/static/css/{filename:str}")
async def serve_static_css(filename: str) -> Response:
    """Serve static CSS files."""
    static_dir = Path(__file__).parent.parent / "static" / "css"
    file_path = static_dir / filename

    # Security: only allow .css and no path traversal
    if (
        not filename.endswith(".css")
        or ".." in filename
        or "/" in filename
        or "\\" in filename
    ):
        return Response(content="Forbidden", status_code=403)

    if not file_path.exists():
        return Response(content="Not Found", status_code=404)

    with open(file_path, "rb") as f:
        content = f.read()

    return Response(
        content=content,
        media_type="text/css",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@get("/static/images/{filename:str}")
async def serve_static_image(filename: str) -> Response:
    """Serve static image files."""
    allowed_media_types = {
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    static_dir = Path(__file__).parent.parent / "static" / "images"
    file_path = static_dir / filename
    suffix = Path(filename).suffix.lower()

    # Security: only allow known image extensions and ensure no path traversal
    if (
        suffix not in allowed_media_types
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
        media_type=allowed_media_types[suffix],
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
    elif not file_path.exists():
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
