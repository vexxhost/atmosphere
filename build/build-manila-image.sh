# Copyright (c) 2024 VEXXHOST, Inc.
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
disk-image-create -t raw -o manila-${ATMOSPHERE_VERSION}.raw vm manila-ubuntu-minimal dhcp-all-interfaces manila-ssh ubuntu-nfs ubuntu-cifs
