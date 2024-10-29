# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Tests for task routes."""

from uuid import UUID

import pytest

from app.db.enums import MappingState, TaskEvent


async def test_read_task_history(client, task_event):
    """Test task events for a project."""
    task_id = task_event.task_id

    assert task_id is not None

    response = await client.get(
        f"/tasks/{task_id}/history?project_id={task_event.project_id}"
    )
    data = response.json()[0]

    assert response.status_code == 200
    # NOTE the json return is a string, so we must wrap in UUID
    assert UUID(data["event_id"]) == task_event.event_id
    assert data["username"] == task_event.username
    assert data["profile_img"] == task_event.profile_img
    assert data["comment"] == task_event.comment
    assert data["state"] == MappingState.LOCKED_FOR_MAPPING


async def test_submit_task_events(client, tasks):
    """Test update the task status."""
    task_id = tasks[0].id
    project_id = tasks[0].project_id

    # LOCK MAP
    response = await client.post(
        f"tasks/{task_id}/event?project_id={project_id}",
        json={"event": TaskEvent.MAP},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["event"] == TaskEvent.MAP
    assert data["state"] == MappingState.LOCKED_FOR_MAPPING

    # FINISH
    response = await client.post(
        f"tasks/{task_id}/event?project_id={project_id}",
        json={"event": TaskEvent.FINISH},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["event"] == TaskEvent.FINISH
    assert data["state"] == MappingState.UNLOCKED_TO_VALIDATE

    # LOCK VALIDATE
    response = await client.post(
        f"tasks/{task_id}/event?project_id={project_id}",
        json={"event": TaskEvent.VALIDATE},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["event"] == TaskEvent.VALIDATE
    assert data["state"] == MappingState.LOCKED_FOR_VALIDATION

    # MARK GOOD / VALIDATED
    response = await client.post(
        f"tasks/{task_id}/event?project_id={project_id}",
        json={"event": TaskEvent.GOOD},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["event"] == TaskEvent.GOOD
    assert data["state"] == MappingState.UNLOCKED_DONE

    # COMMENT
    response = await client.post(
        f"tasks/{task_id}/event?project_id={project_id}",
        json={"event": TaskEvent.COMMENT, "comment": "Hello!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["event"] == TaskEvent.COMMENT
    assert data["state"] is None
    assert data["comment"] == "Hello!"


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
