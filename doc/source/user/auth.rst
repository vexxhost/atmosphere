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

In order to get started with this process, you'll need a OpenID connect token
issued by an identity provider which exists in the Keycloak realm.

1. **Exchange the OpenID connect (OIDC) Token with Keycloak**

   Use the *OpenID connect token* from your identity provider and exchange it for
   a *Keycloak-issued token*.  The following ``curl`` command is provided as an
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

   The response will return a token that is issued by Keycloak which you can use
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


***********************************************
OpenStack CLI with OIDC identity provider users
***********************************************

Since OpenStack is configured to trust Keycloak as an identity provider, you will
need to generate a token from Keycloak and use it to authenticate with the OpenStack
API.

AUTH TYPE v3oidcpassword
========================

If you have users managed by Keycloak, then you can use the username and password of
the user to intract with OpenStack API using *v3oidcpassword* AUTH TYPE which is
supported by Keystone.

.. admonition:: User and project role setup
    :class: info

    You need keycloak admin credentials to create user and set password in atmosphere realm
    using the keycloak web UI, then assign member or admin role to the user in the scope of
    a project in atmosphere domain using OpenStack CLI.

After adding roles to the user in the domain integrated with identity provider, the user can
login to OpenStack dashboard with Horizon redirect you to keycloak to login. If you want to
use the user credentials with OpenStack CLI, then set your openrc-oidcpassword.rc like below.
Use it wih the OpenStack CLI, which will auth with keycloak to get the Keycloak access token
and authenticate with OpenStack keystone to get the project-scoped token.

.. code-block:: sh

   export OS_AUTH_URL="https://identity.thedomain.com/v3"
   export OS_PROJECT_NAME="user-project"
   export OS_PROJECT_DOMAIN_NAME="atmosphere"
   export OS_USERNAME="username"
   export OS_PASSWORD="the-password-of-user-in-keycloak"
   export OS_INTERFACE=public
   export OS_IDENTITY_API_VERSION=3
   export OS_AUTH_TYPE=v3oidcpassword
   export OS_CLIENT_ID=keystone
   export OS_CLIENT_SECRET="anystringhere"
   export OS_IDENTITY_PROVIDER=atmosphere
   export OS_PROTOCOL=openid
   export OS_DISCOVERY_ENDPOINT=https://keycloak.thedomain.com/realms/atmosphere/.well-known/openid-configuration

.. list-table::
   :widths: 40 90
   :header-rows: 1

   * - Environment variable
     - Description
   * - OS_AUTH_URL
     - The URL of the OpenStack Identity service.
   * - OS_PROJECT_NAME
     - The name of the project user belongs to.
   * - OS_PROJECT_DOMAIN_NAME
     - The domain name of the project.
   * - OS_USERNAME
     - The username of the user in Keycloak.
   * - OS_PASSWORD
     - The password of the user in Keycloak.
   * - OS_INTERFACE
     - The API endpoint interface to use for the OpenStack CLI.
   * - OS_IDENTITY_API_VERSION
     - The version of the Identity API to use.
   * - OS_AUTH_TYPE
     - The authentication type to use by OpenStack client.
   * - OS_CLIENT_ID
     - The client ID of the OpenStack keystone client in keycloak.
   * - OS_CLIENT_SECRET
     - Required by OpenStack client, can be any string for this auth type.
   * - OS_IDENTITY_PROVIDER
     - The name of the corresponding identity provider object as created in the Keystone API.
   * - OS_PROTOCOL
     - The protocol to use for the authentication with keycloak.
   * - OS_DISCOVERY_ENDPOINT
     - Identity provider keycloak API endpoints

The above configuration work with the default installation of Atmosphere which creates an
domain *atmosphere* and integrate it with the keycloak server through OIDC protocol. If you
use a different domain name, then replace the domain name and identity provider in the above
configuration.


AUTH TYPE v3oidcdeviceauthz
===========================


If you are using Keycloak with an external OpenID Connect (OIDC) identity provider,
like Microsoft Azure, Google, or Okta, then all authentication requests will be
redirected to the external identity provider for authentication. In this case, you
can't use the user credentials to authenticate with OpenStack API. Instead, you can
use the *v3oidcdeviceauthz* AUTH TYPE which is supported by Keystone.

In this scenario, you will need to use the OpenID Connect token issued by the external
identity provider to exchange for a device code url which can be used to authenticate
with a web browser, after the user authenticate with the external identity provider
and authorize the device code using the browser,the user will get a keystone unscoped
token to authenticate with OpenStack, then the user can exchange the unscoped token
for a project-scoped token to interact with OpenStack API using the OpenStack CLI.
This is very useful when you want to use the OpenStack CLI with an external identity
provider for some specific operations.

.. mermaid::
   :align: center
   :config: {"theme": "forest"}

   sequenceDiagram
       participant Client
       participant OIDC Provider
       participant Keycloak
       participant Browser
       participant Keystone
       participant OpenStack


       Client->>Keycloak: OAUTH device auth code request
       Keycloak-->>Client: Returns device code URL

       Client->>Browser: Authenticate with external OIDC provider
       Keycloak->>Client: Returns Keycloak access_token

       Client->>Keystone: Authenticate with Keycloak Token
       Keystone-->>Client: Returns Keystone Token

       Client->>OpenStack: Use Keystone Token
       OpenStack-->>Client: OpenStack API Access Granted

You can use the following script to get the OpenID connect token from the external
identity provider and authenticate with OpenStack API. Save it as openrc-oidcdeviceauthz.sh
and source it to set the environment variables. It will prompt you a device code url,
which you can use to authenticate with a web browser. After login to the external identity
provider and authorize the device code, you will get a keystone unscoped token, as shown
in the script, we store it to environment variables OS_TOKEN, with the token, then we use
*v3token* auth type. You can then use any OpenStack CLI supported commands to interact with
OpenStack API.


.. code-block:: sh

   #!/usr/bin/env bash
   _output=$(mktemp)
   export OS_AUTH_URL="https://identity.thedomain.com/v3"
   export OS_IDENTITY_API_VERSION=3
   export OS_PROJECT_NAME="user-project"
   export OS_PROJECT_DOMAIN_NAME="atmosphere"
   export OS_AUTH_TYPE="v3token"
   unset OS_TOKEN
   openstack token issue -f value -c id \
     --os-auth-type v3oidcdeviceauthz \
     --os-identity-provider atmosphere \
     --os-protocol openid \
     --os-code-challenge-method 'S256' \
     --os-discovery-endpoint https://keycloak.thedomain.com/realms/atmosphere/.well-known/openid-configuration \
     --os-client-id keystone \
     --os-client-secret anystring | tee -a $_output

   if [ -s $_output ]; then
     export OS_TOKEN=$(tail -1 $_output)
   fi
   rm -f $_output
