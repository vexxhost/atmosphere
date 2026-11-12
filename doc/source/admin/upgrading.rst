#############
Upgrade Guide
#############

This document shows the most common way of upgrading your Atmosphere deployment.

.. admonition:: Avoid jumping Atmosphere major releases
    :class: warning

    It is important to avoid jumping major versions in Atmosphere, which is the
    same advice in OpenStack.

    For example, If you are running Atmosphere Zed release (version 1) and want
    to move to Bobcat (version 3) you should perform 2 upgrades: version 1 to
    version 2 and then version 3.

    If you dont do this, you may face database inconsistencies and failures on
    services like Nova or Neutron, or failed upgrades of components such as
    RabbitMQ.

**************************
Preparing the environment
**************************

On the deployment box, or any other place that you have your Ansible inventory,
you should update the ``requirements.yml`` file and point to the target
Atmosphere release you want to upgrade to.

.. code-block:: yaml

  collections:
  - name: vexxhost.atmosphere
    version: X.Y.Z

Once that is done, you should update your collections by running:

.. code-block:: console

    $ ansible-galaxy install -r requirements.yml --force

It's important to review your inventory, specifically image overrides to make
sure that the image overrides are still necessary, otherwise you may end up
with a broken deployment since the images will not be the ones the Atmosphere
collection expects.

*******************
Running the upgrade
*******************

You can either execute the entire upgrade by running your site-local playbook
which imports ``vexxhost.atmosphere.site``, call the individual playbooks out
of Atmosphere or run a specific tag if you want to upgrade service-by-service
which gives you the most granular control.

.. code-block:: console

    $ ansible-playbook -i hosts.ini playbooks/site.yml

You can also run the Atmosphere provided playbooks by pointing to a specific
playbook of the Ansible collection, in this case, the Ceph playbook:

.. code-block:: console

    $ ansible-playbook -i hosts.ini vexxhost.atmosphere.ceph

You also have the most granular control by running the tags of the playbooks,
for example, if you want to upgrade the Keystone service, you can run the
following command:

.. code-block:: console

    $ ansible-playbook -i hosts.ini vexxhost.atmosphere.openstack --tags keystone

During the upgrade, you may find it useful to have a monitor on all of the pods
in the cluster to ensure that they are becoming ready and not failing. You can
do this by running the following command:

.. code-block:: console

    $ watch -n1 "kubectl get pods --all-namespaces -owide | egrep -v '(Completed|1/1|2/2|3/3|4/4|6/6|7/7)'"

Kubernetes minor upgrades
============================

For a Kubernetes minor upgrade, change
``atmosphere_kubernetes_version`` and running one playbook for each minor:

.. code-block:: console

    $ . atmosphere-venv/bin/activate
    $ ansible-playbook vexxhost.atmosphere.kubernetes -i inventory/hosts.ini

For a deployment virtual environment outside the configuration directory,
activate it before changing to that directory. Use the complete inventory,
including every existing worker. Select a supported exact patch in the next
minor and repeat until the chosen target. Do not skip intermediate minors.
Complete the prerequisites for each step before invoking the playbook.

Collection prerequisites
------------------------

The controller lifecycle hooks and Cilium values merge require the companion
Kubernetes collection changes. Install a collection release that includes
those changes before using this workflow. For source validation, install the
matching collection checkout into the prepared deployment virtual environment:

.. code-block:: console

    $ ansible-galaxy collection install /path/to/ansible-collection-kubernetes --force --no-deps
    $ ansible-galaxy collection install . --force --no-deps

The published 3.5.1 release does not provide the new hooks and filter. Update
the normal dependency minimum to the first release containing the companion
changes before enabling this workflow in a released version.

What the invocation owns
------------------------

Before controller changes, Atmosphere reconciles Cilium's connected-UDP socket
and operator API transport settings on an existing cluster. Already matching
settings skip this preparation. Inventory ``cilium_helm_values`` take
precedence; operator environment variables merge by name. The compatibility
profile enables ``socketLB.hostNamespaceOnly`` and uses two-second HTTP/2 idle
and ping timers. These defaults target the bundled Cilium release; qualify
other versions and topologies separately.
This change does not upgrade Cilium's image or chart.

Successful API health checks do not prove external service connectivity.
An orphaned kube-proxy firewall path can still intercept traffic after the
DaemonSet and ConfigMap are removed. The companion collection therefore
checks host rules before application preparation, including worker-only runs,
and after controller commands. It stops on leftover state. Explicit host
recovery is a separate reviewed operation; see the companion upgrade guide
for ownership checks, protected backups and rollback limits.

Monitor external service traffic and long-lived database sessions throughout
the upgrade, and verify them after each controller phase and at completion.
Run these service acceptance checks separately from the playbook.

For public VIPs managed by Keepalived, check VRRP traffic separately from the
Kubernetes API VIP. A foreign cluster sharing a VRID can affect advertisement
timing even when its VIP and authentication differ. Keepalived 2.2.8 can reset
the master transmit timer while processing invalid advertisements; repeated
traffic can delay advertisements enough for a backup to become master.
Use a unique VRID on the shared network and qualify a fixed Keepalived release.

Consider enabling ``keepalived_lower_prio_no_advert`` when all of these apply:

* The deployed daemon has the affected receive-timer behavior, including
  Keepalived 2.2.8.
