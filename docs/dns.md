# DNS

## PowerDNS
### Pre-requisites
You have to instal a PowerDNS server first. PowerDNS server installation is out of the scope.
### Deploy Designate
You have to configure your PowerDNS information as designate pools by using the variable `openstack_helm_designate_pools`.
In this example, `165.231.78.211`, `53` and `8081` are the IP, DNS port and API port of the PowerDNS server. Please use your exact information.
```yaml
openstack_helm_designate_pools: |
  - name: default
    attributes: {}
    ns_records:
    - "hostname": "ns1.example.com."
      "priority": 1
    # List out the nameservers for this pool. These are the actual DNS servers.
    # We use these to verify changes have propagated to all nameservers.
    nameservers:
      - host: 165.231.78.211
        port: 53
    # List out the targets for this pool. For BIND there will be one
    # entry for each BIND server, as we have to run rndc command on each server
    targets:
      - type: pdns4
        description: PowerDNS Server
        # MiniDNS Configuration options
        masters:
          - host: minidns
            port: 5354
        # PowerDNS Configuration options
        options:
          host: 165.231.78.211
          port: 53
          api_endpoint: http://165.231.78.211:8081
          api_token: REPLACE_ME_WITH_API_TOKEN
```
