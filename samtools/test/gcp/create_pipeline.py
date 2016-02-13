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
Demonstrates:
  * TODO:
"""

from oauth2client.client import GoogleCredentials
from apiclient.discovery import build

PROJECT_ID='**FILL IN PROJECT**'

credentials = GoogleCredentials.get_application_default()
service = build('genomics', 'v1alpha2', credentials=credentials)

pipeline = service.pipelines().create(body={
  'projectId': PROJECT_ID,
  'name': 'samtools index',
  'description': 'Run "samtools index" on a BAM file',
  'docker' : {
    'cmd': 'samtools index /scratch/input.bam /scratch/output.bam.bai',
    'imageName': 'gcr.io/%s/samtools' % PROJECT_ID
  },
  'inputParameters' : [ {
    'name': 'inputFile',
    'description': 'GCS path to a BAM to index',
    'localCopy': {
      'path': 'input.bam',
      'disk': 'data'
    }
  } ],
  'outputParameters' : [ {
    'name': 'outputFile',
    'description': 'GCS path for where to write the BAM index',
    'localCopy': {
      'path': 'output.bam.bai',
      'disk': 'data'
    }
  } ],
  'resources' : {
    'disks': [ {
      'name': 'data',
      'autoDelete': True,
      'mountPoint': '/mnt/data',
      'sizeGb': 10,
      'type': 'PERSISTENT_HDD',
    } ],
    'minimumCpuCores': 1,
    'minimumRamGb': 1,
  }
}).execute()


print pipeline
