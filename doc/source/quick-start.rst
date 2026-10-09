###########
Quick Start
###########

There are several ways that you can quickly get started with Atmosphere to explore
it's capabilities.

**********
Deployment
**********

This section covers all of the different ways you can deploy a quick start
environment for Atmosphere.

.. admonition:: Testing & Development Only
    :class: info

    The quick start installation is not for production use, it's perfect
    for testing and development.

All-in-one
==========

The easiest way to get started with Atmosphere is to deploy the all-in-one
installation.  This will install an entire stack of Atmosphere, with Ceph
and all the OpenStack services inside a single machine.

.. admonition:: Non-reversible Changes
    :class: warning

    The all-in-one will fully take-over the machine by making system-level
    changes.  It's recommended to run it inside a virtual machine or a
    physical machine that can be dedicated to this purpose.

Use a new dedicated host for each release.  An all-in-one deployment changes
the operating system, networking, storage, and container runtime.  Reusing a
host from an earlier release can hide problems or leave incompatible state.

Requirements
------------

You need an **Ubuntu 22.04** system with the following minimum system
requirements:

- Cores: 8 threads (or vCPUs)
- Memory: 32GB

If you plan to run Kubernetes clusters, the following resources are
recommended:

- Cores: 16 threads (or vCPUs)
- Memory: 64GB

.. admonition:: Nested Virtualization
    :class: warning

    If you run the all-in-one inside a virtual machine, the hypervisor must
    expose nested virtualization.  Without it, instances may fail to start or
    perform poorly.

Prepare the host
----------------

Connect to the host and become ``root``.  Run all remaining commands in this
section from the root shell:

.. code-block:: console

    $ sudo -i
    $ apt-get update
    $ apt-get install -y curl git tmux tox
    $ apt-get purge -y snapd

Confirm that the host has enough resources and, for a virtual machine, access
to KVM:

.. code-block:: console

    $ nproc
    $ free -h
    $ df -h /
    $ test -e /dev/kvm && ls -l /dev/kvm
    $ lsblk -o NAME,TYPE,SIZE,MOUNTPOINTS

Do not continue with a virtual machine if ``/dev/kvm`` is missing.  Record any
empty data disks shown by ``lsblk``.  Never select the disk mounted at ``/`` as
a Ceph data device.

Select a release
----------------

Clone Atmosphere and check out an exact release tag.  Replace ``v7.8.1`` with
the release you want to deploy.  Keeping the version in an environment
variable makes this procedure reusable for later releases:

.. code-block:: console

    $ export ATMOSPHERE_VERSION=v7.8.1
    $ git clone https://github.com/vexxhost/atmosphere.git /root/atmosphere
    $ cd /root/atmosphere
    $ git checkout --detach "$ATMOSPHERE_VERSION"
    $ test "$(git describe --tags --exact-match)" = "$ATMOSPHERE_VERSION"
    $ git rev-parse HEAD

The exact-tag check prevents an accidental deployment from a moving branch or
an untagged commit.

Create the inventory and AIO configuration
------------------------------------------

The all-in-one host performs the controller, compute, and Ceph roles.  Download
the example inventory and single-node defaults published with this guide.  The
documentation copies remain available after you check out an older release
tag.  Their URLs include the release tag so configuration from one release is
not silently used with another:

.. code-block:: console

    $ install -d -m 0755 group_vars/all group_vars/cephs
    $ curl --fail --location --output inventory.yaml \
        "https://vexxhost.github.io/atmosphere/_static/aio/${ATMOSPHERE_VERSION}/inventory.yaml"
    $ curl --fail --location --output group_vars/all/molecule.yml \
        "https://vexxhost.github.io/atmosphere/_static/aio/${ATMOSPHERE_VERSION}/molecule.yml"

Do not substitute configuration from another release if either download
fails.  Each release must publish its matching files before it can use this
standalone AIO procedure.

The inventory uses a local connection and places ``instance`` in the
``controllers``, ``computes``, and ``cephs`` groups.  Validate it before making
changes to the host:

.. code-block:: console

    $ tox -e venv -- ansible-inventory -i inventory.yaml --graph

