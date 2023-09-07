# `openstack_helm_ingress`

## Using wildcard certificates

If you have an existing wildcard certificate to use for all your endpoints
with Atmosphere, you can simply configure it as follows;

1. Create a Kubernetes TLS secret using your wildcard certificate, you can refer
   to the [Kubernetes documentation](https://kubernetes.io/docs/concepts/configuration/secret/#tls-secrets)
   for more details.

   ```shell
   kubectl -n openstack create secret tls wildcard-certs --key=/path/to/tls.key --cert=/path/to/tls.crt
   ```

   > **Note**
   >
   > If you have a certificate that needs to be combined with an intermediate
   > certificate, you can combine them all to a single file with the certificate
   > first, followed by the intermediate certificate, followed by the root.

2. Update the `openstack_helm_ingress_secret_name` to point towards the name
   of the secret you created in step 1.

   ```yaml
   openstack_helm_ingress_secret_name: wildcard-certs
   cluster_issuer_type: none

   ```

> **Note**
>
> If you make this change after a deployment, you will need to re-run all of the
> playbooks in order to update all the `Ingress` resources.
