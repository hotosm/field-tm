# Copyright (c) Humanitarian OpenStreetMap Team
#
# This file is part of osm_fieldwork.
#
#     osm-fieldwork is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     osm-fieldwork is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with osm_fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Test functionality of OdkCentralAsync.py, specifically the OdkForm class."""

import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile

from pyodk.client import Client

from osm_fieldwork.OdkCentralAsync import OdkForm as OdkFormAsync

odk_config_file = str(Path(__file__).parent / ".pyodk_config.toml")
test_data_dir = Path(__file__).parent / "test_data"


async def test_list_submission_attachment_urls(odk_submission):
    """Create attachments in bulk, then list the URLs to download."""
    odk_id, form_name = odk_submission

    async with OdkFormAsync(
        url="https://proxy",
        user="test@hotosm.org",
        passwd="Password1234",
    ) as form_async:
        submissions = await form_async.listSubmissions(odk_id, form_name)
        submission_id = submissions[0]["instanceId"]
        attachments = await form_async.listSubmissionAttachments(odk_id, form_name, submission_id)
        assert len(attachments) == 3

    # Use predefined submission photo bytes
    submission_photo_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00\x60\x00\x60\x00\x00\xff\xdb\x00C\x00"

    # Create three temporary files for submission photos
    with (
        NamedTemporaryFile(suffix=".jpg") as temp_photo_1,
        NamedTemporaryFile(suffix=".jpg") as temp_photo_2,
        NamedTemporaryFile(suffix=".jpg") as temp_photo_3,
    ):
        temp_photo_1.write(submission_photo_bytes)
        temp_photo_1.flush()
        temp_photo_2.write(submission_photo_bytes)
        temp_photo_2.flush()
        temp_photo_3.write(submission_photo_bytes)
        temp_photo_3.flush()

        photo_1_path = str(Path(temp_photo_1.name).absolute())
        photo_2_path = str(Path(temp_photo_2.name).absolute())
        photo_3_path = str(Path(temp_photo_3.name).absolute())

        temp_photo_1_name = Path(temp_photo_1.name).name
        temp_photo_2_name = Path(temp_photo_2.name).name
        temp_photo_3_name = Path(temp_photo_3.name).name

        # NOTE this submission does not select an existing entity, but creates a new feature
        submission_id = str(uuid.uuid4())
        submission_xml = f"""
            <data id="{form_name}" version="v1">
            <meta>
                <instanceID>{submission_id}</instanceID>
            </meta>
            <start>2024-11-15T12:28:23.641Z</start>
            <end>2024-11-15T12:29:00.876Z</end>
            <today>2024-11-15</today>
            <phonenumber/>
            <deviceid>collect:OOYOOcNu8uOA2G4b</deviceid>
            <username>testuser</username>
            <instructions/>
            <warmup/>
            <feature/>
            <null/>
            <new_feature>12.750577838121643 -24.776785714285722 0.0 0.0</new_feature>
            <xid/>
            <xlocation>12.750577838121643 -24.776785714285722 0.0 0.0</xlocation>
            <task_id/>
            <status>2</status>
            <survey_questions>
                <buildings>
                <category>housing</category>
                <name/>
                <building_material/>
                <building_levels/>
                <housing/>
                <provider/>
                </buildings>
                <details>
                <power/>
                <water/>
                <age/>
                <building_prefab/>
                <building_floor/>
                <building_roof/>
                <condition/>
                <access_roof/>
                <levels_underground/>
                </details>
                <comment/>
            </survey_questions>
            <verification>
                <digitisation_correct>yes</digitisation_correct>
                <image>{temp_photo_1_name}</image>
                <image2>{temp_photo_2_name}</image2>
                <image3>{temp_photo_3_name}</image3>
            </verification>
            </data>
        """

        with Client(config_path=odk_config_file) as client:
            client.submissions.create(
                project_id=odk_id,
                form_id=form_name,
                xml=submission_xml,
                device_id=None,
                encoding="utf-8",
                attachments=[
                    photo_1_path,
                    photo_2_path,
                    photo_3_path,
                ],
            )

    async with OdkFormAsync(
        url="https://proxy",
        user="test@hotosm.org",
        passwd="Password1234",
    ) as form_async:
        attachment_urls = await form_async.getSubmissionAttachmentUrls(odk_id, form_name, submission_id)
        assert len(attachment_urls) == 3
