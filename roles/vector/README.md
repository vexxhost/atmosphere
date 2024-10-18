# `vector`

This role installs and configures [Vector](https://vector.dev/) to collect all
logs from the hosts and send them to a central location, which is configured
to be the built-in Loki instance.

## Send logs to syslog server

It is possilbe to send logs to a syslog server which has the reception enabled
via socket. You will need to simply set the following inventory variables.


```yaml
vector_helm_values:
  customConfig:
    transforms:
      syslog_logs:
        type: remap
        inputs: ["kubernetes_logs"]
        # let's make RFC 5424 compatible messages for rsyslog
        # read more about the format:
        # https://blog.datalust.co/seq-input-syslog/#rfc5424
        source: |-
          pri = 1 * 8 + to_syslog_severity(.severity) ?? 6

          ., err = join([
            "<" + to_string(pri) + ">" + "1",     # <pri>version
            to_string!(.@timestamp),
            to_string!(.kubernetes.pod_name || .hostname || "${VECTOR_SELF_NODE_NAME}"),
            to_string!(.app || .kubernetes.labels.app || "-"),
            "-",                                  # procid
            to_string!(.messageid || "-"),        # msgid
            "-",                                  # structured-data
            decode_base16!("EFBBBF") + to_string!(.message || encode_json(.))   # msg
          ], separator: " ")

          if err != null {
            log("Unable to construct syslog message for event:" + err + ". Dropping invalid event: " + encode_json(.), level: "error", rate_limit_secs: 10)
          }
    sinks:
      rsyslog_general:
        type: "socket"
        inputs: [syslog_logs]
        # rsyslog server address
        address: "38.108.68.134:514"
        # tcp or udp
        mode: "tcp"
        encoding:
          codec: "text"
        framing:
          method: "newline_delimited"
```
