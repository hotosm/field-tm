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
"""Tests for submission routes."""

import json
from datetime import datetime

import pytest


async def test_read_submissions(client, submission):
    """Test get submissions with a single submission expected."""
    odk_project = submission["project"]
    submission_data = submission["submission_data"]

    response = await client.get(f"/submission?project_id={odk_project.id}")
    assert response.status_code == 200, f"Failed to fetch submissions: {response.text}"

    submission_list = response.json()
    assert isinstance(submission_list, list), "Expected a list of submissions"

    first_submission = submission_list[0]
    test_instance_id = submission_data.get("instanceId")
    assert first_submission["__id"] == test_instance_id, "Instance ID mismatch"
    assert first_submission["meta"]["instanceID"] == test_instance_id, (
        "Meta instanceID mismatch"
    )
    assert first_submission["__system"]["submitterId"] == str(
        submission_data.get("submitterId")
    ), "Submitter ID mismatch"


async def test_download_submission_json(client, submission):
    """Test downloading submissions as JSON."""
    odk_project = submission["project"]

    date = datetime.strptime(
        submission["submission_data"].get("createdAt"), "%Y-%m-%dT%H:%M:%S.%fZ"
    ).strftime("%Y-%m-%d")

    response = await client.get(
        f"/submission/download?project_id={odk_project.id}&file_type=json"
        f"&submitted_date_range={date},{date}"
    )

    assert response.status_code == 200, (
        f"Failed to download JSON submissions. Response: {response.text}"
    )
    assert "Content-Disposition" in response.headers, (
        "Missing Content-Disposition header"
    )

    expected_filename = f"{odk_project.slug}_submissions.json"

    assert response.headers["Content-Disposition"].endswith(expected_filename), (
        f"Expected file name to end with {expected_filename}"
    )

    submissions = response.json()
    assert isinstance(submissions, dict), "Expected JSON response to be a dictionary"
    assert "value" in submissions, "Missing 'value' key in JSON response"
    assert isinstance(submissions["value"], list), "Expected 'value' to be a list"
    assert len(submissions["value"]) > 0, "Expected at least one submission in 'value'"


async def test_download_submission_file(client, submission):
    """Test downloading submissions as zipped CSV file + attachment media."""
    odk_project = submission["project"]

    date = datetime.strptime(
        submission["submission_data"].get("createdAt"), "%Y-%m-%dT%H:%M:%S.%fZ"
    ).strftime("%Y-%m-%d")

    response = await client.get(
        f"/submission/download?project_id={odk_project.id}&file_type=csv"
        f"&submitted_date_range={date},{date}"
    )

    assert response.status_code == 200, (
        f"Failed to download submissions as file. Response: {response.text}"
    )
    assert "Content-Disposition" in response.headers, (
        "Missing Content-Disposition header"
    )

    expected_filename = f"{odk_project.slug}.zip"

    assert response.headers["Content-Disposition"].endswith(expected_filename), (
        f"Expected file name to end with {expected_filename}"
    )
    assert len(response.content) > 0, "Expected non-empty ZIP file content"


async def test_get_submission_count(client, submission):
    """Test fetching the submission count for a project."""
    odk_project = submission["project"]

    response = await client.get(
        f"/submission/get-submission-count?project_id={odk_project.id}"
    )
    assert response.status_code == 200, (
        f"Failed to fetch submission count. Response: {response.text}"
    )

    submission_count = response.json()
    assert isinstance(submission_count, int), (
        "Expected submission count to be an integer"
    )
    assert submission_count > 0, "Submission count should be greater than zero"


async def test_download_submission_geojson(client, submission):
    """Test downloading submissions as a GeoJSON file."""
    odk_project = submission["project"]

    response = await client.get(
        f"/submission/download?project_id={odk_project.id}&file_type=geojson"
    )

    assert response.status_code == 200, (
        f"Failed to download GeoJSON submissions. Response: {response.text}"
    )

    assert "Content-Disposition" in response.headers, (
        "Missing Content-Disposition header"
    )
    expected_filename = f"{odk_project.slug}.geojson"
    assert response.headers["Content-Disposition"].endswith(expected_filename), (
        f"Expected file name to end with {expected_filename}"
    )

    submission_geojson = json.loads(response.content)
    assert isinstance(submission_geojson, dict), (
        "Expected GeoJSON content to be a dictionary"
    )
    assert "type" in submission_geojson, "Missing 'type' key in GeoJSON"
    assert submission_geojson["type"] == "FeatureCollection", (
        "GeoJSON type must be 'FeatureCollection'"
    )
    assert "features" in submission_geojson, "Missing 'features' key in GeoJSON"
    assert isinstance(submission_geojson["features"], list), (
        "Expected 'features' to be a list"
    )
    assert len(submission_geojson["features"]) > 0, (
        "Expected at least one feature in 'features'"
    )


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
