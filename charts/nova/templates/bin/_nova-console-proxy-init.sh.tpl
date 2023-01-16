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

console_kind="{{- .Values.console.console_kind -}}"

if [ "${console_kind}" == "novnc" ] ; then
    client_address="{{- .Values.conf.nova.vnc.vncserver_proxyclient_address -}}"
    client_interface="{{- .Values.console.novnc.vncproxy.vncserver_proxyclient_interface -}}"
    listen_ip="{{- .Values.conf.nova.vnc.vncserver_listen -}}"
elif [ "${console_kind}" == "spice" ] ; then
    client_address="{{- .Values.conf.nova.spice.server_proxyclient_address -}}"
    client_interface="{{- .Values.console.spice.proxy.server_proxyclient_interface -}}"
    listen_ip="{{- .Values.conf.nova.spice.server_listen -}}"
fi

if [ -z "${client_address}" ] ; then
    if [ -z "${client_interface}" ] ; then
        if  [ -x "$(command -v route)" ] ; then
            # search for interface with default routing, if multiple default routes exist then select the one with the lowest metric.
            client_interface=$(route -n | awk '/^0.0.0.0/ { print $5 " " $NF }' | sort | awk '{ print $NF; exit }')
        else
            client_interface=$(ip r | grep default | awk '{print $5}')
        fi
    fi

    # determine client ip dynamically based on interface provided
    client_address=$(ip a s $client_interface | grep 'inet ' | awk '{print $2}' | awk -F "/" '{print $1}' | head -n 1)
fi

if [ -z "${listen_ip}" ] ; then
    listen_ip=$client_address
fi

if [ "${console_kind}" == "novnc" ] ; then
cat <<EOF>/tmp/pod-shared/nova-vnc.ini
[vnc]
vncserver_proxyclient_address = $client_address
vncserver_listen = $listen_ip
EOF
elif [ "${console_kind}" == "spice" ] ; then
cat <<EOF>/tmp/pod-shared/nova-spice.ini
[spice]
server_proxyclient_address = $client_address
server_listen = $listen_ip
EOF
fi