The output must show ``instance`` under all three groups.  An empty group would
cause Ansible to skip deployment plays while appearing to complete them.

Configure Ceph storage
----------------------

For a test host with only its operating-system disk, use the loop-backed Ceph
devices created by the AIO preparation playbook:

.. code-block:: console

    $ curl --fail --location --output group_vars/cephs/osds.yml \
        "https://vexxhost.github.io/atmosphere/_static/aio/${ATMOSPHERE_VERSION}/osds-loopback.yml"

The resulting configuration uses these paths:

.. code-block:: yaml

    ceph_osd_devices:
      - /dev/ceph-instance-osd0/data
      - /dev/ceph-instance-osd1/data
      - /dev/ceph-instance-osd2/data

If the host has dedicated, empty data disks, create
``group_vars/cephs/osds.yml`` with their persistent device paths instead.  For
example:

.. code-block:: yaml

    ceph_osd_devices:
      - /dev/disk/by-id/scsi-example-disk-1
      - /dev/disk/by-id/scsi-example-disk-2
      - /dev/disk/by-id/scsi-example-disk-3

Use paths under ``/dev/disk/by-id`` when possible so the configuration does not
depend on kernel device ordering.  The selected devices are erased during the
deployment.

Release compatibility checks
----------------------------

Before starting a new release, inspect the available deployer:

.. code-block:: console

    $ test -x ./bin/atmosphere && echo "Atmosphere deployer available" || echo "Using Molecule fallback"

Use ``./bin/atmosphere`` when the release provides it.  Releases without that
command use the Molecule fallback described below.

.. admonition:: Atmosphere v7.8.1
    :class: warning

    The ``v7.8.1`` tag contains Molecule 25 configuration but pins Molecule 24
    in ``tox.ini``.  For this tag only, update the three dependency entries
    before starting the deployment:

    .. code-block:: console

        $ sed -i \
            -e 's/molecule==24.9.0/molecule==25.11.0\n  molecule-plugins[docker]/' \
            -e 's/ansible-compat==24.10.0/ansible-compat>=25.1.4/' \
            tox.ini

    Do not carry this edit into a later release without first checking that
    release's ``tox.ini`` and ``molecule/aio/molecule.yml``.

Start the deployment
--------------------

Run the deployment inside ``tmux`` so it continues if the SSH connection
closes.  The session also retains the final output after the command exits:

.. code-block:: console

    $ tmux new -d -s atmosphere \; set-option remain-on-exit on

For an OVN deployment with the Atmosphere deployer, run:

.. code-block:: console

    $ tmux send-keys -t atmosphere \
        'cd /root/atmosphere && ATMOSPHERE_NETWORK_BACKEND=ovn ./bin/atmosphere deploy -i ./inventory.yaml' Enter

If the release does not provide ``./bin/atmosphere``, use the Molecule OVN
fallback:

.. code-block:: console

    $ tmux send-keys -t atmosphere \
        'cd /root/atmosphere && ATMOSPHERE_DEBUG=true tox -e molecule-aio-ovn' Enter

For ML2/Open vSwitch with the Atmosphere deployer, set
``ATMOSPHERE_NETWORK_BACKEND=openvswitch``.  With Molecule, replace
``molecule-aio-ovn`` with ``molecule-aio-openvswitch``.  OVN and Open vSwitch
are different networking backends; choose one before the initial deployment
and keep it for later runs.

Monitor the deployment
----------------------

Check progress without attaching to the session:

.. code-block:: console

    $ tmux ls
    $ tmux capture-pane -t atmosphere -p -S -200 | tail -100

Early output must show that Ansible gathers facts and runs tasks against
``instance``.  Stop and correct the inventory if the output contains any of
the following messages:

.. code-block:: text

    Unable to parse .../inventory.yaml as an inventory source
    provided hosts list is empty
    Could not match supplied host pattern, ignoring: controllers
    Could not match supplied host pattern, ignoring: cephs
    Could not match supplied host pattern, ignoring: computes

A converge action in which every deployment play is skipped is a failure, even
if Molecule labels the action successful.

