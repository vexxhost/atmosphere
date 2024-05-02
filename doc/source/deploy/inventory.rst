==================
Building Inventory
==================

Atmosphere relies on an Ansible inventory in order to drive the deployment of
all the components.

In order to deploy Atmosphere, you will need to build a directory structure
that will contain all the configuration files and secrets required to deploy
the platform.

The recommended layout is as follows:

.. code-block:: text

    cloud-config
    ├── inventory
    │   ├── group_vars
    │   │   ├── all
    │   │   │   ├── ceph.yml
    │   │   │   ├── cluster_issuer.yml
    │   │   │   ├── endpoints.yml
    │   │   │   ├── keepalived.yml
    │   │   │   ├── kube-prometheus-stack.yml
    │   │   │   ├── kubernetes.yml
    │   │   │   ├── neutron.yml
    │   │   │   └── secrets.sops.yml
    │   │   ├── cephs
    │   │   │   └── osds.yml
    │   └── hosts.ini
    ├── playbooks
    │   └── site.yml
    └── requirements.yml

*************
``hosts.ini``
*************

The ``hosts.ini`` file is the Ansible inventory file that will be used to deploy
the platform. It is recommended to use the following layout:

.. code-block:: ini

    [controllers]
    ctl1.cloud.atmosphere.dev
    ctl2.cloud.atmosphere.dev
    ctl3.cloud.atmosphere.dev

    [computes]
    kvm1.cloud.atmosphere.dev
    kvm2.cloud.atmosphere.dev
    kvm3.cloud.atmosphere.dev

    [cephs]
    ceph1.cloud.atmosphere.dev
    ceph2.cloud.atmosphere.dev
    ceph3.cloud.atmosphere.dev

.. admonition:: FQDNs are required!

      The hostnames listed in the inventory file must be a FQDN that resolves to
      the IP address of the host.  If they do not, you will have failures such
      as agents failing to start, live migration failures and other transient
      and hard to diagnose issues.
