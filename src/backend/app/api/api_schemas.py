"""Schemas for external API project creation flow."""

from __future__ import annotations

from area_splitter import SplittingAlgorithm
from pydantic import BaseModel, model_validator

from app.central.central_schemas import ODKCentral
from app.db.enums import DbGeomType, FieldMappingApp, XLSFormType
from app.qfield.qfield_schemas import QFieldCloud


class CreateProjectRequest(BaseModel):
    """Step 1 payload to create a project stub."""

    project_name: str
    field_mapping_app: FieldMappingApp
    description: str
    outline: dict
    hashtags: list[str] | None = None


class XLSFormRequest(BaseModel):
    """Step 2 payload to attach XLSForm from template or base64 upload."""

    template_form_id: int | None = None
    xlsform_base64: str | None = None
    need_verification_fields: bool = True
    mandatory_photo_upload: bool = False
    use_odk_collect: bool = False
    default_language: str = "english"

    @model_validator(mode="after")
    def validate_source(self):
        """Require exactly one source for XLSForm content."""
        has_template = self.template_form_id is not None
        has_upload = bool(self.xlsform_base64)
        if has_template == has_upload:
            raise ValueError(
                "Provide exactly one XLSForm source: "
                "template_form_id or xlsform_base64."
            )
        return self


class DataExtractRequest(BaseModel):
    """Step 3 payload to provide project data extract."""

    geojson: dict | None = None
    osm_category: XLSFormType | None = XLSFormType.buildings
    geom_type: DbGeomType | None = DbGeomType.POLYGON
    centroid: bool = False

    @model_validator(mode="after")
    def validate_data_source(self):
        """Allow either explicit geojson or OSM download parameters."""
        if self.geojson is not None:
            return self
        if not self.osm_category or not self.geom_type:
            raise ValueError(
                "Provide geojson directly, or provide osm_category and geom_type."
            )
        return self


class SplitRequest(BaseModel):
    """Step 4 payload to split AOI into tasks."""

    algorithm: SplittingAlgorithm
    no_of_buildings: int = 50
    dimension_meters: int = 100


class FinalizeRequest(ODKCentral, QFieldCloud):
    """Step 5 payload to finalize downstream project creation."""

    cleanup: bool = False


class ProjectResponse(BaseModel):
    """Simple project response payload."""

    id: int
    project_name: str
    field_mapping_app: FieldMappingApp
    status: str


class DataExtractResponse(BaseModel):
    """Response for step 3 data extraction."""

    project_id: int
    feature_count: int


class SplitResponse(BaseModel):
    """Response for step 4 split processing."""

    project_id: int
    task_count: int
    is_empty: bool


class FinalizeResponse(BaseModel):
    """Response for step 5 finalize."""

    project_id: int
    downstream_url: str
    cleanup: bool
