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


def test_read_task_history(client, task_history):
    """Test task history for a project."""
    task_id = task_history.task_id

    assert task_id is not None

    response = client.get(f"/tasks/{task_id}/history/")
    data = response.json()[0]

    assert response.status_code == 200
    assert data["id"] == task_history.id
    assert data["username"] == task_history.actioned_by.username


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
