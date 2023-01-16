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

CILIUM_VERSION=1.10.7
curl -sL https://helm.cilium.io/cilium-${CILIUM_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

CEPH_CSI_RBD_VERSION=3.5.1
curl -sL https://ceph.github.io/csi-charts/rbd/ceph-csi-rbd-${CEPH_CSI_RBD_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

NODE_FEATURE_DISCOVERY_VERSION=0.11.2
curl -sL https://github.com/kubernetes-sigs/node-feature-discovery/releases/download/v${NODE_FEATURE_DISCOVERY_VERSION}/node-feature-discovery-chart-${NODE_FEATURE_DISCOVERY_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

KUBE_PROMETHEUS_STACK_VERSION=41.7.3
curl -sL https://github.com/prometheus-community/helm-charts/releases/download/kube-prometheus-stack-${KUBE_PROMETHEUS_STACK_VERSION}/kube-prometheus-stack-${KUBE_PROMETHEUS_STACK_VERSION}.tgz \
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

RABBITMQ_CLUSTER_OPERATOR_VERSION=2.6.6
curl -sL https://charts.bitnami.com/bitnami/rabbitmq-cluster-operator-${RABBITMQ_CLUSTER_OPERATOR_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

PXC_OPERATOR_VERSION=1.10.0
curl -sL https://github.com/Percona-Lab/percona-helm-charts/releases/download/pxc-operator-${PXC_OPERATOR_VERSION}/pxc-operator-${PXC_OPERATOR_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

COREDNS_VERSION=1.19.4
curl -sL https://github.com/coredns/helm/releases/download/coredns-${COREDNS_VERSION}/coredns-${COREDNS_VERSION}.tgz \
  | tar -xz -C ${ATMOSPHERE}/charts

# Switch back to original directory
popd
