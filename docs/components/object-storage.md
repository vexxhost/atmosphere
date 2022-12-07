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

## Usage

### S3

The object storage presents an S3-compatible API which can with credentials
generated using the OpenStack CLI.

```console
$ openstack ec2 credentials create
+------------+----------------------------------------------------------------------------------------------------------------------------------------+
| Field      | Value                                                                                                                                  |
+------------+----------------------------------------------------------------------------------------------------------------------------------------+
| access     | 4cbacab165774994bcadba4a5451cbdc                                                                                                       |
| links      | {'self': 'https://identity.example.com/v3/users/dd5664a9739d4afba929b37d3f123f28/credentials/OS-EC2/4cbacab165774994bcadba4a5451cbdc'} |
| project_id | f5ed2d21437644adb2669f9ade9c949b                                                                                                       |
| secret     | b3ca0842898e4692a71a9ae1233e8c8e                                                                                                       |
| trust_id   | None                                                                                                                                   |
| user_id    | dd5664a9739d4afba929b37d3f123f28                                                                                                       |
+------------+----------------------------------------------------------------------------------------------------------------------------------------+
```

With the credentials above, you should be able to access the object storage
using the `access` and `secret` values, with your object storage to be located
at `https://object-storage.<CLOUD-DOMAIN>/`.
