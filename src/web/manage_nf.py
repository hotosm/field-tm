# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
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


import sys
import os
from flask.cli import FlaskGroup


sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

# must come after sys.path.append line (therefore this file is excluded from auto formatting by vscode)
from main_flask import app

cli = FlaskGroup(app)


if __name__ == "__main__":
    cli()
