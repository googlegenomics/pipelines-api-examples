#!/usr/bin/python

# Copyright 2017 Google Inc.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

import time

def poll(service, operation, poll_interval):
  """Poll a genomics operation until completion.

  Args:
      service: genomics service endpoint
      operation: operation object for the operation to poll
      poll_interval: polling interval (in seconds).

  Returns:
      The operation object when it has been marked "done".
  """

  print
  print "Polling for completion of operation"

  while not operation['done']:
    print "Operation not complete. Sleeping %d seconds" % (poll_interval)

    time.sleep(poll_interval)

    operation = service.operations().get(name=operation['name']).execute()

  print
  print "Operation complete"
  print
  return operation
