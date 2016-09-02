# Use samtools to create a BAM index file

This example will enable you to create an index file (BAI) for a BAM, using [samtools](http://www.htslib.org/).
Execution of the `samtools index` command will be on a [Google Compute Engine](https://cloud.google.com/compute/docs/)
virtual machine.

Instructions provided here demonstrate:

1. Building a Docker image containing `samtools`
1. Testing the Docker image by running it on your local workstation/laptop
1. Pushing the Docker image to the Google Container Registry
1. Launching and monitoring the pipeline using command-line tools (`gcloud`)
1. Launching and monitoring the pipeline calling the Genomics API from Python

The `gcloud` command supports defining your pipeline in a JSON or YAML file and then setting per-run parameters from the command line.

The Python example demonstrates full control over the construction of `pipeline.run()` API call.

## (0) Complete the prerequisites

Be sure you have completed the [Prerequisites](../README.md#prerequisites)
listed at the top of this github repository.

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

## (4) Run the Docker image in the cloud, using gcloud

The `gcloud` tool that comes with the Google Cloud SDK includes a command
to run pipelines. You can get details of the command with:

```
gcloud alpha genomics pipelines run --help
```

### (4a) Run the Docker image in the cloud, using gcloud

To run this example, first edit the included [./cloud/samtools.yaml](./cloud/samtools.yaml) file:

* Replace `YOUR-PROJECT-ID` with your project ID.

### (4b) Execute the `pipelines run` command:

```
gcloud alpha genomics pipelines run \
  --pipeline-file cloud/samtools.yaml \
  --inputs inputPath=gs://genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/pilot3_exon_targetted_GRCh37_bams/data/NA06986/alignment/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam \
  --outputs outputPath=gs://YOUR-BUCKET/pipelines-api-examples/samtools/gcloud/output/ \
  --logging gs://YOUR-BUCKET/pipelines-api-examples/samtools/gcloud/logging/ \
  --disk-size datadisk:100
Running: [operations/YOUR-NEW-OPERATION-ID]
```

* Replace `YOUR-BUCKET` with a bucket in your project.

### (4c) Monitor the pipeline operation

This github repo includes a shell script, [../tools/poll.sh](../tools/poll.sh), for monitoring the completion status of an operation.

```
$ ../tools/poll.sh YOUR-NEW-OPERATION-ID 20
Operation not complete. Sleeping 20 seconds
Operation not complete. Sleeping 20 seconds
...
Operation not complete. Sleeping 20 seconds

Operation complete
done: true
metadata:
  events:
  - description: start
    startTime: '2016-05-04T17:22:16.258279445Z'
  - description: pulling-image
    startTime: '2016-05-04T17:22:16.258324967Z'
  - description: localizing-files
    startTime: '2016-05-04T17:22:27.650908389Z'
  - description: running-docker
    startTime: '2016-05-04T17:22:30.615818360Z'
  - description: delocalizing-files
    startTime: '2016-05-04T17:22:31.100643739Z'
  - description: ok
    startTime: '2016-05-04T17:22:34.669517713Z'
name: operations/YOUR-NEW-OPERATION-ID
```

### (4d) Check the results

Check the operation output for a top-level `errors` field.
If none, then the operation should have finished successfully.

```
$ gsutil ls gs://YOUR-BUCKET/pipelines-api-examples/samtools/gcloud/output
gs://YOUR-BUCKET/pipelines-api-examples/samtools/gcloud/output/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam.bai
```

## (5) Run the Docker image in the cloud, using the Python client libraries

The `run_samtools.py` script demonstrates having full programmatic control
over the pipelines.run() API call.

## (5a) Run the Docker image in the cloud

```
PYTHONPATH=.. python cloud/run_samtools.py \
  --project YOUR-PROJECT-ID \
  --zones "us-*" \
  --disk-size 100 \
  --input \
    gs://genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/pilot3_exon_targetted_GRCh37_bams/data/NA06986/alignment/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam \
    gs://genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/pilot3_exon_targetted_GRCh37_bams/data/NA18628/alignment/NA18628.chromY.LS454.ssaha2.CHB.exon_targetted.20100311.bam \
  --output gs://YOUR-BUCKET/pipelines-api-examples/samtools/python/output/ \
  --logging gs://YOUR-BUCKET/pipelines-api-examples/samtools/python/logging \
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
...
                 u'startTime': u'2016-03-31T04:23:46.000Z'},
  u'name': u'operations/YOUR-NEW-OPERATION-ID'}
```

## (5b) Check the results

Check the operation output for a top-level `errors` field.
If none, then the operation should have finished successfully.

```
$ gsutil ls gs://YOUR-BUCKET/pipelines-api-examples/samtools/python/output/
gs://YOUR-BUCKET/pipelines-api-examples/samtools/python/output/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam.bai
gs://YOUR-BUCKET/pipelines-api-examples/samtools/python/output/NA18628.chromY.LS454.ssaha2.CHB.exon_targetted.20100311.bam.bai
```

