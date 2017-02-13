#!/bin/bash
#
# Copyright 2017 Google Inc. All Rights Reserved.
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

# cwl_shutdown_script.sh
#
# This is the shutdown script that runs on Compute Engine before the VM shuts down.

METADATA_URL="http://metadata.google.internal/computeMetadata/v1/instance"
METADATA_HEADERS="Metadata-Flavor: Google"
OPERATION_ID=$(curl "${METADATA_URL}/attributes/operation-id" -H "${METADATA_HEADERS}")
OUTPUT=$(curl "${METADATA_URL}/attributes/output" -H "${METADATA_HEADERS}")
STATUS_LOCAL="/tmp/status-${OPERATION_ID}.txt"

STDOUT=/tmp/stdout-${OPERATION_ID}.txt
STDERR=/tmp/stderr-${OPERATION_ID}.txt

echo "$(date)"
echo "Copying stdout and stderr to Cloud Storage"
CMD="gsutil -m cp ${STDOUT} ${STDERR} ${OUTPUT}/"
echo $CMD
$CMD

echo "Checking job status"
STATUS=$( gsutil cat ${STATUS_LOCAL} )

if [[ ${STATUS} == "RUNNING" ]]; then
  echo "VM terminated manually or due to preemption"
  STATUS_LOCAL="/tmp/status-${OPERATION_ID}.txt"
  echo "TERMINATED" > ${STATUS_LOCAL}
  STATUS_FILE=$(curl "${METADATA_URL}/attributes/status-file" -H "${METADATA_HEADERS}")
  gsutil cp ${STATUS_LOCAL} ${STATUS_FILE}
fi
