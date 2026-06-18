# Copyright (c) 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

set -xe

ATMOSPHERE_VERSION=$(python3 -c "from atmosphere._version import __version__; print(__version__)")

# Create work directory
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# Clone the openstack/manila-image-elements repository
git clone https://github.com/openstack/manila-image-elements $TMPDIR

# Build image
export ELEMENTS_PATH=$TMPDIR/elements
export DIB_RELEASE=noble
disk-image-create -o manila-${ATMOSPHERE_VERSION}.qcow2 vm manila-ubuntu-minimal dhcp-all-interfaces manila-ssh ubuntu-nfs ubuntu-cifs
