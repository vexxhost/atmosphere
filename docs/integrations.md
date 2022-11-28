# Integrations

## OpsGenie

Atmosphere can be integrated with OpsGenie in order to send all alerts to it,
this is useful if you want to have a single place to manage all your alerts.

In order to get started, you will need to complete the following steps inside
OpsGenie:

1. Create an integration inside OpsGenie, you can do this by going to
   _Settings_ > _Integrations_ > _Add Integration_ and selecting _Prometheus_.
2. Copy the API key that is generated for you and setup correct assignment
   rules inside OpsGenie.
3. Create a new heartbeat inside OpsGenie, you can do this by going to
   _Settings_ > _Heartbeats_ > _Create Heartbeat_.  Set the interval to 1 minute.

Afterwards, you can configure the following options for the Atmosphere config:

```yaml
atmosphere_opsgenie_config:
  enabled: true
  api_key: <your-api-key>
  heartbeat_name: <your-heartbeat-name>
```

Once this is done and deployed, you'll start to see alerts inside OpsGenie and
you can also verify that the heartbeat is listed as _ACTIVE_.
