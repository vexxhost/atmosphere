============
Certificates
============

Atmosphere simplifies all the management of your SSL certificates for all of
your API endpoints by automatically issuing and renewing certificates for you
using `cert-manager <https://cert-manager.io>`_.

Types
=====

There are two different ways of issuing certificates.  It can either issue
individual certificates for each API endpoint or it can issue a wildcard
certificate for all of your API endpoints.

Individual Certificates
-----------------------

If you want to issue individual certificates for each API endpoint, you do not
need to do anything.  This is the default behavior of Atmosphere.

Wildcard Certificate
--------------------

If you decide to use wildcard certificates, you can either let the certificate
manager issue and renew the certificate for you or you can use an existing
wildcard certificate.

Automatically Issued
~~~~~~~~~~~~~~~~~~~~

If you want to issue a wildcard certificate for all of your API endpoints using
the certificate manager, you can configure it by setting the the following variable
in your inventory:

.. code-block:: yaml

  openstack_helm_ingress_wildcard_domain: cloud.atmosphere.dev

This will issue a wildcard certificate for ``*.cloud.atmosphere.dev`` and all
subdomains.  The certificate manager will automatically renew the certificate
before it expires.

Existing Certificate
~~~~~~~~~~~~~~~~~~~~

If you want to use an existing wildcard certificate without relying on the
certificate manager issuing and renewing the certificate, you can use the
following steps:

1. Create a Kubernetes TLS secret using your wildcard certificate, you can refer
   to the `Kubernetes documentation <https://kubernetes.io/docs/concepts/configuration/secret/#tls-secrets>`_
   for more details.

   .. code-block:: shell

     kubectl -n openstack create secret tls wildcard-certs --key=/path/to/tls.key --cert=/path/to/tls.crt

   .. note::

      If you have a certificate that needs to be combined with an intermediate
      certificate, you can combine them all to a single file with the certificate
      first, followed by the intermediate certificate, followed by the root.

2. Update the ``openstack_helm_ingress_secret_name`` to point towards the name
   of the secret you created in step 1.

   .. code-block:: yaml

     openstack_helm_ingress_secret_name: wildcard-certs

3. Set ``cluster_issuer_type`` to ``none``, this is required for other roles
   like for example Horizon.

   .. code-block:: yaml

     cluster_issuer_type: none

.. warning::

   If you decide to use an existing wildcard certificate, you will need to
   manually renew the certificate before it expires.

Issuers
=======

In order to be able to automatically issue certificates, you need to configure
an issuer.  There are three different types of issuers that you can use with
Atmosphere.

.. note::

   If you decide to change the certificate issuer after deployment, you will
   need to delete the existing certificate secret in order for the new issuer
   to be able to issue a new certificate.

ACME
----

Atmosphere uses the `ACME <https://tools.ietf.org/html/rfc8555>`_ protocol by
default to request certificates from `LetsEncrypt <https://letsencrypt.org>`_.

There are two different challenge types that can be used to verify ownership of
the domain to issue the certificate using ACME.  Regardless of the challenge
type, you will need to configure an email address to be used for the ACME
account.

.. code-block:: yaml

  cluster_issuer_type: acme
  cluster_issuer_acme_email: user@example.com

If you're running your own internal ACME server, you can configure Atmosphere to
point towards it by setting the ``cluster_issuer_acme_server`` variable.

.. code-block:: yaml

  cluster_issuer_acme_server: https://acme.example.com
  cluster_issuer_acme_email: user@example.com

If the ACME server is using certificates signed by a custom CA, you can add the
following configuration to allow Atmosphere to trust the CA.

.. code-block:: yaml

  cluster_issuer_acme_private_ca: true

HTTP-01 Challenge
~~~~~~~~~~~~~~~~~

This is configured to work out of the box if your APIs are publicly accessible
since it uses an HTTP-01 challenge to verify ownership of the domain.  You just
need to configure an email address.

DNS-01 Challenge
~~~~~~~~~~~~~~~~

Atmosphere uses the ``HTTP-01`` solver by default, which means that as long as
your ACME server can reach your API, you don't need to do anything else.

If your ACME server cannot reach your API, you will need to use the ``DNS-01``
challenges which require you to configure your DNS provider.

RFC2136
*******

If you have a DNS server that supports RFC2136, you can use it to solve the DNS
challenges with the following configuration:

.. code-block:: yaml

  cluster_issuer_acme_email: user@example.com
  cluster_issuer_acme_solver: rfc2136
  cluster_issuer_acme_rfc2136_nameserver: <NAMESERVER>:<PORT>
  cluster_issuer_acme_rfc2136_tsig_algorithm: <ALGORITHM>
  cluster_issuer_acme_rfc2136_tsig_key_name: <KEY_NAME>
  cluster_issuer_acme_rfc2136_tsig_secret_key: <SECRET_KEY>

Route53
*******

