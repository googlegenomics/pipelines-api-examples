# Compress or Decompress files from Cloud Storage

This pipeline provides the use-case of downloading one or more files
from Cloud Storage, compressing or decompressing it (via gzip, gunzip,
bzip2, or bunzip2) and pushing the result to Cloud Storage.

This pipeline does not involve packaging a custom Docker image, and
thus there is no requirement to install Docker on your local machine.
The gzip and bzip2 commands are provided as part of the default `ubuntu` image.

## (1) Run the pipeline in the cloud

When the Prerequisites from this repository's [README.md](../README.md)
are satisfied, then you can run this pipeline as:

```
PYTHONPATH=.. python ./run_gzip.py \
  --project YOUR-PROJECT-ID \
  --zones "us-*" \
  --disk-size 200 \
  --operation "gunzip" \
  --input gs://genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/working/20140123_NA12878_Illumina_Platinum/**.vcf.gz \
  --output gs://YOUR-BUCKET/pipelines-api-examples/compress/output \
  --logging gs://YOUR-BUCKET/pipelines-api-examples/compress/logging \
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
                 u'createTime': u'2016-03-30T17:34:08.000Z',
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
                 u'createTime': u'2016-03-30T17:34:08.000Z',
                 u'endTime': u'2016-03-30T17:36:11.000Z',
                 u'events': [ { u'description': u'start',
                                u'startTime': u'2016-03-30T17:35:34.244369759Z'},
                              { u'description': u'pulling-image',
                                u'startTime': u'2016-03-30T17:35:34.244435642Z'},
                              { u'description': u'localizing-files',
                                u'startTime': u'2016-03-30T17:35:44.884961352Z'},
                              { u'description': u'running-docker',
                                u'startTime': u'2016-03-30T17:35:50.872211301Z'},
                              { u'description': u'delocalizing-files',
                                u'startTime': u'2016-03-30T17:35:58.234466119Z'},
                              { u'description': u'ok',
                                u'startTime': u'2016-03-30T17:36:11.404718158Z'}],
                 u'projectId': u'YOUR-PROJECT-ID',
                 u'request': { u'@type': u'type.googleapis.com/google.genomics.v1alpha2.RunPipelineRequest',
                               u'ephemeralPipeline': { u'description': u'Compress or decompress a file',
                                                       u'docker': { u'cmd': u'cd /mnt/data/workspace && for file in $(/bin/ls); do gunzip ${file}; done',
                                                                    u'imageName': u'ubuntu'},
                                                       u'name': u'compress',
                                                       u'parameters': [ { u'description': u'Cloud Storage path to an input file',
                                                                          u'name': u'inputFile0'},
                                                                        { u'description': u'Cloud Storage path for where to FastQC output',
                                                                          u'name': u'outputPath'}],
                                                       u'projectId': u'YOUR-PROJECT-ID',
                                                       u'resources': { u'disks': [ { u'autoDelete': True,
                                                                                     u'name': u'datadisk'}]}},
                               u'pipelineArgs': { u'clientId': u'',
                                                  u'inputs': { u'inputFile0': u'gs://genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/working/20140123_NA12878_Illumina_Platinum/**.vcf.gz'},
                                                  u'logging': { u'gcsPath': u'gs://YOUR-BUCKET/pipelines-api-examples/compress/logging'},
                                                  u'outputs': { u'outputPath': u'gs://YOUR-BUCKET/pipelines-api-examples/compress/output'},
                                                  u'projectId': u'YOUR-PROJECT-ID',
                                                  u'resources': { u'bootDiskSizeGb': 0,
                                                                  u'disks': [ { u'autoDelete': False,
                                                                                u'mountPoint': u'',
                                                                                u'name': u'datadisk',
                                                                                u'readOnly': False,
                                                                                u'sizeGb': 200,
                                                                                u'source': u'',
                                                                                u'type': u'TYPE_UNSPECIFIED'}],
                                                                  u'minimumCpuCores': 0,
                                                                  u'minimumRamGb': 0,
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
                 u'startTime': u'2016-03-30T17:34:36.000Z'},
  u'name': u'operations/YOUR-NEW-OPERATION-ID'}
```

## (2) Check the results

Check the operation output for a top-level `errors` field.
If none, then the operation should have finished successfully.

```
$ gsutil ls gs://YOUR-BUCKET/pipelines-api-examples/compress/output
gs://YOUR-BUCKET/pipelines-api-examples/compress/output/NA12878.wgs.illumina_platinum.20140122.indel.genotypes.vcf
gs://YOUR-BUCKET/pipelines-api-examples/compress/output/NA12878.wgs.illumina_platinum.20140122.snp.genotypes.vcf
gs://YOUR-BUCKET/pipelines-api-examples/compress/output/NA12878.wgs.illumina_platinum.20140404.indels_v2.vcf
gs://YOUR-BUCKET/pipelines-api-examples/compress/output/NA12878.wgs.illumina_platinum.20140404.snps_v2.vcf
gs://YOUR-BUCKET/pipelines-api-examples/compress/output/NA12878.wgs.illumina_platinum.20140404.svs_v2.vcf
```
