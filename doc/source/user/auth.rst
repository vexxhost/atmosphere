##############
Authentication
##############

*******************************************
Using external token from identity provider
*******************************************

OpenStack trusts Keycloak as its identity provider, so the OpenStack API only
accepts tokens issued by Keycloak. If a workload or a user already has a token
from another OpenID Connect (OIDC) identity provider, Keycloak can accept that
token and issue its own token in return, which then authenticates with the
OpenStack API.

Keycloak supports two ways to do this, depending on who the token represents:

- **Federated client authentication** is for workloads, such as services, CI
  pipelines or Kubernetes service accounts, that get tokens from their own
  identity provider with the client credentials grant. Keycloak authenticates
  the workload as a Keycloak client without a client secret, and issues a token
  for that client's service account.
- **JWT authorization grant** is for users who already have an account in the
  Keycloak realm that is linked to the external identity provider, for example
  because they signed in through it before.

.. mermaid::
   :align: center
   :config: {"theme": "dark"}

   sequenceDiagram
       participant Client
       participant OIDC Provider
       participant Keycloak
       participant Keystone
       participant OpenStack

       Client->>OIDC Provider: Request token
       OIDC Provider-->>Client: Returns OIDC token

       Client->>Keycloak: Send OIDC token as an assertion
       Keycloak-->>Client: Returns Keycloak token

       Client->>Keystone: Authenticate with Keycloak token
       Keystone-->>Client: Returns Keystone token

       Client->>OpenStack: Use Keystone token
       OpenStack-->>Client: OpenStack API access granted

The examples below use the following placeholders:

- ``<KEYCLOAK_URL>``: The URL of your Keycloak instance.
- ``<KEYCLOAK_REALM>``: The Keycloak realm for your Keystone domain, which is
  ``atmosphere`` by default.
- ``<OIDC_TOKEN>``: The token issued by your identity provider.

Configure the identity provider
===============================

Both methods need the external identity provider registered in the Keycloak
realm, so that Keycloak can validate its tokens.

1. In the Keycloak admin console, open the realm and go to **Identity
   providers**, then add an **OpenID Connect v1.0** provider.

2. Set **Issuer** to the ``iss`` claim of the tokens issued by the provider,
   enable **Use JWKS URL** and set **JWKS URL** to the provider's signing keys
   endpoint.

3. Make sure the provider issues tokens with a single ``aud`` claim set to
   ``https://<KEYCLOAK_URL>/realms/<KEYCLOAK_REALM>``. If the provider can't do
   that, enable **Allows Client ID as audience for assertions** in the advanced
   settings and set **Client ID** to the audience that the provider issues.

4. Enable the option for the method that you use:

   - For federated client authentication, enable **Supports client
     assertions**. Keycloak accepts each token only once by default. If the
     workload can't get a new token for every request, also enable **Allows
     client assertions to be re-used**.
   - For the JWT authorization grant, enable **JWT Authorization Grant** in the
     **Authorization Grant Settings** section. Keycloak rejects tokens that are
     valid for longer than **Max allowed assertion expiration**, which is 5
     minutes by default.

Federated client authentication
===============================

1. **Create a client for the workload**

   In **Clients**, create an OpenID Connect client with **Client
   authentication** and **Service account roles** enabled. In the
   **Credentials** tab, set **Client Authenticator** to **Signed JWT -
   Federated**, set **Identity provider** to the alias of the provider that you
   configured, and set **Federated subject** to the ``sub`` claim of the
   workload's tokens.

   Realms created before Keycloak 26.6 don't include this authenticator in the
   client authentication flow. In **Authentication**, duplicate the **clients**
   flow, add the **Signed JWT - Federated** step as **Alternative**, and bind
   the copy as the **Client authentication flow**.

2. **Get a token from Keycloak**

   Send the token from your identity provider as the client assertion. Keycloak
   finds the client from the token, so no client ID or secret is needed.

   .. code-block:: sh

      curl -X POST "https://<KEYCLOAK_URL>/realms/<KEYCLOAK_REALM>/protocol/openid-connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=client_credentials" \
        -d "client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer" \
        -d "client_assertion=<OIDC_TOKEN>"

   The response contains a token for the client's service account, which
   Keycloak names ``service-account-<CLIENT_ID>``. Assign OpenStack roles to
   that user before you use the token with Keystone.

   .. code-block:: json

      {
        "access_token" : ".....",
        "expires_in" : "...."
      }

JWT authorization grant
=======================

1. **Create a client and link the users**

   In **Clients**, create an OpenID Connect client with **Client
   authentication** enabled. In the **Capability config** section, enable
   **JWT Authorization Grant**, then select the provider that you configured in
   **Allowed Identity Providers for JWT Authorization Grant**.

   Keycloak looks up the user from the ``sub`` claim of the token, so each user
   must already be linked to the provider. Keycloak links a user automatically
   when they sign in through the provider, and you can check the link in the
   user's **Identity provider links** tab.

