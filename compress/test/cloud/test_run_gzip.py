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
no call to pipelines.create() is neccessary. No pipeline is persisted
in the pipelines list.

Usage:
  * python test_run_gzip.py \
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
  'ephemeralPipeline' : {
    'projectId': args.project,
    'name': 'compress',
    'description': 'Run "gzip" on a file',
    'docker' : {
      'cmd': 'gzip /mnt/data/my_file',
      'imageName': 'ubuntu'
    },
    'inputParameters' : [ {
      'name': 'inputFile',
      'description': 'Cloud Storage path to an uncompressed file ',
      'localCopy': {
        'path': 'my_file',
        'disk': 'data'
      }
    } ],
    'outputParameters' : [ {
      'name': 'outputFile',
      'description': 'Cloud Storage path for where to write the compressed result',
      'localCopy': {
        'path': 'my_file.gz',
        'disk': 'data'
      }
    } ],
    'resources' : {
      'disks': [ {
        'name': 'data',
        'autoDelete': True,
        'mountPoint': '/mnt/data',
        'sizeGb': args.disk_size,
        'type': 'PERSISTENT_HDD',
      } ],
      'minimumCpuCores': 1,
      'minimumRamGb': 1,
    }
  },
  'pipelineArgs' : {
    'inputs': {
      'inputFile': args.input
    },
    'outputs': {
      'outputFile': args.output
    },
    'logging': {
      'gcsPath': args.logging
    },
    'projectId': args.project,
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
