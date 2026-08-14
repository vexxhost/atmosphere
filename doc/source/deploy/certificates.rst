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

Azure DNS
*********

To configure cert-manager with Azure DNS, create a `Service Principal
<https://cert-manager.io/docs/configuration/acme/dns01/azuredns/#service-principal>`_ and set the following variables:

.. code-block:: yaml

  cluster_issuer_acme_solver: azuredns
  cluster_issuer_acme_azuredns_client_id: <CLIENT_ID>
  cluster_issuer_acme_azuredns_client_secret: <CLIENT_SECRET>
  cluster_issuer_acme_azuredns_subscription_id: <SUBSCRIPTION_ID>
  cluster_issuer_acme_azuredns_tenant_id: <TENANT_ID>
  cluster_issuer_acme_azuredns_resourcegroup_name: <RESOURCEGROUP_NAME>
  cluster_issuer_acme_azuredns_hostedzone_name: <HOSTEDZONE_NAME>

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

If you are using Route53 to host the DNS for your domains, the ``cluster_issuer``
role supports three authentication modes, selected with
``cluster_issuer_acme_route53_auth``.

The supported modes are:

.. list-table::
   :header-rows: 1

   * - Mode
     - Description
     - Uses long-lived AWS keys
   * - ``static``
     - Uses an IAM access key and secret access key.
     - Yes
   * - ``ambient``
     - Uses credentials from the ``cert-manager`` pod environment, such as
       environment variables, an EC2 instance profile, or a mounted AWS
       credentials file.
     - No
   * - ``kubernetes``
     - Uses OIDC-based ``sts:AssumeRoleWithWebIdentity`` with a projected
       ServiceAccount token.
     - No

Static access key (default)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Authenticate with a long-lived IAM user access key and secret access key:

.. code-block:: yaml

  cluster_issuer_acme_email: user@example.com
  cluster_issuer_acme_solver: route53
  cluster_issuer_acme_route53_auth: static
  cluster_issuer_acme_route53_region: <REGION>
  cluster_issuer_acme_route53_hosted_zone_id: <HOSTED_ZONE_ID>
  cluster_issuer_acme_route53_access_key_id: <AWS_ACCESS_KEY_ID>
  cluster_issuer_acme_route53_secret_access_key: <AWS_SECRET_ACCESS_KEY>

.. note::

   You'll need to make sure that your AWS credentials have the correct
   permissions to update the Route53 zone.

Ambient credentials
^^^^^^^^^^^^^^^^^^^

Let ``cert-manager`` pick up credentials from its pod environment (for
example, the EC2 instance metadata service or a credentials file mounted into
the controller pod). No secrets are stored in the cluster.

.. code-block:: yaml

  cluster_issuer_acme_email: user@example.com
  cluster_issuer_acme_solver: route53
  cluster_issuer_acme_route53_auth: ambient
  cluster_issuer_acme_route53_region: <REGION>
  cluster_issuer_acme_route53_hosted_zone_id: <HOSTED_ZONE_ID>
  # Optional: role to assume once ambient credentials are resolved.
  cluster_issuer_acme_route53_role_arn: <IAM_ROLE_ARN>

This mode needs the environment hosting ``cert-manager`` to already expose
AWS credentials through the default AWS SDK credential chain, which
typically means running on AWS infrastructure. If
``cluster_issuer_acme_route53_role_arn`` is set, ``cert-manager`` assumes that
role after resolving the ambient credentials.

Ambient mode can also support IAM Roles Anywhere when the ``cert-manager`` pod
is augmented with the ``aws_signing_helper`` binary and an ``~/.aws/config``
entry that points to it with ``credential_process``. That wiring is outside the
scope of the ``cluster_issuer`` role.

Kubernetes OIDC (keyless)
^^^^^^^^^^^^^^^^^^^^^^^^^

For operators whose policy forbids long-lived AWS keys, ``cert-manager`` can
assume an IAM role using a projected ServiceAccount token. This works with any
Kubernetes cluster, including on-premises, and doesn't require the cluster to
run on AWS.

