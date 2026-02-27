"""Schemas for external API project creation flow."""

from __future__ import annotations

from area_splitter import SplittingAlgorithm
from pydantic import BaseModel, model_validator

from app.central.central_schemas import ODKCentral
from app.db.enums import DbGeomType, FieldMappingApp, XLSFormType
from app.qfield.qfield_schemas import QFieldCloud


class CreateProjectRequest(ODKCentral, QFieldCloud):
    """Single payload to create a complete project end-to-end."""

    # Project metadata
    project_name: str
    field_mapping_app: FieldMappingApp
    description: str
    outline: dict
    hashtags: list[str] | None = None

    # XLSForm — exactly one source required
    template_form_id: int | None = None
    xlsform_base64: str | None = None
    need_verification_fields: bool = True
    mandatory_photo_upload: bool = False
    use_odk_collect: bool = False
    default_language: str = "english"

    # Data extract — provide geojson, osm_category, or neither (collect-new-data mode)
    geojson: dict | None = None
    osm_category: XLSFormType | None = None
    geom_type: DbGeomType = DbGeomType.POLYGON
    centroid: bool = False

    # Task splitting — omit or set to None to skip splitting
    algorithm: SplittingAlgorithm | None = None
    no_of_buildings: int = 10
    dimension_meters: int = 100
    include_roads: bool = True
    include_rivers: bool = True
    include_railways: bool = True
    include_aeroways: bool = True

    # Lifecycle
    cleanup: bool = False

    @model_validator(mode="after")
    def validate_xlsform_source(self):
        """Require exactly one XLSForm source."""
        has_template = self.template_form_id is not None
        has_upload = bool(self.xlsform_base64)
        if has_template == has_upload:
            raise ValueError(
                "Provide exactly one XLSForm source: "
                "template_form_id or xlsform_base64."
            )
        return self


class CreateProjectResponse(BaseModel):
    """Response after full project creation."""

    project_id: int
    fmtm_url: str | None = None
    downstream_url: str
    manager_username: str | None = None
    manager_password: str | None = None
