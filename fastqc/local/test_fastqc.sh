#!/bin/bash

# Copyright 2017 Google Inc.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

# test_fastqc.sh
#
# Simple test script to exercise the fastqc Docker image.
# The Docker image is assumed to have been tagged with the user id
# upon creation:
#
#   docker build -t ${USER}/fastqc PATH/TO/pipelines-api-examples/fastqc/Dockerfile
#
# This test script will download a small BAM file and run "fastqc <file>".

set -o nounset
set -o errexit

readonly DOCKER_IMAGE=${USER}/fastqc

# Use the smallest BAM file in the 1000genomes data (26534 bytes)
readonly TEST_INPUT_URI=http://storage.googleapis.com/genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/pilot3_exon_targetted_GRCh37_bams/data/NA06986/alignment/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam

readonly TEST_INPUT_FILENAME=$(basename ${TEST_INPUT_URI})

# Set up the host path locations
readonly HOST_SCRATCH_DIR=$(pwd)/test_mnt

# Set up the local (container) path locations
readonly LOCAL_SCRATCH=/scratch
readonly LOCAL_INPUT_NAME=${LOCAL_SCRATCH}/input/${TEST_INPUT_FILENAME}
readonly LOCAL_OUTPUT_DIR=${LOCAL_SCRATCH}/output

#
# BEGIN MAIN EXECUTION
#

# Create the test input/output directories on the host
rm -rf ${HOST_SCRATCH_DIR}
mkdir -p ${HOST_SCRATCH_DIR}/input
mkdir -p ${HOST_SCRATCH_DIR}/output

# Pull down the test BAM file
echo "Copying test file ${TEST_INPUT_FILENAME} to ${HOST_SCRATCH_DIR}"
(cd ${HOST_SCRATCH_DIR}/input && curl -O ${TEST_INPUT_URI})

echo
echo "Running fastqc index via docker"
docker run --rm \
  -v ${HOST_SCRATCH_DIR}:${LOCAL_SCRATCH} \
  ${DOCKER_IMAGE} \
  fastqc ${LOCAL_INPUT_NAME} --outdir=${LOCAL_OUTPUT_DIR}

echo
echo "Execution completed"

echo
echo "Scratch directory:"
cd ${HOST_SCRATCH_DIR} && find

