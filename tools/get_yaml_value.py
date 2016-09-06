#!/usr/bin/python

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

# get_yaml_value.py
#
# Utility script for extracting values from YAML.
# This will typically be called from shell scripts, which typically
# have fairly hacky ways of extracting values from YAML.
#
# An example usage would be where a shell script has YAML output from
# a gcloud command for an genomics operation and needs to extract fields:
#
#  OP=$(gcloud --format=yaml alpha genomics operations describe "${OP_ID}")
#  CTIME=$(python tools/get_yaml_value.py "${OP}" "metadata.createTime")
#  ETIME=$(python tools/get_yaml_value.py "${OP}" "metadata.endTime")
#
# Note that gcloud directly supports extracting fields, so the above could also
# be:
#
#  CTIME=$(gcloud alpha genomics operations describe "${OP_ID}"
#           --format='value(metadata.createTime)')
#  ETIME=$(gcloud alpha genomics operations describe "${OP_ID}"
#          --format='value(metadata.endTime)')
#
# but then requires an API calls to get each value.
#
# Note that if the value requested does not exist in the YAML, this script
# exits with an error code (1).

from __future__ import print_function

import sys
import yaml

if len(sys.argv) != 3:
  print("Usage: %s [yaml] [field]" % sys.argv[0], file=sys.stderr)
  sys.exit(1)

def main(yaml_string, field):
  data = yaml.load(yaml_string)

  # field is expected to be period-separated: foo.bar.baz
  fields = field.split('.')

  # Walk the list of fields and check that the key exists.
  curr = data
  for key in fields:
    if key in curr:
      curr = curr[key]
    else:
      sys.exit(1)
  
  print(curr)

if __name__ == '__main__':
  main(sys.argv[1], sys.argv[2])
