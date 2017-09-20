import time
from functools import wraps

from urllib3.exceptions import ReadTimeoutError
from kubernetes import client, watch

from kubevirt.errors import (
    EntityNotFound,
    ConflictingEntities,
    WaitForTimeout,
    WaitForFailureMatch,
)


DEFAULT_GROUP = "kubevirt.io"
DEFAULT_VERSION = "v1alpha1"
DEFAULT_NAMESPACE = "default"


VMS_RESOURCE = "virtualmachines"
MIGRATIONS_RESOURCE = "migrations"


def entity_common_error_wrapper(f):
    @wraps(f)
    def wrapper(self, name, *args, **kwargs):
        try:
            return f(self, name, *args, **kwargs)
        except client.rest.ApiException as ex:
            if ex.status == 404:
                raise EntityNotFound(
                    "%s/%s/%s" % (self._ns, self._plural, name), ex)
            if ex.status == 409:
                raise ConflictingEntities(
                    "%s/%s/%s" % (self._ns, self._plural, name), ex)
            else:
                raise
    return wrapper


class KubeVirtNamespace(object):
    def __init__(self, group, version, namespace):
        self.group = group
        self.version = version
        self.ns = namespace

    def __str__(self):
        return "ns:%s/%s/%s" % (self.group, self.version, self.ns)


class KubeVirtNamespacedObject(object):

    def __init__(self, client, namespace, plular):
        self._c = client
        self._ns = namespace
        self._plural = plular

    @entity_common_error_wrapper
    def get(self, name, **kwargs):
        return self._c.get_namespaced_custom_object(
            self._ns.group, self._ns.version, self._ns.ns, self._plural, name,
            **kwargs
        )

    @entity_common_error_wrapper
    def delete(self, name, **kwargs):
        k = kwargs.copy()
        if 'body' not in k:
            k['body'] = client.V1DeleteOptions()
        return self._c.delete_namespaced_custom_object(
            self._ns.group, self._ns.version, self._ns.ns, self._plural, name,
            **k
        )

    def create(self, obj, **kwargs):
        return self._c.create_namespaced_custom_object(
            self._ns.group, self._ns.version, self._ns.ns, self._plural, obj,
            **kwargs
        )

    def list(self, **kwargs):
        result = self._c.list_namespaced_custom_object(
            self._ns.group, self._ns.version, self._ns.ns, self._plural,
            **kwargs
        )
        return result

    def _watch(self, event_source, request_timeout=None):
        kw = dict()
        if request_timeout:
            kw['_request_timeout'] = request_timeout
        w = watch.Watch()
        try:
            for e in w.stream(event_source, **kw):
                yield e
        except GeneratorExit:
            w.stop()
            raise

    def watch(self, request_timeout=None):
        return self._watch(self.list, request_timeout)

    def _wait_for_x(
        self, timeout, filter_condition, success_condition, failure_condition
    ):
        step = 5  # 5s
        endtime = timeout + time.time()
        while timeout < endtime:
            try:
                for e in self._watch(self.list, request_timeout=step):
                    if not filter_condition(e):
                        continue
                    if success_condition(e):
                        return e['object']
                    if failure_condition(e):
                        raise WaitForFailureMatch(e)
            except ReadTimeoutError:
                continue
        raise WaitForTimeout(str(self._ns), self.timeout)

    def wait_for_item(
        self, name, timeout, success_condition,
        failure_condition=lambda e: False
    ):
        return self._wait_for_x(
            timeout,
            lambda e: e['object'].get('metadata', dict()).get('name') == name,
            success_condition, failure_condition
        )

    def wait_for(
        self, timeout, success_condition, failure_condition=lambda e: False
    ):
        return self._wait_for_x(
            self.list, timeout, lambda e: True, success_condition,
            failure_condition
        )


class KubeVirtClient(object):

    def __init__(self, c=None, group=DEFAULT_GROUP, version=DEFAULT_VERSION):
        if c is None:
            c = client.CustomObjectsApi()
        self._c = c
        self._group = group
        self._version = version

    def _get_namespace(self, name):
        return KubeVirtNamespace(self._group, self._version, name)

    def _get_resource(self, name, namespace=None):
        if namespace is None:
            namespace = DEFAULT_NAMESPACE
        return KubeVirtNamespacedObject(
            self._c, self._get_namespace(namespace), name
        )

    def list_namespaced_vm(self, namespace, **kwargs):
        vms_r = self._get_resource(VMS_RESOURCE, namespace)
        return vms_r.list(**kwargs)

    def create_namespaced_vm(self, namespace, body, **kwargs):
        vms_r = self._get_resource(VMS_RESOURCE, namespace)
        return vms_r.create(body, **kwargs)

    def delete_namespaced_vm(self, namespace, name, **kwargs):
        vms_r = self._get_resource(VMS_RESOURCE, namespace)
        return vms_r.delete(name, **kwargs)

    def list_namespaced_migration(self, namespace, **kwargs):
        mg_r = self._get_resource(MIGRATIONS_RESOURCE, namespace)
        return mg_r.list(**kwargs)

    def create_namespaced_migration(self, namespace, body, **kwargs):
        mg_r = self._get_resource(MIGRATIONS_RESOURCE, namespace)
        return mg_r.create(body, **kwargs)

    def delete_namespaced_migration(self, namespace, name, **kwargs):
        mg_r = self._get_resource(MIGRATIONS_RESOURCE, namespace)
        return mg_r.delete(name, **kwargs)
