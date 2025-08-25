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
}

translations = {f"{key}({value})": _load_translations(f"{value}.json") for key, value in INCLUDED_LANGUAGES.items()}

def add_label_translations(base: dict, label_cols: Optional[list[str]] = []) -> dict:
    field_name = base.get("name")

    # If name is a list (from a DataFrame row-style dict), unwrap it
    if isinstance(field_name, list):
        if len(field_name) == 1:
            field_name = field_name[0]
        else:
            return base  # Can't handle multi-name entries

    if not isinstance(field_name, str):
        return base

    if "label" in label_cols:
        lang_dict = translations.get("english(en)", {})
        label_value = lang_dict.get(field_name)
        if label_value:
            base["label"] = label_value

    elif label_cols:
        for col in label_cols:
            if not col.startswith("label::"):
                continue

            match = re.match(r"label::([^(]+)(?:\(([^)]+)\))?", col)
            if not match:
                continue

            lang_key = match.group(1).strip().lower()
            lang_code = match.group(2) or INCLUDED_LANGUAGES.get(lang_key)

            trans_key = f"{lang_key}({lang_code})" if lang_code else lang_key
            lang_dict = translations.get(trans_key, {})

            label_value = lang_dict.get(field_name)
            if label_value:
                base[col] = label_value
    else:
        for lang_key, lang_dict in translations.items():
            label_key = f"label::{lang_key}"
            label_value = lang_dict.get(field_name)
            if label_value:
                base[label_key] = label_value

    return base
