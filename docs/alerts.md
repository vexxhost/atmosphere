# Alerts

## `etcdDatabaseHighFragmentationRatio`

```console
kubectl -n kube-system exec svc/kube-prometheus-stack-kube-etcd -- \
  etcdctl defrag \
  --cluster \
  --cacert /etc/kubernetes/pki/etcd/ca.crt \
  --key /etc/kubernetes/pki/etcd/server.key \
  --cert /etc/kubernetes/pki/etcd/server.crt
```
