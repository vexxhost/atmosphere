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

cp -vaRf /usr/share/novnc/* /tmp/usr/share/novnc/

# Modern noVNC releases use vnc_lite.html in place of vnc_auto.html.
if [[ ! -e /tmp/usr/share/novnc/vnc_auto.html ]] && \
   [[ -e /tmp/usr/share/novnc/vnc_lite.html ]]; then
  cp /tmp/usr/share/novnc/vnc_lite.html \
    /tmp/usr/share/novnc/vnc_auto.html
fi
