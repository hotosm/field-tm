"""Tests for normalising ODK and QField submissions to one GeoJSON format."""

from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest

from osm_fieldwork.conversion_to_xlsform import convert_to_xlsform
from osm_fieldwork.export import (
    CORE_FIELDS,
    OsmField,
    apply_osm_keys,
    from_odk,
    from_qfield,
    javarosa_to_geojson,
    media_fields,
    osm_fields,
    to_feature_collection,
)
from osm_fieldwork.xlsforms import healthcare

ODK_RECORD = {
    "__id": "uuid:abc",
    "__system": {"submissionDate": "2026-01-02T10:00:00Z", "submitterName": "app"},
    "meta": {"instanceID": "uuid:abc"},
    "start": "2026-01-02T09:55:00Z",
    "deviceid": "secret-device",
    "username": "collect-user",
    "osm_username": "mapper1",
    "xid": "123",
    "xlocation": "27.7 85.3 0.0 0.0",
    "task_id": "4",
    "status": "mapped",
    "fill": "#00ff00",
    "building": {"levels": "2", "material": "brick"},
    "survey_photos": {
        "photos@odata.navigationLink": "x",
        "photos": [{"__id": "r1", "image": "a.jpg"}, {"__id": "r2", "image": "b.jpg"}],
    },
}

QFIELD_FEATURE = {
    "type": "Feature",
    "id": 7,
    "geometry": {"type": "Point", "coordinates": [85.3, 27.7]},
    "properties": {
        "fid": 7,
        "uuid": "q-1",
        "end": "2026-01-03T08:00:00",
        "username": "mapper2",
        "xid": 123,
        "task_id": 4,
        "status": "mapped",
        "levels": "3",
        "image": "DCIM/c.jpg",
    },
}


def test_odk_and_qfield_share_core_fields():
    """Both apps produce the same leading core properties."""
    odk = from_odk(ODK_RECORD, {"image"})
    qfield = from_qfield(QFIELD_FEATURE, {"image"})
    for feature in (odk, qfield):
        assert tuple(feature["properties"])[: len(CORE_FIELDS)] == CORE_FIELDS
        assert feature["properties"]["task_id"] == 4
        assert feature["properties"]["osm_id"] == 123
        assert feature["geometry"] == {"type": "Point", "coordinates": [85.3, 27.7]}


def test_odk_metadata_groups_and_repeats():
    """ODK metadata is mapped, groups flattened, repeat photos collected."""
    props = from_odk(ODK_RECORD, {"image"})["properties"]
    assert props["id"] == "uuid:abc"
    assert props["username"] == "mapper1"
    assert props["submitted_at"] == "2026-01-02T10:00:00Z"
    assert props["attachments"] == ["a.jpg", "b.jpg"]
    assert props["levels"] == "2"
    assert props["material"] == "brick"
    for dropped in ("deviceid", "start", "fill", "xlocation", "instanceID"):
        assert dropped not in props
    # Repeats become a JSON string, so QGIS and uMap can read them
    assert isinstance(props["photos"], str)


def test_odk_new_feature_geometry():
    """A new ODK feature uses its own GeoJSON geometry when no xlocation."""
    shape = {"type": "LineString", "coordinates": [[85.3, 27.7], [85.4, 27.8]]}
    feature = from_odk({"__id": "x", "new_feature": shape})
    assert feature["geometry"] == shape
    assert "new_feature" not in feature["properties"]


def test_qfield_metadata():
    """QField metadata is mapped and internal ids dropped."""
    props = from_qfield(QFIELD_FEATURE, {"image"})["properties"]
    assert props["id"] == "q-1"
    assert props["username"] == "mapper2"
    assert props["submitted_at"] == "2026-01-03T08:00:00"
    assert props["attachments"] == ["DCIM/c.jpg"]
    assert "fid" not in props
    assert "uuid" not in props


def test_qfield_falls_back_to_xlocation():
    """Features without geometry use the xlocation string."""
    feature = from_qfield({"properties": {"xlocation": "27.7 85.3 0 0"}})
    assert feature["geometry"]["type"] == "Point"
    assert feature["properties"]["id"] is None


