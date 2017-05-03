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

# test_view.sh
#
# Simple test script to exercise the samtools docker image.
# The docker image is assumed to have been tagged with the user id
# upon creation:
#
#   docker build -t ${USER}/samtools PATH/TO/pipelines-api-examples/samtools/Dockerfile
#
# This test script will download a small BAM file and run "samtools view"
# to dump out the reads.

set -o nounset
set -o errexit

readonly DOCKER_IMAGE=${USER}/samtools

# Use the smallest BAM file in the 1000genomes data (26534 bytes)
readonly TEST_INPUT_URI=http://storage.googleapis.com/genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/pilot3_exon_targetted_GRCh37_bams/data/NA06986/alignment/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam

readonly TEST_INPUT_FILENAME=$(basename ${TEST_INPUT_URI})
readonly TEST_OUTPUT_FILENAME=${TEST_INPUT_FILENAME/%.bam/.sam}

# Set up the host path locations
readonly HOST_SCRATCH_DIR=$(pwd)/test_mnt
readonly HOST_OUTPUT_FILENAME=${HOST_SCRATCH_DIR}/output/${TEST_OUTPUT_FILENAME}

# Set up the local (container) path locations
readonly LOCAL_SCRATCH=/scratch
readonly LOCAL_INPUT_NAME=${LOCAL_SCRATCH}/input/${TEST_INPUT_FILENAME}
readonly LOCAL_OUTPUT_NAME=${LOCAL_SCRATCH}/output/${TEST_OUTPUT_FILENAME}

# Create the test input/output directories on the host
rm -rf ${HOST_SCRATCH_DIR}
mkdir -p ${HOST_SCRATCH_DIR}/input
mkdir -p ${HOST_SCRATCH_DIR}/output

# Pull down the test BAM file
echo "Copying test file ${TEST_INPUT_FILENAME} to ${HOST_SCRATCH_DIR}"
(cd ${HOST_SCRATCH_DIR}/input && curl -O ${TEST_INPUT_URI})

echo
echo "Running samtools view via docker"
docker run --rm \
  -v ${HOST_SCRATCH_DIR}:${LOCAL_SCRATCH} \
  ${DOCKER_IMAGE} \
  samtools view ${LOCAL_INPUT_NAME} -o ${LOCAL_OUTPUT_NAME}

echo
echo "Execution completed"

echo
echo "Scratch directory:"
cd ${HOST_SCRATCH_DIR} && find

echo
echo "Output file is $(cat ${HOST_OUTPUT_FILENAME} | wc -l) lines"
echo "First 2 lines:"
head -n 2 ${HOST_OUTPUT_FILENAME}

