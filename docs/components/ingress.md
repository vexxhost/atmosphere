# Ingress

The ingress component is the primary entry point for all traffic to the cluster,
it is currently deployed as an instance of `ingress-nginx`.  It is tuned to work
out of the box and should require no changes

!!! warning

   If you make any changes to the ingress configuration, you may see a small
   outage as the ingress controller is restarted.

## Customization

You can customize the deployment of the ingress controller by editing the
`ingress_nginx` section.

!!! warning

    This can result in unsupported behaviour, and is not recommended unless you
    know what you're doing.

### Disabling

If you're looking to disable the ingress component, you can use the following
configuration:

```yaml
atmosphere_config:
  ingress_nginx:
    enabled: false
```

### Overriding chart values

If you're looking to make changes to the Helm chart values used for the deployment
of the Ingress, you can use the following configuration:

```yaml
atmosphere_config:
  ingress_nginx:
    overrides:
      foo: bar
```

This will be merged with the default values for the chart, and will override any
values that Atmosphere includes out of the box.
