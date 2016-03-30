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

"""
Usage:
  * python run_set_vcf_sample_id.py \
      --project <project-id> \
      --zones <gce-zones> \
      --disk-size <size-in-gb> \
      --original-sample-id <original-id> \
      --new-sample-id <new-id> \
      --script-path <gcs-script-path> \
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

Passing the --original-sample-id is optional. If set, then the pipeline
script will verify the value in the input VCF, and if not equal, the
pipeline will fail.

Note that the pipeline API does not allow for input arguments with no
value. Thus if the --original-sample-id is not specified (or is empty),
the ORIGINAL_SAMPLE_ID input parameter is left out of the pipeline definition.
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
parser.add_argument("--original-sample-id", required=False,
                    help="The original sample ID to be validated in the input")
parser.add_argument("--new-sample-id", required=True,
                    help="The new sample ID")
parser.add_argument("--script-path", required=True,
                    help="Cloud Storage path to script file(s)")
parser.add_argument("--input", required=True, nargs="+",
                    help="Cloud Storage path to input file(s)")
parser.add_argument("--output", required=True,
                    help="Cloud Storage path to output file (with the .gz extension)")
parser.add_argument("--logging", required=True,
                    help="Cloud Storage path to send logging output")
parser.add_argument("--poll-interval", default=0, type=int,
                    help="Frequency (in seconds) to poll for completion (default: no polling)")
args = parser.parse_args()
args.script_path.rstrip('/')

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
    'name': 'set_vcf_sample_id',
    'description': 'Set the sample ID in a VCF header',

    # Define the resources needed for this pipeline.
    'resources': {
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
    'docker': {
      'imageName': 'python:2.7',

      # The Pipelines API will create the input directory when localizing files,
      # but does not create the output directory.

      'cmd': ('mkdir /mnt/data/output && '

              'export SCRIPT_DIR=/mnt/data/scripts && '
              'chmod u+x ${SCRIPT_DIR}/* && '

              '${SCRIPT_DIR}/process_vcfs.sh '
                '"${ORIGINAL_SAMPLE_ID:-}" '
                '"${NEW_SAMPLE_ID}" '
                '"/mnt/data/input/*" '
                '"/mnt/data/output"'),
    },

    # The inputFile<n> specified in the pipelineArgs (see below) will
    # specify the Cloud Storage path to copy to /mnt/data/input/.

    'inputParameters': [ {
      'name': 'inputFile%d' % idx,
      'description': 'Cloud Storage path to input file(s)',
      'localCopy': {
        'path': 'input/',
        'disk': 'datadisk'
      }
    } for idx in range(len(args.input)) ] + [ {
      'name': 'setVcfSampleId_Script',
      'description': 'Cloud Storage path to process_vcfs.sh script',
      'defaultValue': '%s/process_vcfs.sh' % args.script_path,
      'localCopy': {
        'path': 'scripts/',
        'disk': 'datadisk'
      }
    }, {
      'name': 'setVcfSampleId_Python',
      'description': 'Cloud Storage path to set_vcf_sample_id.py script',
      'defaultValue': '%s/set_vcf_sample_id.py' % args.script_path,
      'localCopy': {
        'path': 'scripts/',
        'disk': 'datadisk'
      }
    }] + ([{
      'name': 'ORIGINAL_SAMPLE_ID',
      'description': 'Sample ID which must already appear in the VCF header',
    }] if args.original_sample_id else []) + [ {
      'name': 'NEW_SAMPLE_ID',
      'description': 'New sample ID to set in the VCF header',
    } ],

    # By specifying an outputParameter, we instruct the pipelines API to
    # copy /mnt/data/output/* to the Cloud Storage location specified in
    # the pipelineArgs (see below).
    'outputParameters': [ {
      'name': 'outputPath',
      'description': 'Cloud Storage path for where to copy the output',
      'localCopy': {
        'path': 'output/*',
        'disk': 'datadisk'
      }
    } ]
  },

  'pipelineArgs': {
    'projectId': args.project,

    # Override the resources needed for this pipeline
    'resources': {
      'minimumRamGb': 1, # Shouldn't need the default 3.75 GB

      # Expand any zone short-hand patterns
      'zones': defaults.get_zones(args.zones),

      # For the data disk, specify the type and size
      'disks': [ {
        'name': 'datadisk',

        'sizeGb': args.disk_size,
      } ]
    },

    # We can set a series of individual files, but typically usage will
    # just be:
    # 'inputs': {
    #   'inputFile0': 'gs://bucket/<sample>/*.vcf',
    # }
    'inputs': dict( {
      'inputFile%d' % idx: value for idx, value in enumerate(args.input)
    }.items() + ({
      'ORIGINAL_SAMPLE_ID': args.original_sample_id,
    }.items() if args.original_sample_id else []) + {
      'NEW_SAMPLE_ID': args.new_sample_id,
    }.items()),

    # Pass the user-specified Cloud Storage destination path output
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
