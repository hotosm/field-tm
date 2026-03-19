"""gettext-backed translations for XLSForm field labels."""

import gettext
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

DOMAIN = "osm_fieldwork"
LOCALE_DIR = Path(__file__).parent / "locales"
DEFAULT_LANGUAGE_CODE = "en"

INCLUDED_LANGUAGES = {
    "english": "en",
    "french": "fr",
    "spanish": "es",
    "italian": "it",
    "swahili": "sw",
    "nepali": "ne",
    "portuguese": "pt_br",
    "czech": "cs",
    "japanese": "ja",
}


def _normalize_language_code(language_code: str) -> str:
    normalized = language_code.replace("-", "_")
    if "_" not in normalized:
        return normalized.lower()
    language, territory = normalized.split("_", maxsplit=1)
    return f"{language.lower()}_{territory.upper()}"


@lru_cache(maxsize=None)
def _get_translations(language_code: str) -> gettext.NullTranslations:
    return gettext.translation(
        DOMAIN,
        localedir=str(LOCALE_DIR),
        languages=[_normalize_language_code(language_code)],
        fallback=True,
    )


def _translate_label(field_name: str, language_code: str) -> str | None:
    translation = _get_translations(language_code).pgettext("xlsform_label", field_name)
    if translation != field_name:
        return translation

    if language_code == DEFAULT_LANGUAGE_CODE:
        return None

    fallback_translation = _get_translations(DEFAULT_LANGUAGE_CODE).pgettext(
        "xlsform_label",
        field_name,
    )
    return fallback_translation if fallback_translation != field_name else None


def _invalid_translation_languages(label_cols: list[str]) -> list[str]:
    """Return unsupported language names declared in label columns."""
    invalid_langs = []
    for col in label_cols:
        if not col.startswith("label::"):
            continue
        match = re.match(r"label::([^(]+)", col)
        if not match:
            continue
        lang_name = match.group(1).strip().lower()
        if lang_name not in INCLUDED_LANGUAGES:
            invalid_langs.append(lang_name)
    return invalid_langs


def _unwrap_field_name(field_name):
    """Normalize a row-style list value to a single field name string."""
    if isinstance(field_name, list):
        if len(field_name) == 1:
            return field_name[0]
        return None
    return field_name


def _add_default_english_label(base: dict, field_name: str) -> dict:
    """Populate the plain `label` column from the English translation table."""
    label_value = _translate_label(field_name, DEFAULT_LANGUAGE_CODE)
    if label_value:
        base["label"] = label_value
    return base


def _translation_key_for_column(col: str) -> tuple[str, str] | None:
    """Resolve the language key and code for a label column."""
    match = re.match(r"label::([^(]+)(?:\(([^)]+)\))?", col)
    if not match:
        return None

    lang_key = match.group(1).strip().lower()
    lang_code = match.group(2) or INCLUDED_LANGUAGES.get(lang_key)
    return (lang_key, lang_code) if lang_code else None


def _add_requested_label_columns(
    base: dict,
    field_name: str,
    label_cols: list[str],
) -> dict:
    """Populate only the explicitly requested translated label columns."""
    for col in label_cols:
        if not col.startswith("label::"):
            continue

        translation_spec = _translation_key_for_column(col)
        if not translation_spec:
            continue

        _, lang_code = translation_spec
        label_value = _translate_label(field_name, lang_code)
        if label_value:
            base[col] = label_value
    return base


def _add_all_label_columns(base: dict, field_name: str) -> dict:
    """Populate translated labels for every included language."""
    for lang_key, lang_code in INCLUDED_LANGUAGES.items():
        label_value = _translate_label(field_name, lang_code)
        if label_value:
            base[f"label::{lang_key}({lang_code})"] = label_value
    return base


def add_label_translations(base: dict, label_cols: Optional[list[str]] = None) -> dict:
    """Populate translated XLSForm labels for a field definition."""
    label_cols = label_cols or []
    field_name = _unwrap_field_name(base.get("name"))

    invalid_langs = _invalid_translation_languages(label_cols)

    if invalid_langs:
        raise ValueError(
            f"Invalid or unsupported translation(s): {', '.join(invalid_langs)}"
        )

    if not isinstance(field_name, str):
        return base

    if "label" in label_cols:
        return _add_default_english_label(base, field_name)
    if label_cols:
        return _add_requested_label_columns(base, field_name, label_cols)
    return _add_all_label_columns(base, field_name)
