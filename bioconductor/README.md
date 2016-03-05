# Use Bioconductor to count overlaps in a BAM file

This example counts the number of reads overlapping a particular region in the genome.

It uses:

* a [Bioconductor Docker container](https://bioconductor.org/help/docker/)
* an [R script](./countOverlapsFromBAM.R)
* and BAM file and index.

It emits a one-line TSV file containing the count of overlapping reads and metadata identifying the sample from which the result was obtained.

This simplistic example could be extended to:

* Run a more interesting Bioconductor analysis on the BAM file.
* Loop over, for example, all the 1000 Genomes phase 3 BAMs in [gs://genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/phase3/data/\*/high_coverage_alignment/\*.bam](https://console.cloud.google.com/storage/browser/genomics-public-data/ftp-trace.ncbi.nih.gov/1000genomes/ftp/phase3/data/HG00096/high_coverage_alignment/), kicking off the parallel execution of this pipeline on each sample and emitting a distinct output file for each result.

## (1) Fetch the Docker container.
```
docker pull bioconductor/release_core
```
## (2) Test the pipeline locally.
```
wget -O input.bam \
  ftp://ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/pilot3_exon_targetted_GRCh37_bams/data/NA06986/alignment/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam

wget -O input.bam.bai \
  ftp://ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/pilot3_exon_targetted_GRCh37_bams/data/NA06986/alignment/NA06986.chromMT.ILLUMINA.bwa.CEU.exon_targetted.20100311.bam.bai

docker run -v `pwd`:/mnt/data bioconductor/release_core \
  /bin/bash -c "cd /mnt/data/ ; R CMD BATCH countOverlapsFromBAM.R"
```

The result should a one-line TSV file and also the log from the R batch command:
```
~$ cat overlapsCount.tsv
ID:SRR003486	PL:ILLUMINA	LB:Solexa-5005	PI:0	DS:SRP000033	SM:NA06986	CN:BI	20626

~$ cat countOverlapsFromBAM.Rout

R version 3.2.3 RC (2015-12-03 r69731) -- "Wooden Christmas-Tree"
Copyright (C) 2015 The R Foundation for Statistical Computing
Platform: x86_64-pc-linux-gnu (64-bit)
. . .
```
## (3) Upload the script to Cloud Storage.
```
gsutil cp countOverlapsFromBAM.R gs://YOUR-BUCKET/pipelines-api-examples/bioconductor/script.R
```
## (4) Run the pipeline on the cloud.
Edit your copy of [run_bioconductor.py](./run_bioconductor.py) to specify:

  1. The id of the Google Cloud Platform project in which the pipeline should run.
  1. The bucket in which the pipeline output file and log files should be placed.

And then run the script:
```
 python ./run_bioconductor.py
```

It will emit the operation id and poll for completion.

## (5) View the resultant files.
Navigate to your bucket in the [Cloud Console](https://console.cloud.google.com/project/_/storage) to see the resultant TSV file and log files for the operation.

