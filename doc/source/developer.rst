=======================
Developer documentation
=======================

Patches
=======

Images
------

Solving conflicts
~~~~~~~~~~~~~~~~~

Renovate is a tool which keeps dependencies automatically updated in Atmosphere.
When it proposes an update, it's possible that one of the patches pushed upstream
has merged or it does no longer apply cleanly. You may see a message like this:

.. code-block:: console

    ERROR: process "/bin/sh -c git -C /src/ovn-bgp-agent apply --verbose /patches/ovn-bgp-agent/*" did not complete successfully: exit code: 1

In this case, you will need to re-base the patch on top of the latest upstream
commit. You can start by cloning the repository and checking out the branch
which you can find in the ``Dockerfile`` of the image. This example uses the
``ovn-bgp-agent`` image, but the same applies to all other images.

.. code-block:: console

    pushd $(mktemp -d)
    git clone https://opendev.org/openstack/ovn-bgp-agent.git .
    git switch master

Now, you can apply the patches to the repository. You can find the command used
to apply patches in the ``Dockerfile`` of the image. In this case, it's:

.. code-block:: console

    git am -3 ~/src/github.com/vexxhost/atmosphere/images/ovn-bgp-agent/patches/ovn-bgp-agent/*.patch

At this point, you'll likely see a conflict, you can proceed to solve it. Once you
have solved it, you can run `git add <file>` to mark the file as resolved. Once there
are no longer any conflicts to solve, you can run:

.. code-block:: console

    git am --continue

Once you're complete, you can delete all the old patches and create a new patch
series. You can do this by running:

.. code-block:: console

    rm ~/src/github.com/vexxhost/atmosphere/images/ovn-bgp-agent/patches/ovn-bgp-agent/*.patch
    git format-patch -o ~/src/github.com/vexxhost/atmosphere/images/ovn-bgp-agent/patches/ovn-bgp-agent origin/master

Also, you'll need to update the ``Dockerfile`` to point to the new base
commit which will usually be an ``ARG`` ending with ``_GIT_REF``.  You can find
the commit to use by running:

.. code-block:: console

    git rev-parse origin/master

You can then copy the commit hash and replace the ``ARG`` in the ``Dockerfile``
and push the changes to your branch and create a pull request.

Backports
=========

To backport a change, you can simply add the appropriate label to the
pull request, the pattern is ``backport <branch>``.  For example, if you want to
backport a change to the ``stable/2023.1`` branch, you would add the label
``backport stable/2023.1``.  GitHub Actions will generate a pull request
automatically once the pull request merges.

If you need to run a backport after a pull request has merged, you can do so
by adding the labels and then adding a comment with the text ``/backport``.

Upgrade tests
=============

The ``upgrade``, ``upgrade-multinode`` and ``upgrade-full`` Molecule scenarios
test an upgrade from the previous release, modelled on OpenStack's grenade:

* ``upgrade`` deploys the previous release on one node, creates a workload (a
  server with a floating IP and a volume, and an application credential),
  upgrades to the change under test while measuring how long the workload and
  the Keystone API are unreachable, checks that the workload kept running with
  its data, runs the Compute upgrade checks and Tempest.
* ``upgrade-multinode`` does the same on three nodes and live-migrates the
  workload to another compute node after the upgrade.
* ``upgrade-full`` also puts a load balancer in front of the workload and
  checks that it keeps serving the same server.

The previous release is the newest ``stable/*`` branch that is older than the
branch under test. Set ``ATMOSPHERE_UPGRADE_FROM`` to upgrade from another Git
reference.

These scenarios take a few hours each, so they do not run on every pull
request. To run them in CI, for example before a release or when changing
RabbitMQ, Percona XtraDB Cluster or Kubernetes, open a pull request that is not
meant to be merged and adds the jobs to ``.zuul.yaml``:

.. code-block:: yaml

   - project:
       templates:
         - atmosphere-molecule-ubuntu-noble-jobs
       check:
         jobs:
           - atmosphere-molecule-ubuntu-noble-aio-upgrade-openvswitch: &upgrade
               dependencies: [atmosphere-release-manifest]
               voting: false
           - atmosphere-molecule-ubuntu-noble-aio-upgrade-ovn: *upgrade
           - atmosphere-molecule-ubuntu-noble-multinode-upgrade-openvswitch: *upgrade
           - atmosphere-molecule-ubuntu-noble-multinode-upgrade-ovn: *upgrade
           - atmosphere-molecule-ubuntu-noble-aio-upgrade-full: *upgrade

The jobs depend on ``atmosphere-release-manifest`` so that they deploy the
images built for the pull request.

To upgrade from another branch instead, for example to test an upgrade between
two releases that are still being prepared, add this to each job:

.. code-block:: yaml

   vars:
     molecule_environment:
       ATMOSPHERE_UPGRADE_FROM: <branch>
