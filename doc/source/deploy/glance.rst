####################
Glance Configuration
####################

Glance, the image service used by OpenStack, can be configured to use different
storage backends depending on your deployment needs. This document provides
guidance on setting up Glance with either the integrated Ceph cluster that
comes with Atmosphere or using Cinder as a storage backend, with additional
details for configurations that require special handling.

****
Ceph
****

The Atmosphere deployment includes a pre-configured Ceph cluster that is
ready to use with Glance, requiring no additional configuration steps. This
setup is recommended for most users as it provides a seamless and integrated
storage solution.

******
Cinder
******

To configure Glance to use Cinder as its storage backend, which allows for
managing images as block storage volumes, apply the following configuration:

.. code-block:: yaml

    glance_helm_values:
      storage: cinder
      conf:
        glance:
          glance_store:
            stores: cinder
            default_store: cinder
          image_format:
            disk_formats: raw

This configuration sets Cinder as the default and only storage backend for
Glance, with images stored in the ``raw`` disk format.  The configuration
above will use the Cinder default volume type for image storage.

If you want to use a specific volume type, you can merge the following with
the above configuration:

.. code-block:: yaml

    glance_helm_values:
      conf:
        glance:
          glance_store:
            cinder_volume_type: slow

Vendor-Specific Configurations
==============================

Depending on the vendor you use for your Cinder storage backend, you may need
to make some additional changes to accommodate specific requirements or
capabilities offered by that vendor. Below are the configuration details for
common providers.

StorPool
--------

For deployments utilizing StorPool as the storage backend, additional
configuration settings are necessary to ensure proper integration and
functionality.  You can merge the following with the base Cinder configuration
above:

.. code-block:: yaml

    glance_helm_values:
      pod:
        useHostNetwork:
          api: true
        mounts:
          glance_api:
            volumeMounts:
              - name: etc-storpool-conf
                mountPath: /etc/storpool.conf
                readOnly: true
              - name: etc-storpool-conf-d
                mountPath: /etc/storpool.conf.d
                readOnly: true
            volumes:
              - name: etc-storpool-conf
                hostPath:
                  type: File
                  path: /etc/storpool.conf
              - name: etc-storpool-conf-d
                hostPath:
                  type: Directory
                  path: /etc/storpool.conf.d

These adjustments include network settings and mounting necessary configuration
files into the Glance API pod to interact efficiently with the StorPool backend.
