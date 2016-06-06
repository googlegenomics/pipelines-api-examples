ls
#!/bin/bash

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# poll.sh
#
# Polls the completion status of a Google Genomics operation until
# the operation is completed.
#
# When the operation is marked as "done: true", the script emits the
# entire details of the operation.

set -o errexit
set -o nounset

# FUNCTIONS

# get_operation_done_status
#
# Request just the value of the operation top-level "done" field.
# Returns the value in all lower-case.
function get_operation_done_status() {
  gcloud --format='value(done)' \
    alpha genomics operations describe ${OPERATION} \
    | tr 'A-Z' 'a-z'
}
readonly -f get_operation_done_status

# get_operation_all
#
# Requests the full details of the operation in YAML format
function get_operation_all() {
  gcloud --format yaml \
    alpha genomics operations describe ${OPERATION}
}
readonly -f get_operation_all

# MAIN

# Check usage
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 OPERATION-ID <poll-interval-seconds>"
  exit 1
fi

# Extract command-line arguments
readonly OPERATION=${1}
readonly POLL_INTERVAL_SECONDS=${2:-20}  # Default 20 seconds between requests

# Loop until operation complete
while [[ "$(get_operation_done_status)" == "false" ]]; do
  echo "Operation not complete. Sleeping ${POLL_INTERVAL_SECONDS} seconds"
  sleep ${POLL_INTERVAL_SECONDS}
done

# Emit the operation details
echo
echo "Operation complete"
get_operation_all

