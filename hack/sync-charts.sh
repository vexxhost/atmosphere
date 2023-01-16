#!/bin/bash

# Copyright (c) 2023 VEXXHOST, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# This script is used to sync the charts from the upstream repositories into
# the charts directory.  It is used to update the charts to the versions which
# are defined in this file.

set -xe

# Determine the root path for Atmosphere
ATMOSPHERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"

# Create work directory to avoid cluttering up workspace
WORKDIR=$(mktemp -d)
function cleanup {
  rm -rfv ${WORKDIR}
}
trap cleanup EXIT

# Clean-up all of the existing charts
rm -rfv ${ATMOSPHERE}/charts/*

# Switch to folder where we will be syncing charts
pushd ${WORKDIR}

PERCONA_REF="25d8099e1e1f807b6bc90d8d92b6a31a6dff082b"
curl -LO https://github.com/percona/percona-helm-charts/archive/${PERCONA_REF}.tar.gz
tar --strip-components=2 -C ${ATMOSPHERE}/charts -xvzf ${PERCONA_REF}.tar.gz percona-helm-charts-${PERCONA_REF}/charts/pxc-operator

# Switch back to original directory
popd
