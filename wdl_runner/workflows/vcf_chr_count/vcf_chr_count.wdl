# Copyright 2017 Google Inc.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

# vcf_chr_count.wdl
#
# Example workflow which features 3 stages, including a scatter-gather
# stage. The workflow takes as input a VCF file and a comma-separated list
# of chromosomes. The output is a list of each chromosome and the number
# of matching records in the VCF file.
#
# This workflow is NOT the most efficient way to perform this operation
# (as it creates separate pipelines/VMs for some very short stages),
# but is intended as a simple example to demonstrate how to create a
# multi-stage workflow and use a scatter stage.
#
# The first stage splits the VCF into separate files for each chromosome
# in the input list. Each chromosome must exactly match the value in the
# CHROM column (so be sure to use "chr7" instead of "7" if that is the
# value in the CHROM column).
#
# The second stage is a "scatter" stage such that each file is processed
# separately. The individual tasks simply run a wordcount for the total
# number of lines.
#
# The third stage aggregates (gathers) the results of the scatter stage.

# task vcf_split
#
# Accepts a VCF as an input file, along with a comma-separated
# list of chromosome names. The records from the VCF whose CHROM field
# matching the chromosome will be emitted to a chromosome-specific file.
task vcf_split {
  File file
  String chrList

  command <<<
  python - "${file}" "${chrList}" <<CODE

  import sys

  def f_open(chr, chr_list):
    """Opens an output file <chr>.vcf.

    The file is only opened if the chr is in the chr_list or if the
    chr_list is empty.
    """

    if chr in chr_list or not chr_list:
      return open('%s.vcf' % curr_chr, 'w')

    return None

  def f_write(file, line):
    """Writes a line to a file only if the file is not 'None'."""
    if file:
      file.write(line)

  def f_close(file):
    """Closes a file only if the file is not 'None'."""
    if file:
      file.close()

  # Split the input chromosome list
  chr_list = sys.argv[2].split(',') if sys.argv[2] else None

  with open(sys.argv[1]) as f:
    curr_file = None
    curr_chr = ''

    for line in f:
      # Skip all headers
      if line.startswith('#'):
        continue

      # Get the current CHROM field value
      chr = line.split('\t', 2)[0]
      if chr != curr_chr:
        curr_chr = chr
        f_close(curr_file)

        # Open the chromosome-specific file <chr>.vcf
        curr_file = f_open(curr_chr, chr_list)

      # Write the record to the chromosome-specific file
      f_write(curr_file, line)

    f_close(curr_file)

  CODE
  >>>
  output {
    Array[File] outFiles = glob("chr*.vcf")
  }
  runtime {
    docker: "python:2.7"
  }
}

# task vcf_record_count
#
# Takes as input a file name, and emits as output a single line:
#   <filename> <line count>
task vcf_record_count {
  File file

  command <<<
    echo "$(basename ${file}) $(cat ${file} | wc -l)"
  >>>
  output {
    String out = read_string(stdout())
  }
  runtime {
    docker: "ubuntu:latest"
  }
}

# task gather
#
# Takes as input an array of strings and emits them as a sorted set of lines,
task gather {
  Array[String] array

  command <<<
    echo "${sep='\n' array}" | sort > output.txt
  >>>
  output {
    File outFile = "output.txt"
  }
  runtime {
    docker: "ubuntu:latest"
  }
}

# workflow vcf_chr_count
#
# See the file header for full description.
workflow vcf_chr_count {
  File vcf_file
  String chrList

  call vcf_split {
    input: file=vcf_file, chrList=chrList
  }
  scatter (chr_file in vcf_split.outFiles) {
    call vcf_record_count {input: file=chr_file}
  }
  call gather {input: array=vcf_record_count.out}

  output {
    gather.outFile
  }
}
