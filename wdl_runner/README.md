# Run a WDL workflow

## Overview

This example demonstrates running a multi-stage workflow on
Google Cloud Platform.

* The workflow is launched with the Google Genomics [Pipelines API](https://cloud.google.com/genomics/v1alpha2/pipelines).
* The workflow is defined using the Broad Institute's
[Workflow Definition Language](https://software.broadinstitute.org/wdl/) (WDL).
* The workflow stages are orchestrated by the Broad Institute's
[Cromwell](https://github.com/broadinstitute/cromwell).

When submitted using the Pipelines API, the workflow runs
on multiple [Google Compute Engine](https://cloud.google.com/compute/)
virtual machines.
First a master node is created for Cromwell, and then Cromwell submits
each stage of the workflow as one or more separate pipelines.

Execution of a running Pipeline proceeds as:

1. Create Compute Engine virtual machine

2. Execute wdl_runner.py

    a. Run Cromwell (server)

    b. Submit workflow, inputs, and options to Cromwell server

    c. Poll for completion as Cromwell executes:

        1) Call pipelines.run() to execute call 1
        2) Poll for completion of call 1
        3) Call pipelines.run() to execute call 2
        4) Poll for completion of call 2
        5) Call pipelines.run() to execute call 3
        6) Poll for completion of call 3

    d. Copy workflow metadata to output path

    e. Copy workflow outputs to output path

3. Destroy Compute Engine Virtual machine

## Setup Overview