.. code-block:: yaml

  cluster_issuer_acme_email: user@example.com
  cluster_issuer_acme_solver: route53
  cluster_issuer_acme_route53_auth: kubernetes
  cluster_issuer_acme_route53_region: <REGION>
  cluster_issuer_acme_route53_hosted_zone_id: <HOSTED_ZONE_ID>
  cluster_issuer_acme_route53_role_arn: <IAM_ROLE_ARN>
  # Optional; defaults to "cert-manager-route53".
  cluster_issuer_acme_route53_service_account_name: cert-manager-route53

The role creates a ``ServiceAccount`` in the ``cert-manager`` namespace and
allows the ``cert-manager`` controller to request projected tokens for it. The
solver then references that ServiceAccount, and ``cert-manager`` exchanges the
short-lived token for temporary AWS credentials with
``sts:AssumeRoleWithWebIdentity``.

.. note::

   This configuration requires cert-manager v1.15.0 or newer CRDs. Older
   cert-manager CRDs do not include the Route53
   ``auth.kubernetes.serviceAccountRef`` schema, so upgrade cert-manager before
   applying this solver configuration.

The AWS IAM OIDC provider, trust policy, and Route53 permissions are external
prerequisites. Complete the following one-time setup for each Kubernetes cluster
before applying the Atmosphere configuration.

Publish OIDC discovery documents
""""""""""""""""""""""""""""""""

#. Choose the public issuer URL that AWS IAM will use to verify Kubernetes
   ServiceAccount tokens. The following example publishes the OIDC documents in
   a dedicated S3 bucket:

   .. code-block:: shell

      S3_BUCKET_NAME="my-oidc-bucket"
      AWS_REGION="eu-west-1"
      ISSUER_HOSTPATH="${S3_BUCKET_NAME}.s3.${AWS_REGION}.amazonaws.com"

   You can also use a custom domain or another public HTTPS endpoint. The key
   requirement is that AWS IAM can reach the issuer URL over HTTPS.

#. Create the S3 bucket:

   .. code-block:: shell

      aws s3api create-bucket \
        --bucket "${S3_BUCKET_NAME}" \
        --region "${AWS_REGION}" \
        --create-bucket-configuration "LocationConstraint=${AWS_REGION}"

#. Fetch the OIDC discovery documents from the Kubernetes API server:

   .. code-block:: shell

      kubectl get --raw /openid/v1/jwks > jwks.json
      kubectl get --raw /.well-known/openid-configuration > openid-configuration.json

   If you do not have direct API access from your workstation, use
   ``kubectl proxy`` and fetch the same paths through the local proxy:

   .. code-block:: shell

      kubectl proxy &
      curl http://127.0.0.1:8001/openid/v1/jwks > jwks.json
      curl http://127.0.0.1:8001/.well-known/openid-configuration > openid-configuration.json

#. Rewrite the discovery document so both ``issuer`` and ``jwks_uri`` point to
   the public issuer URL:

   .. code-block:: shell

      jq --arg uri "https://${ISSUER_HOSTPATH}/openid/v1/jwks" \
        '.jwks_uri = $uri' \
        openid-configuration.json > openid-configuration-updated.json

      jq --arg iss "https://${ISSUER_HOSTPATH}" \
        '.issuer = $iss' \
        openid-configuration-updated.json > openid-configuration-final.json

#. Upload the discovery documents:

   .. code-block:: shell

      aws s3 cp jwks.json \
        "s3://${S3_BUCKET_NAME}/openid/v1/jwks" \
        --content-type "application/json"

      aws s3 cp openid-configuration-final.json \
        "s3://${S3_BUCKET_NAME}/.well-known/openid-configuration" \
        --content-type "application/json"

#. Allow unauthenticated reads for only the published OIDC documents. Use a
   dedicated bucket because these objects must be public:

   .. code-block:: shell

      aws s3api put-public-access-block \
        --bucket "${S3_BUCKET_NAME}" \
        --public-access-block-configuration \
          "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

      cat > bucket-policy.json <<EOF
      {
        "Version": "2012-10-17",
        "Statement": [
          {
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": [
              "arn:aws:s3:::${S3_BUCKET_NAME}/.well-known/openid-configuration",
              "arn:aws:s3:::${S3_BUCKET_NAME}/openid/v1/jwks"
            ]
          }
        ]
      }
      EOF

      aws s3api put-bucket-policy \
        --bucket "${S3_BUCKET_NAME}" \
        --policy file://bucket-policy.json

