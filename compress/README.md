# Compress a file from Cloud Storage

This pipeline provides the use-case of downloading a file from Cloud Storage,
compressing it via gzip, and pushing the result to Cloud Storage.
The gzip command is provided as part of the default `ubuntu` image.

This pipeline does not involve packaging a custom Docker image, and
thus there is no requirement to install Docker on your local machine.

## (1) Run the pipeline in the cloud

When the Prerequisites from this repository's [README.md](../README.md)
are satisfied, then you can run this pipeline as:

```
PYTHONPATH=.. python ./run_gzip.py \
  --project YOUR-PROJECT-ID \
  --zones "us-*" \
  --disk-size 200 \
  --input gs://genomics-public-data/platinum-genomes/vcf/NA12877_S1.genome.vcf \
  --output gs://YOUR-BUCKET/compress/output_path/NA12877_S1.genome.vcf.gz \
  --logging gs://YOUR-BUCKET/compress/logging_path \
  --poll-interval 20
```

* Replace `YOUR-PROJECT-ID` with your project ID.
* Replace `YOUR-BUCKET` with a bucket in your project.

The `PYTHONPATH` must include the top-level directory of the
`pipelines-api-examples` in order to pick up modules in the
[pipelines_pylib](../pipelines_pylib) directory.

The output will be the JSON description of the operation, followed by periodic
messages for polling. When the operation completes, the full operation will
be emitted.
```
{ u'done': False,
  u'metadata': { u'@type': u'type.googleapis.com/google.genomics.v1.OperationMetadata',
                 u'clientId': u'',
                 u'createTime': u'2016-03-10T04:53:28.000Z',
                 u'events': [],
                 u'projectId': u'YOUR-PROJECT-ID'},
  u'name': u'operations/YOUR-NEW-OPERATION-ID'}

Polling for completion of operation
Operation not complete. Sleeping 20 seconds
Operation not complete. Sleeping 20 seconds
...
Operation not complete. Sleeping 20 seconds
Operation complete

{ u'done': True,
  u'metadata': { u'@type': u'type.googleapis.com/google.genomics.v1.OperationMetadata',
                 u'clientId': u'',
                 u'createTime': u'2016-03-10T04:53:28.000Z',
                 u'endTime': u'2016-03-10T05:08:10.000Z',
                 u'events': [ { u'description': u'start(g1-small)',
                                u'startTime': u'2016-03-10T04:54:44.000Z'},
                              { u'description': u'pulling-image',
                                u'startTime': u'2016-03-10T04:54:53.000Z'},
                              { u'description': u'localizing-files',
                                u'startTime': u'2016-03-10T04:55:29.000Z'},
                              { u'description': u'running-docker',
                                u'startTime': u'2016-03-10T04:58:58.000Z'},
                              { u'description': u'delocalizing-files',
                                u'startTime': u'2016-03-10T05:07:31.000Z'},
                              { u'description': u'ok',
                                u'startTime': u'2016-03-10T05:08:05.000Z'}],
                 u'projectId': u'YOUR-PROJECT-ID',
                 u'request': { u'@type': u'type.googleapis.com/google.genomics.v1alpha2.RunPipelineRequest',
                               u'ephemeralPipeline': { u'description': u'Run "gzip" on a file',
                                                       u'docker': { u'cmd': u'gzip /mnt/data/my_file',
                                                                    u'imageName': u'ubuntu'},
                                                       u'name': u'compress',
                                                       u'parameters': [ { u'description': u'Cloud Storage path to an uncompressed file',
                                                                          u'name': u'inputFile'},
                                                                        { u'description': u'Cloud Storage path for where to write the compressed result',
                                                                          u'name': u'outputFile'}],
                                                       u'projectId': u'YOUR-PROJECT-ID',
                                                       u'resources': { u'disks': [ { u'autoDelete': True,
                                                                                     u'name': u'data',
                                                                                     u'sizeGb': 500,
                                                                                     u'type': u'PERSISTENT_HDD'}],
                                                                       u'minimumCpuCores': 1,
                                                                       u'minimumRamGb': 3.75}},
                               u'pipelineArgs': { u'clientId': u'',
                                                  u'inputs': { u'inputFile': u'gs://genomics-public-data/platinum-genomes/vcf/NA12877_S1.genome.vcf'},
                                                  u'logging': { u'gcsPath': u'gs://YOUR-BUCKET/compress/logging_path'},
                                                  u'outputs': { u'outputFile': u'gs://YOUR-BUCKET/compress/output_path/NA12877_S1.genome.vcf.gz'},
                                                  u'projectId': u'YOUR-PROJECT-ID',
                                                  u'resources': { u'disks': [ { u'autoDelete': False,
                                                                                u'mountPoint': u'',
                                                                                u'name': u'data',
                                                                                u'readOnly': False,
                                                                                u'sizeGb': 200,
                                                                                u'source': u'',
                                                                                u'type': u'PERSISTENT_HDD'}],
                                                                  u'minimumCpuCores': 0,
                                                                  u'minimumRamGb': 1,
                                                                  u'preemptible': False,
                                                                  u'zones': [ u'us-central1-a',
                                                                              u'us-central1-b',
                                                                              u'us-central1-c',
                                                                              u'us-central1-f',
                                                                              u'us-east1-b',
                                                                              u'us-east1-c',
                                                                              u'us-east1-d']},
                                                  u'serviceAccount': { u'email': u'default',
                                                                       u'scopes': [ u'https://www.googleapis.com/auth/compute',
                                                                                    u'https://www.googleapis.com/auth/devstorage.full_control',
                                                                                    u'https://www.googleapis.com/auth/genomics']}}},
                 u'startTime': u'2016-03-10T04:53:57.000Z'},
  u'name': u'operations/YOUR-NEW-OPERATION-ID'}

```

## (2) Check the results

Check the operation output for a top-level `errors` field.
If none, then the operation should have finished successfully.

Navigate to your bucket in the
[Cloud Console](https://console.cloud.google.com/project/_/storage)
to see the output and log files for the operation.
