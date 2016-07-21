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

set -o errexit
set -o nounset

readonly INPUT_PATH=/pipeline/input

# WDL, INPUTS, and OPTIONS file contents are all passed into
# the pipeline as environment variables - write them out as
# files.
mkdir -p "${INPUT_PATH}"
echo "${WDL}" > "${INPUT_PATH}/wf.wdl"
echo "${WORKFLOW_INPUTS}" > "${INPUT_PATH}/wf.inputs.json"
echo "${WORKFLOW_OPTIONS}" > "${INPUT_PATH}/wf.options.json"

# Set the working directory to the location of the scripts
readonly SCRIPT_DIR=$(dirname $0)
cd "${SCRIPT_DIR}"

# Execute the wdl_runner
python -u wdl_runner.py \
 --wdl "${INPUT_PATH}"/wf.wdl \
 --workflow-inputs "${INPUT_PATH}"/wf.inputs.json \
 --working-dir "${WORKSPACE}" \
 --workflow-options "${INPUT_PATH}"/wf.options.json \
 --output-dir "${OUTPUTS}"

