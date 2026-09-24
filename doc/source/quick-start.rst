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

You'll need to start by installing all of the necessary dependencies first,
**you also need to make sure you run all of these commands as ``root``**:

.. code-block:: console

    $ sudo -i
    $ apt-get update
    $ apt-get install git tox

Once done, you can clone the repository locally and switch to the
``atmosphere`` directory:

.. code-block:: console

    $ git clone https://github.com/vexxhost/atmosphere.git
    $ cd atmosphere

Once you're in the directory, you can deploy the all-in-one environment
by running the following command as ``root``:

.. code-block:: console

    $ tox -e molecule-aio-ovn

If you want to use the ML2/Open vSwitch plugin, you can run the following
command:

.. code-block:: console

    $ tox -e molecule-aio-openvswitch

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

OpenStack Preparation
---------------------

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

Deployment with Heat stack
==========================
You can also deploy the environment using the Heat stack that is provided. Once you're ready to get started from OpenStack preparation section, you can run the following command to build the Heat stack:

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

Deploying Atmosphere Without Heat Stack
---------------------------------------

We can ansible playbook also to run the deployment. Once you're ready to get started, you can run the following command to prepare the OS (root mode):

.. code-block:: console

    $ apt update; apt install python3-venv python3-dev gcc -y
    $ python3 -m venv atmosphere-env
    $ source ~/atmosphere-env/bin/activate
    $ pip install ansible
    $ ansible-galaxy collection install vexxhost.atmosphere
    $ mkdir -p cloud-config/playbooks
    $ ansible-playbook -e "workspace_path=~/cloud-config/inventory" -e "ceph_public_network=10.10.10.0/24" -e "domain_name=cloud.atmosphere.dev" vexxhost.atmosphere.generate_workspace
    $ cd ~/cloud-config/

Now we need to prepare the inventory files, you can use the following command to create the inventory files:

.. code-block:: console

    $ nano inventory/hosts.ini

..  code-block:: ini

    [controllers]
    ctl1.cloud.atmosphere.dev
    ctl2.cloud.atmosphere.dev
    ctl3.cloud.atmosphere.dev

    [cephs]
    ceph1.cloud.atmosphere.dev
    ceph2.cloud.atmosphere.dev
    ceph3.cloud.atmosphere.dev

    [computes]
    kvm1.cloud.atmosphere.dev
    kvm2.cloud.atmosphere.dev

You need to make sure that the inventory file is correct and that the hostnames are resolvable. After that we can define the disk to be used as ceph OSD.

.. code-block:: console

    $ nano inventory/group_vars/cephs/osds.yml

..  code-block:: yaml

    ceph_osd_devices:
      - /dev/sdb

.. code-block:: console

    $ nano inventory/group_vars/all/ceph.yml

..  code-block:: yaml

    ceph_mon_fsid: d6c9dd7d-9fa6-5eae-997e-a7d8350c8449
    ceph_mon_public_network: 10.10.10.0/24 #ip a

.. code-block:: console

    $ nano inventory/group_vars/all/endpoints.yml

..  code-block:: yaml

    keycloak_host: keycloak.cloud.atmosphere.dev
    kube_prometheus_stack_alertmanager_host: alertmanager.cloud.atmosphere.dev
    kube_prometheus_stack_grafana_host: grafana.cloud.atmosphere.dev
    kube_prometheus_stack_prometheus_host: prometheus.cloud.atmosphere.dev
    // ... existing code ...

.. code-block:: console

    $ nano inventory/group_vars/all/neutron.yml

..  code-block:: yaml

    neutron_networks:
    - external: true
      mtu_size: 1500
      name: public
      port_security_enabled: true
      provider_network_type: flat
      provider_physical_network: external
      shared: true
      subnets:
      - allocation_pool_end: 192.168.100.250
        allocation_pool_start: 192.168.100.100
        cidr: 192.168.100.0/24
        enable_dhcp: true
        gateway_ip: 192.168.100.254
        name: public-subnet

.. code-block:: console

    $ nano inventory/group_vars/all/keepalived.yml

..  code-block:: yaml

    keepalived_interface: ens3
    keepalived_vip: 10.10.10.100

.. code-block:: console

    $ nano inventory/group_vars/all/kubernetes.yml

..  code-block:: yaml

    kubernetes_hostname: k8s.cloud.atmosphere.dev
    kubernetes_keepalived_vip: 10.10.10.101
    kubernetes_keepalived_vrid: 42
    kubernetes_keepalived_interface: ens3

.. code-block:: console

    $ nano inventory/group_vars/all/all.yml

..  code-block:: yaml

    ---
    ovn_helm_values:
      conf:
        auto_bridge_add:
          br-ex: bond0
        ovn_bridge_mappings: external:br-ex
        ovn_bridge_datapath_type: netdev

    cluster_issuer_type: self-signed
    csi_driver: rbd
    atmosphere_network_backend: ovn

    barbican_helm_values:
      pod:
        replicas:
          api: 1

    glance_helm_values:
      pod:
        replicas:
          api: 1
    glance_images:
      - name: cirros
        url: http://download.cirros-cloud.net/0.6.2/cirros-0.6.2-x86_64-disk.img
        min_disk: 1
        disk_format: raw
        container_format: bare
        is_public: true

    cinder_helm_values:
      pod:
        replicas:
          api: 1
          scheduler: 1

    placement_helm_values:
      pod:
        replicas:
          api: 1

    nova_helm_values:
      pod:
        replicas:
          api_metadata: 1
          osapi: 1
          conductor: 1
          novncproxy: 1
          spiceproxy: 1
      conf:
        nova:
          DEFAULT:
            osapi_compute_workers: 2
            metadata_workers: 2
          conductor:
            workers: 2
          scheduler:
            workers: 2

    neutron_helm_values:
      conf:
        neutron:
          DEFAULT:
            api_workers: 2
            rpc_workers: 2
            metadata_workers: 2

    heat_helm_values:
      conf:
        heat:
          DEFAULT:
            num_engine_workers: 2
          heat_api:
            workers: 2
          heat_api_cfn:
            workers: 2
          heat_api_cloudwatch:
            workers: 2
      pod:
        replicas:
          api: 1
          cfn: 1
          cloudwatch: 1
          engine: 1

    octavia_helm_values:
      conf:
        octavia:
          controller_worker:
            workers: 2
        octavia_api_uwsgi:
          uwsgi:
            processes: 2
      pod:
        replicas:
          api: 1
          worker: 1
          housekeeping: 1

And now we can back to the playbook directory and edit the site.yml:

.. code-block:: console

    $ cd ~/cloud-config/playbooks
    $ nano site.yml

..  code-block:: yaml

    ---
    - import_playbook: vexxhost.atmosphere.site

Once the preparation is done, you can run the following command to deploy the atmosphere environment:

.. code-block:: console

    $ ansible-playbook -i inventory/hosts.ini playbooks/site.yml # or ansible-playbook -i inventory/hosts.ini vexxhost.atmosphere.ceph X X X

Once the deployment is done, you can login to any of the controllers and check for openrc file. And then you can use the openrc file to interact with the openstack CLI.

Miscellaneous
-------------
If you encounter with DNS issue you can execute the following command to fix it:

.. code-block:: console

    $ ansible -i inventory/hosts.ini all -m raw -a "resolvectl dns ens3 1.1.1.1"

You can check the status of the service's endpoints by running the following command:

.. code-block:: console

    $ kubectl get ingress -A

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
