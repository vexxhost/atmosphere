#!/bin/bash

{{/*
Copyright 2023 VEXXHOST, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/}}

set -ex

IRONIC_PORT_ID=$(cat /tmp/pod-shared/IRONIC_PORT_ID)
IRONIC_PORT_MAC=$(cat /tmp/pod-shared/IRONIC_PORT_MAC)

ovs-vsctl --no-wait show

ovs-vsctl --may-exist add-port br-int {{ .Values.network.pxe.device }} \
        -- set Interface {{ .Values.network.pxe.device }} type=internal \
        -- set Interface {{ .Values.network.pxe.device }} external-ids:iface-status=active \
        -- set Interface {{ .Values.network.pxe.device }} external-ids:attached-mac=$IRONIC_PORT_MAC \
        -- set Interface {{ .Values.network.pxe.device }} external-ids:iface-id=$IRONIC_PORT_ID \
        -- set Interface {{ .Values.network.pxe.device }} external-ids:skip_cleanup=true

ip link set dev {{ .Values.network.pxe.device }} address $IRONIC_PORT_MAC

iptables -I INPUT -i {{ .Values.network.pxe.device }} -p udp --dport {{ tuple "baremetal" "internal" "api" . | include "helm-toolkit.endpoints.endpoint_port_lookup" }} -j ACCEPT
