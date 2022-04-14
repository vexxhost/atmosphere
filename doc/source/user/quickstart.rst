Quickstart
==========

The quick start intends to provide the most near-production experience possible,
as it is architected purely towards production-only environments. In order to
get a quick production-ready experience of Atmosphere, you will need access to
an OpenStack cloud.

The quick start is powered by Molecule and it is used in continuous integration
running against the VEXXHOST public cloud so that would be an easy target to
use to try it out.

You will need the following quotas set up in your cloud account:

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
system with ``git`` by running the following command::

   $ git clone https://opendev.org/vexxhost/ansible-collection-atmosphere

You will need ``tox`` installed on your operating system.  You will need to make
sure that you have the appropriate OpenStack environment variables set (such
as ``OS_CLOUD`` or ``OS_AUTH_URL``, etc.).  You can also use the following
environment variables to tweak the behaviour of the Heat stack that is created:

``ATMOSPHERE_STACK_NAME``
    The name of the Heat stack to be created (defaults to ``atmosphere``).

``ATMOSPHERE_PUBLIC_NETWORK``
    The name of the public network to attach floating IPs from (defaults to
    ``public``).

``ATMOSPHERE_IMAGE``
   The name or UUID of the image to be used for deploying the instances (
   defaults to ``Ubuntu 20.04.3 LTS (x86_64) [2021-10-04]``).

``ATMOSPHERE_INSTANCE_TYPE``
   The instance type used to deploy all of the different instances (defaults
   to ``v3-standard-4``).

``ATMOSPHERE_NAMESERVERS``
   A comma-separated list of nameservers to be used for the instances (defaults
   to `1.1.1.1`).

``ATMOSPHERE_USERNAME``
  The username what is used to login into the instances (defaults to ``ubuntu``).

``ATMOSPHERE_DNS_SUFFIX_NAME``
  The DNS domainname that is used for the API and Horizon. (defaults
  to ``nip.io``).

``ATMOSPHERE_ACME_SERVER``
  The ACME server, currenly this is from Letsencrypt, with
  StepCA from smallstep it is possible to run a internal ACME server.
  The CA of that ACME server should be present in the instance image.

Once you're ready to get started, you can run the following command to build
the Heat stack and ::

   $ tox -e molecule -- converge

This will create a Heat stack with the name ``atmosphere`` and start deploying
the cloud.  Once it's complete, you can login to any of the systems by using
the ``login`` sub-command.  For exampel, to login to the first controller node,
you can run the following::

   $ tox -e molecule -- login -h ctl1

In all the controllers, you will find an ``openrc`` file location inside the
``root`` account home directory, as well as the OpenStack client installed there
as well.  You can use it by running the following after logging in::

   $ source /root/openrc
   $ openstack server list

The Kubernetes administrator configuration will also be available on all of the
control plane nodes, you can simply use it by running ``kubectl`` commands on
any of the controllers as ``root``::

   $ kubectl get nodes -owide

Once you're done with your environment and you need to tear it down, you can
use the ``destroy`` sub-command::

   $ tox -e molecule -- destroy

For more information about the different commands used by Molecule, you can
refer to the Molecule documentation.
