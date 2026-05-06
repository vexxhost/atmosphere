# `glance_image`

This role uploads an image into OpenStack Glance and keeps it in sync with
the upstream source URL.

## Change detection

On every run, the role sends an HTTP ``HEAD`` request to ``glance_image_url``.

If the server returns an ``ETag`` header, the role captures it and compares it
against the ``atmosphere:image:etag`` property stored on any existing image
with the same name.  A re-upload is triggered when:

- no image with that name exists yet, or
- the ``atmosphere:image:url`` property differs from ``glance_image_url``, or
- an ``ETag`` is available **and** it differs from the stored
  ``atmosphere:image:etag``.

If the server does **not** return an ``ETag`` header (for example a plain HTTP
file server), the role falls back to URL-only change detection.  As long as
``glance_image_url`` stays the same the role is idempotent; when the URL
changes a re-upload occurs.

## Upload sequence

To ensure a service image is always available under the expected name, the
role uploads the new image first and only renames the previous image as
obsolete once the upload has succeeded.  If the upload fails the old image
remains available under the original name.

The outdated image is renamed to ``<name>-<short-etag>`` (or to
``<name>-<short-id>`` when the existing image carries no stored ``ETag``) and
its tags are replaced with ``atmosphere:image:obsolete``.

## Properties stamped on uploaded images

- ``atmosphere:image:url`` — the exact URL used to download the image.
- ``atmosphere:image:etag`` — the ``ETag`` returned by that URL at upload
  time (only present when the source URL exposes an ``ETag``).

Images uploaded by earlier versions of Atmosphere lack these properties
and are treated as outdated on the next run, which causes a one-time
re-upload.
