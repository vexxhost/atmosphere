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

# Sync using "vendir"
vendir sync

# Keystone
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm~899867/revisions/1/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'keystone/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/keystone
rm -fv ${ATMOSPHERE}/charts/keystone/templates/bin/{_domain-manage-init.sh.tpl,_domain-manage.py.tpl}

# Glance
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm~899864/revisions/2/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'glance/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/glance

# Cinder
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm~899814/revisions/1/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'cinder/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/cinder

# Placement
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm~899914/revisions/3/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'placement/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/placement

# Libvirt
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm-infra~893406/revisions/9/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'libvirt/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/libvirt

# OVN
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm-infra~893739/revisions/2/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'ovn/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/ovn

# Nova
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm~899809/revisions/2/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'nova/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/nova
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm~904250/revisions/3/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'nova/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/nova

# Senlin
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm~899913/revisions/1/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'senlin/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/senlin

# Designate
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm~899932/revisions/1/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'designate/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/designate

# Heat
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm~899931/revisions/1/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'heat/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/heat

# Octavia
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm~899918/revisions/1/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'octavia/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/octavia

# Magnum
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm~899926/revisions/1/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'magnum/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/magnum

# Manila
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm~883168/revisions/11/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'manila/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/manila
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm~899923/revisions/1/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'manila/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/manila

# Neutron
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm~904654/revisions/5/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'neutron/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/neutron
