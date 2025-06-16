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

"""Pydantic models for data submissions."""

from typing import Optional

from pydantic import AwareDatetime, BaseModel
from pydantic.functional_serializers import field_serializer

from app.db.enums import ProjectStatus, ReviewStateEnum
from app.db.postgis_utils import timestamp


class PaginationInfo(BaseModel):
    """Pagination JSON return."""

    has_next: bool
    has_prev: bool
    next_num: Optional[int]
    page: int
    pages: int
    prev_num: Optional[int]
    per_page: int
    total: int


class PaginatedSubmissions(BaseModel):
    """Paginated Submissions."""

    results: list
    pagination: PaginationInfo


class ReviewStateIn(BaseModel):
    """Update to the review state of a submission."""

    instance_id: str
    review_state: ReviewStateEnum


class ReviewStateOut(BaseModel):
    """The response from ODK Central on review state update."""

    instanceId: str  # noqa: N815
    submitterId: int  # noqa: N815
    deviceId: str  # noqa: N815
    createdAt: str  # noqa: N815
    updatedAt: str  # noqa: N815
    reviewState: str  # noqa: N815


class SubmissionDashboard(BaseModel):
    """Submission details dashboard for a project."""

    slug: str
    organisation_name: str
    total_tasks: int
    created_at: AwareDatetime
    organisation_id: Optional[int] = None
    organisation_logo: Optional[str] = None
    total_submissions: Optional[int] = None
    total_contributors: Optional[int] = None
    last_active: Optional[AwareDatetime] = None
    status: Optional[ProjectStatus] = None

    @field_serializer("last_active")
    def get_last_active(self, last_active: Optional[AwareDatetime]) -> str:
        """Date of last activity on project."""
        if last_active is None:
            return None
        if isinstance(last_active, str):
            return last_active

        current_date = timestamp()
        time_difference = current_date - last_active
        days_difference = time_difference.days

        if days_difference == 0:
            return "today"
        elif days_difference == 1:
            return "yesterday"
        elif days_difference < 7:
            return f"{days_difference} day{'s' if days_difference > 1 else ''} ago"
        else:
            return last_active.strftime("%d %b %Y")
