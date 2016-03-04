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
      --disk-size <size-in-gb> \
      --input <gcs-input-path> \
      --output <gcs-output-path> \
      --logging <gcs-logging-path> \
      --poll-interval <interval-in-seconds>

Where the poll-interval is optional (default is no polling).
"""

import argparse
import pprint
import time

from oauth2client.client import GoogleCredentials
from apiclient.discovery import build

# Parse input args
parser = argparse.ArgumentParser()
parser.add_argument("--project", required=True,
                    help="Cloud project id to run the pipeline in")
parser.add_argument("--disk-size", required=True, type=int,
                    help="Size (in GB) of disk for both input and output")
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
      # Specify default VM parameters for the pipeline
      'minimumCpuCores': 1,  # TODO: remove this when the API has a default
      'minimumRamGb': 3.75, # TODO: remove this when the API has a default

      # Create a data disk that is attached to the VM and destroyed when the
      # pipeline terminates.
      'disks': [ {
        'name': 'data',
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
        'disk': 'data'
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
        'disk': 'data'
      }
    } ]
  },

  'pipelineArgs' : {
    'projectId': args.project,

    # Override the resources needed for this pipeline
    'resources' : {
      'minimumRamGb': 1, # For this example, override the 3.75 GB default

      # For the data disk, specify the type and size
      'disks': [ {
        'name': 'data',

        'sizeGb': args.disk_size,
        'type': 'PERSISTENT_HDD', # TODO: remove this when the API picks up the pipeline default
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
  operation_name = operation['name']
  print
  print "Polling for completion of operation"

  while not operation['done']:
    print "Operation not complete. Sleeping %d seconds" % (args.poll_interval)

    time.sleep(args.poll_interval)

    operation = service.operations().get(name=operation_name).execute()

  print
  print "Operation complete"
  print
  pp.pprint(operation)