* Packet timing and daemon logs show received VRRP traffic coinciding with
  missing or delayed master advertisements and unexpected backup takeovers
  while the original master remains healthy. Unrelated same-VRID traffic can
  trigger this even when authentication or the advertised VIP differs.
* A controlled validation confirms that the option restores advertisement
  cadence and stable ownership while intended failover and service access
  still work.

Lower-priority traffic alone does not require enabling the option. Keep the
default for a stable deployment unless its version and topology require the
change. Investigate host scheduling delays, packet loss and genuine master
failures separately; the option is not a general remedy for VIP instability.

The optional ``keepalived_lower_prio_no_advert: true`` renders the corresponding
instance directive for a separately qualified mitigation. It defaults to false
and does not resolve a VRID collision or provide general protection against
invalid VRRP traffic. Check the installed version's behavior, loaded instance
configuration, advertisement cadence, stable VIP ownership and HTTPS traffic
before accepting it. Inventory persistence also requires deploying the updated
Keepalived role; changing a live Secret alone can be overwritten by a later
deployment. Kubernetes-only playbooks do not deploy this role.

The companion collection saves an etcd snapshot and an off-node copy, updates
the stored kubeadm configuration, upgrades controllers serially, completes
DNS reconciliation and then upgrades kubelets serially. Repeating the same
command resumes pending controllers without repeating a completed
``upgrade apply``. Failures stop subsequent mutation while cleanup restores
owned temporary state.

Atmosphere supplies the controller application integration. It hot-reloads
``core.noPublish`` on the pinned NFD workers, preserves their existing labels,
and pauses only Percona's peer-discovery processes. HAProxy and established
SQL connections keep running. Both preparations have host watchdogs and
unconditional restoration. Normal cleanup waits for NFD to load its original
configuration. A watchdog retries restoration if the API is still recovering.

Application protection follows the existing controller group and the bundled
Percona resource names. Its watchdog window remains at least one hour and
extends to twice ``kubernetes_upgrade_operation_timeout`` for longer operations,
covering preparation and recovery without a second configurable timeout.
The NFD namespace uses
``node_feature_discovery_helm_release_namespace``. Only its ConfigMap and pod
prefix retain explicit overrides for custom Helm fullnames:
``atmosphere_kubernetes_upgrade_nfd_configmap`` and
``atmosphere_kubernetes_upgrade_nfd_pod_prefix``. Other application placements
require separate qualification.

The Cilium compatibility profile is internal; site overrides continue to use
``cilium_helm_values``.
The implementation uses the pinned worker's hot-reload log format and
Percona's ``peer-list`` executable. Set
``atmosphere_kubernetes_upgrade_compatibility: false`` only when separately
delivered application and Cilium fixes replace this profile.

Version-specific work
---------------------

For 1.29 and 1.30, kubeadm can replace CoreDNS placement. The collection repairs
it immediately after the controller command, waits for its rollout, and
avoids DNS mutation during worker-only recovery. From 1.31, kubeadm's supported
CoreDNS deployment patch preserves placement and overlapping replicas.
The 1.31 hash migration visits committed BoltDB records, ignoring stale pages.
When the stored configuration supports it, kube-proxy replacement persists
``proxy.disabled`` before kubeadm runs.

The companion collection also reconciles the stored control-plane and DNS image
repositories, including a return from a mirror to upstream defaults. It
preserves custom kubelet settings while refreshing role-owned fields and
validates the merged configuration with the target kubeadm before upload.
Template changes alone do not update those stored component configurations.

From 1.33, controllers keep a certificate-valid custom HA kubelet endpoint;
preparation changes no credentials and does not restart the kubelet. Existing
custom endpoints are retained.

Before 1.34 moves etcd from 3.5 to 3.6, update all members to 3.5.32 or later,
retain verified backups and check for custom v2 data in protected offline
snapshot/WAL copies. Follow the `etcd upgrade procedure
<https://etcd.io/docs/v3.6/upgrades/upgrade_3_6/>`_. The playbook does not
perform this intermediate upgrade or data migration automatically.

Before starting a target kubelet, qualify the runtime and CRI behavior,
including existing containers and a new init-container pod. Persist its
version/checksum and preserve the existing runtime configuration and runc
behavior. Complete any required runtime intermediates separately so inherited
role dependencies cannot revert an accepted runtime.

On affected legacy-cgroup nodes, keep the managed resize gate disabled at
1.33/1.34. Before the first 1.35 kubelet startup, retain the existing stopped
kubelet resource-checkpoint transition and verify its records. Do not carry
the obsolete gate override into 1.35/1.36; preserve the native checkpoint on
later hops instead. Keep the resize admission guard and patch-specific
denylist checks for affected releases. Successful startup does not qualify explicit
in-place pod resize. A cgroup migration remains a separate operation.

Upgrade prerequisites and limits
--------------------------------

Integrated HA application continuity requires qualification of the exact
collection, addon and runtime combination.
The legacy CoreDNS path can still involve kubeadm's first rollout followed by
placement repair. Overlapping replicas do not establish zero DNS request
loss.
The NFD and Percona integration automates the documented temporary workaround;
it does not patch their upstream retry or membership-retention behavior.
The runtime and etcd prerequisite operations above remain separate from the
Kubernetes playbook.