def test_javarosa_to_geojson():
    """Points, lines and closed polygons are inferred."""
    assert javarosa_to_geojson("") is None
    assert javarosa_to_geojson("bad") is None
    line = javarosa_to_geojson("1 2 0 0;3 4 0 0")
    assert line == {"type": "LineString", "coordinates": [[2.0, 1.0], [4.0, 3.0]]}
    polygon = javarosa_to_geojson("1 1;1 2;2 2;1 1")
    assert polygon["type"] == "Polygon"


def test_media_fields():
    """Only attachment question types are returned."""
    survey = pd.DataFrame(
        {
            "type": ["text", "image", "audio", "begin group", None],
            "name": ["name", "photo", "voice", "grp", "x"],
        }
    )
    buffer = BytesIO()
    survey.to_excel(buffer, sheet_name="survey", index=False)
    assert media_fields(buffer.getvalue()) == {"photo", "voice"}


def test_media_fields_mandatory_form():
    """The Field-TM test form parses without error."""
    xls = Path(__file__).parent / "test_data" / "test_form_for_mandatory_fields.xls"
    assert isinstance(media_fields(xls.read_bytes()), set)


def test_to_feature_collection():
    """Features are wrapped in a FeatureCollection."""
    fc = to_feature_collection([from_odk({"__id": "x"})])
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 1


def test_osm_fields_absent_without_column():
    """Forms with no osm_key column keep their question names."""
    buffer = BytesIO()
    pd.DataFrame([{"type": "text", "name": "street"}]).to_excel(
        buffer, sheet_name="survey", index=False
    )
    assert osm_fields(buffer.getvalue()) == {}


def test_osm_fields_from_healthcare_form():
    """The bundled healthcare form tags its questions, flagging multi-selects."""
    fields = osm_fields(convert_to_xlsform(healthcare))
    assert fields["street"] == OsmField("addr:street", False)
    assert fields["healthcare"] == OsmField("healthcare", True)
    assert fields["_mon_hours"] == OsmField(None)


def test_apply_osm_keys():
    """Answers take their OSM key and untagged answers are left alone."""
    fields = {
        "street": OsmField("addr:street", False),
        "healthcare": OsmField("healthcare", True),
        "beds": OsmField("beds", False),
    }
    feature = from_odk(
        {
            "__id": "x",
            "addr": {"street": "Rue A"},
            "healthcare": "clinic laboratory",
            "beds": None,
            "comment": "untagged",
        }
    )
    props = apply_osm_keys(feature, fields)["properties"]
    assert props["addr:street"] == "Rue A"
    assert props["healthcare"] == "clinic;laboratory"
    assert props["beds"] is None
    assert props["comment"] == "untagged"
    assert "street" not in props


@pytest.mark.parametrize("value", ["{clinic,laboratory}", '["clinic", "laboratory"]'])
def test_apply_osm_keys_qgis_multi_select(value):
    """QGIS multi-selects are array strings, not space separated."""
    feature = {"properties": {"healthcare": value}}
    fields = {"healthcare": OsmField("healthcare", True)}
    assert apply_osm_keys(feature, fields)["properties"] == {
        "healthcare": "clinic;laboratory"
    }


def test_working_fields_are_dropped():
    """A form's own helper questions go, other underscore properties stay."""
    feature = from_qfield(
        {"properties": {"_mon_hours": "08:00-12:00", "_layer": "survey"}}
    )
    fields = osm_fields(convert_to_xlsform(healthcare))
    props = apply_osm_keys(feature, fields)["properties"]
    assert "_mon_hours" not in props
    assert props["_layer"] == "survey"


def test_underscore_questions_kept_without_osm_key_column():
    """Forms that do not use osm_key export all of their answers."""
    feature = from_qfield({"properties": {"_custom": "answer"}})
    assert apply_osm_keys(feature, {})["properties"]["_custom"] == "answer"
