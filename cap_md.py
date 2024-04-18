#!/usr/bin/env python3

"""Convert a csv containing CAP checklist items to a markdown file

Headers are:

Requirement (ID)
Policy/Procedure
Phase
Subject Header
Requirement
Note
Evidence of Compliance

"""

import os
import sys
import argparse
import csv
import textwrap


def main(arguments):

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('infile', help="Input file", type=argparse.FileType('r'))
    parser.add_argument('-o', '--outfile', help="Output file",
                        default=sys.stdout, type=argparse.FileType('w'))

    args = parser.parse_args(arguments)

    reader = csv.DictReader(args.infile)
    for row in reader:
        row = {k: textwrap.dedent(v) for k, v in row.items()}

        entry = f"""
# {row['Requirement (ID)']}: {row['Subject Header']}

Policy/Procedure: {row['Policy/Procedure']}
Phase: {row['Phase']}

## Requirement
{row['Requirement']}

## Note
{row['Note']}

## Evidence of Compliance
{row['Evidence of Compliance']}
        """

        args.outfile.write(textwrap.dedent(entry.strip()))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

