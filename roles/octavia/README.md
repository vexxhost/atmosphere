# `octavia`

## Health manager interface MTU

Set `octavia_health_manager_interface_mtu` when the Octavia management
network uses an MTU that differs from the Open vSwitch default. Atmosphere
configures the DHCP client, the Linux `o-hm0` interface, and the Open vSwitch
`mtu_request` value:

```yaml
octavia_health_manager_interface_mtu: 9000
```
