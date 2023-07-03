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

HOSTNAME=$(hostname -s)
PORTNAME=ironic-$HOSTNAME

IRONIC_PORT_ID=$(openstack port show $PORTNAME -c id -f value)
IRONIC_PORT_IP=$(openstack port show $PORTNAME -c fixed_ips -f value | sed -n "s/.*'ip_address': '\([^']*\)'.*/\1/p")
IRONIC_PORT_MAC=$(openstack port show $PORTNAME -c mac_address -f value)

echo $IRONIC_PORT_ID > /tmp/pod-shared/IRONIC_PORT_ID
echo $IRONIC_PORT_IP > /tmp/pod-shared/IRONIC_PORT_IP
echo $IRONIC_PORT_MAC > /tmp/pod-shared/IRONIC_PORT_MAC
