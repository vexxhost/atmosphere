# `cluster_issuer`

Atmosphere simplifies all the management of your SSL certificates for all of
your API endpoints by automatically issuing and renewing certificates for you.

## ACME

Atmosphere uses the [ACME](https://tools.ietf.org/html/rfc8555) protocol by
default to request certificates from [LetsEncrypt](https://letsencrypt.org/).

This is configured to work out of the box if your APIs are publicly accessible,
you just need to configure an email address.

```yaml
cluster_issuer_acme_email: user@example.com
```

If you're running your own internal ACME server, you can configure Atmosphere to
point towards it by setting the `cluster_issuer_acme_server` variable.

```yaml
cluster_issuer_acme_server: https://acme.example.com
cluster_issuer_acme_email: user@example.com
```

### DNS-01 challenges

Atmosphere uses the `HTTP-01` solver by default, which means that as long as
your ACME server can reach your API, you don't need to do anything else.

If your ACME server cannot reach your API, you will need to use the DNS-01
challenges which require you to configure your DNS provider.

#### RFC2136

If you have DNS server that supports RFC2136, you can use it to solve the DNS
challenges, you can use the following configuration:

```yaml
cluster_issuer_acme_email: user@example.com
cluster_issuer_acme_solver: rfc2136
cluster_issuer_acme_rfc2136_nameserver: <NAMESERVER>:<PORT>
cluster_issuer_acme_rfc2136_tsig_algorithm: <ALGORITHM>
cluster_issuer_acme_rfc2136_tsig_key_name: <KEY_NAME>
cluster_issuer_acme_rfc2136_tsig_secret_key: <SECRET_KEY>
```

#### Route53

If you are using Route53 to host the DNS for your domains, you can use the
following configuration:

```yaml
cluster_issuer_acme_email: user@example.com
cluster_issuer_acme_solver: route53
cluster_issuer_acme_route53_region: <REGION>
cluster_issuer_acme_route53_hosted_zone_id: <HOSTED_ZONE_ID>
cluster_issuer_acme_route53_access_key_id: <AWS_ACCESS_KEY_ID>
cluster_issuer_acme_route53_secret_access_key: <AWS_SECRET_ACCESS_KEY>
```

!!! note

   You'll need to make sure that your AWS credentials have the correct
   permissions to update the Route53 zone.

#### Godaddy

If you're using Godaddy for the DNS of your domain, you can use the following
configuration which depends on
`cert-manager-webhook-godaddy`[https://github.com/snowdrop/godaddy-webhook].

```yaml
cluster_issuer_acme_email: user@example.com
cluster_issuer_acme_solver: godaddy
cluster_issuer_acme_godaddy_api_key: <GODADDY_API_KEY>
cluster_issuer_acme_godaddy_secret_key: <GODADDY_SECRET_KEY>
```

#### Infoblox

If you're using Infoblox for the DNS of your domain, you can use the following
configuration which depends on
`cert-manager-webhook-infoblox-wapi`[https://github.com/luisico/cert-manager-webhook-infoblox-wapi].

```yaml
cluster_issuer_acme_email: user@example.com
cluster_issuer_acme_solver: infoblox
cluster_issuer_acme_infoblox_view: <VIEW>
cluster_issuer_acme_infoblox_host: <HOST>
cluster_issuer_acme_infoblox_username: <USERNAME>
cluster_issuer_acme_infoblox_password: <PASSWORD>
```

## Using pre-existing CA

If you have an existing CA that you'd like to use with Atmosphere, you can
simply configure it by including the certificate and private key:

```yaml
cluster_issuer_type: ca
cluster_issuer_ca_certificate: |
  -----BEGIN CERTIFICATE-----
  MIIDBjCCAe4CCQDQ3Z0Z2Z0Z0jANBgkqhkiG9w0BAQsFADCBhTELMAkGA1UEBhMC
  VVMxEzARBgNVBAgTCkNhbGlmb3JuaWExFjAUBgNVBAcTDVNhbiBGcmFuY2lzY28x
  ...
  -----END CERTIFICATE-----
cluster_issuer_ca_private_key: |
  -----BEGIN RSA PRIVATE KEY-----
  MIIEpAIBAAKCAQEAw3Z0Z2Z0Z0jANBgkqhkiG9w0BAQsFADCBhTELMAkGA1UEBhMC
  VVMxEzARBgNVBAgTCkNhbGlmb3JuaWExFjAUBgNVBAcTDVNhbiBGcmFuY2lzY28x
  ...
  -----END RSA PRIVATE KEY-----
```

!!! note

   If your issuer is an intermediate certificate, you will need to ensure that
   they `certificate` key includes the full chain in the correct order of issuer,
   intermediate(s) then root.

## Self-signed certificates

If you are in an environment which does not have a trusted certificate authority
and it does not have access to the internet to be able to use LetsEncrypt, you
can use self-signed certificates by adding the following to your inventory:

```yaml
cluster_issuer_type: self-signed
```

!!! warning

   Self-signed certificates are not recommended for production environments,
   they are only recommended for development and testing environments.
