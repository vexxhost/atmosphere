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

## Default TLS Version and Ciphers

To provide the most secure baseline configuration possible, `ingress-nginx`
defaults to using TLS 1.2 and 1.3 only, with a [secure set of TLS ciphers](https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/configmap/#ssl-ciphers).

### Checking TLS Version and Ciphers

In order to check the TLS version and ciphers used by the ingress controller,
you can use the [sslscan](https://github.com/rbsec/sslscan) tool:

```sh
sslscan dashboard.cloud.example.com
```

### Legacy TLS

The default configuration, though secure, does not support some older browsers
and operating systems.

In order to change this behaviour, you can make to make the following changes
to the `ingress_nginx_helm_values` variable, the following example is using the
[Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/#server=nginx&config=old)
"Old" profile:

```yaml
ingress_nginx_helm_values:
  controller:
    config:
      ssl-protocols: "TLSv1 TLSv1.1 TLSv1.2 TLSv1.3"
      ssl-ciphers: "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:DHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA:ECDHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES256-SHA256:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:DES-CBC3-SHA"
```
