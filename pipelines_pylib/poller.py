#!/usr/bin/python

#
# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
