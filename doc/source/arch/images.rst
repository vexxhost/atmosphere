======
Images
======

*************
Build Process
*************

This section provides an overview of how the container images used by Atmosphere
are built. Understanding this process is crucial for maintaining and customizing
the images for your specific needs.

Multi-Stage Builds
==================

The images are built using a multi-stage build process. This means that all
build-time dependencies are included only in the intermediate stages and are not
present in the final runtime images.

Benefits
--------

The multi-stage build process offers several benefits which improve the
efficiency, security, and performance of the images.

Smaller Image Size
^^^^^^^^^^^^^^^^^^

By excluding build-time dependencies, the final images are significantly
smaller. This reduction in size offers several advantages.

First, it leads to more efficient storage usage, as smaller images consume less
disk space, making it easier to manage and store multiple images. Additionally,
the reduced image size results in faster download times when pulling images from
a container registry, thereby speeding up deployment times.

Furthermore, smaller images require less network bandwidth, which can be beneficial
in environments with limited network resources.

Enhanced Security
^^^^^^^^^^^^^^^^^

Reducing the number of packages and dependencies in the final image decreases
the attack surface, thereby enhancing security. With only essential runtime
dependencies included, the opportunities for attackers to exploit
vulnerabilities are significantly reduced, leading to minimized exposure.

Moreover, a smaller set of packages simplifies auditing, making it easier to
ensure that all components are secure and up-to-date. Additionally, fewer
dependencies mean fewer updates and patches, which simplifies the maintenance
process and reduces the risk of introducing new vulnerabilities.

Improved Performance
^^^^^^^^^^^^^^^^^^^^

Smaller images lead to faster deployment times and lower resource consumption,
which improves overall system performance. Containers based on smaller images
start up more quickly, enhancing the responsiveness of applications and services.

Reduced resource consumption translates to lower memory and CPU usage, allowing
more efficient utilization of system resources. Furthermore, faster deployment
and efficient resource use enable better scalability, allowing the system to
handle increased loads more effectively.

Example
-------

The ``openstack-venv-builder`` image is used to build a virtual environment with
all of the Python dependencies required by the OpenStack services.  It also
contains a modified version of the ``upper-constraints.txt`` file, which has
many of the dependencies pinned to specific versions and modified to avoid
security vulnerabilities.

.. literalinclude:: ../../../images/openstack-venv-builder/Dockerfile
   :language: dockerfile
   :caption: ``images/openstack-venv-builder/Dockerfile``

In addition to that image, the ``openstack-python-runtime`` image is a stripped
down base image as a run-time for OpenStack services with no installed
packages than the base Ubuntu image.

.. literalinclude:: ../../../images/openstack-runtime/Dockerfile
   :language: dockerfile
   :caption: ``images/openstack-runtime/Dockerfile``

With the ``openstack-venv-builder`` & ``openstack-python-runtime`` the image for
a project such as OpenStack Nova can be built using the following Dockerfile.

This Dockerfile uses the ``openstack-venv-builder`` image to build the virtual
environment and then copies the virtual environment into the final image based
on the ``openstack-python-runtime`` image.  With this, it has no other build-time
dependencies and only the runtime dependencies required for the OpenStack Nova
service.

.. literalinclude:: ../../../images/nova/Dockerfile
   :language: dockerfile
   :caption: ``images/nova/Dockerfile``
