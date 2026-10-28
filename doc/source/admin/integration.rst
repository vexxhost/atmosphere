#################
Integration Guide
#################

This section provides detailed instructions on integrating external systems
and services with Atmosphere, enhancing functionality and streamlining workflows.

********
Keycloak
********

Keycloak serves as a comprehensive identity and access management solution,
facilitating the integration of various identity providers for centralized user
authentication and authorization. By leveraging federated identity, Keycloak enables
seamless Single Sign-On (SSO) capabilities across a suite of applications, enhancing
the user experience and bolstering security measures.

Identity Providers
==================

Incorporating identity providers into Keycloak allows users to authenticate via trusted
external sources. This federated authentication scheme simplifies the login process by
using existing credentials, whether from enterprise directories like LDAP or other
identity services.

Azure AD
--------

Azure AD is recognized for its extensive adoption and integration within the enterprise
ecosystem, offers a secure and familiar authentication method for countless users.

You can begin the integration process by creating an application registration in Azure AD
and configuring the necessary settings in Keycloak. The following steps outline the
procedure:

1. Sign in to the Azure portal and access the **Azure Active Directory** service.
2. Navigate to **App registrations** and click **New registration**.
3. Fill in the application name, select the account types it will serve, and
   specify a **Redirect URI**.

At this point, you'll need to grab the **Redirect URI** from the Keycloak client settings
using the following steps:

1. Log into the Keycloak admin console using your administrator credentials.
2. Switch to the ``atmosphere`` realm where you'll be configuring Azure AD.
3. In the **Identity Providers** section, select **Add provider** and choose **Microsoft**.
4. Keycloak will generate a **Redirect URI** which you will use in the Azure AD
   application registration process to ensure that authentication responses are
   correctly routed.

At this point, you'll be able to finalize the Azure AD application registration by
following these remaining steps:

1. Return to the Azure AD application registration page and input the Redirect
   URI from Keycloak.
2. After the application is registered, navigate to **Certificates & secrets**
   to create a client secret.
3. Record the **Client ID** and **Client Secret** provided, as they will be
   needed to configure Keycloak.

At this point, you're ready to configure Keycloak with the Azure AD settings:

1. In the Keycloak admin console, navigate back to the `atmosphere` realm's
   **Identity Providers** section.
2. For the Microsoft provider configuration, enter the **Client ID** and
   **Client Secret** obtained from Azure AD.
3. Adjust any additional settings according to your requirements, such as the
   default scopes, mappers, and other provider-specific configurations.
4. Save your changes to finalize the integration.

By integrating Azure AD with Keycloak, you enable users to authenticate with
their corporate credentials across all applications that are secured by
Keycloak. This provides a consistent and secure user experience, leveraging
the robust features of Azure AD within the flexible framework of Keycloak.

For a deeper dive into the Azure AD configuration within Keycloak, consult the
`Keycloak Microsoft Identity Provider documentation <https://www.keycloak.org/docs/latest/server_admin/#_microsoft>`_.

*********************
Neutron Policy Server
*********************

The `Neutron Policy Server <https://github.com/vexxhost/neutron-policy-server>`_
provides policy checks that need more context than the Neutron policy file can
express, such as looking up other ports or security groups in the database.

The checks are installed in the Neutron image and run inside the Neutron API
server as ``oslo.policy`` rule checks, so they add no extra service or network
round trip. They are referenced in the Neutron policy file like this:

.. list-table::
   :header-rows: 1

   * - Check
     - Purpose
   * - ``address_pair:strict=1``
     - Only allow allowed address pairs that point to addresses of ports in
       the same network and project.
   * - ``port_update:strict=1``
     - Block changes to the IP or MAC address of a port that another port uses
       as an allowed address pair.
   * - ``port_delete:strict=1``
     - Block deleting a port that another port uses as an allowed address pair.
   * - ``quarantine:security_group=quarantine``
     - Block project members from changing the security groups, allowed address
       pairs or port security of a quarantined port.

With ``strict=0``, the address pair checks compare only IP addresses and ignore
MAC addresses.

By default, the policy server checks are enabled and the Neutron policy is
updated to include them. In order to disable them, set the
``neutron_policy_server_integration_enabled`` variable to ``false`` in the
deployment configuration.

Quarantining an instance
========================

A port is quarantined when it has a security group named ``quarantine`` that
belongs to a different project than the port. Project members cannot attach
security groups from other projects to their ports, so only an administrator
can place a port in quarantine.

To quarantine an instance:

#. As an administrator, create a security group named ``quarantine`` in an
   administrative project, with rules that allow only the traffic you need,
   such as access from a security operations network.
#. Replace all security groups on each of the instance's ports with the
   ``quarantine`` security group. Don't leave the project's own security groups
   on the port, since project members can still change their rules.
#. Lock the instance so that project members cannot attach or detach network
   interfaces.

To release the instance, an administrator restores the original security groups
on its ports and unlocks it.
