##############
Authentication
##############

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
    a project in atmosphere domain using OpenStack CLI. After all done, the user can login
    to OpenStack dashboard with Horizon redirect you to keycloak to login. If you want to
    use the user credentials with OpenStack CLI, then set your openrc-oidcpassword.rc like
    below.

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
   export OS_ACCESS_TOKEN_ENDPOINT=https://keycloak.thedomain.com/realms/atmosphere/protocol/openid-connect/token

The above configuration work with the default installation of Atmosphere which creates an
domain *atmosphere* and integrate it with the keycloak server through OIDC protocol. If you
use a different domain name, then replace the domain name and identity provider in the above
configuration.


.. admonition:: Atmosphere version requirement
    :class: warning

    To utilize this authentication type with OpenStackClient, you must ensure that the
    Atmosphere version is one of the following or later:

    - **4.2.12**
    - **3.2.12**
    - **2.2.11**
    - **1.13.11**


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

.. admonition:: Atmosphere version requirement
    :class: warning

    To utilize this authentication type with OpenStackClient, you must ensure that the
    Atmosphere version is one of the following or later:

    - **4.2.12**
    - **3.2.12**
    - **2.2.11**
    - **1.13.11**
