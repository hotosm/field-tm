"""Generate openapi.json via the command line."""

import argparse
import json
from pathlib import Path

from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env.example")

from app.main import api  # noqa: E402


def write_openapi(path: Path) -> None:
    """Get OpenAPI config from FastAPI and write to file."""
    if not path.match("*.json"):
        raise ValueError("Output file must be .json") from None
    with open(path, "w") as f:
        openapi = get_openapi(
            title=api.title,
            version=api.version,
            openapi_version=api.openapi_version,
            description=api.description,
            routes=api.routes,
            tags=api.openapi_tags,
            servers=api.servers,
            terms_of_service=api.terms_of_service,
            contact=api.contact,
            license_info=api.license_info,
        )
        json.dump(openapi, f, separators=(",", ":"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o", dest="output", default="./openapi.json", help="output file"
    )
    args = parser.parse_args()
    write_openapi(Path(args.output))
