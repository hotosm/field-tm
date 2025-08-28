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

import asyncio
import csv
import io
import json

from dateutil.parser import parse as dtparse

from app.config import settings
from app.s3 import get_obj_from_bucket, s3_client


def get_project_submission_s3_path(org, project):
    """Return the S3 path for a project's submission.geojson."""
    return f"{org.id}/{project.id}/submission.geojson"


def load_project_submissions_from_s3(bucket_name, s3_path):
    """Load and parse the submission.geojson from S3, return features list or []."""
    try:
        obj = get_obj_from_bucket(bucket_name, s3_path)
        data = json.load(obj)
        return data.get("features", [])
    except Exception as e:
        import logging

        logging.warning(f"Could not fetch S3 submissions from {s3_path}: {e}")
        return []


def get_project_submission_last_modified(org, project):
    """Return the last modified timestamp of a project's submission.geojson in S3."""
    s3_path = f"{org.id}/{project.id}/submission.geojson"
    client = s3_client()
    try:
        stat = client.stat_object(settings.S3_BUCKET_NAME, s3_path)
        return stat.last_modified.isoformat()
    except Exception:
        return None


def inject_project_info(features, project, org=None):
    """Inject project info to each feature's property."""
    # org is required for last_modified lookup
    if org is None:
        raise ValueError("org must be provided to inject_project_info for S3 metadata.")
    last_uploaded = get_project_submission_last_modified(org, project)
    for sub in features:
        sub_props = sub.get("properties", {})
        sub_props["project_id"] = project.id
        sub_props["project_name"] = project.name
        if last_uploaded:
            sub_props["last_uploaded_to_s3"] = last_uploaded
        sub["properties"] = sub_props
    return features


def filter_features_by_date(features, filters):
    """Filter features by date if filters are provided (for geojson)."""
    if not (filters and "$filter" in filters):
        return features
    import re

    filter_str = filters["$filter"]
    m = re.search(r"ge ([0-9T:\-\+]+) and .*le ([0-9T:\-\+\.]+)", filter_str)
    if not m:
        return features
    start, end = m.group(1), m.group(2)

    start_dt = dtparse(start)
    end_dt = dtparse(end)

    def in_range(sub):
        date_str = sub["properties"].get("__system/submissionDate")
        if not date_str:
            return True
        try:
            dt = dtparse(date_str)
            return start_dt <= dt <= end_dt
        except Exception:
            return True

    return [sub for sub in features if in_range(sub)]


def flatten_features_to_dicts(features):
    """Flatten GeoJSON features to dicts for compatibility with downstream code."""
    return [dict(**sub["properties"], geometry=sub.get("geometry")) for sub in features]


async def fetch_project_submissions(project, org, filters):
    """Fetch submissions for a project from S3 (Minio), split into helpers."""
    s3_path = get_project_submission_s3_path(org, project)
    bucket_name = settings.S3_BUCKET_NAME
    features = load_project_submissions_from_s3(bucket_name, s3_path)
    features = inject_project_info(features, project, org)
    features = filter_features_by_date(features, filters)
    return flatten_features_to_dicts(features)


async def _fetch_with_semaphore(semaphore, project, org, filters):
    """Fetch submissions with concurrency limit of 10 projects."""
    async with semaphore:
        return await fetch_project_submissions(project, org, filters)


async def collect_all_submissions(projects, org, filters, concurrency_limit=10):
    """Aggregate all submissions from all projects within an organisation from S3."""
    semaphore = asyncio.Semaphore(concurrency_limit)
    tasks = [
        _fetch_with_semaphore(semaphore, project, org, filters) for project in projects
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_submissions = [
        sub
        for project_subs in results
        for sub in project_subs
        if isinstance(project_subs, list)
    ]
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
            pass
    return filters
