# Run FASTQC on a list of BAM or FASTQ files

## (1) Create the Docker image.
```
git clone https://github.com/googlegenomics/pipelines-api-examples.git
cd pipelines-api-examples/fastqc/
docker build -t ${USER}/fastqc .
```
## (2) Test locally the Docker image used by the pipeline.
```
./local/test_fastqc.sh
```

The result should be the newly created .html and .zip file in a subdirectory
on your local machine:
```
Copying test file NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam to <snip>/pipelines-api-examples/src/test_mnt
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 26534  100 26534    0     0   6983      0  0:00:03  0:00:03 --:--:--  6982

Running fastqc index via docker
Started analysis of NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam
Analysis complete for NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam

Execution completed

Scratch directory:
.
./output
./output/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311_fastqc.zip
./output/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311_fastqc.html
./input
./input/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam
```

## (3) Push the Docker image to a repository.
In this example, we push the container to [Google Container Registry](https://cloud.google.com/container-registry/) via the following commands:
```
docker tag ${USER}/fastqc gcr.io/YOUR-PROJECT-ID/fastqc
gcloud docker push gcr.io/YOUR-PROJECT-ID/fastqc
```

## (4) Run the Docker image in the cloud
```
PYTHONPATH=.. python cloud/run_fastqc.py \
  --project YOUR-PROJECT-ID \
  --zones us-* \
  --disk-size 100 \
  --input \
    gs://genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/pilot3_exon_targetted_GRCh37_bams/data/NA06986/alignment/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam \
    gs://genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/pilot3_exon_targetted_GRCh37_bams/data/NA18628/alignment/NA18628.chromY.LS454.ssaha2.CHB.exon_targetted.20100311.bam \
  --output gs://YOUR-BUCKET/fastqc/output \
  --logging gs://YOUR-BUCKET/fastqc/logging \
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
                 u'createTime': u'2016-03-10T02:01:42.000Z',
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
                 u'createTime': u'2016-03-10T02:01:42.000Z',
                 u'endTime': u'2016-03-10T02:04:52.000Z',
                 u'events': [ { u'description': u'start(g1-small)',
                                u'startTime': u'2016-03-10T02:03:01.000Z'},
                              { u'description': u'pulling-image',
                                u'startTime': u'2016-03-10T02:03:11.000Z'},
                              { u'description': u'localizing-files',
                                u'startTime': u'2016-03-10T02:03:50.000Z'},
                              { u'description': u'running-docker',
                                u'startTime': u'2016-03-10T02:04:07.000Z'},
                              { u'description': u'delocalizing-files',
                                u'startTime': u'2016-03-10T02:04:29.000Z'},
                              { u'description': u'ok',
                                u'startTime': u'2016-03-10T02:04:43.000Z'}],
                 u'projectId': u'YOUR-PROJECT-ID',
                 u'request': { u'@type': u'type.googleapis.com/google.genomics.v1alpha2.RunPipelineRequest',
                               u'ephemeralPipeline': { u'description': u'Run "FastQC" on one or more files',
                                                       u'docker': { u'cmd': u'mkdir /mnt/data/output && fastqc /mnt/data/input/* --outdir=/mnt/data/output/',
                                                                    u'imageName': u'gcr.io/YOUR-PROJECT-ID/fastqc'},
                                                       u'name': u'fastqc',
                                                       u'parameters': [ { u'description': u'Cloud Storage path to an input file',
                                                                          u'name': u'inputFile0'},
                                                                        { u'description': u'Cloud Storage path to an input file',
                                                                          u'name': u'inputFile1'},
                                                                        { u'description': u'Cloud Storage path for where to FastQC output',
                                                                          u'name': u'outputPath'}],
                                                       u'projectId': u'YOUR-PROJECT-ID',
                                                       u'resources': { u'disks': [ { u'autoDelete': True,
                                                                                     u'name': u'datadisk',
                                                                                     u'sizeGb': 500,
                                                                                     u'type': u'PERSISTENT_HDD'}],
                                                                       u'minimumCpuCores': 1,
                                                                       u'minimumRamGb': 3.75}},
                               u'pipelineArgs': { u'clientId': u'',
                                                  u'inputs': { u'inputFile0': u'gs://genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/pilot3_exon_targetted_GRCh37_bams/data/NA06986/alignment/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam',
                                                               u'inputFile1': u'gs://genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/pilot3_exon_targetted_GRCh37_bams/data/NA18628/alignment/NA18628.chromY.LS454.ssaha2.CHB.exon_targetted.20100311.bam'},
                                                  u'logging': { u'gcsPath': u'gs://YOUR-BUCKET/fastqc/logging'},
                                                  u'outputs': { u'outputPath': u'gs://YOUR-BUCKET/fastqc/output'},
                                                  u'projectId': u'YOUR-PROJECT-ID',
                                                  u'resources': { u'disks': [ { u'autoDelete': True,
                                                                                u'mountPoint': u'',
                                                                                u'name': u'datadisk',
                                                                                u'readOnly': False,
                                                                                u'sizeGb': 100,
                                                                                u'source': u'',
                                                                                u'type': u'PERSISTENT_HDD'}],
                                                                  u'minimumCpuCores': 0,
                                                                  u'minimumRamGb': 1,
                                                                  u'preemptible': False,
                                                                  u'zones': [ u'us-central1-a',
                                                                              u'us-central1-b',
                                                                              u'us-central1-c',
                                                                              u'us-central1-f']},
                                                  u'serviceAccount': { u'email': u'default',
                                                                       u'scopes': [ u'https://www.googleapis.com/auth/compute',
                                                                                    u'https://www.googleapis.com/auth/devstorage.full_control',
                                                                                    u'https://www.googleapis.com/auth/genomics']}}},
                 u'startTime': u'2016-03-10T02:02:09.000Z'},
  u'name': u'operations/YOUR-NEW-OPERATION-ID'}
```

## (5) Check the results

Check the operation output for a top-level `erors` field.
If none, then the operation should have finished successfully.

Navigate to your bucket in the
[Cloud Console](https://console.cloud.google.com/project/_/storage)
to see the output and log files for the operation.
