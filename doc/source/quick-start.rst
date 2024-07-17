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

In order to get started, you'll need a **Ubuntu 22.04** system with the
following minimum system requirements:

- Cores: 8 threads (or vCPUs)
- Memory: 32GB

If you're looking to run Kubernetes clusters, you'll need more memory
for the workloads, it following minimum is recommended (but more memory
is always better!):

- Cores: 16 threads (or vCPUs)
- Memory: 64GB

.. admonition:: Nested Virtualization
    :class: warning

    If you're running this inside a virtual machine, it is **extremely**
    important that the virtual machines supported nested virtualization,
    otherwise the performance of the VMs will be un-usable.

You'll need to start all of the necessary dependencies first:

.. code-block:: bash

    $ sudo apt-get update
    $ sudo apt-get install git tox

Once done, you can clone the repository locally and switch to the
``atmosphere`` directory:

.. code-block:: bash

    $ git clone https://github.com/vexxhost/atmosphere.git
    $ cd atmosphere

Once you're in the directory, you can deploy the all-in-one environment
by running the following command:

.. code-block:: bash

    $ cd atmosphere
    $ sudo tox -e molecule-aio-ovn

If you want to use the ML2/Open vSwitch plugin, you can run the following
command:

.. code-block:: bash

    $ sudo tox -e molecule-aio-openvswitch

Once the deployment is done, it will have a full deployment of all services
inside the same host, so you can use the cloud from the same machine by
referencing the usage section.

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

For the CLI, you can ``source /root/openrc`` and then use the ``openstack``
CLI.  For example, if you want to list the networks, you can run the
following command:

.. code-block:: console

    $ source /root/openrc
    $ openstack network list

For the Horizon dashboard, you can find the URL to access it by running
the following command:

.. code-block:: console

    $ kubectl -n openstack get ingress/dashboard -ojsonpath='{.spec.rules[0].host}'

You can find the credentials to login to the dashboard reading the
`/root/openrc` file.  You can use the following variables to match
the credentials:

- Username: ``OS_USERNAME``
- Password: ``OS_PASSWORD``
- Domain: ``OS_USER_DOMAIN_NAME``
