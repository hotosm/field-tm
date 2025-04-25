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
"""Tests for task routes."""

from uuid import UUID

import pytest

from app.db.enums import MappingState, TaskEvent


async def test_read_tasks(client, project, tasks):
    """Test retrieving all tasks for a project."""
    response = await client.get(f"/tasks?project_id={project.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(tasks)
    for task in data:
        assert "id" in task
        assert "project_id" in task


async def test_get_specific_task(client, project, tasks):
    """Test retrieving a specific task by ID."""
    task = tasks[0]
    response = await client.get(f"/tasks/{task.id}?project_id={project.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task.id
    assert data["project_id"] == task.project_id


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


async def test_submit_task_events(client, tasks, project_team, admin_user):
    """Test update the task status."""
    task_id = tasks[0].id
    non_existent_task_id = tasks[-1].id + 1
    project_id = project_team["project"].id
    team = project_team["team"]

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

    # ASSIGN WITH TEAM
    response = await client.post(
        f"tasks/{task_id}/event?project_id={project_id}&team_id={team.team_id}&notify=false",
        json={
            "event": TaskEvent.ASSIGN,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["event"] == TaskEvent.ASSIGN
    assert UUID(data["team_id"]) == team.team_id
    # User is not assigned when team is assigned
    assert data["user_sub"] is None
    assert data["state"] == MappingState.LOCKED_FOR_MAPPING

    # ASSIGN WITH AN ASSIGNEE
    response = await client.post(
        f"tasks/{task_id}/event?project_id={project_id}&assignee_sub={admin_user.sub}&notify=false",
        json={
            "event": TaskEvent.ASSIGN,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["event"] == TaskEvent.ASSIGN
    assert data["user_sub"] == admin_user.sub
    # Team is not assigned when user is assigned
    assert data["team_id"] is None
    assert data["state"] == MappingState.LOCKED_FOR_MAPPING

    # INVALID TASK
    response = await client.post(
        f"tasks/{non_existent_task_id}/event?project_id={project_id}",
        json={"event": TaskEvent.MAP},
    )
    assert response.status_code == 404

    # INVALID EVENT
    response = await client.post(
        f"tasks/{task_id}/event?project_id={project_id}",
        json={"event": "INVALID_EVENT"},
    )
    assert response.status_code == 422


async def test_get_task_activity(client, tasks, task_events):
    """Test retrieving task activity for a project."""
    project_id = tasks[0].project_id

    response = await client.get(f"/tasks/activity?project_id={project_id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data
    item = data[0]
    assert "date" in item
    assert "mapped" in item
    assert item["mapped"] == 1
    assert "validated" in item
    assert item["validated"] == 1


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
