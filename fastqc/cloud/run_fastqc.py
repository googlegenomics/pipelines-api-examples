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

This sample demonstrates running FASTQC
(http://www.bioinformatics.babraham.ac.uk/projects/fastqc/) over one
or more files in Google Cloud Storage.

This sample demonstrates running the pipeline in an "ephemeral" manner;
no call to pipelines.create() is necessary. No pipeline is persisted
in the pipelines list.

For large input files, it will typically make sense to have a single
call to this script (which makes a single call to the Pipelines API).

For small input files, it may make sense to batch them together into a single call.
Google Compute Engine instance billing is for a minimum of 10 minutes, and then
per-minute billing after that. If you are running FastQC over a BAM file for
mitochondrial DNA, it may take less than 10 minutes.

So if you have a series of such files, batch them together:

 --input "gs://bucket/sample1/chrMT.bam gs://bucket/sample1/chrY.bam gs://<etc>"

Usage:
  * python run_fastqc.py \
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

  'ephemeralPipeline' : {
    'projectId': args.project,
    'name': 'fastqc',
    'description': 'Run "FastQC" on one or more files',

    # Define the resources needed for this pipeline.
    'resources' : {
      # Specify default VM parameters for the pipeline
      'minimumCpuCores': 1,  # TODO: remove this when the API has a default
      'minimumRamGb': 3.75, # TODO: remove this when the API has a default

      # Create a data disk that is attached to the VM and destroyed when the
      # pipeline terminates.
      'disks': [ {
        'name': 'datadisk',
        'autoDelete': True,

        # Within the docker container, specify a mount point for the disk.
        # The pipeline input argument below will specify that inputs should be
        # written to this disk.
        'mountPoint': '/mnt/data',

        # Specify a default size and type
        'sizeGb': 500,            # TODO: remove this when the API has a default
        'type': 'PERSISTENT_HDD', # TODO: remove this when the API has a default
      } ],
    },

    # Specify the docker image to use along with the command
    'docker' : {
      'imageName': 'gcr.io/%s/fastqc' % args.project,

      # The Pipelines API will create the input directory when localizing files,
      # but does not create the output directory.
      'cmd': ('mkdir /mnt/data/output && '
              'fastqc /mnt/data/input/* --outdir=/mnt/data/output/'),
    },

    # The Pipelines API currently supports full GCS paths, along with patterns (globs),
    # but it doesn't directly support a list of files being passed as a single input
    # parameter ("gs://bucket/foo.bam gs://bucket/bar.bam").
    #
    # We can simply generate a series of inputs (input0, input1, etc.) to support this here.
    #
    # 'inputParameters' : [ {
    #   'name': 'inputFile0',
    #   'description': 'Cloud Storage path to an input file',
    #   'localCopy': {
    #     'path': 'input/',
    #     'disk': 'datadisk'
    #   }
    # }, {
    #   'name': 'inputFile1',
    #   'description': 'Cloud Storage path to an input file',
    #   'localCopy': {
    #     'path': 'input/',
    #     'disk': 'datadisk'
    #   }
    # <etc>
    # } ],

    # The inputFile<n> specified in the pipelineArgs (see below) will specify the
    # Cloud Storage path to copy to /mnt/data/input/.

    'inputParameters' : [ {
      'name': 'inputFile%d' % idx,
      'description': 'Cloud Storage path to an input file',
      'localCopy': {
        'path': 'input/',
        'disk': 'datadisk'
      }
    } for idx in range(len(args.input)) ],

    # By specifying an outputParameter, we instruct the pipelines API to
    # copy /mnt/data/output/* to the Cloud Storage location specified in
    # the pipelineArgs (see below).
    'outputParameters' : [ {
      'name': 'outputPath',
      'description': 'Cloud Storage path for where to FastQC output',
      'localCopy': {
        'path': 'output/*',
        'disk': 'datadisk'
      }
    } ]
  },

  'pipelineArgs' : {
    'projectId': args.project,

    # Override the resources needed for this pipeline
    'resources' : {
      'minimumRamGb': 1, # For this example, override the 3.75 GB default

      # Expand any zone short-hand patterns
      'zones': defaults.get_zones(args.zones),

      # For the data disk, specify the type and size
      'disks': [ {
        'name': 'datadisk',
        'autoDelete': True,

        'sizeGb': args.disk_size,
        'type': 'PERSISTENT_HDD', # TODO: remove this when the API picks up the pipeline default
      } ]
    },

    # Pass the user-specified Cloud Storage paths as a map of input files
    # 'inputs' : {
    #   'inputFile0' : 'gs://bucket/foo.bam',
    #   'inputFile1' : 'gs://bucket/bar.bam', 
    #   <etc>
    # }
    'inputs' : {
      'inputFile%d' % idx : value for idx, value in enumerate(args.input)
    },

    # Pass the user-specified Cloud Storage destination path of the FastQC output
    'outputs' : {
      'outputPath': args.output
    },

    # Pass the user-specified Cloud Storage destination for pipeline logging
    'logging': {
      'gcsPath': args.logging
    },

    # TODO: remove this when the API has a default
    'serviceAccount': {
        'email': 'default',
        'scopes': [
            'https://www.googleapis.com/auth/compute',
            'https://www.googleapis.com/auth/devstorage.full_control',
            'https://www.googleapis.com/auth/genomics'
        ]
    }
  }
}).execute()

# Emit the result of the pipeline run submission
pp = pprint.PrettyPrinter(indent=2)
pp.pprint(operation)

# If requested - poll until the operation reaches completion state ("done: true")
if args.poll_interval > 0:
  completed_op = poller.poll(service, operation, args.poll_interval)
  pp.pprint(completed_op)
