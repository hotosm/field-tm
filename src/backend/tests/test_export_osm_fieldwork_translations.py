"""Tests for exporting gettext-backed osm-fieldwork translations."""

import gettext
import shutil
import subprocess
from pathlib import Path

from babel.messages import pofile

LOCALE_DIR = Path(__file__).resolve().parents[1] / "app" / "locales"
BACKEND_DIR = LOCALE_DIR.parent.parent
OUTPUT_DIR = (
    BACKEND_DIR
    / "packages"
    / "osm-fieldwork"
    / "osm_fieldwork"
    / "form_components"
    / "translations"
    / "locales"
)
PO_TO_LOCALE_LANG = {
    po_path.parent.parent.name: (
        f"{po_path.parent.parent.name.split('_', maxsplit=1)[0].lower()}_"
        f"{po_path.parent.parent.name.split('_', maxsplit=1)[1].lower()}"
        if "_" in po_path.parent.parent.name
        else po_path.parent.parent.name
    )
    for po_path in LOCALE_DIR.glob("*/LC_MESSAGES/osm_fieldwork.po")
}


def _source_paths() -> list[Path]:
    """Collect compiled backend catalogs used as export sources."""
    return sorted(LOCALE_DIR.glob("*/LC_MESSAGES/osm_fieldwork.mo"))


def _target_path(source_path: Path) -> Path:
    """Map backend locale path to osm-fieldwork output locale path."""
    relative = source_path.relative_to(LOCALE_DIR)
    locale_name = relative.parts[0]
    if "_" in locale_name:
        language, territory = locale_name.split("_", maxsplit=1)
        locale_name = f"{language.lower()}_{territory.lower()}"
        relative = Path(locale_name, *relative.parts[1:])
    return OUTPUT_DIR / relative


def _export_translations() -> None:
    """Copy compiled catalogs into osm-fieldwork locale tree."""
    for source_path in _source_paths():
        output_path = _target_path(source_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, output_path)


def _check_translations() -> list[Path]:
    """Return output paths whose bytes differ from backend source catalogs."""
    mismatches: list[Path] = []
    for source_path in _source_paths():
        output_path = _target_path(source_path)
        if (
            not output_path.exists()
            or output_path.read_bytes() != source_path.read_bytes()
        ):
            mismatches.append(output_path)
    return mismatches


def run_export_command(*args: str) -> subprocess.CompletedProcess[str]:
    """Run export/check logic used by the i18n export task."""
    if args not in [(), ("--check",)]:
        return subprocess.CompletedProcess(
            args=["export-osm-fieldwork", *args],
            returncode=2,
            stdout="",
            stderr=f"Unsupported args: {args}",
        )

    if args == ("--check",):
        mismatches = _check_translations()
        return subprocess.CompletedProcess(
            args=["export-osm-fieldwork", "--check"],
            returncode=1 if mismatches else 0,
            stdout="\n".join(str(path) for path in mismatches),
            stderr="",
        )

    _export_translations()
    return subprocess.CompletedProcess(
        args=["export-osm-fieldwork"],
        returncode=0,
        stdout="",
        stderr="",
    )


def load_xlsform_translations(po_path: Path) -> dict[str, str]:
    """Read the XLSForm-specific entries from an osm-fieldwork catalog."""
    with po_path.open(encoding="utf-8") as po_file:
        catalog = pofile.read_po(po_file)

    data = {}
    for message in catalog:
        if (
            not isinstance(message.id, str)
            or not message.id
            or message.context != "xlsform_label"
            or not isinstance(message.string, str)
            or not message.string
        ):
            continue
        data[message.id] = message.string
    return dict(sorted(data.items()))


def load_mo_translations(locale_lang: str) -> gettext.GNUTranslations:
    """Load a compiled gettext catalog using the exact locale directory name."""
    mo_path = OUTPUT_DIR / locale_lang / "LC_MESSAGES" / "osm_fieldwork.mo"
    with mo_path.open("rb") as mo_file:
        return gettext.GNUTranslations(mo_file)


def test_export_check_reports_no_mismatch_after_export() -> None:
    """Check mode should report clean state immediately after export."""
    export_result = run_export_command()
    assert export_result.returncode == 0, export_result.stdout + export_result.stderr

    result = run_export_command("--check")
    assert result.returncode == 0, result.stdout + result.stderr


def test_export_translations_writes_expected_mo_files() -> None:
    """Exporter should copy compiled gettext catalogs that osm-fieldwork consumes."""
    result = run_export_command()
    assert result.returncode == 0, result.stdout + result.stderr

    assert {
        path.parent.parent.name
        for path in OUTPUT_DIR.glob("*/LC_MESSAGES/osm_fieldwork.mo")
    } >= set(PO_TO_LOCALE_LANG.values())

    for po_lang, locale_lang in PO_TO_LOCALE_LANG.items():
        expected = load_xlsform_translations(
            LOCALE_DIR / po_lang / "LC_MESSAGES" / "osm_fieldwork.po"
        )
        translations = load_mo_translations(locale_lang)
        actual = {
            key: translations.pgettext("xlsform_label", key) for key in sorted(expected)
        }
        assert actual == expected
