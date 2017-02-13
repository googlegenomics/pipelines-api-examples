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

# cwl_runner.sh
#
# From your shell prompt, launch a Google Compute Engine VM to run
# a Common Workflow Language (CWL) workflow.

# TODO: Update URLs to the real location where these will live
STARTUP_SCRIPT_URL="gs://jbingham-scratch/cwl/cwl_startup_script2.sh"

HELP=
WORKFLOW_PATH=
SETTINGS_PATH=
INPUT=
INPUT_RECURSIVE=
OUTPUT=
KEEP_ALIVE=
DISK_SIZE=200
MACHINE_TYPE="n1-standard-1"
PREEMPTIBLE=
ZONE=
OPERATION_ID=$$

read -r -d '' HELP_MESSAGE << EOM

USAGE: $0 [args]

-h --help
  Show help message and exit

Common options:
-w --workflow-file PATH
  REQUIRED. The absolute path to the .cwl workflow definition file in Cloud Storage.
-s --settings-file PATH
  REQUIRED. The absolute path to the .json settings file in Cloud Storage.
-i --input GCS_PATH1[,GCS_PATH2,...]
  The absolute path(s) in Cloud Storage to the file(s) that must be copied to the VM's local disk. 
-r --input-recursive GCS_PATH1[,GCS_PATH2,...]
  The absolute path(s) in Cloud Storage to the folder(s) that must be copied to the VM's local disk. 
-m --machine-type STRING
  The Google Compute Engine VM machine type name. Default: ${MACHINE_TYPE}.
-o --output GCS_PATH
  REQUIRED. The path where the CWL outputs and log files will be copied after the workflow completes.

Other options:
-d --disk-size INT
  The disk size in Gb. Default: ${DISK_SIZE}.
-k --keep-alive
  Leave the VM running after the workflow completes or fails so that you can ssh in for debugging.
-p --preemptible
  Run with a preemptible VM that costs less but may be terminated before finishing.
-z --zone STRING
  The zone to launch the VM and disk in. If omitted, your default project zone will be used.

EOM

# Parse command-line
while [[ $# -gt 0 ]] 
do
key="$1"

case $key in
  -h|--help)
  HELP="true"
  ;;
  -w|--workflow-file)
  WORKFLOW_FILE="$2"
  shift
  ;;
  -s|--settings-file)
  SETTINGS_FILE="$2"
  shift
  ;;
  -i|--input)
  INPUT="$2"
  shift
  ;;
  -r|--input-recursive)
  INPUT_RECURSIVE="$2"
  shift
  ;;
  -o|--output)
  OUTPUT="$2"
  shift
  ;;
  -d|--disk-size)
  DISK_SIZE="$2"
  shift
  ;;
  -k|--keep-alive)
  KEEP_ALIVE="true"
  ;;
  -p|--preemptible)
  PREEMPTIBLE="--preemptible"
  ;;
  -m|--machine-type)
  MACHINE_TYPE="$2"
  shift
  ;;
  -z|--zone)
  ZONE="--zone $2"
  shift
  ;;
  *)
  # unknown option
  ;;
esac
shift
done

set -e errexit

if [[ ${HELP} ]]; then
  echo "${HELP_MESSAGE}"
  exit 1
fi

if [[ -z "${WORKFLOW_FILE}" || -z "${SETTINGS_FILE}" || -z "${OUTPUT}" ]]; then
  echo "Error: Missing required argument(s)."
  echo "${HELP_MESSAGE}"
  exit 1
fi

DISK_NAME="cwl-disk-${OPERATION_ID}"
DISK_CMD="gcloud compute disks create ${DISK_NAME} ${ZONE} --size ${DISK_SIZE}"

VM_NAME="cwl-vm-${OPERATION_ID}"
VM_CMD="gcloud compute instances create ${VM_NAME} \
--disk name=${DISK_NAME},device-name=${DISK_NAME},auto-delete=yes \
--machine-type ${MACHINE_TYPE} \
--scopes storage-rw,compute-rw \
${ZONE} \
${PREEMPTIBLE} \
--metadata \
startup-script-url=${STARTUP_SCRIPT_URL},\
operation-id=${OPERATION_ID},\
workflow-file=${WORKFLOW_FILE},\
settings-file=${SETTINGS_FILE},\
input=\"${INPUT}\",\
input-recursive=\"${INPUT_RECURSIVE}\",\
output=${OUTPUT},\
keep-alive=${KEEP_ALIVE}"

echo "Generating script commands and writing to file"
TMP_PREFIX=".tmp-"
TMP_SCRIPT="${TMP_PREFIX}script-${OPERATION_ID}.sh"
echo "#!/bin/bash" > ${TMP_SCRIPT}
echo $DISK_CMD >> ${TMP_SCRIPT}
echo $VM_CMD >> ${TMP_SCRIPT}

echo "Copying script to the output path in Cloud Storage"
gsutil cp ${TMP_SCRIPT} ${OUTPUT}/${TMP_SCRIPT/${TMP_PREFIX}/}
rm ${TMP_SCRIPT}

echo "Creating Google Compute Engine VM and disk"
echo $DISK_CMD
$DISK_CMD

echo $VM_CMD
$VM_CMD

cat << EOM
Congratulations! Your job is running.

To monitor your job from the cloud console, go to:
https://console.cloud.google.com/compute/instances

To monitor your job from the command-line, run:
gcloud compute instances describe ${VM_NAME} ${ZONE}

While your VM is running, you can see it in the console and describe it from the command-line.
When the workflow completes, the VM will no longer be found.

To debug a failed run, look at the log files in your output directory. 
From the cloud console, go to:
https://console.cloud.google.com/storage/browser

From the command-line:
gsutil cat ${OUTPUT}/stderr-${OPERATION_ID}.txt | less
gsutil cat ${OUTPUT}/stdout-${OPERATION_ID}.txt | less

For additional debugging, you can rerun this script with --keep-alive and ssh into the VM.
If you use --keep-alive, you will need to manually delete the VM to avoid charges.
EOM
