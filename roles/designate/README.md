# `designate`

## PowerDNS

### Pre-requisites

You have to install a PowerDNS server first, this is outside the scope of this
document.  You can review instructions on how to prepare the PowerDNS server
through the [Designate](https://docs.openstack.org/designate/latest/admin/backends/pdns4.html)
documentation.

### Configuration

You will need to configure your PowerDNS server to allow the Designate API to
talk to it.  This is done by adding the following to your PowerDNS configuration
into your inventory file.

In this example, PowerDNS will be configured to validate if the DNS changes have
been propagated to all DNS servers by hitting the PowerDNS backend.  It will
use the virtual IP address of the cloud to request AXFRs.

In this example, it's assumed that the PowerDNS server is running at `192.168.1.10`
and reachable by the Kubernetes cluster using `secret123` as the token.

!!! note

    You will need to make sure you configure your Glue DNS records with your
    registrar to point towards your PowerDNS instances (also frequently called
    "registering nameservers").  This is out of the scope of this document.

```yaml
designate_pools:
  - name: default
    description: Default PowerDNS Pool

    ns_records:
      - hostname: ns1.example.com.
        priority: 1
      - hostname: ns2.example.com.
        priority: 2

    nameservers:
      - host: 192.168.1.10
        port: 53

    targets:
      - type: pdns4
        description: PowerDNS4 DNS Server
        masters:
          - host: "{{ keepalived_vip }}"
            port: 5354
        options:
          host: 192.168.1.10
          port: 53
          api_endpoint: http://192.168.1.10:8081
          api_token: secret123
```

## Bind9

### Pre-requisites

You have to install a Bind9 server first, this is outside the scope of this
document.  You can review instructions on how to prepare the Bind9 server
through the [Designate](https://docs.openstack.org/designate/latest/admin/backends/bind9.html)
documentation.

### Configuration

You will need to configure your Bind9 server to allow the Designate API to
talk to it.

In this example, Designate will be configured to validate if the DNS changes have
been propagated to all DNS servers by hitting the Bind9 backend.  It will
use the virtual IP address of the cloud to request AXFRs.

In this example, it's assumed that the Bind9 server is running at `192.168.1.10`
and reachable by the Kubernetes cluster.

You have to create a secret for `rndc.key` file in the Kubernetes cluster first.
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: bind9-rndc-key
  namespace: openstack
stringData:
  rndc.key: |
    key "rndc-key" {
        algorithm hmac-md5;
        secret "<b64-encoded string>";
    };
```

!!! note

    You will need to make sure you configure your Glue DNS records with your
    registrar to point towards your Bind9 instances (also frequently called
    "registering nameservers").  This is out of the scope of this document.

```yaml
designate_helm_values:
  pod:
    mounts:
      designate_worker:
        init_container: null
        designate_worker:
          volumeMounts:
            - name: rndc-key
              mountPath: /etc/designate/rndc.key
              subPath: rndc.key
              readOnly: true
          volumes:
            - name: rndc-key
              secret:
                secretName: bind9-rndc-key
                defaultMode: 0444
designate_pools:
  - name: default
    description: Default Bind9 Pool

    ns_records:
      - hostname: ns1.example.com.
        priority: 1
      - hostname: ns2.example.com.
        priority: 2

    nameservers:
      - host: 192.168.1.10
        port: 53

    targets:
      - type: bind9
        description: BIND9 DNS Server
        masters:
          - host: "{{ keepalived_vip }}"
            port: 5354
        options:
          host: 192.168.1.10
          port: 53
          rndc_host: 192.168.1.10
          rndc_port: 953
          rndc_key_file: /etc/designate/rndc.key
          clean_zonefile: false
```
