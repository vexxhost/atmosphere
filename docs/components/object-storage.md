# Object Storage

Atmosphere makes object storage available through Ceph over both the S3 and the
Swift API.

## Configuration

In order to make sure that the object storage is configured correctly, you'll
need to provide the following configuration:

```yaml
atmosphere_object_storage_service_user_password: "password"
```

!!! note

    In future releases of Atmosphere, secrets will be automatically generated
    if they are not provided, however they are required for now.

## Manual configuration

!!! warning

    The current process involves a few manual steps such as generating endpoints,
    and users for the service.  This will be automated in the future.

1. Create user for the object storage service and provide access to the service
   project.

   ```bash
   openstack user create --domain service --password <PASSWORD> swift
   openstack role add --project service --user-domain service --user swift admin
   ```

1. Create service and endpoints for the object storage service.

    ```bash
    openstack service create --name swift --description "OpenStack Object Storage" object-store
    openstack endpoint create --region <REGION> object-store public 'https://object-storage.<CLOUD-DOMAIN>/swift/v1/%(tenant_id)s'
    openstack endpoint create --region <REGION> object-store internal 'http://rook-ceph-rgw-rook-ceph.rook-ceph.svc.cluster.local/swift/v1/%(tenant_id)s'
    ```
