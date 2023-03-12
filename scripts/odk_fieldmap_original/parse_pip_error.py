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

#!/usr/bin/python3
import os
import re
import sys


def parse_error(string, version):
    # split the error message into a list of version numbers
    possibles = string.split(',')

    # Clean the strings in the list
    possibles = [text.strip() for text in possibles]

    # Find those beginning with the correct first three numbers
    regex = re.compile('^' + version)
    filtered = list(filter(regex.search, possibles))
    print(filtered)
    print('\n')

    def sortbylastnum(instring):
        nums = instring.split('.')
        last = int(nums[len(nums) - 1])
        return last

    sortedcandidates = sorted(filtered, key=sortbylastnum)

    with open('pygdalversion.txt', 'w') as outfile:
        outfile.write(sortedcandidates[-1])


if __name__ == "__main__":
    parse_error(sys.argv[1], sys.argv[2])
