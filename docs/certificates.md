# Certificates

## Using LetsEncrypt DNS challenges

### RFC2136

If you have DNS server that supports RFC2136, you can use it to solve the DNS
challenges, you'll need to have the following information:

- Email address
- Nameserver IP address
- TSIG Algorithm
- TSIG Key Name
- TSIG Key Secret

You'll need to update your Ansible inventory to be the following:

```yaml
cert_manager_issuer:
  acme:
    email: <EMAIL>
    privateKeySecretRef:
      name: letsencrypt-prod
    server: https://acme-v02.api.letsencrypt.org/directory
    solvers:
    - dns01:
        rfc2136:
          nameserver: <NS>:<PORT>
          tsigAlgorithm: <ALGORITHM>
          tsigKeyName: <NAME>
          tsigSecretSecretRef:
            key: tsig-secret-key
            name: tsig-secret
```

After you're done, you'll need to add a new secret to the Kubernetes cluster,
you will need to do it by using the following YAML file:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tsig-secret
  namespace: openstack
type: Opaque
stringData:
  tsig-secret-key: <KEY>
```

## Using self-signed certificates

If you are in an environment which does not have a trusted certificate authority
and it does not have access to the internet to be able to use LetsEncrypt, you
can use self-signed certificates by adding the following to your inventory:

```yaml
cert_manager_issuer:
  ca:
    secretName: root-secret
```

## Using pre-existing CA

If you have your own CA and want to use it, you will need to update your Ansible inventory to be the following:

```yaml
cert_manager_issuer:
  ca:
    secretName: custom-openstack-ca-key-pair
```

After you're done, you'll need to add a new secret to the Kubernetes cluster,
you will need to do it by using the following YAML file:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: custom-openstack-ca-key-pair
  namespace: openstack
type: Opaque
stringData:
  tls.crt: |
    CA_CERTIFICATE_HERE
  tls.key: |
    CA_PRIVATE_KEY_HERE
```
NOTE: If your issuer represents an intermediate, ensure that tls.crt contains the issuer's full chain in the correct order: issuer -> intermediate(s) -> root.