2. **Get a token from Keycloak**

   Replace ``<KEYCLOAK_CLIENT_ID>`` and ``<KEYCLOAK_CLIENT_SECRET>`` with the
   credentials of the client that you created.

   .. code-block:: sh

      curl -X POST "https://<KEYCLOAK_URL>/realms/<KEYCLOAK_REALM>/protocol/openid-connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer" \
        -d "client_id=<KEYCLOAK_CLIENT_ID>" \
        -d "client_secret=<KEYCLOAK_CLIENT_SECRET>" \
        -d "assertion=<OIDC_TOKEN>"

   The response contains an access token for the linked user. This grant never
   returns a refresh token, so request a new token when it expires.

   .. code-block:: json

      {
        "access_token" : ".....",
        "expires_in" : "...."
      }

Use the Keycloak token with OpenStack
=====================================

1. **Authenticate with Keystone Using the Keycloak Token**

   With the token issued by Keycloak, you can now authenticate with Keystone in order
   to obtain a fernet token which can be used to talk to all of the OpenStack APIs.

   You will need to replace the following placeholders in the example code:

   - ``<OPENSTACK_AUTH_URL>``: The URL of your Keystone authentication endpoint.
   - ``<KEYCLOAK_OIDC_TOKEN>``: The token issued by Keycloak.

   .. code-block:: sh

      curl "<OPENSTACK_AUTH_URL>/v3/OS-FEDERATION/identity_providers/atmosphere/protocols/openid/auth" \
        -H "Authorization: Bearer <KEYCLOAK_OIDC_TOKEN>"

   This response will return an unscoped Keystone token (not tied to any project) which
   will be in the ``X-Subject-Token`` header.

   .. code-block:: http

      HTTP/1.1 201 Created
      X-Subject-Token: <UNSCOPED_KEYSTONE_TOKEN>

2. **List projects using the Keystone Token** (optional, if you already know the project ID)

   At this point, you have an unscoped token issued by Keystone which is not bound
   to any project.  You will need to exchange that token for a project-scoped token
   in order to be able to interact with the OpenStack APIs.

   You can choose to list what projects you have access to using the Keystone token
   that you have obtained.

   You will need to replace the following placeholders in the example code:

   - ``<OPENSTACK_AUTH_URL>``: The URL of your Keystone authentication endpoint.
   - ``<UNSCOPED_KEYSTONE_TOKEN>``: The token issued by Keystone.

   .. code-block:: sh

      curl "<OPENSTACK_AUTH_URL>/v3/projects" \
        -H "X-Auth-Token: <UNSCOPED_KEYSTONE_TOKEN>"

   This response will return a list of projects that you have access to.

   .. code-block:: json

      {
        "projects": [
          {
            "id": "....",
            "name": "....",
            "description": "...."
          }
        ]
      }

3. **Exchange the unscoped token for a project-scoped token**

   Once you have identified the project that you want to interact with, you can
   exchange the unscoped token for a project-scoped token.

   You will need to replace the following placeholders in the example code:

   - ``<OPENSTACK_AUTH_URL>``: The URL of your Keystone authentication endpoint.
   - ``<UNSCOPED_KEYSTONE_TOKEN>``: The token issued by Keystone.
   - ``<PROJECT_ID>``: The ID of the project that you want to interact with.

   .. code-block:: sh

      curl "<OPENSTACK_AUTH_URL>/v3/auth/projects" \
        -H "Content-Type: application/json" \
        -H "X-Auth-Token: <UNSCOPED_KEYSTONE_TOKEN>" \
        -d '{
          "auth": {
            "identity": {
              "methods": ["token"],
              "token": {
                "id": "<UNSCOPED_KEYSTONE_TOKEN>"
              }
            },
            "scope": {
              "project": {
                "id": "<PROJECT_ID>"
              }
            }
          }
        }'

   This response will return a project-scoped token which you can use to interact
   with the OpenStack APIs which will be in the ``X-Subject-Token`` header.

   .. code-block:: http

      HTTP/1.1 201 Created
      X-Subject-Token: <SCOPED_KEYSTONE_TOKEN>

   OpenStack Keystone will provide the token details in the response body, including
   the full catalog of services that you have access to.

   .. code-block:: json

      {
        "token": {
          "methods": [
            "token"
          ],
          "expires_at": "....",
          "issued_at": "....",
          "user": {
            "domain": {
              "id": "....",
              "name": "...."
            },
            "id": "....",
            "name": "...."
          },
          "audit_ids": [
            "...."
          ],
          "catalog": [
            {
              "endpoints": [
                {
                  "id": "....",
                  "interface": "....",
                  "region": "....",
                  "url": "...."
                }
              ],
              "id": "....",
              "name": "....",
              "type": "...."
            }
          ],
          "project": {
            "domain": {
              "id": "....",
              "name": "...."
            },
            "id": "....",
            "name": "...."
          }
        }
      }

   You can then use the project-scoped token to interact with the OpenStack APIs,
   such as creating a server, listing servers, etc.
