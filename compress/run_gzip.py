#!/usr/bin/python

#
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

"""Python sample demonstrating use of the Google Genomics Pipelines API.

This sample demonstrates running a pipeline to compress a file that is in
Google Cloud Storage.

This sample demonstrates running the pipeline in an "ephemeral" manner;
no call to pipelines.create() is necessary. No pipeline is persisted
in the pipelines list.

Usage:
  * python run_gzip.py \
      --project <project-id> \
      --zones <gce-zones> \
      --disk-size <size-in-gb> \
      --input <gcs-input-path> \
      --output <gcs-output-path> \
      --logging <gcs-logging-path> \
      --poll-interval <interval-in-seconds>

Where the poll-interval is optional (default is no polling).

Users will typically want to restrict the Compute Engine zones to avoid Cloud
Storage egress charges. This script supports a short-hand pattern-matching
for specifying zones, such as:

  --zones "*"                # All zones
  --zones "us-*"             # All US zones
  --zones "us-central1-*"    # All us-central1 zones

an explicit list may be specified, space-separated:
  --zones us-central1-a us-central1-b
"""

import argparse
import pprint

from oauth2client.client import GoogleCredentials
from apiclient.discovery import build

from pipelines_pylib import defaults
from pipelines_pylib import poller

# Parse input args
parser = argparse.ArgumentParser()
parser.add_argument("--project", required=True,
                    help="Cloud project id to run the pipeline in")
parser.add_argument("--disk-size", required=True, type=int,
                    help="Size (in GB) of disk for both input and output")
parser.add_argument("--zones", required=True, nargs="+",
                    help="List of Google Compute Engine zones (supports wildcards)")
parser.add_argument("--input", required=True,
                    help="Cloud Storage path to input file")
parser.add_argument("--output", required=True,
                    help="Cloud Storage path to output file (with the .gz extension)")
parser.add_argument("--logging", required=True,
                    help="Cloud Storage path to send logging output")
parser.add_argument("--poll-interval", default=0, type=int,
                    help="Frequency (in seconds) to poll for completion (default: no polling)")
args = parser.parse_args()

# Create the genomics service
credentials = GoogleCredentials.get_application_default()
service = build('genomics', 'v1alpha2', credentials=credentials)

# Run the pipeline
operation = service.pipelines().run(body={
  # The ephemeralPipeline provides the template for the pipeline
  # The pipelineArgs provide the inputs specific to this run

  # There are some nuances in the API that are still being ironed out
  # to make this more compact.

  'ephemeralPipeline' : {
    'projectId': args.project,
    'name': 'compress',
    'description': 'Run "gzip" on a file',

    # Define the resources needed for this pipeline.
    'resources' : {
      # Create a data disk that is attached to the VM and destroyed when the
      # pipeline terminates.
      'disks': [ {
        'name': 'datadisk',
        'autoDelete': True,

        # Within the docker container, specify a mount point for the disk.
        # The pipeline input argument below will specify that inputs should be
        # written to this disk.
        'mountPoint': '/mnt/data',
      } ],
    },

    # Specify the docker image to use along with the command
    'docker' : {
      'imageName': 'ubuntu', # Stock ubuntu contains the gzip command

      # Compress a file that will be downloaded from Cloud Storage to the data disk. 
      # The local copy of the file will be named "my_file". See the inputParameters.
      'cmd': 'gzip /mnt/data/my_file',
    },

    # This example takes a single input parameter - a path to a Cloud Storage file to
    # be copied to the data disk's mount point (/mnt/data) and name it to "my_file".
    #
    # The inputFile specified in the pipelineArgs (see below) specify the
    # Cloud Storage path to copy to /mnt/data/my_file.
    'inputParameters' : [ {
      'name': 'inputFile',
      'description': 'Cloud Storage path to an uncompressed file',
      'localCopy': {
        'path': 'my_file',
        'disk': 'datadisk'
      }
    } ],

    # gzip compresses in-place, so the output file from gzip is my_file.gz.
    # By specifying an outputParameter, we instruct the pipelines API to
    # copy /mnt/data/my_file.gz to the Cloud Storage location specified in
    # the pipelineArgs (see below).
    'outputParameters' : [ {
      'name': 'outputFile',
      'description': 'Cloud Storage path for where to write the compressed result',
      'localCopy': {
        'path': 'my_file.gz',
        'disk': 'datadisk'
      }
    } ]
  },

  'pipelineArgs' : {
    'projectId': args.project,

    # Override the resources needed for this pipeline
    'resources' : {
      # Expand any zone short-hand patterns
      'zones': defaults.get_zones(args.zones),

      # For the data disk, specify the type and size
      'disks': [ {
        'name': 'datadisk',

        'sizeGb': args.disk_size,
      } ]
    },

    'inputs': {
      # Pass the user-specified Cloud Storage path of the file to compress
      'inputFile': args.input
    },
    'outputs': {
      # Pass the user-specified Cloud Storage destination path of the compressed file
      'outputFile': args.output
    },
    'logging': {
      # Pass the user-specified Cloud Storage destination for pipeline logging
      'gcsPath': args.logging
    },
  }
}).execute()

# Emit the result of the pipeline run submission
pp = pprint.PrettyPrinter(indent=2)
pp.pprint(operation)

if args.poll_interval > 0:
  completed_op = poller.poll(service, operation, args.poll_interval)
  pp.pprint(completed_op)
