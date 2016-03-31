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

This sample demonstrates running a pipeline to compress or decompress
a file that is in Google Cloud Storage.

This sample demonstrates running the pipeline in an "ephemeral" manner;
no call to pipelines.create() is necessary. No pipeline is persisted
in the pipelines list.

Usage:
  * python run_compress.py \
      --project <project-id> \
      --zones <gce-zones> \
      --disk-size <size-in-gb> \
      --operation <compression-operation> \
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
parser.add_argument("--operation", required=False, default="gzip",
                    choices=[ "gzip", "gunzip", "bzip2", "bunzip2" ],
                    help="Choice of compression/decompression command")
parser.add_argument("--input", required=True, nargs="+",
                    help="Cloud Storage path to input file(s)")
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

  'ephemeralPipeline': {
    'projectId': args.project,
    'name': 'compress',
    'description': 'Compress or decompress a file',

    # Define the resources needed for this pipeline.
    'resources': {
      # Create a data disk that is attached to the VM and destroyed when the
      # pipeline terminates.
      'disks': [ {
        'name': 'datadisk',
        'autoDelete': True,

        # Within the Docker container, specify a mount point for the disk.
        # The pipeline input argument below will specify that inputs should be
        # written to this disk.
        'mountPoint': '/mnt/data',
      } ],
    },

    # Specify the Docker image to use along with the command
    'docker': {
      'imageName': 'ubuntu', # Stock ubuntu contains the gzip, bzip2 commands

      'cmd': ('cd /mnt/data/workspace && '
              'for file in $(/bin/ls); do '
                '%s ${file}; '
              'done' % args.operation),
    },

    # The Pipelines API currently supports full GCS paths, along with patterns (globs),
    # but it doesn't directly support a list of files being passed as a single input
    # parameter ("gs://bucket/foo.bam gs://bucket/bar.bam").
    #
    # We can simply generate a series of inputs (input0, input1, etc.) to support this here.
    #
    # 'inputParameters': [ {
    #   'name': 'inputFile0',
    #   'description': 'Cloud Storage path to an input file',
    #   'localCopy': {
    #     'path': 'workspace/',
    #     'disk': 'datadisk'
    #   }
    # }, {
    #   'name': 'inputFile1',
    #   'description': 'Cloud Storage path to an input file',
    #   'localCopy': {
    #     'path': 'workspace/',
    #     'disk': 'datadisk'
    #   }
    # <etc>
    # } ],

    # The inputFile<n> specified in the pipelineArgs (see below) will specify the
    # Cloud Storage path to copy to /mnt/data/workspace/.

    'inputParameters': [ {
      'name': 'inputFile%d' % idx,
      'description': 'Cloud Storage path to an input file',
      'localCopy': {
        'path': 'workspace/',
        'disk': 'datadisk'
      }
    } for idx in range(len(args.input)) ],

    # By specifying an outputParameter, we instruct the pipelines API to
    # copy /mnt/data/workspace/* to the Cloud Storage location specified in
    # the pipelineArgs (see below).
    'outputParameters': [ {
      'name': 'outputPath',
      'description': 'Cloud Storage path for where to FastQC output',
      'localCopy': {
        'path': 'workspace/*',
        'disk': 'datadisk'
      }
    } ]
  },

  'pipelineArgs': {
    'projectId': args.project,

    # Override the resources needed for this pipeline
    'resources': {
      # Expand any zone short-hand patterns
      'zones': defaults.get_zones(args.zones),

      # For the data disk, specify the type and size
      'disks': [ {
        'name': 'datadisk',

        'sizeGb': args.disk_size,
      } ]
    },

    # Pass the user-specified Cloud Storage paths as a map of input files
    # 'inputs': {
    #   'inputFile0': 'gs://bucket/foo.bam',
    #   'inputFile1': 'gs://bucket/bar.bam', 
    #   <etc>
    # }
    'inputs': {
      'inputFile%d' % idx : value for idx, value in enumerate(args.input)
    },

    # Pass the user-specified Cloud Storage destination path of output
    'outputs': {
      'outputPath': args.output
    },

    # Pass the user-specified Cloud Storage destination for pipeline logging
    'logging': {
      'gcsPath': args.logging
    },
  }
}).execute()

# Emit the result of the pipeline run submission
pp = pprint.PrettyPrinter(indent=2)
pp.pprint(operation)

# If requested - poll until the operation reaches completion state ("done: true")
if args.poll_interval > 0:
  completed_op = poller.poll(service, operation, args.poll_interval)
  pp.pprint(completed_op)
