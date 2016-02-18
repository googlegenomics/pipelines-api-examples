# pipelines-api-examples

This repository contains examples for the Pipelines API.

The pipelines API is an easy way to create, run, and monitor command-line tools on Google Compute Engine in a Docker container. You can use it like you would a job scheduler. Input files are copied from a Cloud Storage bucket to a local disk, and output files are copied back to Cloud Storage. You can submit batch operations from your laptop, and have them run in the cloud, using any tools that you can package up with Docker, or that someone has already packaged up and shared.

## Prerequisites

1. Clone or fork this repository.
1. If you have not already done so, install docker: https://docs.docker.com/engine/installation/#installation
1. If you have not already done so, follow the Google Genomics [getting started instructions](https://cloud.google.com/genomics/install-genomics-tools) to set up your environment including [installing gcloud](https://cloud.google.com/sdk/) and running `gcloud init`.
1. Install or update the python client via `pip install --upgrade google-api-python-client`.  For more detail see https://cloud.google.com/genomics/v1/libraries.

## Examples

* [Use samtools to create a BAM index file](./samtools)

## See Also

* [Pipelines API docs](https://cloud.google.com/genomics/reference/rest/v1alpha2/pipelines)
* [PyDocs](https://developers.google.com/resources/api-libraries/documentation/genomics/v1alpha2/python/latest/)
