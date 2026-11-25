======
Images
======

Atmosphere deploys every service from container images pinned by digest. This
page describes how the OpenStack service images and the hypervisor image are
built. :doc:`../deploy/images` describes how to pull them through a registry
cache or mirror.

************************
OpenStack service images
************************

Starting with Atmosphere 8.x (OpenStack 2026.1), the OpenStack service images
are built from source on Debian 13 (``debian:13-slim``) with Python 3.13. Each
major release has its own stream of images, published as
``ghcr.io/vexxhost/<service>:<release>``, for example ``nova:2026.1`` for
Atmosphere 8.x. Every build is also published under an immutable
``<release>-<commit>`` tag, and Atmosphere pins each image by digest, so a
release always deploys the images it was tested with.

Each image is built in stages:

* A shared base image installs Python and the Python packages that every
  service uses, from a lock file with pinned versions and hashes.
* A builder stage builds the service and its plugins into wheels from their
  Git sources.
* The final image adds the operating system packages the service needs and
  installs its wheels on top of the base image.

Compilers and other build tools stay in the builder stage, so the final images
only contain what the services need at run time. Every image is built for
``amd64`` and ``arm64`` and smoke tested before it is published.

Changes that Atmosphere needs before upstream releases them are carried in
VEXXHOST forks of the OpenStack projects, as a short list of commits on top of
the upstream stable branch. Every change that a release carries is also carried
by the next release unless upstream has merged it, so upgrading never drops a
fix.

****************
Hypervisor image
****************

The ``libvirtd`` image runs libvirt and QEMU on the compute nodes. It is built
on Ubuntu with the Ubuntu Cloud Archive, since live migration needs QEMU
versions and machine types that stay compatible between hosts. VEXXHOST
rebuilds Ubuntu's QEMU package with a small number of patches, such as one that
keeps live migration working between AMD hosts that run different kernel
versions.

.. list-table::
   :header-rows: 1

   * - Atmosphere
     - Base
     - libvirt
     - QEMU
   * - 7.x (2025.2)
     - Ubuntu 24.04
     - 10.0.0
     - 8.2.2
   * - 8.x (2026.1)
     - Ubuntu 24.04
     - 10.0.0
     - 8.2.2

Upgrading from 7.x to 8.x keeps the same libvirt and QEMU versions, so
instances can live-migrate in both directions between upgraded compute nodes
and nodes that still run 7.x.
