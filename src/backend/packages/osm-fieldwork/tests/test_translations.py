"""Tests for gettext-backed XLSForm translations."""

from osm_fieldwork.form_components.translations import add_label_translations


def test_add_label_translations_uses_gettext_catalogs() -> None:
    base = {"name": "digitisation_correct"}

    translated = add_label_translations(base.copy(), ["label::english(en)", "label::french(fr)"])

    assert translated["label::english(en)"] == "Digitisation Correct"
    assert translated["label::french(fr)"] == "Numérisation correcte"


def test_add_label_translations_populates_default_label_from_english() -> None:
    translated = add_label_translations({"name": "survey_questions"}, ["label"])

    assert translated["label"] == "Survey Questions"
