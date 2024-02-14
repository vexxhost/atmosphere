# Keycloak

Keycloak serves as a comprehensive identity and access management solution, facilitating the integration of various identity providers for centralized user authentication and authorization. By leveraging federated identity, Keycloak enables seamless Single Sign-On (SSO) capabilities across a suite of applications, enhancing the user experience and bolstering security measures.

## Identity Providers

Incorporating identity providers into Keycloak allows users to authenticate via trusted external sources. This federated authentication scheme simplifies the login process by using existing credentials, whether from enterprise directories like LDAP or other identity services.

### Azure AD

Azure AD is recognized for its extensive adoption and integration within the enterprise ecosystem, offers a secure and familiar authentication method for countless users.

#### Create an Application Registration

##### Begin the Application Registration Process

1. Sign in to the Azure portal and access the **Azure Active Directory** service.
2. Navigate to **App registrations** and click **New registration**.
3. Fill in the application name, select the account types it will serve, and specify a **Redirect URI**.

##### Obtain the Redirect URI from Keycloak

1. Log into the Keycloak admin console using your administrator credentials.
2. Switch to the `atmosphere` realm where you'll be configuring Azure AD.
3. In the **Identity Providers** section, select **Add provider** and choose **Microsoft**.
4. Keycloak will generate a **Redirect URI** which you will use in the Azure AD application registration process to ensure that authentication responses are correctly routed.

##### Finalize Azure AD Application Registration

1. Return to the Azure AD application registration page and input the Redirect URI from Keycloak.
2. After the application is registered, navigate to **Certificates & secrets** to create a client secret.
3. Record the **Client ID** and **Client Secret** provided, as they will be needed to configure Keycloak.

#### Configure Keycloak

With the Client ID and Client Secret in hand, you can now set up Keycloak to use Azure AD as an identity provider.

1. In the Keycloak admin console, navigate back to the `atmosphere` realm's **Identity Providers** section.
2. For the Microsoft provider configuration, enter the **Client ID** and **Client Secret** obtained from Azure AD.
3. Adjust any additional settings according to your requirements, such as the default scopes, mappers, and other provider-specific configurations.
4. Save your changes to finalize the integration.

By integrating Azure AD with Keycloak, you enable users to authenticate with their corporate credentials across all applications that are secured by Keycloak. This provides a consistent and secure user experience, leveraging the robust features of Azure AD within the flexible framework of Keycloak. For a deeper dive into the Azure AD configuration within Keycloak, consult the [Keycloak Microsoft Identity Provider documentation](https://www.keycloak.org/docs/latest/server_admin/#_microsoft).
