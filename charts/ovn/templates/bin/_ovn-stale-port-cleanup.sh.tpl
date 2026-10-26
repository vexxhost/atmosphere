#!/bin/bash

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Periodically remove stale OVS ports from the integration bridge.
#
# A "stale" port is an OVS Port whose attached Interface has no corresponding
# kernel netdev. This commonly happens because libvirt removes the tap device
# when a VM is destroyed but the matching OVS port entry is left behind on
# br-int. Accumulation of these orphans causes ovn-controller poll-loop
# stalls, OVS disconnections, and packet drops.
#
# Detection criteria (all must hold):
#   * Port lives on the configured integration bridge (default: br-int).
#   * Interface has the "iface-id" external_id (it is/was a Neutron VIF).
#   * Either the Interface "error" column is non-empty (typically
#     "could not open network device tapXXXX (No such device)") or the
#     kernel netdev for the Interface "name" is not visible to `ip link`.
#
# Anti-race protection:
#   The Neutron OVS agent creates the OVS port with iface-id set BEFORE
#   libvirt creates the tap device. To avoid deleting a brand-new VIF
#   that has not finished plugging, every candidate must remain stale
#   across MIN_STALE_OBSERVATIONS consecutive cycles (default: 2) before
#   deletion. The observation state lives in /var/run inside the pod
#   and is reset whenever the port becomes healthy again.
#
# Operator opt-out:
#   Interfaces with external_ids:skip_cleanup="true" are never deleted.

set -o pipefail

INTEGRATION_BRIDGE="${INTEGRATION_BRIDGE:-br-int}"
OVS_DB_SOCKET="${OVS_DB_SOCKET:-/run/openvswitch/db.sock}"
INTERVAL_SECONDS="${INTERVAL_SECONDS:-3600}"
MAX_DELETIONS_PER_CYCLE="${MAX_DELETIONS_PER_CYCLE:-200}"
MIN_STALE_OBSERVATIONS="${MIN_STALE_OBSERVATIONS:-2}"
DRY_RUN="${DRY_RUN:-0}"

STATE_DIR="${STATE_DIR:-/var/run/ovn-stale-port-cleanup}"
mkdir -p "${STATE_DIR}"

OVS_VSCTL="ovs-vsctl --db=unix:${OVS_DB_SOCKET} --timeout=10"

log() {
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [stale-port-cleanup] $*"
}

# True (0) if the kernel netdev exists in the host network namespace.
# We rely on `ip link show` because the pod runs with hostNetwork=true,
# so netlink reflects the host. This is more accurate than reading
# /sys/class/net (which is a per-netns view that may not be mounted
# from the host).
netdev_exists() {
    ip -o link show dev "$1" &>/dev/null
}

# Persist that we observed `iface` as stale at least once. Returns the
# updated observation count via stdout.
record_stale_observation() {
    local iface="$1"
    local f="${STATE_DIR}/${iface}.count"
    local n=0
    [[ -r "${f}" ]] && n="$(cat "${f}" 2>/dev/null || echo 0)"
    n=$((n + 1))
    echo "${n}" > "${f}"
    echo "${n}"
}

clear_stale_observation() {
    rm -f "${STATE_DIR}/$1.count"
}

