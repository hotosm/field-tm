"""Translations for XLSForm fields."""

import json
from pathlib import Path
from typing import Optional
import pandas as pd

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
print("Translations loaded:", translations)

def add_label_translations(base: dict, default_language: Optional[str] = None) -> dict:
    field_name = base.get("name")
    print(type(default_language))
    if isinstance(default_language, pd.Series):
        print("default_language is a Series, converting to string")
        default_language = default_language.item()
    print("default_language:", default_language)
    print("add_label_translations")
    print("base before label translations:")
    print(base)
    default_language_key = next((k for k, v in INCLUDED_LANGUAGES.items() if v == default_language), None)
    print("default_language_key:", default_language_key)
    # If name is a list (from a DataFrame row-style dict), unwrap it
    if isinstance(field_name, list):
        if len(field_name) == 1:
            field_name = field_name[0]
        else:
            return base  # Can't handle multi-name entries

    if not isinstance(field_name, str):
        return base

    for lang_key, lang_dict in translations.items():
        label_key = f"label::{lang_key}"
        label_value = lang_dict.get(field_name)
        print(label_key, label_value)
        if label_value:
            base[label_key] = label_value

    print("base after label translations:")
    print(base)
    return base
