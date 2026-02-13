"""Static asset HTMX routes."""

from app.htmx.setup_step_routes import (
    serve_apple_touch_icon,
    serve_favicon_ico,
    serve_favicon_png,
    serve_favicon_svg,
    serve_maskable_icon,
    serve_pwa_192,
    serve_pwa_512,
    serve_pwa_64,
    serve_static_image,
)  # noqa: F401

__all__ = [
    "serve_static_image",
    "serve_favicon_ico",
    "serve_favicon_png",
    "serve_favicon_svg",
    "serve_apple_touch_icon",
    "serve_maskable_icon",
    "serve_pwa_192",
    "serve_pwa_512",
    "serve_pwa_64",
]
