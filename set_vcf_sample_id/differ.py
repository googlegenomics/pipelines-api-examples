#!/usr/bin/env python

# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# differ.py
#
# Simple tool to emit the number of lines that differ between two
# files where the files are expected to be almost identical.
# Sometimes you need a very simple diff where the standard "diff" tool
# is overkill and can fall down on large files ("memory exhausted").
#
# So for example, if you have two files that are expected to have the
# exact same number of lines, but with a few differences in the contents
# of some lines, then this is a low-footprint diff counting tool.

import sys

def main():
  """Entry point to the script."""

  if len(sys.argv) != 3:
    print >> sys.stderr, "Usage: %s [file1] [file2]" % sys.argv[0]
    sys.exit(1)

  left = open(sys.argv[1], "r")
  right = open(sys.argv[2], "r")

  count = 0

  line_left = left.readline()
  while line_left:
    line_right = right.readline()
    if not line_right:
      count += 1
    elif line_left != line_right:
      count += 1

    line_left = left.readline()

  while right.readline():
    count += 1

  print count

if __name__ == "__main__":
  main()

