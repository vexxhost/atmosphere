# host_bond0_vlan_setup

Synthetic VLAN-trunked `bond0` + `br-ex` sub-IF setup for AIO scenarios
that need a VLAN trunk on a single physical uplink (mcapi-bm,
ib-bm — see `notes/logs/ironic/{mcapi-bm,ib-bm}/` in `ricolin/rico-utils`).

The role installs an idempotent host script
(`/usr/local/sbin/atmosphere-bond0-setup`) and a systemd unit
(`atmosphere-bond0.service`) that re-applies the topology on every boot:

1. Creates `bond0` (active-backup) + a `dummy0` slave so OVN's
   `auto_bridge_add: {br-ex: bond0}` has a real bond to claim.
2. **(Fix #9)** Replaces any kernel-type `bond0.<vid>@bond0` sub-IFs
   with **OVS internal ports** on `br-ex`, tagged with their VID.
3. Assigns sub-IF IPs (10.103.0.10 + 10.103.0.1, 10.96.240.200,
   172.24.6.254 by default — override with `host_bond0_vlan_setup_subifs`).
4. Enables `net.ipv4.ip_forward=1` and `iptables -t nat ... MASQUERADE`
   for OVN tenant + ironic provisioning CIDRs.

## Why Fix #9 matters

Once `bond0` is an OVS port on `br-ex`, kernel-type 8021q sub-IFs
(`bond0.<vid>@bond0`) **do not receive frames OVS forwards down the bond
trunk** — those frames go straight to the wire. Anything bound to a
host VLAN IP becomes unreachable from the OVS-attached side, manifesting
as PXE-E18 timeouts on ironic deploys and as broken OVN router-gateway
ARP. The script detects pre-existing kernel sub-IFs via the `@bond0:`
token in `ip -o link show` output and deletes them before the
`ovs-vsctl --may-exist add-port br-ex bond0.<vid> type=internal` call,
so the OVS create actually succeeds instead of silently no-op'ing on
the netlink name collision.

Discovered in the **ib-bm** session (2026-05-09, host 38.108.68.45).
Symmetric to the R7a guard that already exists in
`molecule/aio-vlan/converge.yml`.

## Variables

See `defaults/main.yml`. Default is **`host_bond0_vlan_setup_enabled:
false`** — the role is a no-op unless explicitly enabled, so standard
AIO/HCI deployments are unaffected.

| Variable | Default | Purpose |
| --- | --- | --- |
| `host_bond0_vlan_setup_enabled` | `false` | Master switch |
| `host_bond0_vlan_setup_uplink` | `""` (auto-detect via `ip route get 8.8.8.8`) | MASQUERADE egress iface |
| `host_bond0_vlan_setup_subifs` | `bond0.{103,4094,4090}` w/ canonical IPs | Per-VLAN sub-IF specs |
| `host_bond0_vlan_setup_masquerade_sources` | `[10.103.0.0/24, 172.24.6.0/24]` | NAT source CIDRs |

## Usage

In a top-level playbook, e.g. `playbooks/host_bond0_vlan_setup.yml`:

```yaml
- hosts: all
  become: true
  roles:
    - role: host_bond0_vlan_setup
      vars:
        host_bond0_vlan_setup_enabled: true
```

For molecule scenarios, add the role import to `prepare.yml` (or
`converge.yml`) and set the enable var in `group_vars/all/molecule.yml`.

## Caution: `bond0.4094` carries the kube-vip control-plane VIP

If you are applying this role *after* the AIO is already converged (as
opposed to first boot), recreating `bond0.4094` will cut
`10.96.240.10` (the VIP fronting kube-apiserver). Restart the kube-vip
static pod immediately after the swap so it re-binds to the new
OVS-internal sub-IF:

```bash
crictl stop $(crictl ps -q --name kube-vip)
```

`bond0.103` and `bond0.4090` have no comparable consumers and can be
swapped without downtime.
