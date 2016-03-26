#!/usr/bin/env python

# Copyright 2016 Google Inc. All Rights Reserved.
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

# set_vcf_sample_id.py
#
# This script processes a single sample VCF file and replaces the
# sample ID in the header line.
#
# This could be replaced (almost) with a one-line sed script:
#
#   sed -e 's/\(^#CHROM\t.*\t\)original$/\1new/' \
#
# What this script adds is a little more control, notably with error
# handling. sed will not report the number of changes, so to determine
# if a change was made, you'd need to make a second pass over the file.
#
# This script reads from stdin and writes to stdout.
#
# Usage:
#   python set_vcf_sample_id.py original_id new_id
#
# If the original_id is specified, it will be verified before making the change.
# If the original_id is set to "", verification will be skipped.

import sys

def main():
  """Entry point to the script."""

  if len(sys.argv) != 3:
    print >> sys.stderr, 'Usage: %s original_id new_id' % sys.argv[0]
    sys.exit(1)

  original_id = sys.argv[1]
  new_id = sys.argv[2]

  lines_processed = 0
  lines_changed = 0
  for line in sys.stdin:
    lines_processed = lines_processed + 1
    # Only line we care about is the #^CHROM line
    if line.startswith('#CHROM\t'):
      fields = line.rstrip('\n').split('\t')

      # If an "original_id" was specified, verify that is what is in the file
      if original_id:
        curr_id = fields[-1]
        if curr_id != original_id:
          print >> sys.stderr, \
            "ERROR: Current sample ID does not match expected: %s != %s\n" % (
            curr_id, original_id)
          sys.exit(1)

      # Set the new value into the fields array and recreate the line
      fields[-1] = new_id
      line = '\t'.join(fields) + '\n'

      lines_changed = lines_changed + 1

    # Emit the current line
    sys.stdout.write(line)

  # Emit some statistics to stderr
  print >> sys.stderr, "Total lines: %d" % lines_processed
  print >> sys.stderr, "Changed lines: %d" % lines_changed

  if lines_changed != 1:
    print >> sys.stderr, "Changed lines is not 1"
    sys.exit(1)
    
if __name__ == "__main__":
  main()

