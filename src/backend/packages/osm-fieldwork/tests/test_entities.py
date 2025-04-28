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
"""Test functionality of OdkCentral.py Entities methods."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from aiohttp.client_exceptions import ClientError


async def test_entity_modify(odk_dataset_cleanup):
    """Test modifying an entity."""
    odk_id, dataset_name, entity_uuid, dataset = odk_dataset_cleanup
    print(dataset_name)
    async with dataset:
        updated_entity = await dataset.updateEntity(odk_id, dataset_name, entity_uuid, label="new label")
    assert updated_entity.get("currentVersion").get("label") == "new label"

    async with dataset:
        updated_entity = await dataset.updateEntity(
            odk_id, dataset_name, entity_uuid, data={"status": "complete", "project_id": "100"}
        )
    new_data = updated_entity.get("currentVersion").get("data", {})
    assert new_data.get("status") == "complete"
    assert new_data.get("project_id") == "100"


async def test_create_invalid_entities(odk_dataset_cleanup):
    """Test uploading invalid data to an entity (HTTP 400)."""
    odk_id, dataset_name, entity_uuid, dataset = odk_dataset_cleanup
    async with dataset:
        # NOTE entity must have a geometry data field
        with pytest.raises(ValueError):
            await dataset.createEntity(odk_id, dataset_name, label="test", data={"status": 0})

        # NOTE data fields cannot be integer, this should raise error
        with pytest.raises(ClientError):
            await dataset.createEntity(odk_id, dataset_name, label="test", data={"geometry": "", "status": 0})

        # Also test bulk entity create using integer data
        with pytest.raises(ClientError):
            await dataset.createEntities(
                odk_id,
                dataset_name,
                [
                    {"label": "test entity 2", "data": {"osm_id": 55, "geometry": "test"}},
                    {"label": "test entity 3", "data": {"osm_id": "66", "geometry": "test"}},
                ],
            )

        # Bulk Entity creation, not a list
        with pytest.raises(ValueError):
            await dataset.createEntities(
                odk_id,
                dataset_name,
                {"label": "test", "data": {}},
            )


async def test_create_invalid_dataset(odk_dataset):
    """Test creating invalid dataset."""
    odk_id, dataset = odk_dataset

    dataset_name = f"new_dataset_{uuid4()}"
    async with dataset:
        with pytest.raises(ValueError):
            await dataset.createDataset(odk_id, dataset_name, properties="string")

        with pytest.raises(ValueError):
            await dataset.createDataset(odk_id, dataset_name, properties=[1, 2])


async def test_bulk_create_entity_count(odk_dataset_cleanup):
    """Test bulk creation of Entities."""
    odk_id, dataset_name, entity_uuid, dataset = odk_dataset_cleanup
    async with dataset:
        await dataset.createEntities(
            odk_id,
            dataset_name,
            [
                {"label": "test entity 1", "data": {"osm_id": "44", "geometry": "test"}},
                {"label": "test entity 2", "data": {"osm_id": "55", "geometry": "test"}},
                {"label": "test entity 3", "data": {"osm_id": "66", "geometry": "test"}},
            ],
        )
        entity_count = await dataset.getEntityCount(odk_id, dataset_name)

    # NOTE this may be cumulative from the session... either 4 or 5
    assert entity_count >= 4


async def test_get_entity_data(odk_dataset_cleanup):
    """Test getting entity data, including via a OData filter."""
    odk_id, dataset_name, entity_uuid, dataset = odk_dataset_cleanup
    async with dataset:
        await dataset.createEntities(
            odk_id,
            dataset_name,
            [
                {"label": "test entity 1", "data": {"geometry": "test"}},
                {"label": "test entity 2", "data": {"geometry": "test"}},
                {"label": "test entity 3", "data": {"geometry": "test"}},
                {"label": "test entity 4", "data": {"geometry": "test"}},
                {"label": "test entity 5", "data": {"geometry": "test"}},
                {"label": "test entity 6", "data": {"geometry": "test"}},
                {"label": "test entity 7", "data": {"geometry": "test"}},
                {"label": "test entity 8", "data": {"geometry": "test"}},
            ],
        )

        all_entities = await dataset.getEntityData(odk_id, dataset_name)
        # NOTE this may be cumulative from the session... either 9 or 12
        assert len(all_entities) >= 9

        entities_with_metadata = await dataset.getEntityData(odk_id, dataset_name, include_metadata=True)
        assert len(entities_with_metadata.get("value")) >= 9
        assert entities_with_metadata.get("@odata.context").endswith("$metadata#Entities")

        # Paginate, 5 per page
        filtered_entities = await dataset.getEntityData(odk_id, dataset_name, url_params="$top=5&$count=true")
        assert filtered_entities.get("@odata.count") >= 9
        assert "@odata.nextLink" in filtered_entities.keys()

        # Get current time NOTE time format = 2022-01-31T23:59:59.999Z
        time_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # Update first 5 entities prior to filter
        entity_uuids = [_entity.get("__id") for _entity in all_entities]
        for uuid in sorted(entity_uuids[:5]):
            await dataset.updateEntity(odk_id, dataset_name, uuid, data={"status": "LOCKED_FOR_MAPPING"})

        filter_updated = await dataset.getEntityData(
            odk_id,
            dataset_name,
            url_params=f"$filter=__system/updatedAt gt {time_now}",
        )
        assert len(filter_updated) == 5
        for entity in filter_updated:
            assert entity.get("status") == "LOCKED_FOR_MAPPING"


async def test_get_entity_data_select_params(odk_dataset_cleanup):
    """Test selecting specific param for an Entity."""
    odk_id, dataset_name, entity_uuid, dataset = odk_dataset_cleanup
    async with dataset:
        entities_select_params = await dataset.getEntityData(
            odk_id,
            dataset_name,
            url_params="$select=__id, __system/updatedAt, geometry",
        )

        assert entities_select_params, "No entities returned"
        first_entity = entities_select_params[0]
        assert "__id" in first_entity, "Missing '__id' key"
        assert "__system" in first_entity and "updatedAt" in first_entity["__system"], "Missing '__system/updatedAt' key"
        assert "geometry" in first_entity, "Missing 'geometry' key"


async def test_get_single_entity(odk_dataset_cleanup):
    """Test getting specific Entity by UUID."""
    odk_id, dataset_name, entity_uuid, dataset = odk_dataset_cleanup
    async with dataset:
        single_entity = await dataset.getEntity(
            odk_id,
            dataset_name,
            entity_uuid,
        )

    assert single_entity.get("uuid") == entity_uuid
    entity_info = single_entity.get("currentVersion")
    # if ran in parallel, this is updated by test_entity_modify!
    assert (label := entity_info.get("label")) == "test entity" or label == "new label"
    assert entity_info.get("data", {}).get("osm_id") == "1"
