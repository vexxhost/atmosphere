#####################
Horizon Configuration
#####################

Horizon, the dashboard service used by OpenStack.

Customize logo Configurations
=============================

Horizon allow customize logos in dashboard. You can replace logo, splash logo and icon with
below values:

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

It's recommanded to use base64 encoded string to parse content as special characters in SVG
file might be wrongly handled by Helm/Go.
