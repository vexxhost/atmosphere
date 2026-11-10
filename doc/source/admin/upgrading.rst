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

    $ ansible-galaxy collection install -r requirements.yml --force-with-deps
    $ ansible-galaxy collection list vexxhost.atmosphere
    $ ansible-galaxy collection list vexxhost.kubernetes

``--force-with-deps`` refreshes dependent collections as well as Atmosphere.
An already installed collection can satisfy a minimum version constraint while
missing fixes needed for your upgrade. Check the installed versions and paths
to confirm that Ansible will use the collections you intended to install.

It's important to review your inventory, specifically image overrides to make
sure that the image overrides are still necessary, otherwise you may end up
with a broken deployment since the images will not be the ones the Atmosphere
collection expects.

.. _kubernetes-upgrades:

********************
Upgrading Kubernetes
********************

The instructions in this section apply to the ``vexxhost.kubernetes`` 3.5.0
and later upgrade workflow required by this branch. For an older Atmosphere
release, use the playbooks and documentation for its installed dependency
versions. The older Kubernetes collection upgrade page contains examples for
collection 1.5.2, including Keepalived/HAProxy and manual package upgrades;
those examples do not describe the workflow below.

Plan each version change
========================

Record the current Kubernetes node versions before choosing an exact target:

.. code-block:: console

    $ kubectl get nodes -o wide
    $ kubectl get pods -A -o wide

For clouds using Magnum, also list the existing Cluster API clusters:

.. code-block:: console

    $ kubectl get cluster -A

Check the management cluster and workload cluster versions against the support
matrices of the installed and target Cluster API providers. Updating Atmosphere
can also update those providers; their requirements can affect the order of
the upgrades. The Atmosphere default Kubernetes version alone does not establish
compatibility with every Magnum configuration.

Upgrade Kubernetes one minor version at a time. Check the release notes for
each intermediate version and confirm that the container runtime and CNI
support both the current and next version. Review any API server arguments,
kubeadm patches and legacy kubelet settings before proceeding. Resolve a failed
upgrade preflight using its guidance before retrying.

Take an etcd backup and preserve the inventory and installed collection
versions before starting. Use a maintenance window and verify the Kubernetes
API, etcd and OpenStack services after each phase.

Prepare the VIP and container runtime
=====================================

The ``Configure Kubernetes VIP`` play in the Kubernetes collection uses
``vexxhost.kubernetes.kube_vip``. Include this preparation before changing the
Kubernetes version. Atmosphere's Kubernetes playbook passes the selected
``kube_vip`` and ``pause`` images to the dependency, including image mirrors
and overrides. Use that playbook instead of copying the old
``keepalived``/``haproxy`` role example.

Check which implementation currently owns the API VIP. On each controller,
inspect the static pod manifests and their running pods for ``kube-vip``,
``keepalived`` and ``haproxy``. Preserve the existing VIP address, interface and
any external load balancer configuration. The inventory names
``kubernetes_keepalived_vip`` and ``kubernetes_keepalived_interface`` remain
inputs to kube-vip; their names do not mean that Keepalived should be installed.

.. warning::

    On a legacy deployment, the kube-vip role removes the Keepalived/HAProxy
    static pod manifests and configuration, changes local API server references
    from port ``16443`` to ``6443``, and can restart kubelet. Plan this HA cutover
    as a separate maintenance phase and expect an API interruption. If an
    external load balancer manages the API endpoint, review the existing
    ``kube_vip_enabled`` setting and backend ports before applying changes.

Keep ``atmosphere_kubernetes_version`` set to the current cluster version while
preparing the VIP and runtime. Preview the selected changes with the complete
inventory:

.. code-block:: console

    $ ansible-playbook -i hosts.ini vexxhost.atmosphere.kubernetes \
        --tags kube-vip,containerd --check --diff

Check mode previews the tasks that support it; it does not perform the cutover
or prove that the cluster will remain healthy. After reviewing the changes,
apply the same phase without ``--check``:

.. code-block:: console

    $ ansible-playbook -i hosts.ini vexxhost.atmosphere.kubernetes \
        --tags kube-vip,containerd --diff

Confirm that all controllers can reach the API through the VIP and that the
control plane is healthy before changing the Kubernetes version.

Run the Kubernetes upgrade
==========================

Set ``atmosphere_kubernetes_version`` to the exact approved target version,
without a leading ``v``, in your inventory, for example in
``inventory/group_vars/all/kubernetes.yml``. Atmosphere passes this value as
``kubernetes_version`` to the Kubernetes collection. Setting only
``kubernetes_version`` in the inventory does not select the target for
``vexxhost.atmosphere.kubernetes``.

Run the complete Kubernetes playbook against the full cluster inventory:

.. code-block:: console

    $ ansible-playbook -i hosts.ini vexxhost.atmosphere.kubernetes

The Kubernetes role checks the version change, prepares the kubeadm
configuration and binaries, upgrades the control plane, then upgrades kubelets
one node at a time, with controllers first and health checks between nodes.
Use this workflow instead of running the old package-only roles or restarting
all kubelets together. A controller-only or worker-only limit changes which
nodes participate; it is not a substitute for this complete upgrade run.

The playbook also configures Cilium after the Kubernetes role. If the installed
CNI needs an earlier upgrade to support the next Kubernetes version, complete
that prerequisite separately before starting this run.

After the playbook finishes, verify the API, node versions, pods and OpenStack
operations before moving to the next minor version or resuming the Atmosphere
service upgrade:

.. code-block:: console

    $ kubectl get --raw=/readyz
    $ kubectl get nodes -o wide
    $ kubectl get pods -A -o wide

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
