# Certificates

## Manual certificate renewal
To renew certificates manually, run the following commands on all the control-plane nodes.

- Renew your all certificates.
```sh
kubeadm certs renew all
```
- After running the command you should restart the control plane Pods. This is required since dynamic certificate reload is currently not supported for all components and certificates. Static Pods are managed by the local kubelet and not by the API Server, thus kubectl cannot be used to delete and restart them.
```sh
ps auxf | egrep '(kube-(apiserver|controller-manager|scheduler)|etcd)' | awk '{ print $2 }' | xargs kill
```
