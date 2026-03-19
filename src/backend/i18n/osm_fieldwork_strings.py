"""Extraction-only gettext markers for osm-fieldwork XLSForm labels."""

from gettext import pgettext


def get_osm_fieldwork_msgids() -> tuple[str, ...]:
    """Return the msgids that belong to the osm-fieldwork gettext domain."""
    return (
        pgettext("xlsform_label", "digitisation_correct"),
        pgettext("xlsform_label", "digitisation_problem"),
        pgettext("xlsform_label", "digitisation_problem_other"),
        pgettext("xlsform_label", "end_note"),
        pgettext("xlsform_label", "existing"),
        pgettext("xlsform_label", "feature"),
        pgettext("xlsform_label", "feature_exists"),
        pgettext("xlsform_label", "image"),
        pgettext("xlsform_label", "lumped"),
        pgettext("xlsform_label", "mapping_mode"),
        pgettext("xlsform_label", "new"),
        pgettext("xlsform_label", "new_feature"),
        pgettext("xlsform_label", "no"),
        pgettext("xlsform_label", "osm_username"),
        pgettext("xlsform_label", "other"),
        pgettext("xlsform_label", "split"),
        pgettext("xlsform_label", "survey_questions"),
        pgettext("xlsform_label", "task"),
        pgettext("xlsform_label", "verification"),
        pgettext("xlsform_label", "yes"),
    )
