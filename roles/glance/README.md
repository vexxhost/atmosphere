# `glance`

Images in `glance_images` can declare `owner` and `owner_domain`. The role
passes both values to `atmosphere.common.glance_image`, which resolves the
project and reconciles image ownership. Omit both keys to preserve the default
upload project.

Use either `url`, or a digest-pinned OCI source with `oci_reference`,
`oci_path`, and `oci_sha512`. OCI artifacts are extracted and checksum-verified
by `atmosphere.common.glance_image` before upload.

```yaml
glance_images:
  - name: trusted-image
    url: https://images.example.invalid/trusted-image.raw
    disk_format: raw
    container_format: bare
    is_public: true
    owner: service
    owner_domain: service
    properties:
      os_distro: ubuntu
```

```yaml
glance_images:
  - name: trusted-oci-image
    oci_reference: docker.io/example/image@sha256:<manifest-digest>
    oci_path: /images/image.qcow2
    oci_sha512: <qcow2-sha512>
    disk_format: qcow2
    container_format: bare
```
