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
"""Test functionality of OdkCentralAsync.py, specifically attachment methods."""

from pathlib import Path

from osm_fieldwork.OdkCentralAsync import OdkForm as OdkFormAsync

test_data_dir = Path(__file__).parent / "test_data"


async def test_list_submission_attachment_urls(odk_submission, pyodk_config):
    """Create attachments in bulk, then list the URLs to download."""
    odk_id, form_name, submission_id = odk_submission

    async with OdkFormAsync(
        url="http://central:8383",
        user="admin@hotosm.org",
        passwd="Password1234",
    ) as form_async:
        # The dummy form from conftest includes 3 submission images.
        attachments = await form_async.listSubmissionAttachments(odk_id, form_name, submission_id)
        sorted_attachments = sorted(attachments, key=lambda x: x['name'])
        assert len(attachments) == 3
        assert sorted_attachments == [
            {'name': '1.jpg', 'exists': False},
            {'name': '2.jpg', 'exists': False},
            {'name': '3.jpg', 'exists': False},
        ]

        # NOTE here we initially attempted to use tempfile + jpg magic bytes, but
        # this approach failed. We need to upload an actual file for the mimetype
        # to be determined correctly, which in turn allows Minio to determine the
        # correct Content-Type header in the response
        submission_photo_filename = "submission_image.png"
        submission_photo_filepath = f"{test_data_dir}/{submission_photo_filename}"

        # NOTE this submission does not select an existing entity, but creates a new feature
        # This is intentionally not uploaded in this test while S3-sync issues are unresolved.
        submission_id = "dummy-id-not-uploaded"
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
                <image>{submission_photo_filename}</image>
            </verification>
            </data>
        """

    # FIXME fix this test
    # FIXME for some reason they aren't accessing minio for the submission upload?
    # FIXME setup an alias for minio connection, then
    # FIXME mc admin trace fmtm

    # with Client(pyodk_config) as client:
    #     client.submissions.create(
    #         project_id=odk_id,
    #         form_id=form_name,
    #         xml=submission_xml,
    #         device_id=None,
    #         encoding="utf-8",
    #         attachments=[submission_photo_filepath],
    #     )

    # # Wait for the submission attachments to be processed as background job
    # await asyncio.sleep(5)

    # async with OdkFormAsync(
    #     url="http://central:8383",
    #     user="admin@hotosm.org",
    #     passwd="Password1234",
    # ) as form_async:
    #     attachments = await form_async.listSubmissionAttachments(odk_id, form_name, submission_id)
    #     assert attachments[0].get("exists") is True

    #     # First we need to sync the S3 content and wait a few seconds for it
    #     await form_async.s3_reset()
    #     await form_async.s3_sync()
    #     await asyncio.sleep(5)

    #     attachment_urls = await form_async.getSubmissionAttachmentUrls(odk_id, form_name, submission_id)
    #     assert len(attachment_urls) == 1
