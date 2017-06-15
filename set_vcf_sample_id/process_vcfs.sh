#!/bin/bash

# Copyright 2017 Google Inc.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

# process_vcfs.sh
#
# Simple shell script which can be used to change the "sample ID" in
# a single-sample VCF file. For example, suppose your VCF "header line"
# looks like:
#
#   #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT SAMPLE-001
#
# but you want it to look like:
#
#   #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT SAMPLE-001-TEST-01
#
# and you have note just a single VCF, but many (maybe one VCF per chromosome).
#
# This script can be run on a list of VCFs to update the header.
# The VCFs can be uncompressed or compressed with gzip or bzip2.
# If the input VCFs are compressed, then the output VCFs will be too.
#
# ** Note that this script will delete the input VCF from the local disk. **
# ** This script is intended to be run as part of a Pipeline on a VM in   **
# ** the cloud. Deleting the local copy of the input file allows for the  **
# ** disk to be sized at less than 2x all of the input VCF files, namely: **
# **                                                                      **
# **    disk size ~= 2*size(largest uncompressed VCF)                     **
# **                 + size(remaining VCFs)                               **
# **                                                                      **

set -o errexit
set -o nounset

# Usage:
#  ./process_vcfs.sh \
#      [original_sample_id] \
#      [new_sample_id] \
#      [input_path] \
#      [output_path]
#
#  original_sample_id: If set to a non-empty string, the sample ID in the
#                      input VCF header will be verified before update
#  new_sample_id: Set to the new sample ID
#  input_path: on-disk directory or pattern of input VCF files
#  output_path: on-disk directory to copy output VCF files

readonly ORIG_SAMPLE_ID="${1}"
readonly NEW_SAMPLE_ID="${2}"
readonly INPUT_PATH="${3%/}"   # Trim trailing slash (if any)
readonly OUTPUT_PATH="${4%/}"  # Trim trailing slash (if any)

function log() {
  echo "${1}"
}
readonly -f log

# Dump out some details for of the script parameters and environment

log "BEGIN: log runtime details:"
log "Original sample id: ${ORIG_SAMPLE_ID}"
log "New sample id: ${NEW_SAMPLE_ID}"
log "Input path: ${INPUT_PATH}"
log "Output path: ${OUTPUT_PATH}"

log "find /mnt"
find /mnt

log "df -k -h"
df -k -h

log "env"
env
log "END: log runtime details"

# Process the input files

declare -i COUNT=0
declare -i SKIPPED=0
declare -i UPDATED=0

readonly START=$(date +%s)
for FILE in ${INPUT_PATH}; do
  # Check if the input file is compressed.
  # We'll need to decompress it for processing and then compress the output.
  COMPRESSION=""
  case "${FILE}" in
    *.gz)
      COMPRESSION=gz
      gunzip ${FILE}
      FILE=${FILE%.gz}
      ;;

   *.bz2)
      COMPRESSION=bz2
      bunzip2 ${FILE}
      FILE=${FILE%.bz2}
      ;;
  esac

  INPUT_DIR=$(dirname ${FILE})
  FILE_NAME=$(basename ${FILE})

  log "Updating header for file ${FILE_NAME}"
  cat ${FILE} |
    python \
      "${SCRIPT_DIR}/set_vcf_sample_id.py" \
      "${ORIG_SAMPLE_ID}" "${NEW_SAMPLE_ID}" \
      > ${OUTPUT_PATH}/${FILE_NAME}

  # To minimize disk usage, remove the input file now
  rm -f ${FILE}

  UPDATED=$((UPDATED + 1))

  # Compress the output file if the input was compressed
  case "${COMPRESSION}" in
    gz)
      gzip ${OUTPUT_PATH}/${FILE_NAME}
      ;;
    bz2)
      bzip2 ${OUTPUT_PATH}/${FILE_NAME}
      ;;
  esac

  COUNT=$((COUNT + 1))
done
readonly END=$(date +%s)

log ""
log "Updated: ${UPDATED}"
log "Skipped: ${SKIPPED}"
log "Total: ${COUNT} files processed in $((END-START)) seconds"

