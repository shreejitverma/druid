#!/usr/bin/env python3

# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import subprocess
import sys
import requests


if len(sys.argv) != 5:
  sys.stderr.write('usage: program <github-username> <previous-release-commit> <new-release-commit> <milestone-number-to-tag>\n')
  sys.stderr.write("  e.g., program myusername 75c70c2ccc 29f3a328da 30\n")
  sys.stderr.write("  It is also necessary to set a GIT_TOKEN environment variable containing a personal access token.\n")
  sys.exit(1)

expected_apache_html_url_prefix = "https://github.com/apache/druid/pull/"

github_username = sys.argv[1]
previous_release_commit = sys.argv[2]
new_release_commit = sys.argv[3]
milestone = sys.argv[4]
milestone_json = {'milestone': milestone}

# Find all commits between that commit and the current release branch
command = f"git rev-list {previous_release_commit}..{new_release_commit}"
all_commits = subprocess.check_output(command, shell=True).decode('UTF-8')

for sha in all_commits.splitlines():
  try:
    url = f"https://api.github.com/repos/apache/druid/commits/{sha}/pulls"
    headers = {'Accept': 'application/vnd.github.groot-preview+json'}
    pull_requests = requests.get(url, headers=headers, auth=(github_username, os.environ["GIT_TOKEN"])).json()

    print(
        f"Retrieved {len(pull_requests)} pull requests associated to commit {sha}"
    )
    for pr in pull_requests:
      pr_number = pr['number']
      if expected_apache_html_url_prefix not in pr['html_url']:
        print(
            f"Skipping Pull Request {pr_number} associatd with commit {sha} since the PR is not from the Apache repo."
        )
        continue
      if pr['milestone'] is None:
        print(f"Tagging Pull Request {pr_number} with milestone {milestone}")
        url = f"https://api.github.com/repos/apache/druid/issues/{pr_number}"
        requests.patch(url, json=milestone_json, auth=(github_username, os.environ["GIT_TOKEN"]))
      else:
        print(
            f"Skipping Pull Request {pr_number} since it's already tagged with milestone {milestone}"
        )

  except Exception as e:
    print(f"Got exception for commit: {sha}  ex: {e}")
    continue

