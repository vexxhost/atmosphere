# Purestorage

To use Purestorage as storage, we need to configure the compute node, Nova & Cinder.

In the Atmosphere cinder image the pip purestorage package is already installed.

For more information about the configuration please visit the [openstack documentation](https://docs.openstack.org/cinder/zed/configuration/block-storage/drivers/pure-storage-driver.html)

## Configure Cinder

Use the following override to configure cinder.

```yaml
cinder_helm_values:
  pod:
    useHostNetwork:
      volume: true
      backup: true
    security_context:
      cinder_volume:
        container:
          cinder_volume:
            readOnlyRootFilesystem: true
            privileged: true
      cinder_backup:
        container:
          cinder_backup:
            privileged: true
  bootstrap:
    volume_types:
      # volume type for PURE with multiattach on
      MULTI-ATTACH:
        multiattach: "\"<is> True\""
        volume_backend_name: "PURE1"
        access_type: "private"
  conf:
    enable_iscsi: true
    cinder:
      DEFAULT:
        enabled_backends: pure1,rbd1
      PURE:
        volume_backend_name: pure1
        volume_driver: cinder.volume.drivers.pure.PureISCSIDriver
        san_ip: <PURE API PORT>
        pure_api_token: <PUREAPI>
        driver_ssl_cert_verify: False
        pure_automatic_max_oversubscription_ratio: True
        image_volume_cache_enabled: True
        image_volume_cache_max_size_gb: 200
        image_volume_cache_max_count: 50
        use_multipath_for_image_xfer: True
```

## Configure Nova

Enable the enable_iscsi setting for Nova

```yaml
nova_helm_values:
  conf:
    enable_iscsi: true
```
