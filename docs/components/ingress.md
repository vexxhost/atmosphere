# Ingress

The ingress component is the primary entry point for all traffic to the cluster,
it is currently deployed as an instance of `ingress-nginx`.  It is tuned to work
out of the box and should require no changes

!!! warning

   If you make any changes to the ingress configuration, you may see a small
   outage as the ingress controller is restarted.

## Customization

You can customize `ingress-nginx`controller deployment by making changes to the
Helm chart values used for the deployment.
Define `ingress_nginx_helm_values` ansible variable to override values:

```yaml
ingress_nginx_helm_values:
  foo: bar
```

This will be merged with the default values for the chart.
