# Operations guide


This guide intends to provide the user with some of the most basic
operations in an environment deployed using Atmosphere. It includes
processes to help troubleshoot issues, scaling in and out, and adding
new components.


## Configuring and Customizing Deployment

Atmosphere lets you define your deployment layout using simple YAML files to define ansible
inventories. Normally, a directory structure would look like this:

```yaml
   <env>/group_vars/all
   <env>/hosts.ini
```

Where `hosts.ini` is the primary inventory file that typically contains definitions for controllers, cephs, and computes.

Inside `group_vars` you can set the groups accordingly to your needs. You can create yml files for `all/all.yml` with all overrides in one place or organize files by services,
just for a comprehensive way of setting overrides for each service you want. For example, let's define the endpoints for the environment as follows:

```yaml
   # cat group_vars/all/endpoints.yml
   # ---
   # openstack_helm_endpoints_region_name: <region name>
   # openstack_helm_endpoints_keystone_api_host: <identity endpoint>
```

To check which values you can override for every chart, please check the [roles](https://github.com/vexxhost/atmosphere/tree/main/roles) and
their respective charts.

## Add and Remove Compute nodes


### Add Compute node


To add a new compute node to your environment, the first thing that the operator needs to do is add it to the ansible inventory and check connectivity:

```yaml
   $ ansible -m ping <node>  -i inventory/hosts.ini

   Example:
   $ ansible -m ping <hostname> -i inventory/hosts.ini
   <hostname> | SUCCESS => {
   "ansible_facts": {
      "discovered_interpreter_python": "/usr/bin/python3"
       },
      "changed": false,
      "ping": "pong"
   }
```

Once that is working correctly, we should just run the [kubernetes.yml](https://github.com/vexxhost/atmosphere/blob/main/playbooks/kubernetes.yml)
playbook targeting the new node

```yaml
   ansible-playbook playbooks/kubernetes.yml --limit <node> -i inventory/hosts.ini
```

Check if the node is `Ready` after playbook execution:

```yaml
   kubectl get nodes
```

Check the progress of the deployment, and once it is completed successfully, you can see your new compute available on Openstack:

```yaml
   watch -n1 kubectl -n openstack get po -owide | grep <node>
```

### Remove Compute node


To remove a compute node, the operator should first ensure the compute is empty and disabled in OpenStack.

Once that is checked, we should remove the kubernetes node from the deployment:

On the target node to be removed, let's stop kubelet process:

```yaml
   # systemctl stop kubelet
``` 

Then we should properly remove the node from Kubernetes infrastructure:

```yaml
   # kubectl delete node/<node>
````

The last step should be taken inside OpenStack, such as removing the compute and network agents:

```yaml
   # openstack compute service delete <service> ( service should be the compute service ID )
   # openstack network agent delete <network-agent> ( network-agent should be the agent ID )
````

## Renewing Kubernetes Certificates

Once Kubernetes is deployed on your environment, its certificates are valid for one year unless an upgrade is done on the cluster.

If you have proactive monitoring with [kube-prometheus-stack](https://github.com/vexxhost/atmosphere/tree/main/roles/kube_prometheus_stack), there is
an alert that checks once we get close to a Kubernetes [certificate expiration](https://github.com/prometheus-community/helm-charts/blob/9867df750ef5455365d6b1e82fee36dff63a0b0b/charts/kube-prometheus-stack/templates/prometheus/rules-1.14/kubernetes-system-apiserver.yaml#L28>)

If you don't want to upgrade your cluster, you can follow the steps below to renew your Kubernetes certificates:

**_NOTE_**: You need to run these commands on each controller.

```yaml
   # kubeadm alpha certs renew all
   # ps auxf | egrep ' (kube-(apiserver|controller-manager|scheduler)|etcd)' | awk '{ print $2 }' | xargs kill
```
For more details, check [kubernetes official documentation](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/).

## Configuring Monitoring


To be able to enable the [Kube Prometheus Stack](https://github.com/prometheus-community/helm-charts>) and fetch alerts from your environment,
you should configure overrides for the charts Atmosphere is currently using by creating a `group_vars/all/kube-prometheus-stack.yml`.
The `kube_prometheus_stack_values` variable can be used to override the values you want to.

The following example is a basic integration with opsgenie and alertmanager:

```yaml
   kube_prometheus_stack_values:
     alertmanager:
       config:
         route:
           receiver: opsgenie
           routes:
             - receiver: heartbeat
               matchers:
                 - alertname = "Watchdog"
               group_wait: 0s
               group_interval: 30s
               repeat_interval: 15s
         receivers:
           - name: opsgenie
             opsgenie_configs:
               - api_key: "{{ opsgenie_api_key }}"
           - name: heartbeat
             webhook_configs:
               - url: <opsgenie webhook url>
                 send_resolved: true
                 http_config:
                   basic_auth:
                     password: "{{ opsgenie_api_key }}"
     prometheus:
       prometheusSpec:
         additionalAlertManagerConfigs:
           - scheme: https
             basic_auth:
               username: alertmanager
               password: "{{ alertmanager_password }}"
             static_configs:
               - targets:
                   - <alertmanager url>
         externalLabels:
           region: <region>
           env: <env>
```
To apply the changes above, you need to run the [openstack.yml](https://github.com/vexxhost/atmosphere/blob/main/playbooks/openstack.yml) playbooks
using `--tag kube-prometheus-stack`.

## Checking logs

The operator can retrieve the logs of applications inside the Kubernetes cluster typically using the command:

```yaml
   kubectl -n <namespace> logs <component> <container>
```

Following this way, you might not get all the logs that are happening on each particular pod inside a service. However, there is a tool called [kail](https://github.com/boz/kail)
which streams logs from all containers of all matched pods.
