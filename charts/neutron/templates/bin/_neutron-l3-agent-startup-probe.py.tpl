#!/usr/bin/env python3

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

"""
Start-up probe script for the L3 agent which checks if the agent is running a
full sync. This is done by connecting to the backdoor socket and checking if
the fetch_and_sync_all_routers green thread is running.

If it is, the start up probe will fail and it will prevent the pod rollout
from continuing until the full sync is complete. This is to prevent the
agent from being restarted while it is syncing all routers.
"""

import glob
import socket
import sys

# Prepare the expected status
full_sync = False


with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
    # Switch to a small timeout
    client.settimeout(2)

    # Detect the PID using glob
    backdoor_socket = glob.glob("/tmp/neutron-l3-agent-*-backdoor")[0]

    # Connect to the backdoor socket
    client.connect(backdoor_socket)

    # Get list of all green threads
    client.sendall(b"pgt()\n")

    # Get all threads until we timeout
    try:
        while True:
            data = client.recv(1024).decode("utf-8")
            if "fetch_and_sync_all_routers" in data:
                full_sync = True
    except socket.timeout:
        pass
    client.close()


# Check if we have a full sync
if full_sync:
    sys.stderr.write("NOK: L3 agent is running full sync.")
    sys.exit(1)
else:
    sys.stdout.write("OK: L3 agent is not running full sync.")
    sys.exit(0)
