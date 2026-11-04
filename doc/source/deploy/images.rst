############################
Container images and mirrors
############################

Every Atmosphere commit and release is described by a *release manifest*: a
list of every container image it deploys, each pinned by digest. Deployments
can use a release manifest directly, pull through a registry cache with an
image prefix, redirect images with mirror rules, or run fully disconnected from
a mirror created with ``atmosphere-release``.

Image references are resolved by Ansible when Atmosphere renders its
manifests, so these options work with any Kubernetes distribution and
container runtime.

*****************
Release manifests
*****************

Release manifests are published as OCI artifacts to
``ghcr.io/vexxhost/atmosphere-release``:

* ``<commit sha>`` for every commit on ``main`` and the ``stable/*`` branches
* ``<branch>`` for the latest commit on a branch, such as ``main`` or
  ``stable-2025.2``
* ``<version>`` for every release, such as ``v7.9.0``

The manifest published for a merged pull request is the one that CI deployed
and tested for it, as long as no other change to the image list was merged in
between; otherwise it is generated again and annotated with
``com.vexxhost.atmosphere.tested: "false"``. A release does not resolve any
image again: it ships the manifest published for the released commit. The
manifest is also attached to each GitHub release as ``release-manifest.yaml``,
and the images in the Ansible collection on Ansible Galaxy are pinned to the
same digests.

To deploy the images of a specific release manifest, set:

.. code-block:: yaml

    atmosphere_release_manifest: ghcr.io/vexxhost/atmosphere-release:v7.9.0

An OCI reference is read through ``atmosphere_image_mirrors`` and
``atmosphere_image_prefix``, like every image, so a deployment that pulls
through a registry cache or mirror also reads the manifest from it. The value
can also be the path to a ``release-manifest.yaml`` file on the Ansible
controller, which is used as it is.

If the registry uses a certificate from a private CA, point
``atmosphere_release_manifest_ca_file`` at that CA certificate on the Ansible
controller:

.. code-block:: yaml

    atmosphere_release_manifest: registry.internal/atmosphere/ghcr.io/vexxhost/atmosphere-release:v7.9.0
    atmosphere_release_manifest_ca_file: /etc/pki/registry-ca.pem

Registry credentials are read from the Docker configuration
(``~/.docker/config.json``) of the user running Ansible. When
``atmosphere_release_manifest`` is empty, the images listed in the
``defaults`` role of the installed collection are used.

The Kubernetes control plane images are pinned for the default
``atmosphere_kubernetes_version``. If you deploy another Kubernetes version,
they use the tag for that version instead.

*************************
Pull-through image prefix
*************************

If you use a pull-through registry cache, such as Harbor proxy cache projects
named after each upstream registry (``docker.io``, ``ghcr.io``, ``quay.io``,
``registry.k8s.io``), set ``atmosphere_image_prefix``:

.. code-block:: yaml

    atmosphere_image_prefix: harbor.example.com/

The prefix is added in front of every image reference, for example
``harbor.example.com/quay.io/ceph/ceph:v18.2.7@sha256:...``. Pulls by digest
work through pull-through caches, so the prefix can be combined with a release
manifest. Your cache needs a proxy project for every registry the release
uses.

************
Mirror rules
************

Mirror rules redirect images to other locations. Each rule has a ``source``,
which is a registry, a namespace or a single repository, and a ``mirror``
that replaces the matching part of the image repository. The tag and digest
are kept. When several rules match an image, the most specific one wins, and
``atmosphere_image_prefix`` applies to the images that no rule matches.

For example, with Harbor proxy cache projects that are not named after the
upstream registries:

.. code-block:: yaml

    atmosphere_image_mirrors:
      - source: docker.io
        mirror: harbor.example.com/dockerhub-proxy
      - source: quay.io
        mirror: harbor.example.com/quay-proxy
      - source: ghcr.io
        mirror: harbor.example.com/ghcr-proxy
      - source: registry.k8s.io
        mirror: harbor.example.com/k8s-proxy

With these rules, ``quay.io/ceph/ceph:v18.2.7@sha256:...`` is pulled from
``harbor.example.com/quay-proxy/ceph/ceph:v18.2.7@sha256:...``.

kubeadm pulls the Kubernetes control plane images by tag from a single image
repository, so ``kube-apiserver``, ``kube-controller-manager``,
``kube-scheduler`` and ``kube-proxy`` must resolve to the same repository
prefix and keep their names.

************************
Overriding single images
************************

``atmosphere_image_overrides`` replaces individual images after the release
manifest, the mirror rules and the image prefix have been applied. The values
are used exactly as written:

.. code-block:: yaml

    atmosphere_image_overrides:
      haproxy: registry.example.com/haproxy:2.5@sha256:...

Pin overrides by digest so that every deployment of the environment pulls the
same image.

*******************
Mirroring a release
*******************

``atmosphere-release`` copies a release to your own registry. Download it for
your platform from the assets of an Atmosphere release on GitHub, or install it
with Go:

.. code-block:: console

    $ go install github.com/vexxhost/atmosphere/cmd/atmosphere-release@<version>

Authenticate to the registries with ``docker login`` first;
``atmosphere-release`` uses the Docker credentials configuration.

Images are copied completely, with every platform, so their digests do not
change, and every digest is verified after copying. This can take a lot of
space, because many upstream images include several architectures.

Connected mirror
================

Mirror a release into a registry and write the variables for your inventory:

.. code-block:: console

    $ atmosphere-release mirror ghcr.io/vexxhost/atmosphere-release:v7.9.0 \
        --to registry.example.com/atmosphere \
        --rules-output inventory/group_vars/all/mirror.yml

The generated file sets ``atmosphere_release_manifest`` to the mirrored copy of
the release manifest and ``atmosphere_image_mirrors`` to the rules for the
mirror.

The ``--layout`` option controls how images are named in the mirror:

``nested`` (default)
    Images keep their full path under the destination, for example
    ``registry.example.com/atmosphere/quay.io/ceph/ceph``. Use it with
    registries that allow nested repository paths, such as Harbor or the CNCF
    Distribution registry.

``flat``
    The full source path becomes one repository name, for example
    ``registry.example.com/atmosphere/quay.io--ceph--ceph``. Use it with
    registries that limit how deep repository paths can be, such as GitLab, or
    Red Hat Quay without ``FEATURE_EXTENDED_REPOSITORY_NAMES``.

``single-repo``
    Every image is stored in the destination repository and tagged with its
    source, for example
    ``registry.example.com/atmosphere:quay.io--ceph--ceph--v18.2.7``. This
    layout needs ``--kubernetes-prefix``.

In every layout, the images kubeadm uses keep their names under one prefix.
kubeadm also pulls the etcd and CoreDNS images that match your Kubernetes
version; add them with ``--extra-image``:

.. code-block:: console

    $ atmosphere-release mirror ghcr.io/vexxhost/atmosphere-release:v7.9.0 \
        --to registry.example.com/atmosphere --layout flat \
        --extra-image registry.k8s.io/etcd:3.5.15-0 \
        --extra-image registry.k8s.io/coredns/coredns:v1.11.1 \
        --rules-output inventory/group_vars/all/mirror.yml

Disconnected environments
=========================

Export a release to a directory on a host with internet access, carry the
directory into the disconnected environment, then import it into your
registry:

.. code-block:: console

    $ atmosphere-release mirror ghcr.io/vexxhost/atmosphere-release:v7.9.0 \
        --to-dir /media/atmosphere-v7.9.0
    $ atmosphere-release mirror --from-dir /media/atmosphere-v7.9.0 \
        --to registry.internal/atmosphere \
        --rules-output inventory/group_vars/all/mirror.yml

The directory is an OCI image layout. The layout of the registry mirror is
chosen when importing.

*******************************
Checking and comparing releases
*******************************

Check that your image prefix and mirror rules resolve every image of a
release, and print the resulting references:

.. code-block:: console

    $ atmosphere-release check ghcr.io/vexxhost/atmosphere-release:v7.9.0 \
        --prefix harbor.example.com/ --rules mirror-rules.yml --print

Show the image changes between two releases:

.. code-block:: console

    $ atmosphere-release diff ghcr.io/vexxhost/atmosphere-release:v7.8.0 \
        ghcr.io/vexxhost/atmosphere-release:v7.9.0

The ``image_manifest`` role and playbook are deprecated in favour of
``atmosphere-release mirror``, and will be removed in a future release.
