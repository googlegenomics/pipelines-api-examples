# Copyright 2017 Google Inc.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

FROM java:8
MAINTAINER Matt Bookman <mbookman@google.com>

# Download FASTQC unzip it and link it to /usr/bin
RUN wget http://www.bioinformatics.babraham.ac.uk/projects/fastqc/fastqc_v0.11.4.zip && \
  unzip fastqc_v0.11.4.zip && \
  chmod +x FastQC/fastqc && \
  cp -r FastQC /usr/share/ && \
  ln -s /usr/share/FastQC/fastqc /usr/bin/

