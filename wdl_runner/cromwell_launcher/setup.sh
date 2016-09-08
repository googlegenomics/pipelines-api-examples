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

# Caller must have provided a shell function or command "retry_cmd".

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

