#!/bin/bash

# Copyright 2017 Google Inc.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

# cwl_runner.sh
#
# From your shell prompt, launch a Google Compute Engine VM to run
# a Common Workflow Language (CWL) workflow with cwltool.

declare WORKFLOW_PATH=
declare SETTINGS_PATH=
declare INPUT=
declare INPUT_RECURSIVE=
declare OUTPUT=
declare KEEP_ALIVE=
declare DISK_SIZE=200
declare MACHINE_TYPE="n1-standard-1"
declare PREEMPTIBLE=
declare RUNNER="cwltool"
declare ZONE=
readonly OPERATION_ID=$$

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
-I --input-recursive GCS_PATH1[,GCS_PATH2,...]
  The absolute path(s) in Cloud Storage to the folder(s) that must be copied to the VM's local disk. 
-m --machine-type STRING
  The Google Compute Engine VM machine type name. Default: ${MACHINE_TYPE}.
-o --output GCS_PATH
  REQUIRED. The path where CWL outputs and logs will be copied after the workflow completes.

Other options:
-d --disk-size INT
  The disk size in Gb. Default: ${DISK_SIZE}.
-k --keep-alive
  Leave the VM running after the workflow completes or fails so that you can ssh in for debugging.
-p --preemptible
  Run with a preemptible VM that costs less but may be terminated before finishing.
-r --runner STRING
  The CWL runner to use. Values can be "cwltool" or "rabix". Default: ${RUNNER}.
-z --zone STRING
  The zone to launch the VM and disk in. If omitted, your default project zone will be used.

EOM

set -o errexit
set -o nounset

# Parse command-line
while [[ $# -gt 0 ]]; do
  KEY="$1"

  case ${KEY} in
    -h|--help)
    echo "${HELP_MESSAGE}"
    exit 1
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
    -I|--input-recursive)
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
    -m|--machine-type)
    MACHINE_TYPE="$2"
    shift
    ;;
    -p|--preemptible)
    PREEMPTIBLE="--preemptible"
    ;;
    -z|--zone)
    ZONE="--zone $2"
    shift
    ;;
    -r|--runner)
    RUNNER="$2"
    shift
    ;;
    *)
    # unknown option
    ;;
  esac
  shift
done

if [[ -z "${WORKFLOW_FILE}" || -z "${SETTINGS_FILE}" || -z "${OUTPUT}" ]]; then
  >&2 echo "Error: Workflow file, settings file, and output are required."
  exit 1
fi

readonly DISK_NAME="cwl-disk-${OPERATION_ID}"
readonly DISK_CMD="gcloud compute disks create ${DISK_NAME} ${ZONE} --size ${DISK_SIZE}"

readonly SCRIPT_DIR="$( cd $( dirname ${BASH_SOURCE[0]} ) && pwd )"

readonly STARTUP_SCRIPT_NAME="cwl_startup.sh"
readonly STARTUP_SCRIPT="${SCRIPT_DIR}/${STARTUP_SCRIPT_NAME}"
readonly STARTUP_SCRIPT_URL="${OUTPUT}/${STARTUP_SCRIPT_NAME%.*}-${OPERATION_ID}.sh"

readonly SHUTDOWN_SCRIPT_NAME="cwl_shutdown.sh"
readonly SHUTDOWN_SCRIPT="${SCRIPT_DIR}/${SHUTDOWN_SCRIPT_NAME}"
readonly SHUTDOWN_SCRIPT_URL="${OUTPUT}/${SHUTDOWN_SCRIPT_NAME%.*}-${OPERATION_ID}.sh"

readonly STATUS_FILE="${OUTPUT}/status-${OPERATION_ID}.txt"

readonly VM_NAME="cwl-vm-${OPERATION_ID}"
readonly VM_CMD="gcloud compute instances create ${VM_NAME} \
--disk name=${DISK_NAME},device-name=${DISK_NAME},auto-delete=yes \
--machine-type ${MACHINE_TYPE} \
--scopes storage-rw,compute-rw \
${ZONE} \
${PREEMPTIBLE} \
--metadata \
startup-script-url=${STARTUP_SCRIPT_URL},\
shutdown-script-url=${SHUTDOWN_SCRIPT_URL},\
operation-id=${OPERATION_ID},\
workflow-file=${WORKFLOW_FILE},\
settings-file=${SETTINGS_FILE},\
input=\"${INPUT}\",\
input-recursive=\"${INPUT_RECURSIVE}\",\
output=${OUTPUT},\
runner=${RUNNER},\
status-file=${STATUS_FILE},\
keep-alive=${KEEP_ALIVE}"

>&2 echo $(date)
>&2 echo "Generating script commands and writing to file"
readonly TMP_SCRIPT=".$(basename ${0%.*} )-${OPERATION_ID}.sh"
cat > "${TMP_SCRIPT}" << EOF
#!/bin/bash
>&2 ${DISK_CMD}
>&2 ${VM_CMD}
echo ${OPERATION_ID}
EOF

>&2 echo "Copying scripts to the output path in Cloud Storage"
gsutil cp "${STARTUP_SCRIPT}" "${STARTUP_SCRIPT_URL}"
gsutil cp "${SHUTDOWN_SCRIPT}" "${SHUTDOWN_SCRIPT_URL}"
gsutil cp "${TMP_SCRIPT}" "${OUTPUT}/${TMP_SCRIPT/./}"
rm "${TMP_SCRIPT}"

>&2 echo "Creating Google Compute Engine VM and disk"
>&2 echo "${DISK_CMD}"
>&2 ${DISK_CMD}

>&2 echo "${VM_CMD}"
>&2 ${VM_CMD}

echo ${OPERATION_ID}

>&2 cat << EOM

Congratulations! Your job is running.

To monitor your job, check the status to see if it's RUNNING, COMPLETED, or FAILED:
gsutil cat "${STATUS_FILE}"

While your job is running, you can see the VM in the cloud console and command-line.
When the job completes, the VM will no longer be found unless --keep-alive is set.

Cloud console: 
https://console.cloud.google.com/compute/instances

Command-line:  
gcloud compute instances describe ${VM_NAME} ${ZONE}

To cancel a running job, you can delete the VM from the cloud console or command-line:
gcloud compute instances delete ${VM_NAME} ${ZONE}

To debug a failed run, look at the log files in your output directory. 

Cloud console: 
https://console.cloud.google.com/storage/browser/${OUTPUT/gs:\/\//}

Command-line:
gsutil cat "${OUTPUT}/stderr-${OPERATION_ID}.txt" | less
gsutil cat "${OUTPUT}/stdout-${OPERATION_ID}.txt" | less

For additional debugging, you can rerun this script with --keep-alive and ssh into the VM.
If you use --keep-alive, you will need to manually delete the VM to avoid charges.
EOM
