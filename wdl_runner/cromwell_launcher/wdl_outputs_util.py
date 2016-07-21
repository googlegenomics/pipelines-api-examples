#!/usr/bin/python

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# wdl_outputs_util.py
#
# When Cromwell finishes running a workflow on Compute Engine, the
# output files are not in their final location, they are down under
# the workflow's "workspace" path.
#
# The routines in this file can be used to get the list of output files
# to copy.


def get_matching_element(value, match_string):
  """Returns a list of values which match the given prefix string.

  The input value can be a singleton string, a list, or a dict.
  If the input value is a list or dict, this function will be called
  recursively (via get_matching_list_values or get_matching_dict_values
  respectively).
  """

  match_list = list()

  if isinstance(value, list):
    match_list += get_matching_list_values(value, match_string)

  elif isinstance(value, dict):
    match_list += get_matching_dict_values(value, match_string)

  elif isinstance(value, unicode) or isinstance(value, str):
    if value.startswith(match_string) != -1:
      match_list.append(value)

  else:
    # We don't search floats or bools.
    pass

  return match_list


def get_matching_list_values(l, match_string):
  """Returns a list of values from a list which match the given string."""

  match_list = list()
  for value in l:
    match_list += get_matching_element(value, match_string)

  return match_list


def get_matching_dict_values(d, match_string):
  """Returns a list of values from a dict which match the given string."""

  match_list = list()
  for value in d.itervalues():
    match_list += get_matching_element(value, match_string)

  return match_list


def get_workflow_output(outputs, working_dir):
  return get_matching_dict_values(outputs, working_dir)

