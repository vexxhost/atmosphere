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

# Clean-up all of the existing charts
rm -rfv ${ATMOSPHERE}/charts/*

CEPH_CSI_RBD_VERSION=3.5.1
curl -sL https://ceph.github.io/csi-charts/rbd/ceph-csi-rbd-${CEPH_CSI_RBD_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

NODE_FEATURE_DISCOVERY_VERSION=0.11.2
curl -sL https://github.com/kubernetes-sigs/node-feature-discovery/releases/download/v${NODE_FEATURE_DISCOVERY_VERSION}/node-feature-discovery-chart-${NODE_FEATURE_DISCOVERY_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

KUBE_PROMETHEUS_STACK_VERSION=49.0.0
curl -sL https://github.com/prometheus-community/helm-charts/releases/download/kube-prometheus-stack-${KUBE_PROMETHEUS_STACK_VERSION}/kube-prometheus-stack-${KUBE_PROMETHEUS_STACK_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

LOKI_VERSION=4.6.1
curl -sL https://github.com/grafana/helm-charts/releases/download/helm-loki-${LOKI_VERSION}/loki-${LOKI_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

VECTOR_VERSION=0.19.0
curl -sL https://github.com/vectordotdev/helm-charts/releases/download/vector-${VECTOR_VERSION}/vector-${VECTOR_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

PROMETHEUS_PUSHGATEWAY_VERSION=1.16.0
curl -sL https://github.com/prometheus-community/helm-charts/releases/download/prometheus-pushgateway-${PROMETHEUS_PUSHGATEWAY_VERSION}/prometheus-pushgateway-${PROMETHEUS_PUSHGATEWAY_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

INGRESS_NGINX_VERSION=4.0.17
curl -sL https://github.com/kubernetes/ingress-nginx/releases/download/helm-chart-${INGRESS_NGINX_VERSION}/ingress-nginx-${INGRESS_NGINX_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

CERT_MANAGER_VERSION=v1.7.1
curl -sL https://charts.jetstack.io/charts/cert-manager-${CERT_MANAGER_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

CERT_MANAGER_WEBHOOK_INFOBLOX_WAPI_VERSION=1.5.2
curl -sL https://github.com/luisico/cert-manager-webhook-infoblox-wapi/releases/download/helm-chart-${CERT_MANAGER_WEBHOOK_INFOBLOX_WAPI_VERSION}/cert-manager-webhook-infoblox-wapi-${CERT_MANAGER_WEBHOOK_INFOBLOX_WAPI_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

RABBITMQ_CLUSTER_OPERATOR_VERSION=2.6.6
curl -sL https://charts.bitnami.com/bitnami/rabbitmq-cluster-operator-${RABBITMQ_CLUSTER_OPERATOR_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

PXC_OPERATOR_VERSION=1.12.0
curl -sL https://github.com/Percona-Lab/percona-helm-charts/releases/download/pxc-operator-${PXC_OPERATOR_VERSION}/pxc-operator-${PXC_OPERATOR_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

COREDNS_VERSION=1.19.4
curl -sL https://github.com/coredns/helm/releases/download/coredns-${COREDNS_VERSION}/coredns-${COREDNS_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

MEMCACHED_VERSION=0.1.12
curl -sL https://tarballs.opendev.org/openstack/openstack-helm-infra/memcached-${MEMCACHED_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

KEYSTONE_VERSION=0.3.0
curl -sL https://tarballs.opendev.org/openstack/openstack-helm/keystone-${KEYSTONE_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

BARBICAN_VERSION=0.3.2
curl -sL https://tarballs.opendev.org/openstack/openstack-helm/barbican-${BARBICAN_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

CEPH_PROVISIONERS_VERSION=0.1.8
curl -sL https://tarballs.opendev.org/openstack/openstack-helm-infra/ceph-provisioners-${CEPH_PROVISIONERS_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

GLANCE_VERSION=0.4.12
curl -sL https://tarballs.opendev.org/openstack/openstack-helm/glance-${GLANCE_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

CINDER_VERSION=0.3.13
curl -sL https://tarballs.opendev.org/openstack/openstack-helm/cinder-${CINDER_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

PLACEMENT_VERSION=0.3.7
curl -sL https://tarballs.opendev.org/openstack/openstack-helm/placement-${PLACEMENT_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

OPEN_VSWITCH_VERSION=0.1.15
curl -sL https://tarballs.opendev.org/openstack/openstack-helm-infra/openvswitch-${OPEN_VSWITCH_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

LIBVIRT_VERSION=0.1.23
curl -sL https://tarballs.opendev.org/openstack/openstack-helm-infra/libvirt-${LIBVIRT_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm-infra~893406/revisions/5/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'libvirt/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/libvirt

LOCAL_PATH_PROVISIONER_VERSION=0.0.24
curl -sL https://github.com/rancher/local-path-provisioner/archive/refs/tags/v${LOCAL_PATH_PROVISIONER_VERSION}.tar.gz \
  | tar -xz -C ${ATMOSPHERE}/charts --strip-components=3 local-path-provisioner-${LOCAL_PATH_PROVISIONER_VERSION}/deploy/chart/

OVN_VERSION=0.1.4
curl -sL https://tarballs.opendev.org/openstack/openstack-helm-infra/ovn-${OVN_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm-infra~893739/revisions/2/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'ovn/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/ovn

NEUTRON_VERSION=0.3.19
curl -sL https://tarballs.opendev.org/openstack/openstack-helm/neutron-${NEUTRON_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm~893733/revisions/2/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'neutron/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/neutron

NOVA_VERISON=0.3.22
curl -sL https://tarballs.opendev.org/openstack/openstack-helm/nova-${NOVA_VERISON}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm~893563/revisions/1/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'nova/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/nova

SENLIN_VERSION=0.2.9
curl -sL https://tarballs.opendev.org/openstack/openstack-helm/senlin-${SENLIN_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

DESIGNATE_VERSION=0.2.9
curl -sL https://tarballs.opendev.org/openstack/openstack-helm/designate-${DESIGNATE_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

HEAT_VERSION=0.3.3
curl -sL https://tarballs.opendev.org/openstack/openstack-helm/heat-${HEAT_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

OCTAVIA_VERSION=0.2.9
curl -sL https://tarballs.opendev.org/openstack/openstack-helm/octavia-${OCTAVIA_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

MAGNUM_VERSION=0.2.9
curl -sL https://tarballs.opendev.org/openstack/openstack-helm/magnum-${MAGNUM_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

HORIZON_VERSION=0.3.11
curl -sL https://tarballs.opendev.org/openstack/openstack-helm/horizon-${HORIZON_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

TEMPEST_VERSION=0.2.7
curl -sL https://tarballs.opendev.org/openstack/openstack-helm/tempest-${TEMPEST_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

ROOK_CEPH_VERSION=1.10.10
curl -sL https://charts.rook.io/release/rook-ceph-v${ROOK_CEPH_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

ROOK_CEPH_CLUSTER_VERSION=1.10.10
curl -sL https://charts.rook.io/release/rook-ceph-cluster-v${ROOK_CEPH_CLUSTER_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

MANILA_VERSION=0.1.5
curl -sL https://tarballs.opendev.org/openstack/openstack-helm/manila-${MANILA_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm~883168/revisions/11/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'manila/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/manila
curl 'https://review.opendev.org/changes/openstack%2Fopenstack-helm~896819/revisions/2/patch?download' \
  | base64 --decode \
  | filterdiff -p1 -x 'releasenotes/*' \
  | filterdiff -p2 -x 'Chart.yaml' \
  | filterdiff -p1 -i 'manila/*' \
  | patch -p2 -d ${ATMOSPHERE}/charts/manila

KEYCLOAK_VERSION=16.0.3
curl -sL https://charts.bitnami.com/bitnami/keycloak-${KEYCLOAK_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts
