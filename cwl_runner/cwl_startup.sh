#!/bin/bash

# Copyright 2017 Google Inc.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

# cwl_startup_script.sh
#
# This is the startup script that runs on Compute Engine to run
# a Common Workflow Language (CWL) workflow with cwltool.

readonly METADATA_URL="http://metadata.google.internal/computeMetadata/v1/instance"
readonly METADATA_HEADERS="Metadata-Flavor: Google"
readonly OPERATION_ID=$(curl "${METADATA_URL}/attributes/operation-id" -H "${METADATA_HEADERS}")
readonly OUTPUT=$(curl "${METADATA_URL}/attributes/output" -H "${METADATA_HEADERS}")
readonly STATUS_FILE=$(curl "${METADATA_URL}/attributes/status-file" -H "${METADATA_HEADERS}")
readonly STATUS_LOCAL="/tmp/status-${OPERATION_ID}.txt"
STATUS="RUNNING"

echo "$(date)"
echo "Status ${STATUS}"
echo "${STATUS}" > ${STATUS_LOCAL}
gsutil cp ${STATUS_LOCAL} ${STATUS_FILE}

echo "Redirecting stdout and stderr"
readonly STDOUT=/tmp/stdout-${OPERATION_ID}.txt
readonly STDERR=/tmp/stderr-${OPERATION_ID}.txt
exec >  >(tee -ia ${STDOUT})
exec 2> >(tee -ia ${STDERR} >&2)

echo "$(date)"
echo "Running startup script"

echo "Initializing variables"
readonly WORKFLOW_FILE=$(curl "${METADATA_URL}/attributes/workflow-file" -H "${METADATA_HEADERS}")
readonly SETTINGS_FILE=$(curl "${METADATA_URL}/attributes/settings-file" -H "${METADATA_HEADERS}")
readonly INPUT=$(curl "${METADATA_URL}/attributes/input" -H "${METADATA_HEADERS}")
readonly INPUT_RECURSIVE=$(curl "${METADATA_URL}/attributes/input-recursive" -H "${METADATA_HEADERS}")
readonly DISK_NAME=google-$(curl "${METADATA_URL}/disks/1/device-name" -H "${METADATA_HEADERS}")
readonly RUNNER=$(curl "${METADATA_URL}/attributes/runner" -H "${METADATA_HEADERS}")

echo "$(date)"
echo "Mounting and formatting disk"
readonly MOUNT_POINT="/mnt/data"
sudo mkfs.ext4 -F -E lazy_itable_init=0,lazy_journal_init=0,discard /dev/disk/by-id/${DISK_NAME}
sudo mkdir -p ${MOUNT_POINT}
sudo mount -o discard,defaults /dev/disk/by-id/${DISK_NAME} ${MOUNT_POINT}
sudo chmod 777 ${MOUNT_POINT}

echo "$(date)"
echo "Creating folders for workflow inputs and outputs"
readonly INPUT_FOLDER="${MOUNT_POINT}/input"
readonly OUTPUT_FOLDER="${MOUNT_POINT}/output"
readonly TMP_FOLDER="${MOUNT_POINT}/tmp"
sudo mkdir -m 777 -p "${INPUT_FOLDER}"
sudo mkdir -m 777 -p "${OUTPUT_FOLDER}"
sudo mkdir -m 777 -p "${TMP_FOLDER}"

echo "$(date)"
echo "Copying input files to local disk"
while IFS=';' read -ra URL_LIST; do
  for URL in "${URL_LIST[@]}"; do
    URL=$(echo ${URL} | tr -d '"')  # Remove quotes
    URL_LOCAL="${INPUT_FOLDER}/$(dirname ${URL//:\//})"
    CMD="mkdir -p ${URL_LOCAL}"
    echo "${CMD}"
    ${CMD}
    CMD="gsutil -m -o GSUtil:parallel_composite_upload_threshold=150M cp ${URL} ${URL_LOCAL}"
    echo "${CMD}"
    ${CMD}
  done
done <<< "${INPUT}"

echo "$(date)"
echo "Recursively copying input folders to local disk"
while IFS=';' read -ra URL_LIST; do
  for URL in "${URL_LIST[@]}"; do
    URL=$(echo ${URL} | tr -d '"')  # Remove quotes
    URL_LOCAL="${INPUT_FOLDER}/${URL//:\//}"
    CMD="mkdir -p ${URL_LOCAL}"
    echo "${CMD}"
    ${CMD}
    CMD="gsutil -m -o GSUtil:parallel_composite_upload_threshold=150M rsync -r ${URL}/ ${URL_LOCAL}"
    echo "${CMD}"
    ${CMD}
  done
done <<< "${INPUT_RECURSIVE}"

