ansible-playbook -i localhost demo/playbook.yml

```yaml
$ kubectl get memcacheds example-memcached -o yaml  

apiVersion: cache.example.com/v1alpha1
kind: Memcached
  name: example-memcached
  namespace: default
  selfLink: /apis/cache.example.com/v1alpha1/namespaces/default/memcacheds/example-memcached
  uid: 2a94ff2b-84e0-40ce-8b5e-2b7e4d2bc0e2
status:
  conditions:
  - ansibleResult:
      changed: 0
      completion: 2019-10-16T13:23:21.64021
      failures: 0
      ok: 3
      skipped: 0
    lastTransitionTime: "2019-10-15T13:26:58Z"
    message: Awaiting next reconciliation
    reason: Successful
    status: "True"
    type: Running
  diditwork: why yes it did
```
