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
COMMAND="${@:-start}"

OVS_DB=/run/openvswitch/conf.db
OVS_SCHEMA=/usr/share/openvswitch/vswitch.ovsschema
OVS_PID=/run/openvswitch/ovsdb-server.pid
OVS_SOCKET=/run/openvswitch/db.sock

function start () {
  umask 000
  exec ovsinit --ovs-db ${OVS_DB} --ovs-schema ${OVS_SCHEMA} -- /usr/sbin/ovsdb-server ${OVS_DB} \
          -vconsole:emer \
          -vconsole:err \
          -vconsole:info \
          --pidfile=${OVS_PID} \
          --remote=punix:${OVS_SOCKET} \
          --remote=db:Open_vSwitch,Open_vSwitch,manager_options \
{{- if .Values.conf.openvswitch_db_server.ptcp_port }}
          --remote=ptcp:{{ .Values.conf.openvswitch_db_server.ptcp_port }} \
{{- end }}
          --private-key=db:Open_vSwitch,SSL,private_key \
          --certificate=db:Open_vSwitch,SSL,certificate \
          --bootstrap-ca-cert=db:Open_vSwitch,SSL,ca_cert
}

function stop () {
  echo skipped due to ovsinit
}

$COMMAND