The complete deployment can take more than an hour.  It is successful only
when the retained output ends with a zero exit status and the Molecule or
Atmosphere success summary.  For the Molecule fallback, look for output similar
to:

.. code-block:: text

    molecule-aio-ovn: OK
    congratulations :)

The verification stage runs the integration tests.  Do not use Kubernetes pod
status alone to decide that installation has finished because services can be
running before the deployment and verification command completes.

Validate the environment
------------------------

After the deployment succeeds, load the generated OpenStack credentials and
check all three layers:

.. code-block:: console

    $ source /root/openrc
    $ cephadm shell -- ceph status
    $ kubectl get nodes
    $ kubectl get pods --all-namespaces
    $ openstack service list
    $ openstack network list
    $ openstack image list

The integration-test results remain in the ``atmosphere`` tmux session.  Keep
the session until you have reviewed them.  You can remove the completed session
afterward:

.. code-block:: console

    $ tmux kill-session -t atmosphere

Once validation succeeds, use the cloud from the same machine by following the
usage section below.

Multi-node
==========

The multi-node intends to provide the most near-production experience possible,
as it is architected purely towards production-only environments. In order to
get a quick production-ready experience of Atmosphere, this will deploy a full
stack of Atmosphere, with Ceph and all the OpenStack services across multiple
machines in a lab environment.

OpenStack
---------

You can deploy Atmosphere on top of an existing OpenStack environment where many
virtual machines will be deployed in the same way that you'd have multiple
physical machines in a datacenter for a production environment.

The quick start is powered by Molecule and it is used in continuous integration
running against the VEXXHOST public cloud so that would be an easy target to
use to try it out.

ou will need the following quotas set up in your cloud account:

* 8 instances
* 32 cores
* 128GB RAM
* 360GB storage

These resources will be used to create a total of 8 instances broken up as
follows:

* 3 Controller nodes
* 3 Ceph OSD nodes
* 2 Compute nodes

First of all, you'll have to make sure you clone the repository locally to your
system with `git` by running the following command:

.. code-block:: console

    $ git clone https://github.com/vexxhost/atmosphere

You will need ``tox`` installed on your operating system.  You will need to make
sure that you have the appropriate OpenStack environment variables set (such
as ``OS_CLOUD`` or ``OS_AUTH_URL``, etc.).  You can also use the following
environment variables to tweak the behaviour of the Heat stack that is created:

* ``ATMOSPHERE_STACK_NAME``: The name of the Heat stack to be created (defaults to
  `atmosphere`).
* ``ATMOSPHERE_PUBLIC_NETWORK``: The name of the public network to attach floating
  IPs from (defaults to ``public``).
* ``ATMOSPHERE_IMAGE``: The name or UUID of the image to be used for deploying the
  instances (defaults to ``Ubuntu 20.04.3 LTS (x86_64) [2021-10-04]``).
