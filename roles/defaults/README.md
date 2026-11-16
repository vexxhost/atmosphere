# `defaults`

This is a meta role that contains a set of defaults which are used across the
other roles.  It is setup as a dependency in all of the other roles so that
these defaults are always available.

## Role Variables

* `atmosphere_images`: List of images which will be used for the deployment.
* `atmosphere_image_prefix`: Prefix added in front of every image reference,
  for pull-through registry caches.
* `atmosphere_image_mirrors`: Rules that redirect images from a `source`
  registry, namespace or repository to a `mirror` location.
* `atmosphere_image_overrides`: Images that replace individual entries of
  `atmosphere_images`, used exactly as written.
* `atmosphere_release_manifest`: Release manifest to deploy the images of,
  either an OCI reference or a file path. When empty, `atmosphere_images` is
  used.
* `atmosphere_release_manifest_ca_file`: CA certificate to trust when
  downloading `atmosphere_release_manifest` from a registry.

See the "Container images and mirrors" deployment guide for details.
