#!/bin/bash

{{/*
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

chown ${NEUTRON_USER_UID} /var/lib/neutron/openstack-helm

{{- if and ( empty .Values.conf.neutron.DEFAULT.host ) ( .Values.pod.use_fqdn.neutron_agent ) }}
mkdir -p /tmp/pod-shared
tee > /tmp/pod-shared/neutron-agent.ini << EOF
[DEFAULT]
host = $(hostname --fqdn)
EOF
{{- end }}
