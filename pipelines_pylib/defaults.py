#!/usr/bin/python

# Copyright 2017 Google Inc.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

# A hard-coded list of the current Compute Engine zones
# If this needs to live on, then it should be replaced by a call to.
# compute.zones().list().
_ZONES = [
  "asia-east1-a", "asia-east1-b", "asia-east1-c",
  "europe-west1-b", "europe-west1-c", "europe-west1-d",
  "us-central1-a", "us-central1-b", "us-central1-c", "us-central1-f",
  "us-east1-b", "us-east1-c", "us-east1-d",
  "us-west1-a", "us-west1-b",
]

def get_zones(input_list):
  """Returns a list of zones based on any wildcard input.

  This function is intended to provide an easy method for producing a list
  of desired zones for a pipeline to run in.

  Currently the API default zone list is "any zone". The problem with
  "any zone" is that it may lead to incurring Cloud Storage egress charges.
  A user with a bucket in "US" (multi-region) would typically want to
  restrict pipelines to run in either us-central1 or us-east1. The user
  typically cares more about region than zone.

  This function allows for a simple short-hand such as:
     [ "us-*" ]
     [ "us-central1-*" ]

  These examples will expand out to the full list of US and us-central1 zones
  respectively.
"""

  output_list = []

  for zone in input_list:
    if zone.endswith("*"):
      prefix = zone[:-1]
      output_list.extend(filter(lambda z: z.startswith(prefix), _ZONES))
    else:
      output_list.append(zone)

  return output_list
