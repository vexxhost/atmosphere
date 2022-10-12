# Certificates

Atmosphere simplifies all the management of your SSL certificates for all of
your API endpoints by automatically issuing and renewing certificates for you.

## ACME

Atmosphere uses the [ACME](https://tools.ietf.org/html/rfc8555) protocol by
default to request certificates from [LetsEncrypt](https://letsencrypt.org/).

This is configured to work out of the box if your APIs are publicly accessible,
you just need to configure an email address.

```yaml
atmosphere_issuer_config:
  email: foo@bar.com
```

If you're running your own internal ACME server, you can configure Atmosphere to
point towards it by setting the `server` field.

```yaml
atmosphere_issuer_config:
  email: foo@bar.com
  server: https://acme.example.com
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
atmosphere_issuer_config:
  email: foo@bar.com
  solver:
    type: rfc2136
    nameserver: <NAMESERVER>:<PORT>
    tsig_algorithm: <ALGORITHM>
    tsig_key_name: <NAME>
    tsig_secret: <SECRET>
```

#### Route53

If you are using Route53 to host the DNS for your domains, you can use the
following configuration:

```yaml
atmosphere_issuer_config:
  email: foo@bar.com
  solver:
    type: route53
    hosted_zone_id: <HOSTED_ZONE_ID>
    access_key_id: <AWS_ACCESS_KEY_ID>
    secret_access_key: <AWS_SECRET_ACCESS_KEY>
```

!!! note

    You'll need to make sure that your AWS credentials have the correct
    permissions to update the Route53 zone.

## Using pre-existing CA

If you have an existing CA that you'd like to use with Atmosphere, you can
simply configure it by including the certificate and private key:

```yaml
atmosphere_issuer_config:
  type: ca
  certificate: |
    -----BEGIN CERTIFICATE-----
    MIIDBjCCAe4CCQDQ3Z0Z2Z0Z0jANBgkqhkiG9w0BAQsFADCBhTELMAkGA1UEBhMC
    VVMxEzARBgNVBAgTCkNhbGlmb3JuaWExFjAUBgNVBAcTDVNhbiBGcmFuY2lzY28x
    ...
    -----END CERTIFICATE-----
  private_key: |
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
atmosphere_issuer_config:
  type: self-signed
```

!!! warning

    Self-signed certificates are not recommended for production environments,
    they are only recommended for development and testing environments.
