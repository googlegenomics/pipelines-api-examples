# Run a CWL workflow

## This example demonstrates running a multi-stage workflow on Google Cloud Platform

* The workflow is launched with a bash script that calls the [Google Cloud SDK](https://cloud.google.com/sdk)
* The workflow is defined using the [Common Workflow Language (CWL)](http://www.commonwl.org)
* The workflow stages are orchestrated using [cwltool](https://github.com/common-workflow-language/cwltool/tree/master/cwltool)

Here's what the bash script does to run a CWL workflow:
1. Create a disk
1. Create a Compute Engine VM with that disk
1. Run a startup script on the VM

The startup script running on the VM will:
1. Mount and format the disk
1. Download input files from Google Cloud Storage
1. Install Docker
1. Install cwltool
1. Run the CWL workflow and wait until completion
1. Copy output files to Google Cloud Storage
1. Copy stdout and stderr logs to Google Cloud Storage
1. Shutdown and delete the VM and disk

## Prerequisites

1. Download the one required file, `cwl_runner.sh`, or, if you prefer, clone or fork this github repository.
1. Enable the Genomics, Cloud Storage, and Compute Engine APIs on a new or existing Google Cloud Project using the [Cloud Console](https://console.cloud.google.com/flows/enableapi?apiid=storage_component,compute_component&redirect=https://console.cloud.google.com)
1. Install and initialize the [Google Cloud SDK](https://cloud.google.com/sdk).
1. Follow the Cloud Storage instructions for [Creating Storage Buckets](https://cloud.google.com/storage/docs/creating-buckets) to create a bucket to store workflow output and logging

## Running a sample workflow in the cloud

This script can (in theory!) run any CWL workflow.

You can run the script with `--help` to see all of the command-line options.

```
./cwl_runner.sh --help
```

As an example, let's run a real workflow from the [Genome Data Commons](https://gdc.cancer.gov) stored in a [GDC github project](https://github.com/nci-gdc/gdc-dnaseq-cwl).

This particular workflow requires a reference genome bundle, a DNA reads file in BAM format, and several CWL tool definitions. All of those files have already been copied into a Cloud Storage bucket, so we can just reference them when we run the CWL workflow.

Here's an example command-line:

```
./cwl_runner.sh \
  --workflow-file gs://jbingham-scratch/gdc-dnaseq-cwl/workflows/dnaseq/transform.cwl \
  --settings-file gs://jbingham-scratch/cwl/input/gdc-dnaseq-input.json \
  --input-recursive gs://jbingham-scratch/gdc-dnaseq-cwl \
  --input gs://jbingham-scratch/cwl/input/* \
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

To monitor your job from the cloud console, go to:

```
https://console.cloud.google.com/compute/instances
```

To monitor your job from the command-line, run:

```
gcloud compute instances describe cwl-vm-14011 
```

While your VM is running, you can describe it. 
When the workflow completes, the VM will no longer be found.

## Troubleshooting

To debug a failed run, look at the log files in your output directory. 
From the cloud console, go to:

```
https://console.cloud.google.com/storage/browser
```

From the command-line:

```
gsutil cat gs://jbingham-scratch/cwl/output/stderr-14011.txt | less
gsutil cat gs://jbingham-scratch/cwl/output/stdout-14011.txt | less
```

For additional debugging, you can rerun this script with --keep-alive and ssh into the VM.
If you use --keep-alive, you will need to manually delete the VM to avoid charges.
