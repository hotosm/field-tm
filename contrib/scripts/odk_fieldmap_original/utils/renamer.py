# Copyright (c) Humanitarian OpenStreetMap Team
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

#!/bin/python3

"""Accepts
- A directory with forms or QR codes for an Field-TM project.

Renames all of the files with the schema needed by the Field-TM uploader.
"""
import os
import sys


def rename(indir, basename, formtype="buildings"):
    filelist = os.listdir(indir)
    for f in filelist:
        old = os.path.join(indir, f)
        new = os.path.join(indir, f.replace(f"{basename}", f"{basename}_{formtype}_"))
        os.rename(old, new)


if __name__ == "__main__":
    """
    Renames a directory full of files to match Field-TM format
    """

    indir = sys.argv[1]
    basename = sys.argv[2]
    formtype = sys.argv[3]

    print("\nHere goes nothing.\n")
    r = rename(indir, basename, formtype)
    print(r)
