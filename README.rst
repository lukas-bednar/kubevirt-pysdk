KubeVirt Python SDK
===================

Requirements
------------

* kubernetes

Usage
-----

.. code:: python

  from pprint import pprint
  from kubernetes import config
  from kubevirt import KubeVirtClient

  NAMESPACE = "default"

  kubeconfig = 'path/to/.kubeconfig'
  config.load_kube_config(kubeconfig)

  c = KubeVirtClient()
  vm_list = c.list_namespaced_vm(NAMESPACE)
  pprint(vm_list)
  # {'apiVersion': 'kubevirt.io/v1alpha1',
  #  'items': [{'apiVersion': 'kubevirt.io/v1alpha1',
  #             'kind': 'VM',
  #             'metadata': {'clusterName': '',
  #                          'name': 'testvm',
  #                          'namespace': 'default',
  #                          'selfLink': '/apis/kubevirt.io/v1alpha1/namespaces/default/vms/testvm',
  #             }
  #             spec: {...},
  #             ....
  #             'status': {
  #                         ...
  #                        'phase': 'Running'}}],
  #  'kind': 'VMList',
  #  'metadata': {'resourceVersion': '1914224',
  #               'selfLink': '/apis/kubevirt.io/v1alpha1/namespaces/default/vms'}}
```