# Drop state files for interfaces no longer present so the directory
# does not grow unbounded.
gc_state_dir() {
    local known="$1"  # newline-separated iface names currently in OVSDB
    local f base
    shopt -s nullglob
    for f in "${STATE_DIR}"/*.count; do
        base="$(basename "${f}" .count)"
        if ! grep -Fxq "${base}" <<< "${known}"; then
            rm -f "${f}"
        fi
    done
    shopt -u nullglob
}

cleanup_cycle() {
    local bridge="$1"
    local deletions=0
    local candidates=0
    local confirmed=0

    if ! ${OVS_VSCTL} br-exists "${bridge}" 2>/dev/null; then
        log "bridge ${bridge} does not exist; skipping cycle"
        return 0
    fi

    # Pre-fetch the set of interface names currently attached to br-int.
    # Doing this once avoids an O(n) iface-to-br call per Interface row.
    local br_ifaces
    br_ifaces="$(${OVS_VSCTL} list-ports "${bridge}" 2>/dev/null || true)"
    if [[ -z "${br_ifaces}" ]]; then
        log "no ports on ${bridge}; nothing to do"
        gc_state_dir ""
        return 0
    fi

    # Snapshot Interface rows that look like Neutron VIFs (iface-id set).
    # Only ask for the name column so we never have to parse the comma-
    # heavy external_ids map at the CSV layer.
    local vif_ifaces
    vif_ifaces="$(${OVS_VSCTL} --columns=name --no-headings --data=bare \
        find Interface external_ids:iface-id\!=\"\" 2>/dev/null \
        | awk 'NF>0 {print $1}' || true)"

    if [[ -z "${vif_ifaces}" ]]; then
        log "no Neutron VIF interfaces in OVSDB"
        gc_state_dir ""
        return 0
    fi

    # Intersect: VIF interfaces actually attached to the integration bridge.
    local target_ifaces
    target_ifaces="$(grep -Fxf <(printf '%s\n' "${br_ifaces}") <<< "${vif_ifaces}" || true)"

    gc_state_dir "${target_ifaces}"

    [[ -z "${target_ifaces}" ]] && { log "no VIF interfaces on ${bridge}"; return 0; }

    while IFS= read -r iface_name; do
        [[ -z "${iface_name}" ]] && continue

        # Per-interface get is safe regardless of map content.
        local iface_error iface_ext
        iface_error="$(${OVS_VSCTL} --if-exists get Interface "${iface_name}" error 2>/dev/null || echo '[]')"
        iface_ext="$(${OVS_VSCTL} --if-exists get Interface "${iface_name}" external_ids 2>/dev/null || echo '{}')"

        local stale_reason=""
        if [[ -n "${iface_error}" && "${iface_error}" != "[]" && "${iface_error}" != '""' ]]; then
            stale_reason="interface error: ${iface_error}"
        elif ! netdev_exists "${iface_name}"; then
            stale_reason="kernel netdev missing"
        else
            # Healthy now; clear any prior observation count.
            clear_stale_observation "${iface_name}"
            continue
        fi

        if [[ "${iface_ext}" == *'skip_cleanup="true"'* ]]; then
            log "skipping ${iface_name} (skip_cleanup=true)"
            continue
        fi

        candidates=$((candidates + 1))
        local count
        count="$(record_stale_observation "${iface_name}")"

        if (( count < MIN_STALE_OBSERVATIONS )); then
            log "candidate ${iface_name} (${stale_reason}); observation ${count}/${MIN_STALE_OBSERVATIONS}, deferring"
            continue
        fi

        confirmed=$((confirmed + 1))
        log "stale port confirmed on ${bridge}: ${iface_name} (${stale_reason}, observed ${count}x)"

        if [[ "${DRY_RUN}" == "1" ]]; then
            continue
        fi

        if (( deletions >= MAX_DELETIONS_PER_CYCLE )); then
            log "deletion cap (${MAX_DELETIONS_PER_CYCLE}) reached; deferring remainder to next cycle"
            break
        fi

        if ${OVS_VSCTL} --if-exists del-port "${bridge}" "${iface_name}"; then
            deletions=$((deletions + 1))
            clear_stale_observation "${iface_name}"
            log "deleted stale port ${iface_name} from ${bridge}"
        else
            log "WARNING: failed to delete port ${iface_name} from ${bridge}"
        fi
    done <<< "${target_ifaces}"

    log "cycle complete: candidates=${candidates} confirmed=${confirmed} deletions=${deletions} dry_run=${DRY_RUN}"
}

log "starting (bridge=${INTEGRATION_BRIDGE} interval=${INTERVAL_SECONDS}s max_per_cycle=${MAX_DELETIONS_PER_CYCLE} min_obs=${MIN_STALE_OBSERVATIONS} dry_run=${DRY_RUN})"

trap 'log "received termination signal, exiting"; exit 0' SIGTERM SIGINT

while true; do
    cleanup_cycle "${INTEGRATION_BRIDGE}" || log "cycle failed (continuing)"
    sleep "${INTERVAL_SECONDS}" &
    wait $!
done
