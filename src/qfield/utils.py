"""Shared helpers (parse_extent, parse_bool, etc.)."""

from pathlib import Path
from typing import Any


def parse_and_validate_extent(extent_str: str) -> list[float]:
    """Parse and validate extent string."""
    try:
        values = [float(x.strip()) for x in extent_str.split(",")]
        if len(values) != 4:
            raise ValueError("Extent must have exactly 4 values: xmin,ymin,xmax,ymax")
        return values
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid extent format: {e}")


def parse_bool(value: Any, default: bool = True) -> bool:
    """Parse a JSON-ish boolean with a safe default."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    if value is None:
        return default
    return bool(value)


def set_project_file_permissions(project_path: str | Path) -> None:
    """Set permissive 777 permissions for upstream file access."""
    project_path = Path(project_path)
    for file_path in project_path.iterdir():
        file_path.chmod(0o777)
    for file_path in (project_path / "final").iterdir():
        file_path.chmod(0o777)