If you are using Route53 to host the DNS for your domains, you can use the
following configuration:

.. code-block:: yaml

  cluster_issuer_acme_email: user@example.com
  cluster_issuer_acme_solver: route53
  cluster_issuer_acme_route53_region: <REGION>
  cluster_issuer_acme_route53_hosted_zone_id: <HOSTED_ZONE_ID>
  cluster_issuer_acme_route53_access_key_id: <AWS_ACCESS_KEY_ID>
  cluster_issuer_acme_route53_secret_access_key: <AWS_SECRET_ACCESS_KEY>

.. note::

   You'll need to make sure that your AWS credentials have the correct
   permissions to update the Route53 zone.

GoDaddy
*******

If you're using GoDaddy for the DNS of your domain, you can use the following
configuration which depends on
`cert-manager-webhook-godaddy <https://github.com/snowdrop/godaddy-webhook>`_.

.. code-block:: yaml

  cluster_issuer_acme_email: user@example.com
  cluster_issuer_acme_solver: godaddy
  cluster_issuer_acme_godaddy_api_key: <GODADDY_API_KEY>
  cluster_issuer_acme_godaddy_secret_key: <GODADDY_SECRET_KEY>

Infoblox
********

If you're using Infoblox for the DNS of your domain, you can use the following
configuration which depends on
`cert-manager-webhook-infoblox-wapi <https://github.com/luisico/cert-manager-webhook-infoblox-wapi>`_.

.. code-block:: yaml

  cluster_issuer_acme_email: user@example.com
  cluster_issuer_acme_solver: infoblox
  cluster_issuer_acme_infoblox_view: <VIEW>
  cluster_issuer_acme_infoblox_host: <HOST>
  cluster_issuer_acme_infoblox_username: <USERNAME>
  cluster_issuer_acme_infoblox_password: <PASSWORD>

Venafi
------

Venafi is a commercial certificate authority which can be used with Atmosphere
to issue certificates.  Regardless of the way that you authenticate to Venafi,
you will need to configure the issuer.

.. code-block:: yaml

  cluster_issuer_type: venafi
  cluster_issuer_venafi_zone: <ZONE>
  cluster_issuer_venafi_tpp_url: <URL>
  cluster_issuer_venafi_tpp_ca_bundle: |
    -----BEGIN CERTIFICATE-----
    MIIDBjCCAe4CCQDQ3Z0Z2Z0Z0jANBgkqhkiG9w0BAQsFADCBhTELMAkGA1UEBhMC
    VVMxEzARBgNVBAgTCkNhbGlmb3JuaWExFjAUBgNVBAcTDVNhbiBGcmFuY2lzY28x
    ...
    -----END CERTIFICATE-----

Authentication
~~~~~~~~~~~~~~

There are two different ways to authenticate to Venafi to issue certificates,
either using a username and password or using an access token.  The username and
password method is phased out in newer versions of Venafi, so it is recommended
to use the access token method.

Username and Password
*********************

If you are using a username and password to authenticate to Venafi, you can
configure it with the following variables:

.. code-block:: yaml

  cluster_issuer_venafi_username: <USERNAME>
  cluster_issuer_venafi_password: <PASSWORD>

Access Token
************

If you are using an access token to authenticate to Venafi, you can configure it
with the following variable:

.. code-block:: yaml

  cluster_issuer_venafi_access_token: <ACCESS_TOKEN>

Certificate fields
~~~~~~~~~~~~~~~~~~

If your Venafi zone is strict about the fields that are required or their
values, you can use the `cert-manager supported annotations <https://cert-manager.io/docs/usage/ingress/#supported-annotations>`_
to configure the certificate values.

In order to apply these annotations to all ingresses managed by Atmosphere, you
can use the ``ingress_global_annotations`` variable in your inventory which will
apply the annotations to all ingresses.

.. code-block:: yaml

  ingress_global_annotations:
    cert-manager.io/subject-organizations: VEXXHOST, Inc.
    cert-manager.io/subject-organizationalunits: Cloud Infrastructure
    cert-manager.io/subject-localities: Montreal
    cert-manager.io/subject-provinces: Quebec
    cert-manager.io/subject-countries: CA

Using Pre-existing CA
---------------------

If you have an existing CA that you'd like to use with Atmosphere, you can
configure it by including the certificate and private key:

.. code-block:: yaml

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

.. note::

   If your issuer is an intermediate certificate, you will need to ensure that
   the ``certificate`` key includes the full chain in the correct order of issuer,
   intermediate(s), then root.

Self-signed Certificates
------------------------

If you are in an environment which does not have a trusted certificate authority
and it does not have access to the internet to be able to use LetsEncrypt, you
can use self-signed certificates by adding the following to your inventory:

.. code-block:: yaml

  cluster_issuer_type: self-signed

.. warning::

   Self-signed certificates are not recommended for production environments.
   They are only recommended for development and testing environments.
