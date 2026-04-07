#######
Horizon
#######

The Horizon component serves as the web-based user interface for OpenStack,
allowing users to interact with the cloud infrastructure.

By default, Horizon is configured to work out of the box with minimal changes
needed.  However, it can be extensively customized to fit the branding and
requirements of your organization.

.. admonition:: Deploying Horizon

    If you make any changes to Horizon only and you want to deploy the Horizon
    changes only, you can run the following command:

    .. code-block:: bash

        ansible-playbook vexxhost.atmosphere.openstack -t horizon

********
Branding
********

To customize the logos used in the Horizon dashboard, you need to update the
Horizon Helm values with your custom logo files. Follow the steps below:

.. code-block:: yaml

    horizon_helm_values:
      conf:
        horizon:
          branding:
            logo: "{{ lookup('file', inventory_dir ~ '/files/logo.svg') | b64encode }}"
            logo_splash: "{{ lookup('file', inventory_dir ~ '/files/logo-splash.svg') | b64encode }}"
            favicon: "{{ lookup('file', inventory_dir ~ '/files/favicon.svg') | b64encode }}"
      manifests:
        configmap_logo: true

It's recommended that you use ``base64`` encoded string for the values since the
content of the files might contain special characters that could be wrongly
handled by Helm, such as SVG files.
