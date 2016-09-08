#!/bin/bash

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

# This script should be kept in-sync with the Dockerfile located in
# the same src directory.

set -o errexit
set -o nounset

# Caller of the setup script can configure the extent to which any
# single setup command will be retried on failure by setting the
# environment variables:
#
#  SETUP_RETRY_INTERVAL_SECONDS (default 10)
#  SETUP_RETRY_MAX_SECONDS      (default 300)
#
readonly RETRY_INTERVAL_SECONDS=${SETUP_RETRY_INTERVAL_SECONDS:-10}
readonly RETRY_MAX_SECONDS=${SETUP_RETRY_MAX_SECONDS:-5*60}

# retry_cmd
#
# Any operation that is dependent on internet connectivity and server
# availability is vulnerable to intermittent failure.
#
# This function will sleep a designated interval between failures
# (retry_interval).
# The aggregated sleep time is capped at a designated maximum (retry_max).
function retry_cmd () {
  local cmd="${1}"
  local retry_interval="${2:-${RETRY_INTERVAL_SECONDS}}"
  local retry_max="${3:-${RETRY_MAX_SECONDS}}"

  echo "RUNNING: ${cmd}"
  echo

  retry_time=0
  while ((retry_time < retry_max)); do
    if eval "${cmd}"; then
      echo
      echo "SUCCEEDED: ${cmd}"

      return
    fi

    if ((retry_time < retry_max)); then
      echo "SLEEP: ${retry_interval} seconds before retrying"
      sleep ${retry_interval}
      ((retry_time+=retry_interval))
    fi
  done

  echo "Total retry time (${retry_time}) reached max ($((retry_max))) seconds"
  echo "FAILED: ${cmd}"
  exit 1
}
readonly -f retry_cmd

# Assumes: FROM java:openjdk-8-jre

# Install python
apt-get update && \
retry_cmd 'apt-get install python --yes' && \
apt-get clean && \
rm -rf /var/lib/apt/lists/*

# Install gcloud
# See https://cloud.google.com/sdk/
if [[ ! -e /root/google-cloud-sdk ]]; then
  retry_cmd 'curl https://sdk.cloud.google.com | bash'
fi

# Add the install location explicitly to the path (for non-interactive shells)
export PATH=/root/google-cloud-sdk/bin:$PATH

# Install pip for the next two steps...
apt-get update && \
retry_cmd 'apt-get install python-pip --yes'

# Install Python "requests" (for cromwell_driver.py) package
retry_cmd 'pip install requests'

# Install Google Python client (for file_util.py) package
retry_cmd 'pip install --upgrade google-api-python-client'

# Remove pip
apt-get remove --yes python-pip && \
apt-get clean && \
rm -rf /var/lib/apt/lists/*

# Copy the wdl_runner python and dependencies
mkdir /wdl_runner
cp cromwell_driver.py \
   file_util.py \
   sys_util.py \
   wdl_outputs_util.py \
   wdl_runner.py \
   wdl_runner.sh \
   /wdl_runner/
chmod u+x /wdl_runner/wdl_runner.sh

# Copy Cromwell and the Cromwell conf template
mkdir /cromwell
(cd /cromwell && \
    retry_cmd 'curl -L -O https://github.com/broadinstitute/cromwell/releases/download/0.19.3/cromwell-0.19.3.jar')
ln /cromwell/cromwell-0.19.3.jar /cromwell/cromwell.jar
cp jes_template.conf /cromwell/

# Set up the runtime environment
export CROMWELL=/cromwell/cromwell.jar
export CROMWELL_CONF=/cromwell/jes_template.conf

