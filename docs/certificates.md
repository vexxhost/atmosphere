# Certificates

## Using self-signed certificates

If you are in an environment which does not have a trusted certificate authority
and it does not have access to the internet to be able to use LetsEncrypt, you
can use self-signed certificates by adding the following to your inventory:

```yaml
cert_manager_issuer:
  ca:
    secretName: root-secret
```