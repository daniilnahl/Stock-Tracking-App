"""Explicit packaged dashboard resources; construction performs no asset IO."""

from pathlib import Path

from starlette.responses import Response


# Deliberately no directory mount, discovered manifest, caller path or fallback.
# Keep packaging and installed-wheel tests in sync when approved assets change.
ASSETS = {
    "/": ("index.html", "text/html"),
    "/dashboard-assets/hosting.css": ("hosting.css", "text/css"),
    "/dashboard-assets/hosting.js": ("hosting.js", "text/javascript"),
    "/dashboard-assets/stock-pixel.ttf": ("stock-pixel.ttf", "font/ttf"),
    "/dashboard-assets/LICENSE.txt": ("LICENSE.txt", "text/plain"),
}


def resource_bytes(name):
    """Read only an internal allowlist value, lazily after request rejection."""
    return Path(__file__).with_name("dashboard_assets").joinpath(name).read_bytes()


def register_dashboard(app):
    def handler(name, media_type):
        async def asset():
            return Response(resource_bytes(name), media_type=media_type)
        return asset

    for route, (name, media_type) in ASSETS.items():
        app.add_api_route(route, handler(name, media_type), methods=["GET"],
                          include_in_schema=False)
