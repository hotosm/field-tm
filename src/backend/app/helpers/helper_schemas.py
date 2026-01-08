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
"""Schemas for helper endpoints and shared schemas."""

from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class PaginationInfo:
    """Pagination metadata matching frontend expectations."""

    has_next: bool
    has_prev: bool
    page: int
    pages: int
    per_page: int
    total: int
    next_num: Optional[int] = None
    prev_num: Optional[int] = None


@dataclass
class PaginatedResponse(Generic[T]):
    """Generic paginated response wrapper."""

    results: list[T]
    pagination: PaginationInfo
