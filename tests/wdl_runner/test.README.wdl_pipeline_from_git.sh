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

# test.README.wdl_pipeline_from_git.sh
#
# Tests the sample pipeline in the wdl_runner/README.md file which is launched
# using wdl_pipeline_from_git.yaml:
#
# 1- Launch the operation
# 2- Poll for completion
# 3- Check the results
#
# The operation typically takes a bit less than 20 minutes to complete, but
# this is very dependent on the runtime conditions including:
#
# * Compute engine quota available in Cloud project 
# * Network connectivity, server availability, and download throughput for:
#   * debian mirrors
#   * github
#   * Cloud Storage
#
# So we set a 60 minute timeout for the operation. If the timeout occurs,
# an attempt will be made to kill the operation.

# Assume the following are set:
#  YOUR_BUCKET

set -o errexit
set -o nounset

readonly SCRIPT_DIR=$(dirname "${0}")
readonly REPO_ROOT=$(cd ${SCRIPT_DIR}/../../ && pwd) 

# Launch the script from the wdl_runner directory (as the README indicates)
cd ${REPO_ROOT}/wdl_runner

readonly LOGGING="gs://${YOUR_BUCKET}/pipelines-api-examples/wdl_runner/logging"
readonly OUTPUTS="gs://${YOUR_BUCKET}/pipelines-api-examples/wdl_runner/output"
readonly WORKSPACE="gs://${YOUR_BUCKET}/pipelines-api-examples/wdl_runner/workspace"

# Don't launch the test if the output or workspace paths already exist
echo "Checking if workspace directory exists"
if gsutil ls ${WORKSPACE} 2>/dev/null; then
  2>&1 echo "WORKSPACE path exists: ${WORKSPACE}"
  2>&1 echo "Remove contents and rerun."
  exit 1
fi
echo "Checking if output directory exists"
if gsutil ls ${OUTPUTS} 2>/dev/null; then
  2>&1 echo "Output path exists: ${OUTPUTS}"
  2>&1 echo "Remove contents and rerun."
  exit 1
fi

# 1- Launch the operation
readonly OPERATION_ID=$(\
  gcloud \
    alpha genomics pipelines run \
    --pipeline-file workflows/wdl_pipeline_from_git.yaml \
    --zones us-east1-d \
    --logging "${LOGGING}" \
    --inputs-from-file WDL=workflows/vcf_chr_count/vcf_chr_count.wdl \
    --inputs-from-file WORKFLOW_INPUTS=workflows/vcf_chr_count/vcf_chr_count.sample.inputs.json \
    --inputs-from-file WORKFLOW_OPTIONS=workflows/common/basic.jes.us.options.json \
    --inputs WORKSPACE="${WORKSPACE}" \
    --inputs OUTPUTS="${OUTPUTS}" \
    --format 'value(name)'
)

echo "Started operation ${OPERATION_ID}"

# 2- Poll for completion
readonly MONITOR_SH="${REPO_ROOT}/wdl_runner/tools/monitor_wdl_pipeline.sh"
readonly MONITOR_INTERVAL=60
readonly MONITOR_MAX=$((60 * 60))
if ! "${MONITOR_SH}" \
        "${OPERATION_ID}" "${MONITOR_INTERVAL}" "${MONITOR_MAX}"; then
  gcloud --quiet alpha genomics operations cancel "${OPERATION_ID}"
  exit 1
fi

# 3- Check the results
readonly RESULT_EXPECTED=$(cat <<EOF
chrM.vcf 197
chrX.vcf 4598814
chrY.vcf 653100
EOF
)

readonly RESULT=$(gsutil cat "${OUTPUTS}"/output.txt)
if ! diff <(echo "${RESULT_EXPECTED}") <(echo "${RESULT}"); then
  echo "Output file does not match expected"
  exit 1
fi

echo
echo "Output file matches expected:"
echo "*****************************"
echo "${RESULT}"
echo "*****************************"
