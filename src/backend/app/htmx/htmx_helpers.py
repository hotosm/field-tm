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

"""Shared helper utilities for HTMX route handlers."""


def callout(variant: str, msg: str) -> str:
    """Build a wa-callout HTML snippet.

    Args:
        variant: The callout variant (e.g. 'danger', 'success', 'warning', 'info').
        msg: The message text to display inside the callout.

    Returns:
        An HTML string containing a <wa-callout> element.
    """
    return f'<wa-callout variant="{variant}"><span>{msg}</span></wa-callout>'