Code packaging for the Pipelines API is typically done through
[Docker](https://www.docker.com/) images.  The instructions provided
here give you two options for running the Pipeline:

* Create your own Docker image containing all orchestration code
* Use a stock Docker image and pull orchestration code directly from github

Creating your own Docker image provides the best runtime performance,
along with the greatest control and reliabilty of the running code.

Pulling from github at runtime provides the simplest getting started experience,
but with the cost and the potential for failure that comes with code download
and installation from multiple sources.

### Code summary

The code pulled to the pipeline's master VM includes:

* [OpenJDK 8](http://openjdk.java.net/projects/jdk8/) runtime engine (JRE)
* [Python 2.7](https://www.python.org/download/releases/2.7/) interpreter
* [Cromwell release 0.19](https://github.com/broadinstitute/cromwell/releases/tag/0.19)
* [Python and shell scripts from this repository](./src)

## (0) Prerequisites

1. Clone or fork this repository.

2. If you plan to create your own Docker images, then
[install docker](https://docs.docker.com/engine/installation/#installation)

3. Enable the Genomics, Cloud Storage, and Compute Engine APIs on a new
   or existing Google Cloud Project using the [Cloud Console](https://console.cloud.google.com/flows/enableapi?apiid=genomics,storage_component,compute_component&redirect=https://console.cloud.google.com)

4. Follow the Google Genomics [getting started instructions](https://cloud.google.com/genomics/install-genomics-tools#install-genomics-tools) to install and authorize the Google Cloud SDK.

5. Follow the Cloud Storage instructions for [Creating Storage Buckets](https://cloud.google.com/storage/docs/creating-buckets) to create a bucket for workflow output and logging 

## (1) Create and stage the wdl_runner Docker image

*If you are going to have code downloaded from github at pipeline runtime, skip
this step.*

Every Google Cloud project provides a private repository for saving and
serving Docker images called the [Google Container Registry](https://cloud.google.com/container-registry/docs/).

The following instructions allow you to stage a Docker image in your project's
Container Registry with all necessary code for orchestrating your workflow.

### (1a) Create the Docker image.

```
git clone https://github.com/googlegenomics/pipelines-api-examples.git
cd pipelines-api-examples/wdl_runner/
docker build -t ${USER}/wdl_runner ./cromwell_launcher
```

### (1b) Push the Docker image to a repository.

In this example, we push the container to
[Google Container Registry](https://cloud.google.com/container-registry/)
via the following commands:

```
docker tag ${USER}/wdl_runner gcr.io/YOUR-PROJECT-ID/wdl_runner
gcloud docker push gcr.io/YOUR-PROJECT-ID/wdl_runner
```

* Replace `YOUR-PROJECT-ID` with your project ID.

## (2) Run the sample workflow in the cloud

### Run the pipeline, pulling code from github

#### Run the following command:

```
gcloud \
  alpha genomics pipelines run \
  --pipeline-file workflows/wdl_pipeline_from_git.yaml \
  --zones us-central1-f \
  --logging gs://YOUR-BUCKET/pipelines-api-examples/wdl_runner/logging \
  --inputs-from-file WDL=workflows/vcf_chr_count/vcf_chr_count.wdl \
  --inputs-from-file WORKFLOW_INPUTS=workflows/vcf_chr_count/vcf_chr_count.sample.inputs.json \
  --inputs-from-file WORKFLOW_OPTIONS=workflows/common/basic.jes.us.options.json \
  --inputs WORKSPACE=gs://YOUR-BUCKET/pipelines-api-examples/wdl_runner/workspace \
  --inputs OUTPUTS=gs://YOUR-BUCKET/pipelines-api-examples/wdl_runner/output
```

* Replace `YOUR-BUCKET` with a bucket in your project.

The output will be an operation ID for the Pipeline.

### Run the pipeline, using the wdl_runner Docker image

#### Edit the file [./workflows/wdl_pipeline.yaml](./workflows/wdl_pipeline.yaml).

* Replace `YOUR-PROJECT-ID` with your project ID.

#### Run the following command:

```
gcloud \
  alpha genomics pipelines run \
  --pipeline-file workflows/wdl_pipeline.yaml \
  --zones us-central1-f \
  --logging gs://YOUR-BUCKET/pipelines-api-examples/wdl_runner/logging \
  --inputs-from-file WDL=workflows/vcf_chr_count/vcf_chr_count.wdl \
  --inputs-from-file WORKFLOW_INPUTS=workflows/vcf_chr_count/vcf_chr_count.sample.inputs.json \
  --inputs-from-file WORKFLOW_OPTIONS=workflows/common/basic.jes.us.options.json \
  --inputs WORKSPACE=gs://YOUR-BUCKET/pipelines-api-examples/wdl_runner/workspace \
  --inputs OUTPUTS=gs://YOUR-BUCKET/pipelines-api-examples/wdl_runner/output
```

* Replace `YOUR-BUCKET` with a bucket in your project.

The output will be an operation ID for the Pipeline.

## (3) Monitor the pipeline operation

This github repo includes a shell script, [../tools/poll.sh](../tools/poll.sh), for monitoring the completion status of an operation.

```
$../tools/poll.sh YOUR-NEW-OPERATION-ID
Operation not complete. Sleeping 20 seconds
Operation not complete. Sleeping 20 seconds
...
Operation not complete. Sleeping 20 seconds

Operation complete
done: true
metadata:
  '@type': type.googleapis.com/google.genomics.v1.OperationMetadata
  clientId: ''
  createTime: '2016-06-23T18:22:31.000Z'
  endTime: '2016-06-23T18:41:18.000Z'
...
  startTime: '2016-06-23T18:22:42.000Z'
name: operations/YOUR-NEW-OPERATION-ID
```

## (4) Check the results

Check the operation output for a top-level `errors` field.
If none, then the operation should have finished successfully.

## (5) Check that the output exists

```
$ gsutil ls -l gs://YOUR-BUCKET/pipelines-api-examples/wdl_runner/output
        46  2016-06-23T18:41:14Z  gs://YOUR-BUCKET/pipelines-api-examples/wdl_runner/output/output.txt
     12979  2016-06-23T18:41:11Z  gs://YOUR-BUCKET/pipelines-api-examples/wdl_runner/output/wdl_run_metadata.json
TOTAL: 2 objects, 13025 bytes (12.72 KiB)
```

* Replace `YOUR-BUCKET` with a bucket in your project.

## (6) Check the output

```
$ gsutil cat gs://YOUR-BUCKET/pipelines-api-examples/wdl_runner/output/output.txt
chrM.vcf 197
chrX.vcf 4598814
chrY.vcf 653100
```

* Replace `YOUR-BUCKET` with a bucket in your project.

## (7) Clean up the intermediate workspace files

When Cromwell runs, per-stage output and other intermediate files are
written to the WORKSPACE path you specified in the `gcloud` command above.

To remove these files, run:

```
gsutil -m rm gs://YOUR-BUCKET/pipelines-api-examples/wdl_runner/workspace/**
```

* Replace `YOUR-BUCKET` with a bucket in your project.

# Running reproducible workflows

To ensure that the same software is used for each run of your workflows,
create a Docker image as described above, and use the ``wdl_pipeline.yaml``
file.

If you prefer not to build your own Docker image, but instead use
``wdl_pipeline_from_git.yaml``, then for each run of a workflow, the master
node that runs Cromwell will download the latest version of:

* [java:openjdk-8-jre Docker image](https://hub.docker.com/_/openjdk/)
* [Python runtime](https://packages.debian.org/jessie/python)
* [Google Cloud SDK](https://cloud.google.com/sdk/)
* [Python pip](https://packages.debian.org/jessie/python/python-pip)
* [Python requests](https://pypi.python.org/pypi/requests)
* [Google Python Client](https://github.com/google/google-api-python-client)

and will download a fixed version of Cromwell.

You may want to ensure that changes to *this* repository do not impact the
reproducibility or reliability of your workflows. You can select a specific
software commit for this repository by passing the `GIT_BRANCH` pipeline
argument. For example, adding:

  --inputs GIT_BRANCH=f412317d5a34de3c239d161bd27a84cee1b1438e

to the ``gcloud ... genomics pipelines run`` command will ensure that the
code used to download and launch Cromwell is from time of the
[Aug 10, 2016 commit](https://github.com/googlegenomics/pipelines-api-examples/commit/f412317d5a34de3c239d161bd27a84cee1b1438e).

You can see a list of commits in this repository [on github](/commits/master)
or with the command:

  git log

from within your clone of the repository.