#. Verify that both public endpoints return valid JSON:

   .. code-block:: shell

      curl "https://${ISSUER_HOSTPATH}/.well-known/openid-configuration"
      curl "https://${ISSUER_HOSTPATH}/openid/v1/jwks"

Configure the Kubernetes API server
"""""""""""""""""""""""""""""""""""

The Kubernetes API server must use the public issuer URL so the projected
tokens it mints are verifiable by AWS. On every control plane node, update the
static pod manifest for ``kube-apiserver``.

Replace an existing issuer flag such as:

.. code-block:: yaml

  - --service-account-issuer=https://kubernetes.default.svc.cluster.local

with the issuer configuration:

.. code-block:: yaml

  - --service-account-issuer=https://<ISSUER_HOSTPATH>
  - --service-account-issuer=https://kubernetes.default.svc.cluster.local
  - --service-account-jwks-uri=https://<ISSUER_HOSTPATH>/openid/v1/jwks
  - --api-audiences=https://kubernetes.default.svc.cluster.local,https://<ISSUER_HOSTPATH>,sts.amazonaws.com

Replace ``<ISSUER_HOSTPATH>`` with the host path you published, such as
``my-oidc-bucket.s3.eu-west-1.amazonaws.com``. After you save the manifest, the
kubelet restarts the ``kube-apiserver`` pod automatically.

Verify the token issuer and audience with a temporary pod:

.. code-block:: shell

  kubectl run token-test --image=busybox --restart=Never -- sleep 3600
  kubectl exec token-test -- cat /run/secrets/kubernetes.io/serviceaccount/token

Decode the token with a JWT decoder and verify that ``iss`` is
``https://<ISSUER_HOSTPATH>`` and that ``aud`` includes
``https://kubernetes.default.svc.cluster.local``, ``https://<ISSUER_HOSTPATH>``,
and ``sts.amazonaws.com``.

Remove the temporary pod when you are done:

.. code-block:: shell

  kubectl delete pod token-test

Configure AWS IAM
"""""""""""""""""

#. Register the issuer URL as an OIDC provider in AWS IAM:

   .. code-block:: shell

      THUMBPRINT=$(openssl s_client \
        -connect "${ISSUER_HOSTPATH}:443" \
        -servername "${ISSUER_HOSTPATH}" \
        </dev/null 2>/dev/null | \
        openssl x509 -fingerprint -noout | sed 's/://g' | cut -d= -f2)

      aws iam create-open-id-connect-provider \
        --url "https://${ISSUER_HOSTPATH}" \
        --client-id-list sts.amazonaws.com \
        --thumbprint-list "${THUMBPRINT}"

#. Create an IAM role with a trust policy restricted to the Route53
   ServiceAccount:

   .. code-block:: shell

      ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
      OIDC_PROVIDER="${ISSUER_HOSTPATH}"

      cat > trust-policy.json <<EOF
      {
        "Version": "2012-10-17",
        "Statement": [
          {
            "Effect": "Allow",
            "Principal": {
              "Federated": "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/${OIDC_PROVIDER}"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
              "StringEquals": {
                "${OIDC_PROVIDER}:sub": "system:serviceaccount:cert-manager:cert-manager-route53",
                "${OIDC_PROVIDER}:aud": "sts.amazonaws.com"
              }
            }
          }
        ]
      }
      EOF

      aws iam create-role \
        --role-name cert-manager-route53 \
        --assume-role-policy-document file://trust-policy.json

   If you set ``cluster_issuer_acme_route53_service_account_name`` to a custom
   name, use that name in the trust policy subject instead of
   ``cert-manager-route53``.

#. Attach the Route53 permissions that cert-manager needs for DNS-01
   challenges:

   .. code-block:: shell

      cat > route53-policy.json <<EOF
      {
        "Version": "2012-10-17",
        "Statement": [
          {
            "Effect": "Allow",
            "Action": [
              "route53:GetChange",
              "route53:ChangeResourceRecordSets",
              "route53:ListHostedZonesByName"
            ],
            "Resource": "*"
          }
        ]
      }
      EOF

      aws iam put-role-policy \
        --role-name cert-manager-route53 \
        --policy-name Route53Access \
        --policy-document file://route53-policy.json

