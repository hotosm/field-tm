# Copyright (c) Humanitarian OpenStreetMap Team
#
# This file is part of Field-TM.
#
#     Field-TM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Field-TM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Field-TM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Utils for download organisation submissions."""

import csv
import io

from app.organisations.organisation_deps import get_org_odk_creds
from app.submissions import submission_crud


async def populate_odk_credentials_for_projects(projects, org):
    """Fill in missing ODK credentials for each project."""
    odk_creds = await get_org_odk_creds(org)
    for project in projects:
        if not (
            project.odk_central_url
            and project.odk_central_user
            and project.odk_central_password
        ):
            project.odk_central_url = odk_creds.odk_central_url
            project.odk_central_user = odk_creds.odk_central_user
            project.odk_central_password = odk_creds.odk_central_password
            project.odk_credentials = odk_creds  # Needed by pyodk client


def build_submission_filters(submitted_date_range: str):
    """Create a filter dictionary for date range to be applied to submissions API."""
    filters = {}
    if submitted_date_range:
        try:
            start_date, end_date = submitted_date_range.split(",")
            filters["$filter"] = (
                f"__system/submissionDate ge {start_date}T00:00:00+00:00 and "
                f"__system/submissionDate le {end_date}T23:59:59.999+00:00"
            )
        except ValueError:
            pass  # Gracefully skip if format is invalid
    return filters


async def collect_all_submissions(projects, filters):
    """Fetch all submissions for each project and enrich them with project metadata.

    Logs count per project to help debug missing results.
    """
    all_submissions = []

    for project in projects:
        data = await submission_crud.get_submission_by_project(project, filters)
        values = data.get("value", []) or []

        for sub in values:
            sub["project_id"] = project.id
            sub["project_name"] = project.name
            all_submissions.append(sub)

    return all_submissions


def extract_geometry(submission):
    """Extract a GeoJSON-compatible geometry object from a submission.

    Priority:
    1. Use 'geometry' field if it's a valid GeoJSON object.
    2. Fallback to 'latitude' and 'longitude' fields.
    3. Return null if no valid geometry found.
    """
    if "geometry" in submission and isinstance(submission["geometry"], dict):
        return submission["geometry"]

    elif "latitude" in submission and "longitude" in submission:
        try:
            lat = float(submission["latitude"])
            lon = float(submission["longitude"])
            return {"type": "Point", "coordinates": [lon, lat]}
        except (ValueError, TypeError):
            return None

    return None


def generate_csv_string(submissions: list) -> str:
    """Generate CSV text from a list of submissions."""
    output = io.StringIO()
    fieldnames = sorted({key for sub in submissions for key in sub.keys()})
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(submissions)
    return output.getvalue()


def generate_geojson_dict(submissions: list) -> dict:
    """Generate a GeoJSON FeatureCollection from submissions."""
    features = []

    for sub in submissions:
        geometry = extract_geometry(sub)
        properties = {
            k: v
            for k, v in sub.items()
            if k not in ("geometry", "latitude", "longitude")
        }

        feature = {
            "type": "Feature",
            "geometry": geometry,
            "properties": properties,
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }
