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
Running samtools index via Docker

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

## (4) Run the Docker image in the cloud
```
PYTHONPATH=.. python cloud/run_samtools.py \
  --project YOUR-PROJECT-ID \
  --zones "us-*" \
  --disk-size 100 \
  --input \
    gs://genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/pilot3_exon_targetted_GRCh37_bams/data/NA06986/alignment/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam \
    gs://genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/pilot3_exon_targetted_GRCh37_bams/data/NA18628/alignment/NA18628.chromY.LS454.ssaha2.CHB.exon_targetted.20100311.bam \
  --output gs://YOUR-BUCKET/pipelines-api-examples/samtools/output \
  --logging gs://YOUR-BUCKET/pipelines-api-examples/samtools/logging \
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
                 u'createTime': u'2016-03-31T04:23:17.000Z',
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
                 u'createTime': u'2016-03-31T04:23:17.000Z',
                 u'endTime': u'2016-03-31T04:25:08.000Z',
                 u'events': [ { u'description': u'start',
                                u'startTime': u'2016-03-31T04:24:44.636717470Z'},
                              { u'description': u'pulling-image',
                                u'startTime': u'2016-03-31T04:24:44.637120289Z'},
                              { u'description': u'localizing-files',
                                u'startTime': u'2016-03-31T04:24:58.338833235Z'},
                              { u'description': u'running-docker',
                                u'startTime': u'2016-03-31T04:25:04.834650298Z'},
                              { u'description': u'delocalizing-files',
                                u'startTime': u'2016-03-31T04:25:05.369221780Z'},
                              { u'description': u'ok',
                                u'startTime': u'2016-03-31T04:25:08.447627565Z'}],
                 u'projectId': u'YOUR-PROJECT-ID',
                 u'request': { u'@type': u'type.googleapis.com/google.genomics.v1alpha2.RunPipelineRequest',
                               u'ephemeralPipeline': { u'description': u'Run samtools on one or more files',
                                                       u'docker': { u'cmd': u'mkdir /mnt/data/output && find /mnt/data/input && for file in $(/bin/ls /mnt/data/input); do samtools index /mnt/data/input/${file} /mnt/data/output/${file}.bai; done',
                                                                    u'imageName': u'gcr.io/YOUR-PROJECT-ID/samtools'},
                                                       u'name': u'samtools',
                                                       u'parameters': [ { u'description': u'Cloud Storage path to an input file',
                                                                          u'name': u'inputFile0'},
                                                                        { u'description': u'Cloud Storage path to an input file',
                                                                          u'name': u'inputFile1'},
                                                                        { u'description': u'Cloud Storage path for where to samtools output',
                                                                          u'name': u'outputPath'}],
                                                       u'projectId': u'YOUR-PROJECT-ID',
                                                       u'resources': { u'disks': [ { u'autoDelete': True,
                                                                                     u'name': u'datadisk'}]}},
                               u'pipelineArgs': { u'clientId': u'',
                                                  u'inputs': { u'inputFile0': u'gs://genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/pilot3_exon_targetted_GRCh37_bams/data/NA06986/alignment/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam',
                                                               u'inputFile1': u'gs://genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/pilot3_exon_targetted_GRCh37_bams/data/NA18628/alignment/NA18628.chromY.LS454.ssaha2.CHB.exon_targetted.20100311.bam'},
                                                  u'logging': { u'gcsPath': u'gs://YOUR-BUCKET/pipelines-api-examples/samtools/logging'},
                                                  u'outputs': { u'outputPath': u'gs://YOUR-BUCKET/pipelines-api-examples/samtools/output'},
                                                  u'projectId': u'YOUR-PROJECT-ID',
                                                  u'resources': { u'bootDiskSizeGb': 0,
                                                                  u'disks': [ { u'autoDelete': False,
                                                                                u'mountPoint': u'',
                                                                                u'name': u'datadisk',
                                                                                u'readOnly': False,
                                                                                u'sizeGb': 100,
                                                                                u'source': u'',
                                                                                u'type': u'TYPE_UNSPECIFIED'}],
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
                 u'startTime': u'2016-03-31T04:23:46.000Z'},
  u'name': u'operations/YOUR-NEW-OPERATION-ID'}
```

## (5) Check the results

Check the operation output for a top-level `errors` field.
If none, then the operation should have finished successfully.

```
$ gsutil ls gs://YOUR-BUCKET/pipelines-api-examples/samtools/output
gs://YOUR-BUCKET/pipelines-api-examples/samtools/output/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam.bai
gs://YOUR-BUCKET/pipelines-api-examples/samtools/output/NA18628.chromY.LS454.ssaha2.CHB.exon_targetted.20100311.bam.bai
```
