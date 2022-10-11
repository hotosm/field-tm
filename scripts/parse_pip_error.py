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
