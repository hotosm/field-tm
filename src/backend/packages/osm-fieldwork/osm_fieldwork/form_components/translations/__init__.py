"""Translations for XLSForm fields."""

import json
from pathlib import Path
import re
from typing import Optional

# Load translation JSON files as dictionaries
def _load_translations(file_name):
    path = Path(__file__).parent / file_name
    with path.open(encoding="utf-8") as f:
        return json.load(f)

INCLUDED_LANGUAGES = {
    "english": "en",
    "french": "fr",
    "spanish": "es",
    "italian": "it",
    "swahili": "sw",
    "nepali": "ne",
    "portuguese": "pt-BR",
    "czech": "cs",
    "japanese": "ja",
}

translations = {f"{key}({value})": _load_translations(f"{value}.json") for key, value in INCLUDED_LANGUAGES.items()}

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
    label_value = translations.get("english(en)", {}).get(field_name)
    if label_value:
        base["label"] = label_value
    return base


def _translation_key_for_column(col: str) -> str | None:
    """Resolve the translation table key for a label column."""
    match = re.match(r"label::([^(]+)(?:\(([^)]+)\))?", col)
    if not match:
        return None

    lang_key = match.group(1).strip().lower()
    lang_code = match.group(2) or INCLUDED_LANGUAGES.get(lang_key)
    return f"{lang_key}({lang_code})" if lang_code else lang_key


def _add_requested_label_columns(
    base: dict,
    field_name: str,
    label_cols: list[str],
) -> dict:
    """Populate only the explicitly requested translated label columns."""
    for col in label_cols:
        if not col.startswith("label::"):
            continue

        trans_key = _translation_key_for_column(col)
        if not trans_key:
            continue

        label_value = translations.get(trans_key, {}).get(field_name)
        if label_value:
            base[col] = label_value
    return base


def _add_all_label_columns(base: dict, field_name: str) -> dict:
    """Populate translated labels for every included language."""
    for lang_key, lang_dict in translations.items():
        label_value = lang_dict.get(field_name)
        if label_value:
            base[f"label::{lang_key}"] = label_value
    return base


def add_label_translations(base: dict, label_cols: Optional[list[str]] = None) -> dict:
    """Populate translated XLSForm labels for a field definition."""
    label_cols = label_cols or []
    field_name = _unwrap_field_name(base.get("name"))

    invalid_langs = _invalid_translation_languages(label_cols)

    if invalid_langs:
        raise ValueError(f"Invalid or unsupported translation(s): {', '.join(invalid_langs)}")

    if not isinstance(field_name, str):
        return base

    if "label" in label_cols:
        return _add_default_english_label(base, field_name)
    if label_cols:
        return _add_requested_label_columns(base, field_name, label_cols)
    return _add_all_label_columns(base, field_name)
