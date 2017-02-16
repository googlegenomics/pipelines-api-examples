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

# cwl_shutdown.sh
#
# This is the shutdown script that runs on Compute Engine before the VM shuts down.

echo "$(date)"
echo "Running shutdown script"

readonly METADATA_URL="http://metadata.google.internal/computeMetadata/v1/instance"
readonly METADATA_HEADERS="Metadata-Flavor: Google"
readonly OUTPUT=$(curl "${METADATA_URL}/attributes/output" -H "${METADATA_HEADERS}")
readonly OPERATION_ID=$(curl "${METADATA_URL}/attributes/operation-id" -H "${METADATA_HEADERS}")
readonly STATUS_LOCAL="/tmp/status-${OPERATION_ID}.txt"

readonly STDOUT=/tmp/stdout-${OPERATION_ID}.txt
readonly STDERR=/tmp/stderr-${OPERATION_ID}.txt

echo "$(date)"
echo "Copying stdout and stderr to Cloud Storage"
CMD="gsutil -m cp ${STDOUT} ${STDERR} ${OUTPUT}/"
echo "${CMD}"
${CMD}

# Typically shutdown will cause a running job to fail and status will be set to FAILED
# In case the status is left as RUNNING, set it to FAILED
STATUS="$(cat ${STATUS_LOCAL})"
echo "Status ${STATUS}"

if [[ "${STATUS}" == "RUNNING" ]]; then
  echo "Setting status to FAILED"
  echo "FAILED" > ${STATUS_LOCAL}
  STATUS_FILE=$(curl "${METADATA_URL}/attributes/status-file" -H "${METADATA_HEADERS}")
  gsutil cp ${STATUS_LOCAL} ${STATUS_FILE}
fi
