"""Bundled XLSForms, with Field-TM fields added, must load in Collect and Central.

ODK Validate (bundled with pyxform, needs Java) parses with JavaRosa, Collect's engine.
"""

from io import BytesIO
from pathlib import Path

import pytest
from osm_fieldwork.conversion_to_xlsform import convert_to_xlsform
from osm_fieldwork.xlsforms import xlsforms_path
from pyxform.xls2xform import convert

from app.central import central_crud

BUNDLED_FORMS = sorted(Path(xlsforms_path).glob("*.yaml"))


@pytest.mark.parametrize(
    "use_odk_collect", [True, False], ids=["odk-collect", "default"]
)
@pytest.mark.parametrize("form_path", BUNDLED_FORMS, ids=lambda path: path.stem)
async def test_bundled_form_loads_in_odk(odk_project, form_path, use_odk_collect):
    """The processed form passes ODK Validate and Central accepts it."""
    _xform_id, xlsform = await central_crud.append_fields_to_user_xlsform(
        BytesIO(convert_to_xlsform(str(form_path))),
        form_name=f"FTM_{form_path.stem}",
        use_odk_collect=use_odk_collect,
    )

    result = convert(xlsform, validate=True)

    await central_crud.create_odk_xform(
        odk_id=odk_project,
        xform_data=BytesIO(result.xform.encode()),
        odk_credentials=None,
    )
