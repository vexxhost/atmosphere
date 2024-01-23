# Nova

## Troubleshooting

### Provisioning failure due to `downloading` volume

If you're trying to provision a new instance that is using a volume where the
backend needs to download images directly from Glance (such as PowerStore for
example) and it fails with the following error:

```text
Build of instance 54a41735-a4cb-4312-b812-52e4f3d8c500 aborted: Volume 728bdc40-fc22-4b65-b6b6-c94ee7f98ff0 did not finish being created even after we waited 187 seconds or 61 attempts. And its status is downloading.
```

This means that the volume service could not download the image before the
compute service timed out.  Out of the box, Atmosphere ships with the volume
cache enabled to help offset this issue.  However, if you're using a backend
that does not support the volume cache, you can increase the timeout by setting
the following in your `inventory/group_vars/all/nova.yml` file:

```yaml
nova_helm_values:
  conf:
    enable_iscsi: true
    nova:
      DEFAULT:
        block_device_allocate_retries: 300
```
