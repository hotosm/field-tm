"""Export bundled raw XLSForm templates to local disk."""

from __future__ import annotations

import argparse
from pathlib import Path

from osm_fieldwork.conversion_to_xlsform import convert_to_xlsform
from osm_fieldwork.xlsforms import xlsforms_path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "xlsforms"


def export_raw_xlsforms(output_dir: Path) -> list[Path]:
    """Write the raw bundled XLSForms to the given directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    exported_files: list[Path] = []
    for yaml_path in sorted(Path(xlsforms_path).glob("*.yaml")):
        xlsform_path = output_dir / f"{yaml_path.stem}.xlsx"
        xlsform_path.write_bytes(convert_to_xlsform(str(yaml_path)))
        exported_files.append(xlsform_path)

    return exported_files


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Export the bundled raw XLSForm templates used by Field-TM to disk."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=(
            "Directory to write the exported .xlsx files into. "
            f"Defaults to {DEFAULT_OUTPUT_DIR}."
        ),
    )
    return parser


def main() -> int:
    """Run the export command."""
    args = build_parser().parse_args()
    exported_files = export_raw_xlsforms(args.output_dir)

    print(f"Exported {len(exported_files)} XLSForms to {args.output_dir}")
    for path in exported_files:
        print(path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
