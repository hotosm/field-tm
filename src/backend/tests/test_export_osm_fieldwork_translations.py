"""Tests for exporting gettext-backed osm-fieldwork translations."""

import gettext
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from babel.messages import pofile

LOCALE_DIR = Path(__file__).resolve().parents[1] / "app" / "locales"
OUTPUT_DIR = (
    Path(__file__).resolve().parents[1]
    / "packages"
    / "osm-fieldwork"
    / "osm_fieldwork"
    / "form_components"
    / "translations"
    / "locales"
)


def _find_repo_root() -> Path | None:
    """Walk up from this file to find the repo root (contains Justfile)."""
    path = Path(__file__).resolve().parent
    while path != path.parent:
        if (path / "Justfile").exists():
            return path
        path = path.parent
    return None


REPO_ROOT = _find_repo_root()
PO_TO_LOCALE_LANG = {
    "cs": "cs",
    "en": "en",
    "es": "es",
    "fr": "fr",
    "it": "it",
    "ja": "ja",
    "ne": "ne",
    "pt_br": "pt_br",
    "sw": "sw",
}


_requires_repo = pytest.mark.skipif(
    REPO_ROOT is None, reason="Repo root not found (running outside source tree)"
)


def run_export_command(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the osm-fieldwork export task with an isolated UV cache."""
    just_path = shutil.which("just")
    assert just_path is not None, (
        "Expected `just` to be installed for i18n export tests."
    )

    with tempfile.TemporaryDirectory() as uv_cache_dir:
        return subprocess.run(  # noqa: S603
            [just_path, "i18n", "export-osm-fieldwork", *args],
            cwd=REPO_ROOT,
            env={**os.environ, "UV_CACHE_DIR": uv_cache_dir},
            capture_output=True,
            text=True,
            check=False,
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


@_requires_repo
def test_committed_osm_fieldwork_mo_matches_compiled_catalogs() -> None:
    """Packaged osm-fieldwork .mo artifacts should match backend catalogs."""
    result = run_export_command("--check")
    assert result.returncode == 0, result.stdout + result.stderr


@_requires_repo
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
