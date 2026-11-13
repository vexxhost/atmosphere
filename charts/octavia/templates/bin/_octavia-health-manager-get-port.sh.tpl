#!/bin/bash

{{/*
Copyright 2019 Samsung Electronics Co., Ltd.

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

HOSTNAME=$(hostname -s)
PORTNAME=octavia-health-manager-port-$HOSTNAME

HM_PORT_ID=$(openstack port show "$PORTNAME" -c id -f value)
HM_PORT_MAC=$(openstack port show "$PORTNAME" -c mac_address -f value)
HM_NETWORK_ID=$(openstack port show "$PORTNAME" -c network_id -f value)
HM_PORT_MTU=$(openstack network show "$HM_NETWORK_ID" -c mtu -f value)

if ! [[ $HM_PORT_MTU =~ ^[1-9][0-9]{1,4}$ ]] || (( HM_PORT_MTU < 68 || HM_PORT_MTU > 65535 )); then
    echo "Invalid Octavia management network MTU: $HM_PORT_MTU" >&2
    exit 1
fi

printf '%s\n' "$HM_PORT_ID" > /tmp/pod-shared/HM_PORT_ID
printf '%s\n' "$HM_PORT_MAC" > /tmp/pod-shared/HM_PORT_MAC
printf '%s\n' "$HM_PORT_MTU" > /tmp/pod-shared/HM_PORT_MTU
