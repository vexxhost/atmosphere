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

**********
HTTP proxy
**********

If you nodes can only access the internet through an HTTP proxy, you will need
to set the following variables within your inventory which will make sure that
the ``containerd`` and ``dockerd`` services are able to pull images through
this HTTP proxy, as well as the ``download_artifact`` role which is used to
download artifacts for deploying the cluster.

.. code-block:: yaml

    http_proxy: http://proxy.example.com:3128
    https_proxy: http://proxy.example.com:3128
    no_proxy: localhost,127.0.0.0/8,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,169.254.0.0/16,.svc,.cluster.local

If you have any other services that need to access the internet without going
through the proxy, you can add them to the ``no_proxy`` variable.
