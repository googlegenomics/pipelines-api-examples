# Copyright 2017 Google Inc.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

FROM ubuntu
MAINTAINER Matt Bookman <mbookman@google.com>

# Update the aptitude cache, install samtools, and clean up
# the local aptitude repository
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y samtools && \
    apt-get clean
