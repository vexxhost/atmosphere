# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM openstack-venv-builder AS build
ARG OPENSTACKCLIENT_GIT_REF=bc1930c20ede2018413dc5b89b5dd99c46fdd054
# NOTE(rlin): Directly use stable/2025.1 source for python-openstackclient until
#             https://review.opendev.org/c/openstack/python-openstackclient/+/944991
#             released for stable/2025.1.
ADD --keep-git-dir=true https://opendev.org/openstack/python-openstackclient.git#${OPENSTACKCLIENT_GIT_REF} /src/python-openstackclient
RUN git -C /src/python-openstackclient fetch --unshallow
RUN --mount=type=cache,target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /upper-constraints.txt \
        osc-placement \
        python-barbicanclient \
        python-designateclient \
        python-glanceclient \
        python-heatclient \
        python-ironicclient \
        python-magnumclient \
        python-manilaclient \
        python-neutronclient \
        python-octaviaclient \
        /src/python-openstackclient \
        python-swiftclient
EOF

FROM python-base
COPY --from=build --link /var/lib/openstack /var/lib/openstack

# NOTE(mnaser): The Magnum client relies on the SHELL environment variable
#               to determine the shell to use.
ENV SHELL=/bin/bash

# NOTE(mnaser): When we call this container, we mount the current directory
#               into `/opt` and then we can call `openstack` commands.
WORKDIR /opt
