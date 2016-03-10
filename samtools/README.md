# Use samtools to create a BAM index file

## (1) Create the Docker image.
```
git clone https://github.com/googlegenomics/pipelines-api-examples.git
cd pipelines-api-examples/samtools/
docker build -t ${USER}/samtools .
```
## (2) Test locally the Docker image used by the pipeline.
```
./local/test_index.sh
```

The result should be the newly created .bam.bai file in a subdirectory on your local machine:
```
Running samtools index via docker

Execution completed

Scratch directory:
.
./output
./output/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam.bai
./input
./input/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam
```

## (3) Push the Docker image to a repository.
In this example, we push the container to [Google Container Registry](https://cloud.google.com/container-registry/) via the following commands:
```
docker tag ${USER}/samtools gcr.io/YOUR-PROJECT-ID/samtools
gcloud docker push gcr.io/YOUR-PROJECT-ID/samtools
```

## (4) Create the pipeline definition.

Edit your copy of [create_pipeline.py](./cloud/create_pipeline.py) to specify the id of the Google Cloud Platform project in which the pipeline should be defined and then run the script.
```
python cloud/create_pipeline.py
```
The output will be the JSON description of the pipeline.
```
{ u'description': u'Run "samtools index" on a BAM file',
  u'docker': { u'cmd': u'samtools index /mnt/data/input.bam /mnt/data/output.bam.bai',
               u'imageName': u'gcr.io/YOUR-PROJECT-ID/samtools'},
  u'inputParameters': [ { u'defaultValue': u'',
                          u'description': u'GCS path to a BAM to index',
                          u'localCopy': { u'disk': u'data',
                                          u'path': u'input.bam'},
                          u'name': u'inputFile',
                          u'type': u'TYPE_UNSPECIFIED',
                          u'value': u''}],
  u'name': u'samtools index',
  u'outputParameters': [ { u'defaultValue': u'',
                           u'description': u'GCS path for where to write the BAM index',
                           u'localCopy': { u'disk': u'data',
                                           u'path': u'output.bam.bai'},
                           u'name': u'outputFile',
                           u'type': u'TYPE_UNSPECIFIED',
                           u'value': u''}],
  u'parameters': [],
  u'pipelineId': u'YOUR-NEW-PIPELINE-ID',
  u'projectId': u'YOUR-PROJECT-ID',
  u'resources': { u'disks': [ { u'autoDelete': True,
                                u'mountPoint': u'/mnt/data',
                                u'name': u'data',
                                u'readOnly': False,
                                u'sizeGb': 10,
                                u'source': u'',
                                u'type': u'PERSISTENT_HDD'}],
                  u'minimumCpuCores': 1,
                  u'minimumRamGb': 1,
                  u'preemptible': False,
                  u'zones': []}}
```
## (5) Run the pipeline on the cloud.
Edit your copy of [run_pipeline.py](./cloud/run_pipeline.py) to specify:

  1. the id for the pipeline created in the prior step
  1. the id of the Google Cloud Platform project in which the pipeline should run
  1. the email address of the Compute Engine default service account. (this can be found in the "Editor" group on the [Cloud Console](https://console.cloud.google.com/project/_/permissions/projectpermissions))
  1. the bucket in which the pipeline output file and log files should be placed.

and then run the script:
```
 python ./cloud/run_pipeline.py
```

The output will be the JSON description of the operation.
```
{ u'done': False,
  u'metadata': { u'@type': u'type.googleapis.com/google.genomics.v1.OperationMetadata',
                 u'clientId': u'',
                 u'createTime': u'2016-02-17T23:51:20.000Z',
                 u'events': [],
                 u'projectId': u'YOUR-PROJECT-ID'},
  u'name': u'operations/YOUR-NEW-OPERATION-ID'}
```

## (6) Check for completion of the operation.
A script could be written to poll for status, but here we use the API explorer to check the status of the operation:

  1. Navigate to the [APIs Explorer](https://developers.google.com/apis-explorer/#p/genomics/v1alpha2/genomics.operations.get).
  1. In the `name` field, paste in the id of the operation returned in the prior step.  **Be sure to include the `operation/` prefix.**
  1. Click on "Authorize and Execute".

The result will be a JSON description of the current status of the operation.  When the value of the `done` field is "true", move onto the next step.
  
## (7) View the resultant file.
Navigate to your bucket in the [Cloud Console](https://console.cloud.google.com/project/_/storage) to see the resultant bam.bai file and log files for the operation.

