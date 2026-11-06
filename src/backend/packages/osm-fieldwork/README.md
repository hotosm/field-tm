# OSM Fieldwork

<!-- markdownlint-disable -->
<p align="center">
  <img src="https://raw.githubusercontent.com/hotosm/field-tm/main/docs/images/hot_logo.png" style="width: 200px;" alt="HOT"></a>
</p>
<p align="center">
  <em>XLSForm templates and form helpers used by Field-TM.</em>
</p>
<p align="center">
  <a href="https://pypi.org/project/osm-fieldwork" target="_blank">
      <img src="https://img.shields.io/pypi/v/osm-fieldwork?color=%2334D058&label=pypi%20package" alt="Package version">
  </a>
  <a href="https://pypistats.org/packages/osm-fieldwork" target="_blank">
      <img src="https://img.shields.io/pypi/dm/osm-fieldwork.svg" alt="Downloads">
  </a>
  <a href="https://github.com/hotosm/field-tm/blob/main/src/backend/packages/osm-fieldwork/LICENSE.md" target="_blank">
      <img src="https://img.shields.io/badge/license-GPL%203.0-orange.svg" alt="License">
  </a>
</p>

---

📖 **Documentation**: <a href="https://hotosm.github.io/osm-fieldwork/" target="_blank">https://hotosm.github.io/osm-fieldwork/</a>

🖥️ **Source Code**: <a href="https://github.com/hotosm/field-tm/blob/main/src/backend/packages/osm-fieldwork" target="_blank">https://github.com/hotosm/field-tm/blob/main/src/backend/packages/osm-fieldwork</a>

---

## What's in it

XLSForm templates and helpers for Field-TM. For ODK Central clients, use pyodk.

- `xlsforms/`: XLSForm templates for common OSM surveys (buildings,
  health facilities, water points, etc.).
- `update_xlsform.py`: adds the Field-TM mandatory fields to a survey and
  adapts forms for QField. Also available as the `ftm_xlsform` command.
- `conversion_to_xlsform.py`: converts YAML form definitions to XLSForm.
- `form_components/`: the shared mandatory fields and choices.
- `json_data_models/`: raw-data-api query configs for each form category.
- `export.py`: normalises ODK and QField submissions into one standard
  GeoJSON format (`from_odk`, `from_qfield`), for QGIS, uMap etc.

## Form credits

The health facility form (`xlsforms/health.yaml`) is adapted from the
[healthsites.io](https://healthsites.io) campaign form.

## Installation

```bash
pip install osm-fieldwork
```

## Usage

```bash
ftm_xlsform --help
```

Or from Python:

```python
from osm_fieldwork.update_xlsform import append_field_mapping_fields
```

## Translations

Field labels are translated with gettext in the `osm_fieldwork` domain; see
`docs/decisions/0005-gettext-babel-translations.md` in the Field-TM repo.