* ``ATMOSPHERE_INSTANCE_TYPE``(Deprecated): The instance type used to deploy all of the
  different instances.(It doesn't have its own default value.)
  This has been deprecated from v1.4.0. You can configure the instance type per a
  machine role using ``ATMOSPHERE_CONTROLLER_INSTANCE_TYPE``,
  ``ATMOSPHERE_COMPUTE_INSTANCE_TYPE``, and ``ATMOSPHERE_STORAGE_INSTANCE_TYPE``
  variables. For backwards compatibility, if variables specific to the machine roles
  are not set and ``ATMOSPHERE_INSTANCE_TYPE`` is set, ``ATMOSPHERE_INSTANCE_TYPE`` value
  is used.
* ``ATMOSPHERE_CONTROLLER_INSTANCE_TYPE``: The instance type used to deploy controller
  instances (defaults to ``v3-standard-16``).
* ``ATMOSPHERE_COMPUTE_INSTANCE_TYPE``: The instance type used to deploy compute
  instances (defaults to ``v3-standard-4``).
* ``ATMOSPHERE_STORAGE_INSTANCE_TYPE``: The instance type used to deploy storage
  instances (defaults to ``v3-standard-4``).
* ``ATMOSPHERE_NAMESERVERS``: A comma-separated list of nameservers to be used for
  the instances (defaults to ``1.1.1.1``).
* ``ATMOSPHERE_USERNAME``: The username what is used to login into the instances (
  defaults to ``ubuntu``).
* ``ATMOSPHERE_DNS_SUFFIX_NAME``: The DNS domainname that is used for the API and
  Horizon. (defaults to ``nip.io``).
* ``ATMOSPHERE_ACME_SERVER``: The ACME server, currenly this is from LetsEncrypt,
  with StepCA from SmallStep it is possible to run a internal ACME server.
  The CA of that ACME server should be present in the instance image.
* ``ATMOSPHERE_ANSIBLE_VARS_PATH``: The path for ansible group_vars and host_vars.
  This to build a multinode development cluster with own configs, that are not
  generated by molecule. This way you can test your configs before you bring
  them to production.

Once you're ready to get started, you can run the following command to build
the Heat stack:

.. code-block:: console

    $ tox -e molecule-venv -- converge

This will create a Heat stack with the name `atmosphere` and start deploying
the cloud.  Once it's complete, you can login to any of the systems by using
the `login` sub-command.  For exampel, to login to the first controller node,
you can run the following:

.. code-block:: console

    $ tox -e molecule-venv -- login -h ctl1

At this point, you can proceed to the usage section to see how to interact
with the cloud.

Once you're done with your environment and you need to tear it down, you can
use the `destroy` sub-command:

.. code-block:: console

    $ tox -e molecule-venv -- destroy

For more information about the different commands used by Molecule, you can
refer to the Molecule documentation.

*****
Usage
*****

Once the deployment is done, you can either use the CLI to interact with
the OpenStack environment, or you can access the Horizon dashboard.

Command Line Interface (CLI)
============================

When using the CLI, there are two different ways of authenticating
to the OpenStack environment.  You can either use local credentials
or you can use Single-Sign On (SSO) with the OpenStack CLI.

Local Credentials
-----------------

On any of the control plane node, you can find the credentials in the
``/root/openrc`` file.  In an all-in-one environment, this will be the
same machine where you deployed the environment.

For example, if you want to list the networks, you can run the following
command (you only need to source the file once):

.. code-block:: console

    $ source /root/openrc
    $ openstack network list

Single-Sign On (SSO)
--------------------

If you want to use the Keycloak SSO with the OpenStack CLI, you will need
to install the `keystoneauth-websso <https://github.com/vexxhost/keystoneauth-websso>`_ plugin first.

To install it using ``pip``, run the following command:

.. code-block:: console

    $ pip install keystoneauth-websso

You can create a ``clouds.yml`` file with the following content inside
of the ``~/.config/openstack`` directory:

.. code-block:: yaml

    clouds:
      atmosphere:
        auth_type: v3websso
        auth_url: https://identity.example.com
        identity_provider: atmosphere
        protocol: openid

You can then use OpenStack CLI commands by either setting the ``OS_CLOUD``
environment variable or using the ``--os-cloud`` option, for example
to list the networks:

.. code-block:: console

    $ openstack --os-cloud atmosphere network list

Or, alternatively you can use the environment variable:

.. code-block:: console

    $ export OS_CLOUD=atmosphere
    $ openstack network list

Dashboard
=========

For the Horizon dashboard, you can find the URL to access it by running
the following command:

.. code-block:: console

    $ kubectl -n openstack get ingress/dashboard -ojsonpath='{.spec.rules[0].host}'

You can either login to the dashboard using the local credentials or
using single-sign on (SSO).

Local Credentials
-----------------

You can find the credentials to login to the dashboard reading the
`/root/openrc` file on any of the control plane nodes.  You can use
the following variables to match the credentials:

- Username: ``OS_USERNAME``
- Password: ``OS_PASSWORD``
- Domain: ``OS_USER_DOMAIN_NAME``

Single-Sign On (SSO)
--------------------

You can select the "Atmosphere" option in the login page and you will
be redirected to the Keycloak login page.
