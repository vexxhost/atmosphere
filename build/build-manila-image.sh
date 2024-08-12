# Copyright (c) 2024 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

set -xe

ATMOSPHERE_VERSION=$(pbr info -s atmosphere)

# Create work directory
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# Clone the openstack/manila-image-elements repository
git clone https://opendev.org/openstack/manila-image-elements $TMPDIR

# Build image
export ELEMENTS_PATH=$TMPDIR/elements
disk-image-create -o manila-${ATMOSPHERE_VERSION}.qcow2 vm manila-ubuntu-minimal dhcp-all-interfaces manila-ssh ubuntu-nfs ubuntu-cifs