Apply the Atmosphere configuration
""""""""""""""""""""""""""""""""""

After the OIDC issuer and IAM role are ready, set the Atmosphere variables and
run the playbook:

.. code-block:: yaml

  cluster_issuer_acme_email: user@example.com
  cluster_issuer_acme_solver: route53
  cluster_issuer_acme_route53_auth: kubernetes
  cluster_issuer_acme_route53_region: <REGION>
  cluster_issuer_acme_route53_hosted_zone_id: <HOSTED_ZONE_ID>
  cluster_issuer_acme_route53_role_arn: arn:aws:iam::123456789012:role/cert-manager-route53

Route53 variables
^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Variable
     - Default
     - Description
   * - ``cluster_issuer_acme_route53_auth``
     - ``static``
     - Authentication mode. Set to ``static``, ``ambient``, or ``kubernetes``.
   * - ``cluster_issuer_acme_route53_region``
     - Not set
     - AWS region for Route53 API calls.
   * - ``cluster_issuer_acme_route53_hosted_zone_id``
     - Not set
     - Route53 hosted zone ID.
   * - ``cluster_issuer_acme_route53_access_key_id``
     - Not set
     - IAM access key ID for ``static`` mode.
   * - ``cluster_issuer_acme_route53_secret_access_key``
     - Not set
     - IAM secret access key for ``static`` mode.
   * - ``cluster_issuer_acme_route53_role_arn``
     - Not set
     - IAM role ARN to assume. This is required for ``kubernetes`` mode and
       optional for ``static`` and ``ambient`` modes.
   * - ``cluster_issuer_acme_route53_service_account_name``
     - ``cert-manager-route53``
     - ServiceAccount name for ``kubernetes`` mode.
   * - ``cluster_issuer_acme_route53_secret_name``
     - ``cert-manager-issuer-route53-credentials``
     - Kubernetes Secret name for static credentials.

Cloudflare
**********

If you are using Cloudflare to host the DNS for your domains, you can use the
following configuration:

.. code-block:: yaml

  cluster_issuer_acme_email: user@example.com
  cluster_issuer_acme_solver: cloudflare
  cluster_issuer_acme_cloudflare_api_token: <CLOUDFLARE_API_TOKEN>

If Cloudflare's account name is different from ACME Issuer's email address
then also set:

.. code-block:: yaml

  cluster_issuer_acme_cloudflare_email: my-cloudflare-acc@example.com

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

.. note::

   GoDaddy DNS API has some limitations. To use it you need:
    - Accounts with 10 or more domains
    - Accounts with a Discount Domain Club subscription

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
  cluster_issuer_venafi_ca: |
    -----BEGIN CERTIFICATE-----
    MIIDBjCCAe4CCQDQ3Z0Z2Z0Z0jANBgkqhkiG9w0BAQsFADCBhTELMAkGA1UEBhMC
    VVMxEzARBgNVBAgTCkNhbGlmb3JuaWExFjAUBgNVBAcTDVNhbiBGcmFuY2lzY28x
    ...
    -----END CERTIFICATE-----
  cluster_issuer_venafi_zone: <ZONE>
  cluster_issuer_venafi_tpp_url: <URL>
  cluster_issuer_venafi_tpp_ca_bundle: |
    -----BEGIN CERTIFICATE-----
    MIIDBjCCAe4CCQDQ3Z0Z2Z0Z0jANBgkqhkiG9w0BAQsFADCBhTELMAkGA1UEBhMC
    VVMxEzARBgNVBAgTCkNhbGlmb3JuaWExFjAUBgNVBAcTDVNhbiBGcmFuY2lzY28x
    ...
    -----END CERTIFICATE-----

.. note::

   If your issuer is an intermediate certificate, you will need to ensure that
   the ``certificate`` key includes the full chain in the correct order of issuer,
   intermediate(s), then root.

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
can use the ``atmosphere_ingress_annotations`` variable in your inventory which will
apply the annotations to all ingresses. ``ingress_global_annotations`` variable is
deprecated.

.. code-block:: yaml

  atmosphere_ingress_annotations:
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
