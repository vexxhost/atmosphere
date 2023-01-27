# Ingress

The ingress component is the primary entry point for all traffic to the cluster,
it is currently deployed as an instance of `ingress-nginx`.  It is tuned to work
out of the box and should require no changes

!!! warning

   If you make any changes to the ingress configuration, you may see a small
   outage as the ingress controller is restarted.

### Overriding chart values

If you're looking to make changes to the Helm chart values used for the deployment
of the Ingress, you can define `ingress_nginx_helm_values` ansible variable:

```yaml
ingress_nginx_helm_values:
  foo: bar
```

This will be merged with the default values for the chart.
