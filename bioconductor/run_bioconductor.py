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

This sample demonstrates a pipeline that uses Bioconductor to analyze
files in Google Cloud Storage.

This pipeline is run in an "ephemeral" manner; no call to pipelines.create()
is necessary. No pipeline is persisted in the pipelines list.
"""

import pprint
import time

from oauth2client.client import GoogleCredentials
from apiclient.discovery import build

PROJECT_ID='**FILL IN PROJECT ID**'
BUCKET='**FILL IN BUCKET**'

# Output will be written underneath gs://<BUCKET>/<PREFIX>/
PREFIX='pipelines-api-examples/bioconductor'

# Update this path if you uploaded the script elsewhere in Cloud Storage.
SCRIPT='gs://%s/%s/script.R' % (BUCKET, PREFIX)

# This script will poll for completion of the pipeline.
POLL_INTERVAL_SECONDS = 20

# Create the genomics service.
credentials = GoogleCredentials.get_application_default()
service = build('genomics', 'v1alpha2', credentials=credentials)

# Run the pipeline.
operation = service.pipelines().run(body={
  # The ephemeralPipeline provides the template for the pipeline.
  # The pipelineArgs provide the inputs specific to this run.
  'ephemeralPipeline' : {
    'projectId': PROJECT_ID,
    'name': 'Bioconductor: count overlaps in a BAM',
    'description': 'This sample demonstrates a subset of the vignette https://bioconductor.org/packages/release/bioc/vignettes/BiocParallel/inst/doc/Introduction_To_BiocParallel.pdf.',

    # Define the resources needed for this pipeline.
    'resources' : {
      # Specify default VM parameters for the pipeline.
      'minimumCpuCores': 1,  # TODO: remove this when the API has a default.
      'minimumRamGb': 3.75, # TODO: remove this when the API has a default.

      # Create a data disk that is attached to the VM and destroyed when the
      # pipeline terminates.
      'disks': [ {
        'name': 'data',
        'autoDelete': True,

        # Within the docker container, specify a mount point for the disk.
        # The pipeline input argument below will specify that inputs should be
        # written to this disk.
        'mountPoint': '/mnt/data',

        # Specify a default size and type.
        'sizeGb': 100,            # TODO: remove this when the API has a default
        'type': 'PERSISTENT_HDD', # TODO: remove this when the API has a default
      } ],
    },

    # Specify the docker image to use along with the command. See
    # http://www.bioconductor.org/help/docker/ for more detail.
    'docker' : {
      'imageName': 'bioconductor/release_core',

      # Change into the directory in which the script and input reside. Then
      # run the R script in batch mode to completion.
      'cmd': '/bin/bash -c "cd /mnt/data/ ; R CMD BATCH script.R"',
    },

    'inputParameters' : [ {
      'name': 'script',
      'description': 'Cloud Storage path to the R script to run.',
      'localCopy': {
        'path': 'script.R',
        'disk': 'data'
      }
    }, {
      'name': 'bamFile',
      'description': 'Cloud Storage path to the BAM file.',
      'localCopy': {
        'path': 'input.bam',
        'disk': 'data'
      }
    }, {
      'name': 'indexFile',
      'description': 'Cloud Storage path to the BAM index file.',
      'localCopy': {
        'path': 'input.bam.bai',
        'disk': 'data'
        }
    } ],

    'outputParameters' : [ {
      'name': 'outputFile',
      'description': 'Cloud Storage path for where to write the result.',
      'localCopy': {
        'path': 'overlapsCount.tsv',
        'disk': 'data'
      }
    }, {
      'name': 'rBatchLogFile',
      'description': 'Cloud Storage path for where to write the R batch log file.',
      'localCopy': {
        'path': 'script.Rout',
        'disk': 'data'
      }
    } ]
  },

  'pipelineArgs' : {
    'projectId': PROJECT_ID,

    # Here we use a very tiny BAM as an example but this pipeline could be invoked in
    # a loop to kick off parallel execution of this pipeline on, for example, all the
    # 1000 Genomes phase 3 BAMs in
    # gs://genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/phase3/data/*/alignment/*.mapped.ILLUMINA.bwa.*.low_coverage.20120522.bam'
    # emitting a distinct output file for each result. Then you can:
    #     gsutil cat gs://<BUCKET>/<PREFIX>/output/*tsv > allOverlapsCount.tsv
    # to create the final consolidated TSV file.
    'inputs': {
      'script': SCRIPT,
      'bamFile': 'gs://genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/pilot3_exon_targetted_GRCh37_bams/data/NA06986/alignment/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam',
      'indexFile': 'gs://genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/pilot3_exon_targetted_GRCh37_bams/data/NA06986/alignment/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam.bai'
    },
    # Pass the user-specified Cloud Storage destination for pipeline output.
    'outputs': {
      # The R script explicitly writes out one file of results.
      'outputFile': 'gs://%s/%s/output/overlapsCount.tsv' % (BUCKET, PREFIX),
      # R, when run in batch mode, writes console output to a file.
      'rBatchLogFile': 'gs://%s/%s/output/script.Rout' % (BUCKET, PREFIX)
    },
    # Pass the user-specified Cloud Storage destination for pipeline logging.
    'logging': {
      'gcsPath': 'gs://%s/%s/logging' % (BUCKET, PREFIX)
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

# Emit the result of the pipeline run submission and poll for completion.
pp = pprint.PrettyPrinter(indent=2)
pp.pprint(operation)
operation_name = operation['name']
print
print "Polling for completion of operation"

while not operation['done']:
  print "Operation not complete. Sleeping %d seconds" % (POLL_INTERVAL_SECONDS)
  time.sleep(POLL_INTERVAL_SECONDS)
  operation = service.operations().get(name=operation_name).execute()

print
print "Operation complete"
print
pp.pprint(operation)
