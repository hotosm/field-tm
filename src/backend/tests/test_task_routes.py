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

import pytest

from app.db.enums import TaskStatus


async def test_read_task_history(client, task_history):
    """Test task history for a project."""
    task_id = task_history.task_id

    assert task_id is not None

    response = await client.get(f"/tasks/{task_id}/history/")
    data = response.json()[0]

    assert response.status_code == 200
    assert data["id"] == task_history.id
    assert data["username"] == task_history.actioned_by.username


async def test_update_task_status(client, tasks):
    """Test update the task status."""
    task_id = tasks[0].id
    project_id = tasks[0].project_id
    new_status = TaskStatus.LOCKED_FOR_MAPPING

    response = await client.post(
        f"tasks/{task_id}/new-status/{new_status.value}?project_id={project_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert data["status"] == new_status.name


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
