#!/usr/bin/env Rscript

# Copyright 2017 Google Inc.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

# This example is adapted from Bioconductor Vignette:
#   https://bioconductor.org/packages/release/bioc/vignettes/BiocParallel/inst/doc/Introduction_To_BiocParallel.pdf

library(GenomicAlignments) ## for GenomicRanges and readGAlignments()

# Update this to choose a different genomic region
# or modify this script to take a parameter for this value.
gRanges = GRanges("MT", IRanges((1000:3999)*10, width=1000))

# These file paths are relative to the Docker container. Do not update them
# without making the corresponding changes in the pipeline definition.
bamFile = "input.bam"
bamIndex = "input.bam.bai"
outputFile = "overlapsCount.tsv"

param = ScanBamParam(which=range(gRanges))

# Retrieve the BAM header information. This information is added to the output
# so that if we run this pipeline on many different BAM files, we can
# differentiate between results
header = scanBamHeader(bamFile, index=bamIndex, param=param)

# Retrieve the alignments overlapping the desired regions.
gal <- readGAlignments(file = bamFile, index = bamIndex, param = param)

# This just a simple sum, but a more elaborate analysis could occur here.
count = sum(countOverlaps(gRanges, gal))

# In this case our output is simply one tab-separated row of data,
# but it could be a dataframe, an image, a serialized R object, etc...
result = paste(
  paste(header$input.bam$text$`@RG`,
        collapse="\t"),
  count,
  sep="\t")

write(result, file = outputFile)
