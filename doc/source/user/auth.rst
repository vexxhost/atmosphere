##############
Authentication
##############

*******************************************
Using external token from identity provider
*******************************************

Since OpenStack is configured to trust Keycloak as an identity provider, you will
need to generate a token from Keycloak and use it to authenticate with the OpenStack
API.

If you are using Keycloak with an OpenID Connect (OIDC) identity provider, you
may want to exchange a token generated from your identity provider for a token
from Keycloak, which can then be used to authenticate with the OpenStack API.

.. mermaid::
   :align: center
   :config: {"theme": "dark"}

   sequenceDiagram
       participant Client
       participant OIDC Provider
       participant Keycloak
       participant Keystone
       participant OpenStack

       Client->>OIDC Provider: Request Token (Client Credentials)
       OIDC Provider-->>Client: Returns OIDC Token

       Client->>Keycloak: Exchange OIDC Token
       Keycloak-->>Client: Returns Keycloak OIDC Token

       Client->>Keystone: Authenticate with Keycloak Token
       Keystone-->>Client: Returns Keystone Token

       Client->>OpenStack: Use Keystone Token
       OpenStack-->>Client: OpenStack API Access Granted

In order to get started with this process, you'll need an OpenID connect token
issued by an identity provider which exists in the Keycloak realm.

1. **Exchange the OpenID connect (OIDC) Token with Keycloak**

   Use the *OpenID connect token* from your identity provider and exchange it for
   a *Keycloak-issued token*. The following ``curl`` command is provided as an
   example but you can use any tool that can make HTTP requests.

   You will need to replace the following placeholders in the example code:

   - ``<KEYCLOAK_URL>``: The URL of your Keycloak instance.
   - ``<KEYCLOAK_CLIENT_ID>``: The client ID of the Keycloak client.
   - ``<KEYCLOAK_CLIENT_SECRET>``: The client secret of the Keycloak client.

   .. code-block:: sh

      curl -X POST "https://<KEYCLOAK_URL>/realms/atmosphere/protocol/openid-connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=urn:ietf:params:oauth:grant-type:token-exchange" \
        -d "client_id=<KEYCLOAK_CLIENT_ID>" \
        -d "client_secret=<KEYCLOAK_CLIENT_SECRET>" \
        -d "subject_token=<OIDC_TOKEN>" \
        -d "subject_token_type=urn:ietf:params:oauth:token-type:access_token"

   The response will return a token that's issued by Keycloak which you can use
   to authenticate with the OpenStack API.

   .. code-block:: json

      {
        "access_token" : ".....",
        "refresh_token" : ".....",
        "expires_in" : "...."
      }


2. **Authenticate with Keystone Using the Keycloak Token**

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

3. **List projects using the Keystone Token** (optional, if you already know the project ID)

   At this point, you have an unscoped token issued by Keystone which isn't bound
   to any project. You'll need to exchange that token for a project-scoped token
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

4. **Exchange the unscoped token for a project-scoped token**

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