echo "Copying workflow file to local disk"
readonly WORKFLOW_LOCAL="${INPUT_FOLDER}/${WORKFLOW_FILE//:\//}"
CMD="mkdir -p $(dirname ${WORKFLOW_LOCAL})"
echo "${CMD}"
${CMD}
CMD="gsutil -m cp ${WORKFLOW_FILE} ${WORKFLOW_LOCAL}"
echo "${CMD}"
${CMD}

echo "Copying settings file to local disk"
readonly SETTINGS_LOCAL="${INPUT_FOLDER}/${SETTINGS_FILE//:\//}"
CMD="mkdir -p $(dirname ${SETTINGS_LOCAL})"
echo "${CMD}"
${CMD}
CMD="gsutil -m cp ${SETTINGS_FILE} ${SETTINGS_LOCAL}"
echo "${CMD}"
${CMD}

echo "$(date)"
echo "Installing Docker and CWL runner ${RUNNER}"

if [[ ${RUNNER} == "cwltool" ]]; then
  sudo apt-get update
  sudo apt-get --yes install apt-utils docker.io gcc python-dev python-setuptools ca-certificates
  sudo easy_install -U virtualenv
  sudo systemctl start docker.service

  echo "$(date)"
  echo "Starting virtualenv"
  virtualenv cwl
  source cwl/bin/activate
  pip install cwlref-runner

  echo "$(date)"
  echo "Running the CWL workflow"
  export HOME="/root"  # cwl runner needs it; startup scripts don't have it defined
  cd "${INPUT_FOLDER}"
  CMD="cwl-runner --outdir ${OUTPUT_FOLDER} --tmpdir-prefix ${TMP_FOLDER} --tmp-outdir-prefix ${TMP_FOLDER} ${WORKFLOW_LOCAL} ${SETTINGS_LOCAL}"
  echo "${CMD}"
  ${CMD} && STATUS="COMPLETED" || STATUS="FAILED"

  deactivate

elif [[ ${RUNNER} == "rabix" ]]
then
  sudo apt-get --yes install openjdk-8-jre
  sudo apt-get update
  sudo apt-get --yes install apt-utils docker.io gcc ca-certificates
  sudo systemctl start docker.service

  cd "${INPUT_FOLDER}"
  wget https://github.com/rabix/bunny/releases/download/v1.0.0-rc2/rabix-1.0.0-rc2.tar.gz && tar -xvf rabix-1.0.0-rc2.tar.gz
  RABIX="${INPUT_FOLDER}/rabix-1.0.0-rc2/rabix"

  echo "$(date)"
  echo "Running the CWL workflow"
  export HOME="/root"  # cwl runner needs it; startup scripts don't have it defined
  CMD="${RABIX} --basedir ${OUTPUT_FOLDER} --outdir ${OUTPUT_FOLDER} --tmpdir-prefix ${TMP_FOLDER} --tmp-outdir-prefix ${TMP_FOLDER} ${WORKFLOW_LOCAL} ${SETTINGS_LOCAL}"
  echo "${CMD}"
  ${CMD} && STATUS="COMPLETED" || STATUS="FAILED"

else
  >&2 echo "Error. Unknown CWL runner: ${RUNNER}"
fi

echo "$(date)"
echo "Finished running CWL"
echo "Copying output files to Cloud Storage"
CMD="gsutil -m -o GSUtil:parallel_composite_upload_threshold=150M rsync -r ${OUTPUT_FOLDER}/ ${OUTPUT}/"
echo "${CMD}"
${CMD}

echo "$(date)"
echo "Status ${STATUS}"
echo ${STATUS} > ${STATUS_LOCAL}
CMD="gsutil cp ${STATUS_LOCAL} ${STATUS_FILE}"
echo "${CMD}"
${CMD}

KEEP_ALIVE=$(curl "${METADATA_URL}/attributes/keep-alive" -H "${METADATA_HEADERS}")
if [[ "${KEEP_ALIVE}" = "true" ]]; then
  echo "$(date)"
  echo "Leaving VM running because keep-alive == true"
  echo "Copying stdout and stderr to Cloud Storage"
  CMD="gsutil -m cp ${STDOUT} ${STDERR} ${OUTPUT}/"
  echo "${CMD}"
  ${CMD}
else
  echo "Shutting down and deleting the VM"
  ZONE=$(curl "${METADATA_URL}/zone" -H "${METADATA_HEADERS}")
  INSTANCE_NAME=$(curl "${METADATA_URL}/name" -H "${METADATA_HEADERS}")
  CMD="sudo gcloud --quiet compute instances delete --zone ${ZONE} ${INSTANCE_NAME}"
  echo "${CMD}"
  ${CMD}
fi
