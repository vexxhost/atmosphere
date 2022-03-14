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

You will need ``tox`` installed on your operating system, you can simply make
sure that you have the appropriate OpenStack environment variables set (such
as ``OS_CLOUD`` or ``OS_AUTH_URL``, etc.) and then you can run the following
command::

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