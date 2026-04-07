# `keystone`

## Integrating with LDAP

### FreeIPA

You can use the following values as an example for configuring Keystone to
use FreeIPA for the `contoso` domain inside Keystone.

```yaml
keystone_helm_values:
  conf:
    ks_domains:
      contoso:
        identity:
          driver: ldap
        ldap:
          url: ldaps://ipa.contoso.com
          user: uid=keystone,cn=users,cn=accounts,dc=contoso,dc=com
          password: secret123
          suffix: dc=contoso,dc=com
          user_tree_dn: cn=users,cn=accounts,dc=contoso,dc=com
          user_objectclass: person
          # user_filter: (memberOf=cn=openstack,cn=groups,cn=accounts,dc=contoso,dc=com)
          user_id_attribute: uid
          user_name_attribute: uid
          user_enabled_attribute: nsAccountLock
          user_enabled_default: false
          user_enabled_invert: true
          group_tree_dn: cn=groups,cn=accounts,dc=contoso,dc=com
          # group_filter: (cn=openstack-*)
          group_name_attribute: cn
```

> **Note**
>
> The `user_filter` and `group_filter` are commented out because they are
> optional if you want to limit the users and groups that Keystone will use.
