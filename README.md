# pipelines-api-examples

This repository contains examples for the [Google Genomics Pipelines API]
(https://cloud.google.com/genomics/reference/rest/v1alpha2/pipelines).

The API provides an easy way to create, run, and monitor command-line tools
on Google Compute Engine running in a Docker container. You can use it like
you would a job scheduler.

The most common use case is to run an off-the-shelf tool or custom script
that reads and writes files. You may want to run such a tool over files in
Google Cloud Storage. You may want to run this independently over hundreds
or thousands of files.

The typical flow for a pipeline is:

  1. Create a Compute Engine virtual machine
  1. Copy one or more files from Cloud Storage to a disk
  1. Run the tool on the file(s)
  1. Copy the output to Cloud Storage
  1. Destroy the Compute Engine virtual machine

You can submit batch operations from your laptop, and have them run in the cloud.
You can do the packaging to Docker yourself, or use existing Docker images.

## Prerequisites

1. Clone or fork this repository.
1. If you plan to create your own Docker images, then install docker: https://docs.docker.com/engine/installation/#installation
1. If you have not already done so, follow the Google Genomics [getting started instructions](https://cloud.google.com/genomics/install-genomics-tools) to set up your environment including [installing gcloud](https://cloud.google.com/sdk/) and running `gcloud init`.
1. Install or update the python client via `pip install --upgrade google-api-python-client`.  For more detail see https://cloud.google.com/genomics/v1/libraries.

## Examples

* [Compress a file](./compress)
* [Run FastQC over a list of BAM or FASTQ files](./fastqc)
* [Use samtools to create a BAM index file](./samtools)
* [Use Bioconductor to count overlaps in a BAM file](./bioconductor)

## See Also

* [Pipelines API docs](https://cloud.google.com/genomics/reference/rest/v1alpha2/pipelines)
* [PyDocs](https://developers.google.com/resources/api-libraries/documentation/genomics/v1alpha2/python/latest/)
