# Run a CWL workflow

## This example demonstrates running a multi-stage workflow on Google Cloud Platform

* The workflow is launched with a bash script, [cwl_runner.sh](cwl_runner.sh), that calls the gcloud command-line tool that is included in the [Google Cloud SDK](https://cloud.google.com/sdk)
* The workflow is defined using the [Common Workflow Language (CWL)](http://www.commonwl.org)
* The workflow stages are orchestrated using [cwltool](https://github.com/common-workflow-language/cwltool/tree/master/cwltool) or [rabix](https://github.com/rabix/bunny).

To run a CWL workflow, `cwl_runner.sh` will:

1. Create a disk
1. Create a Compute Engine VM with that disk
1. Run a startup script on the VM

The startup script, [cwl_startup.sh](cwl_startup.sh), will run on the VM and:

1. Mount and format the disk
1. Download input files from Google Cloud Storage
1. Install Docker
1. Install cwltool
1. Run the CWL workflow and wait until completion
1. Copy output files to Google Cloud Storage
1. Copy stdout and stderr logs to Google Cloud Storage
1. Shutdown and delete the VM and disk

__Note that the CWL runner does not use the [Pipelines API](https://cloud.google.com/genomics/reference/rest/v1alpha2/pipelines). If you don't have enough quota, the script will fail; it won't be queued to run when quota is available.__

## Prerequisites

1. Download the required script files, `cwl_runner.sh`, `cwl_startup.sh` and `cwl_shutdown.sh`, or, if you prefer, clone or fork this github repository.
1. Enable the Genomics, Cloud Storage, and Compute Engine APIs on a new or existing Google Cloud Project using the [Cloud Console](https://console.cloud.google.com/flows/enableapi?apiid=storage_component,compute_component&redirect=https://console.cloud.google.com)
1. Install and initialize the [Google Cloud SDK](https://cloud.google.com/sdk).
1. Follow the Cloud Storage instructions for [Creating Storage Buckets](https://cloud.google.com/storage/docs/creating-buckets) to create a bucket to store workflow output and logging

## Running a sample workflow in the cloud

This script should be able to support any CWL workflow supported by cwltool.

You can run the script with `--help` to see all of the command-line options.

```
./cwl_runner.sh --help
```

As an example, let's run a real workflow from the [Genome Data Commons](https://gdc.cancer.gov) stored in a [GDC github project](https://github.com/nci-gdc/gdc-dnaseq-cwl).

This particular workflow requires:

* a reference genome bundle
* a DNA reads file in BAM format
* several CWL tool definitions

All of the required files have already been copied into Google Cloud Storage (at gs://genomics-public-data/cwl-examples/gdc-dnaseq-cwl), so we can just reference them when we run the CWL workflow.

Here's an example command-line:

```
./cwl_runner.sh \
  --workflow-file gs://genomics-public-data/cwl-examples/gdc-dnaseq-cwl/workflows/dnaseq/transform.cwl \
  --settings-file gs://genomics-public-data/cwl-examples/gdc-dnaseq-cwl/input/gdc-dnaseq-input.json \
  --input-recursive gs://genomics-public-data/cwl-examples/gdc-dnaseq-cwl \
  --output gs://MY-BUCKET/MY-PATH \
  --machine-type n1-standard-4
```

Set `MY-BUCKET/MY-PATH` to a path in a Cloud Storage bucket that you have write access to.

The workflow will start running. If all goes well, it should complete in a couple of hours.

Here's some more information about what's happening:

* The command will run the CWL workflow definition located at the `workflow-file` path in Cloud Storage, using the workflow settings in the `settings-file`.
* All path parameters defined in the `settings-file` are relative to the location of the file.
* A reference genome is required as input; the reference genome files are identified by the `input` wildcard path.
* This particular GDC workflow uses lots of relative paths to the definition files for the individual workflow steps. In order to preserve relative paths, the GDC directory is recursively copied from the path passed to `input-recursive`.
* Output files and logs will be written to the `output` folder.
* The whole workflow will run on a single VM instance of the specified `machine-type`.

## Monitoring your workflow

Once your job starts, it will have an `OPERATION-ID` assigned, which you can use to check status and find the VM and disk in your cloud project.

To monitor your job, check the status to see if it's RUNNING, COMPLETED, or FAILED:
```
gsutil cat gs://MY-BUCKET/MY-PATH/status-OPERATION-ID.txt
```

While your job is running, you can see the VM in the [Cloud Console](https://console.cloud.google.com/compute/instances) and command-line. When the job completes, the VM will no longer be found unless `--keep-alive` is set. Command-line:  

```
gcloud compute instances describe cwl-vm-OPERATION-ID
```

## Canceling a job

To cancel a running job, you can terminate the VM from the cloud console or command-line:
```
gcloud compute instances delete cwl-vm-OPERATION-ID
```

## Debugging a job

To debug a failed run, look at the log files in your output directory. 

Cloud console:
```
https://console.cloud.google.com/storage/browser
```

Command-line:
```
gsutil cat gs://MY-BUCKET/MY-PATH/stderr-OPERATION-ID.txt | less
gsutil cat gs://MY-BUCKET/MY-PATH/stdout-OPERATION-ID.txt | less
```

For additional debugging, you can rerun this script with --keep-alive and ssh into the VM.
If you use --keep-alive, you will need to manually delete the VM to avoid charges.
