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

This sample demonstrates the invocation of a pipeline that will use samtools to create an index file for a BAM.

Specifically it configures:
  * which pipeline to run via the pipeline id
  * which input file from Google Cloud Storage to use as input
  * the Cloud Storage path to use for the resultant output file
  * the Cloud Storage path to use for log files for the operation
  * the project, service account, and scopes with which the operation will run
"""

import pprint
from oauth2client.client import GoogleCredentials
from apiclient.discovery import build

PIPELINE_ID='**FILL IN PIPELINE ID**'
PROJECT_ID='**FILL IN PROJECT ID**'
SERVICE_ACCOUNT='**FILL IN SERVICE ACCOUNT**'
BUCKET='**FILL IN BUCKET**'

credentials = GoogleCredentials.get_application_default()
service = build('genomics', 'v1alpha2', credentials=credentials)

pipeline = service.pipelines().run(body={
  'pipelineId': PIPELINE_ID,
  'pipelineArgs' : {
    'inputs': {
      'inputFile': 'gs://genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/pilot3_exon_targetted_GRCh37_bams/data/NA06986/alignment/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam'
    },
    'outputs': {
      'outputFile': 'gs://%s/pipelines-api-examples/samtools/output/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam.bai' % BUCKET
    },
    'logging': {
      'gcsPath': 'gs://%s/pipelines-api-examples/samtools/logging' % BUCKET
    },
    'projectId': PROJECT_ID,
    'serviceAccount': {
        'email': SERVICE_ACCOUNT,
        'scopes': [
            'https://www.googleapis.com/auth/cloud-platform'
        ]
    }
  }
}).execute()

pp = pprint.PrettyPrinter(indent=2)
pp.pprint(pipeline)
