"""Shared helpers (parse_extent, parse_bool, etc.)."""

import logging
from pathlib import Path
from typing import Any


def register_plugin_data_dirs(
    project, final_output_dir: Path, log: logging.Logger
) -> None:
    """Declare every top-level subdir as a QFieldSync data dir.

    libqfieldsync's ``OfflineConverter`` only recursively copies subdirs
    that the project file lists in ``QFieldSync/dataDirs`` (alongside
    ``attachmentDirs``).  Without this entry, QFieldCloud's packaging
    step strips everything except the ``.qgz``, the ``{basename}.qml``
    project plugin, and layer-attached files -- so bundled subdir trees
    like ``plugins/livefield/`` never reach the device, and QField's
    plugin loader errors with "file doesn't exist".
    """
    if not final_output_dir.is_dir():
        return

    subdirs = sorted(
        entry.name for entry in final_output_dir.iterdir() if entry.is_dir()
    )
    if not subdirs:
        return

    existing, _ok = project.readListEntry("QFieldSync", "dataDirs", [])
    merged = sorted({*existing, *subdirs})
    if merged == sorted(existing):
        return

    project.writeEntry("QFieldSync", "dataDirs", merged)
    log.info("Registered QFieldSync dataDirs for device packaging: %s", merged)


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
